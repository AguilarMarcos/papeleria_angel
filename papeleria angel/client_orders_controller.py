# client_orders_controller.py - VERSIÓN CORREGIDA
import mysql.connector
from database import conectar
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _validar_fecha(fecha_str):
    if not fecha_str:
        return None
    fecha_str = fecha_str.strip()
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        try:
            return datetime.strptime(fecha_str, "%Y/%m/%d").strftime("%Y-%m-%d")
        except:
            return None


def _determinar_estado(total, abono, tolerancia=0.01):
    total = _safe_float(total)
    abono = _safe_float(abono)

    if abono >= total - tolerancia:
        return 'Completado'
    elif abono > tolerancia:
        return 'Abonado'
    else:
        return 'Pendiente'


# ============================================================
# CRUD
# ============================================================

def obtener_pedidos_cliente():
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                pc.id,
                c.nombre AS cliente_nombre,
                c.apellido AS cliente_apellido,
                pc.fecha_pedido,
                pc.fecha_entrega_estimada,
                pc.total AS total_pedido,
                (SELECT IFNULL(SUM(monto), 0) FROM abonos WHERE pedido_cliente_id = pc.id) AS abonado
            FROM pedidos_cliente pc
            INNER JOIN clientes c ON pc.cliente_id = c.id
            ORDER BY pc.fecha_pedido DESC;
        """
        cursor.execute(query)
        pedidos = cursor.fetchall()

        for pedido in pedidos:
            pedido['estado_actual'] = _determinar_estado(
                pedido['total_pedido'], 
                pedido['abonado']
            )
            pedido['cliente_nombre_completo'] = f"{pedido['cliente_nombre']} {pedido['cliente_apellido']}"

        return pedidos

    except mysql.connector.Error as e:
        logger.error(f"Error MySQL: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


def obtener_abonos_pedido(pedido_id):
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT a.id, a.fecha_abono, a.monto, a.metodo_pago,
                   u.nombre AS usuario_cajero
            FROM abonos a
            INNER JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.pedido_cliente_id = %s
            ORDER BY a.fecha_abono ASC;
        """
        cursor.execute(query, (pedido_id,))
        return cursor.fetchall()

    except mysql.connector.Error as e:
        logger.error(f"Error MySQL: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


def registrar_pedido_cliente(cliente_id, fecha_entrega_estimada_str, total_pedido, anticipo=0):
    conn = None
    cursor = None

    fecha_entrega = _validar_fecha(fecha_entrega_estimada_str)
    total = _safe_float(total_pedido)
    anticipo = _safe_float(anticipo)

    if total <= 0:
        return False, "El total debe ser mayor a 0."

    try:
        conn = conectar()
        cursor = conn.cursor()

        fecha_pedido = datetime.now().strftime('%Y-%m-%d')

        # Insert sin columna inexistente "abonado"
        query_pedido = """
            INSERT INTO pedidos_cliente (cliente_id, fecha_pedido, fecha_entrega_estimada, total, estado)
            VALUES (%s, %s, %s, %s, %s)
        """
        estado_inicial = _determinar_estado(total, anticipo)
        cursor.execute(query_pedido, (cliente_id, fecha_pedido, fecha_entrega, total, estado_inicial))
        pedido_id = cursor.lastrowid

        # Registrar anticipo si existe
        if anticipo > 0.01:
            cursor.execute("""
                INSERT INTO abonos (pedido_cliente_id, fecha_abono, monto, metodo_pago, usuario_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (pedido_id, fecha_pedido, anticipo, "Anticipo", 1))

        conn.commit()
        return True, f"Pedido #{pedido_id} registrado."

    except mysql.connector.Error as e:
        conn.rollback()
        return False, f"Error MySQL: {e}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


def registrar_abono(pedido_id, monto, metodo, usuario_id):
    conn = None
    cursor = None
    monto = _safe_float(monto)

    if monto <= 0:
        return False, "El abono debe ser mayor a 0."

    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)

        # Obtener total
        cursor.execute("SELECT total FROM pedidos_cliente WHERE id = %s", (pedido_id,))
        pedido = cursor.fetchone()
        if not pedido:
            return False, "Pedido no encontrado."

        total = _safe_float(pedido["total"])

        # SUMA REAL de abonos (fix)
        cursor.execute("SELECT IFNULL(SUM(monto), 0) AS abonado FROM abonos WHERE pedido_cliente_id = %s",
                       (pedido_id,))
        abono_actual = _safe_float(cursor.fetchone()["abonado"])

        pendiente = total - abono_actual
        if monto > pendiente + 0.01:
            return False, f"El abono excede el pendiente (${pendiente:.2f})."

        # Insertar el abono
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO abonos (pedido_cliente_id, fecha_abono, monto, metodo_pago, usuario_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (pedido_id, fecha, monto, metodo, usuario_id))

        # Recalcular estado
        nuevo_abono = abono_actual + monto
        nuevo_estado = _determinar_estado(total, nuevo_abono)

        cursor.execute("UPDATE pedidos_cliente SET estado = %s WHERE id = %s",
                       (nuevo_estado, pedido_id))

        conn.commit()
        return True, f"Abono registrado. Estado: {nuevo_estado}"

    except mysql.connector.Error as e:
        conn.rollback()
        return False, f"Error MySQL: {e}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


def eliminar_pedido_cliente(pedido_id):
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        # Verificar si existe
        cursor.execute("SELECT id FROM pedidos_cliente WHERE id = %s", (pedido_id,))
        if not cursor.fetchone():
            return False, "Pedido no existe."

        # Eliminar dependencias
        cursor.execute("DELETE FROM abonos WHERE pedido_cliente_id = %s", (pedido_id,))
        cursor.execute("DELETE FROM detalle_pedido_cliente WHERE pedido_id = %s", (pedido_id,))

        # Eliminar pedido
        cursor.execute("DELETE FROM pedidos_cliente WHERE id = %s", (pedido_id,))

        conn.commit()
        return True, "Pedido eliminado."

    except mysql.connector.Error as e:
        conn.rollback()
        return False, f"Error MySQL: {e}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
