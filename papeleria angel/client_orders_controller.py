# client_orders_controller.py
import mysql.connector
from database import conectar
from datetime import datetime
import logging

# Configuración de logging (ajusta según tu entorno)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
# client_orders_controller.py
import mysql.connector
from database import conectar
from datetime import datetime
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _safe_float(value, default=0.0):
    """Convierte cualquier valor a float, manejando None y cadenas."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _validar_fecha(fecha_str):
    """Valida y normaliza una fecha. Retorna YYYY-MM-DD o None."""
    if not fecha_str:
        return None
    try:
        fecha = datetime.strptime(fecha_str.strip(), "%Y-%m-%d")
        return fecha.strftime("%Y-%m-%d")
    except ValueError:
        try:
            fecha = datetime.strptime(fecha_str.strip(), "%Y/%m/%d")
            return fecha.strftime("%Y-%m-%d")
        except ValueError:
            return None


def _determinar_estado(total, abonado, tolerancia=0.01):
    """Determina el estado del pedido basado en total y abonado."""
    total = _safe_float(total)
    abonado = _safe_float(abonado)
    
    pendiente = round(total - abonado, 2)
    
    if pendiente <= tolerancia:  # ≤ 1 centavo
        return "Completado"
    elif abonado > 0:
        return "Abonado"
    else:
        return "Pendiente"


def registrar_pedido_simple(cliente_id, usuario_id, total, abono_inicial=0.00, descripcion="", fecha_entrega_estimada=None):
    """Registra un nuevo pedido con total y abono inicial. Todo en una transacción."""
    conn = None
    cursor = None
    
    try:
        cliente_id = int(cliente_id)
        usuario_id = int(usuario_id)
        total = _safe_float(total)
        abono_inicial = _safe_float(abono_inicial)
        descripcion = str(descripcion).strip()[:500]
        fecha_entrega = _validar_fecha(fecha_entrega_estimada)

        if total <= 0:
            return False, "❌ El total del encargo debe ser mayor a cero."
        if abono_inicial < 0:
            return False, "❌ El abono inicial no puede ser negativo."
        if abono_inicial > total + 0.01:
            return False, f"❌ El abono inicial (${abono_inicial:.2f}) no puede superar el total (${total:.2f})."

        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor()
        conn.start_transaction()

        fecha_pedido = datetime.now().strftime('%Y-%m-%d')
        total_abonado = round(abono_inicial, 2)
        estado = _determinar_estado(total, total_abonado)

        query_pedido = """
            INSERT INTO pedidos_cliente 
            (cliente_id, usuario_id, fecha_pedido, fecha_entrega_estimada, total, descripcion, total_abonado, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_pedido, (
            cliente_id, usuario_id, fecha_pedido, fecha_entrega,
            total, descripcion, total_abonado, estado
        ))
        pedido_id = cursor.lastrowid

        if abono_inicial > 0:
            fecha_abono = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            query_abono = "INSERT INTO abonos (pedido_cliente_id, monto, fecha_abono) VALUES (%s, %s, %s)"
            cursor.execute(query_abono, (pedido_id, round(abono_inicial, 2), fecha_abono))

        conn.commit()
        return True, f"✅ Encargo #{pedido_id} registrado. Total: ${total:.2f}. Abonado: ${abono_inicial:.2f}."

    except ValueError as ve:
        if conn:
            conn.rollback()
        logger.warning(f"Error de validación al registrar pedido: {ve}")
        return False, "❌ Error: Los valores deben ser numéricos y válidos."
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error MySQL al registrar pedido: {e}")
        return False, f"❌ Error al registrar encargo: {e.msg if hasattr(e, 'msg') else str(e)}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al registrar pedido")
        return False, "❌ Error inesperado al registrar el encargo."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def obtener_pedidos_cliente():
    """Obtiene todos los pedidos activos con información completa del cliente y usuario."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                pc.id,
                pc.fecha_pedido,
                pc.fecha_entrega_estimada,
                pc.total,
                pc.total_abonado,
                pc.estado,
                pc.descripcion,
                c.id AS cliente_id,
                c.nombre AS cliente_nombre,
                c.apellido AS cliente_apellido,
                c.telefono,
                u.id AS usuario_id,
                u.nombre AS usuario_nombre
            FROM pedidos_cliente pc
            INNER JOIN clientes c ON pc.cliente_id = c.id
            INNER JOIN usuarios u ON pc.usuario_id = u.id
            ORDER BY pc.fecha_pedido DESC, pc.id DESC
        """
        cursor.execute(query)
        pedidos = cursor.fetchall()

        for p in pedidos:
            p['cliente_nombre_completo'] = f"{p['cliente_nombre']} {p['cliente_apellido']}".strip()
            p['total'] = _safe_float(p['total'])
            p['total_abonado'] = _safe_float(p['total_abonado'])
            p['pendiente_pago'] = round(p['total'] - p['total_abonado'], 2)

        return pedidos

    except mysql.connector.Error as e:
        logger.error(f"Error MySQL al obtener pedidos: {e}")
        return []
    except Exception as e:
        logger.exception("Error inesperado al obtener pedidos")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def registrar_abono(pedido_cliente_id, monto):
    conn = None
    cursor = None
    try:
        pedido_cliente_id = int(pedido_cliente_id)
        monto = _safe_float(monto)

        if monto <= 0:
            return False, "❌ El monto del abono debe ser mayor a cero."

        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        cursor.execute("""
            SELECT id, total, total_abonado, estado
            FROM pedidos_cliente 
            WHERE id = %s AND estado != 'Cancelado'
            FOR UPDATE
        """, (pedido_cliente_id,))
        pedido = cursor.fetchone()

        if not pedido:
            return False, "❌ Pedido no encontrado o está cancelado."

        total = _safe_float(pedido['total'])
        total_abonado_actual = _safe_float(pedido['total_abonado'])
        nuevo_total_abonado = round(total_abonado_actual + monto, 2)

        if nuevo_total_abonado > total + 0.01:
            pendiente = round(total - total_abonado_actual, 2)
            return False, f"❌ El abono de ${monto:.2f} excede el saldo pendiente (${pendiente:.2f})."

        fecha_abono = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO abonos (pedido_cliente_id, monto, fecha_abono)
            VALUES (%s, %s, %s)
        """, (pedido_cliente_id, round(monto, 2), fecha_abono))

        nuevo_estado = _determinar_estado(total, nuevo_total_abonado)
        cursor.execute("""
            UPDATE pedidos_cliente 
            SET total_abonado = %s, estado = %s 
            WHERE id = %s
        """, (nuevo_total_abonado, nuevo_estado, pedido_cliente_id))

        conn.commit()
        return True, f"✅ Abono de ${monto:.2f} registrado. Estado: '{nuevo_estado}'."

    except ValueError:
        if conn:
            conn.rollback()
        return False, "❌ El monto debe ser un número válido."
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error MySQL al registrar abono: {e}")
        return False, f"❌ Error al registrar abono: {e.msg}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al registrar abono")
        return False, "❌ Error inesperado al registrar el abono."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def eliminar_pedido_cliente(pedido_id):
    """Elimina un pedido y sus abonos relacionados (hard delete)."""
    conn = None
    cursor = None
    try:
        pedido_id = int(pedido_id)
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor()
        conn.start_transaction()

        cursor.execute("SELECT id, estado FROM pedidos_cliente WHERE id = %s", (pedido_id,))
        pedido = cursor.fetchone()
        if not pedido:
            return False, "❌ Pedido no encontrado."

        cursor.execute("DELETE FROM abonos WHERE pedido_cliente_id = %s", (pedido_id,))
        cursor.execute("DELETE FROM pedidos_cliente WHERE id = %s", (pedido_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            return False, "❌ No se pudo eliminar el pedido (puede estar bloqueado)."

        conn.commit()
        return True, f"✅ Pedido #{pedido_id} y sus registros relacionados eliminados."

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error MySQL al eliminar pedido: {e}")
        return False, f"❌ Error al eliminar: {e.msg}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al eliminar pedido")
        return False, "❌ Error inesperado durante la eliminación."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def _safe_float(value, default=0.0):
    """Convierte cualquier valor a float, manejando None y cadenas."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _validar_fecha(fecha_str):
    """Valida y normaliza una fecha. Retorna YYYY-MM-DD o None."""
    if not fecha_str:
        return None
    try:
        # Acepta YYYY-MM-DD y también YYYY/MM/DD
        fecha = datetime.strptime(fecha_str.strip(), "%Y-%m-%d")
        return fecha.strftime("%Y-%m-%d")
    except ValueError:
        try:
            fecha = datetime.strptime(fecha_str.strip(), "%Y/%m/%d")
            return fecha.strftime("%Y-%m-%d")
        except ValueError:
            return None


def _determinar_estado(total, abonado, tolerancia=0.01):
    """Determina el estado del pedido basado en total y abonado."""
    total = _safe_float(total)
    abonado = _safe_float(abonado)
    
    pendiente = round(total - abonado, 2)
    
    if pendiente <= tolerancia:  # ≤ 1 centavo
        return "Completado"
    elif abonado > 0:
        return "Abonado"
    else:
        return "Pendiente"


# =================================================================
# CRUD: Pedidos de Clientes (SIMPLIFICADO)
# =================================================================

def registrar_pedido_simple(cliente_id, usuario_id, total, abono_inicial=0.00, descripcion="", fecha_entrega_estimada=None):
    """Registra un nuevo pedido con total y abono inicial. Todo en una transacción."""
    conn = None
    cursor = None
    
    try:
        # Validaciones de entrada
        cliente_id = int(cliente_id)
        usuario_id = int(usuario_id)
        total = _safe_float(total)
        abono_inicial = _safe_float(abono_inicial)
        descripcion = str(descripcion).strip()[:500]  # Límite de 500 chars
        fecha_entrega = _validar_fecha(fecha_entrega_estimada)

        if total <= 0:
            return False, "❌ El total del encargo debe ser mayor a cero."
        if abono_inicial < 0:
            return False, "❌ El abono inicial no puede ser negativo."
        if abono_inicial > total + 0.01:
            return False, f"❌ El abono inicial (${abono_inicial:.2f}) no puede superar el total (${total:.2f})."

        # Conexión
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor()

        # Fecha actual (solo fecha para el pedido, datetime para abonos)
        fecha_pedido = datetime.now().strftime('%Y-%m-%d')
        total_abonado = round(abono_inicial, 2)
        estado = _determinar_estado(total, total_abonado)

        # 🔒 Iniciar transacción explícita
        conn.start_transaction()

        # 1. Insertar pedido
        query_pedido = """
            INSERT INTO pedidos_cliente 
            (cliente_id, usuario_id, fecha_pedido, fecha_entrega_estimada, total, descripcion, total_abonado, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_pedido, (
            cliente_id, usuario_id, fecha_pedido, fecha_entrega,
            total, descripcion, total_abonado, estado
        ))
        pedido_id = cursor.lastrowid

        # 2. Registrar abono inicial (si > 0)
        if abono_inicial > 0:
            fecha_abono = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            query_abono = "INSERT INTO abonos (pedido_cliente_id, monto, fecha_abono) VALUES (%s, %s, %s)"
            cursor.execute(query_abono, (pedido_id, round(abono_inicial, 2), fecha_abono))

        # ✅ Confirmar transacción
        conn.commit()
        return True, f"✅ Encargo #{pedido_id} registrado. Total: ${total:.2f}. Abonado: ${abono_inicial:.2f}."

    except ValueError as ve:
        if conn:
            conn.rollback()
        logger.warning(f"Error de validación al registrar pedido: {ve}")
        return False, "❌ Error: Los valores deben ser numéricos y válidos."
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error MySQL al registrar pedido: {e}")
        return False, f"❌ Error al registrar encargo: {e.msg if hasattr(e, 'msg') else str(e)}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al registrar pedido")
        return False, "❌ Error inesperado al registrar el encargo."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def obtener_pedidos_cliente():
    """Obtiene todos los pedidos activos con información completa del cliente y usuario."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                pc.id,
                pc.fecha_pedido,
                pc.fecha_entrega_estimada,
                pc.total,
                pc.total_abonado,
                pc.estado,
                pc.descripcion,
                c.id AS cliente_id,
                c.nombre AS cliente_nombre,
                c.apellido AS cliente_apellido,
                c.telefono,
                u.id AS usuario_id,
                u.nombre AS usuario_nombre
            FROM pedidos_cliente pc
            INNER JOIN clientes c ON pc.cliente_id = c.id
            INNER JOIN usuarios u ON pc.usuario_id = u.id
            ORDER BY pc.fecha_pedido DESC, pc.id DESC
        """
        cursor.execute(query)
        pedidos = cursor.fetchall()

        # Procesar resultados
        for p in pedidos:
            # Combina nombre completo
            p['cliente_nombre_completo'] = f"{p['cliente_nombre']} {p['cliente_apellido']}".strip()
            # Convierte a float para cálculos seguros
            p['total'] = _safe_float(p['total'])
            p['total_abonado'] = _safe_float(p['total_abonado'])
            p['pendiente_pago'] = round(p['total'] - p['total_abonado'], 2)

        return pedidos

    except mysql.connector.Error as e:
        logger.error(f"Error MySQL al obtener pedidos: {e}")
        return []
    except Exception as e:
        logger.exception("Error inesperado al obtener pedidos")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def registrar_abono(pedido_cliente_id, monto):
    conn = None
    cursor = None
    try:
        pedido_cliente_id = int(pedido_cliente_id)
        monto = _safe_float(monto)

        if monto <= 0:
            return False, "❌ El monto del abono debe ser mayor a cero."

        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor(dictionary=True)

        # 🔒 Iniciar transacción
        conn.start_transaction()

        # 1. Obtener datos actuales del pedido
        cursor.execute("""
            SELECT id, total, total_abonado, estado
            FROM pedidos_cliente 
            WHERE id = %s AND estado != 'Cancelado'
            FOR UPDATE
        """, (pedido_cliente_id,))
        pedido = cursor.fetchone()

        if not pedido:
            return False, "❌ Pedido no encontrado o está cancelado."

        total = _safe_float(pedido['total'])
        total_abonado_actual = _safe_float(pedido['total_abonado'])
        nuevo_total_abonado = round(total_abonado_actual + monto, 2)

        # Validar límite
        if nuevo_total_abonado > total + 0.01:
            pendiente = round(total - total_abonado_actual, 2)
            return False, f"❌ El abono de ${monto:.2f} excede el saldo pendiente (${pendiente:.2f})."

        # 2. Insertar abono
        fecha_abono = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO abonos (pedido_cliente_id, monto, fecha_abono)
            VALUES (%s, %s, %s)
        """, (pedido_cliente_id, round(monto, 2), fecha_abono))

        # 3. Actualizar pedido
        nuevo_estado = _determinar_estado(total, nuevo_total_abonado)
        cursor.execute("""
            UPDATE pedidos_cliente 
            SET total_abonado = %s, estado = %s 
            WHERE id = %s
        """, (nuevo_total_abonado, nuevo_estado, pedido_cliente_id))

        conn.commit()
        return True, f"✅ Abono de ${monto:.2f} registrado. Estado: '{nuevo_estado}'."

    except ValueError:
        if conn:
            conn.rollback()
        return False, "❌ El monto debe ser un número válido."
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error MySQL al registrar abono: {e}")
        return False, f"❌ Error al registrar abono: {e.msg}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al registrar abono")
        return False, "❌ Error inesperado al registrar el abono."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def obtener_abonos_pedido(pedido_id):
    """Obtiene el historial de abonos para un pedido específico."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT monto, fecha_abono 
            FROM abonos 
            WHERE pedido_cliente_id = %s 
            ORDER BY fecha_abono ASC
        """
        cursor.execute(query, (int(pedido_id),))
        abonos = cursor.fetchall()
        
        # Asegurar formato de monto como float
        for a in abonos:
            a['monto'] = _safe_float(a['monto'])
        return abonos

    except Exception as e:
        logger.error(f"Error al obtener abonos del pedido {pedido_id}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def eliminar_pedido_cliente(pedido_id):
    """Elimina un pedido y sus abonos relacionados (hard delete)."""
    conn = None
    cursor = None
    try:
        pedido_id = int(pedido_id)
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor()

        # 🔒 Iniciar transacción
        conn.start_transaction()

        # 1. Verificar existencia y estado
        cursor.execute("SELECT id, estado FROM pedidos_cliente WHERE id = %s", (pedido_id,))
        pedido = cursor.fetchone()
        if not pedido:
            return False, "❌ Pedido no encontrado."

        # 2. Eliminar en orden inverso de dependencias
        cursor.execute("DELETE FROM abonos WHERE pedido_cliente_id = %s", (pedido_id,))
        cursor.execute("DELETE FROM detalle_pedido_cliente WHERE pedido_id = %s", (pedido_id,))
        cursor.execute("DELETE FROM pedidos_cliente WHERE id = %s", (pedido_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            return False, "❌ No se pudo eliminar el pedido (puede estar bloqueado)."

        conn.commit()
        return True, f"✅ Pedido #{pedido_id} y sus registros relacionados eliminados."

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error MySQL al eliminar pedido: {e}")
        return False, f"❌ Error al eliminar: {e.msg}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al eliminar pedido")
        return False, "❌ Error inesperado durante la eliminación."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()