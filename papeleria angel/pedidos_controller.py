# pedidos_controller.py
import mysql.connector
from database import conectar
from datetime import datetime
from decimal import Decimal
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _safe_int(value, default=None):
    """Convierte a int de forma segura."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_decimal(value):
    """Convierte a Decimal para cálculos exactos."""
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return Decimal('0.00')


def registrar_pedido(proveedor_id, items, fecha_entrega_estimada=None):
    """Registra un nuevo pedido con sus ítems. Todo en una transacción."""
    conn = None
    cursor = None
    
    try:
        proveedor_id = _safe_int(proveedor_id)
        if proveedor_id is None or proveedor_id <= 0:
            return False, "❌ Proveedor inválido."

        if not items or not isinstance(items, list):
            return False, "❌ El pedido debe contener al menos un ítem."

        total = sum(_safe_decimal(item.get('subtotal', 0)) for item in items)
        if total <= 0:
            return False, "❌ El total del pedido debe ser mayor a cero."

        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor()
        conn.start_transaction()

        fecha_pedido = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO pedidos (proveedor_id, fecha_pedido, fecha_entrega_estimada, total, estado)
            VALUES (%s, %s, %s, %s, 'Pendiente')
        """, (proveedor_id, fecha_pedido, fecha_entrega_estimada, float(total)))

        pedido_id = cursor.lastrowid

        detalle_data = []
        for item in items:
            producto_id = _safe_int(item.get('producto_id'))
            cantidad = _safe_int(item.get('cantidad', 0))
            precio_unitario = _safe_decimal(item.get('precio_unitario', 0))
            subtotal = _safe_decimal(item.get('subtotal', 0))

            if not producto_id or cantidad <= 0 or precio_unitario <= 0:
                raise ValueError(f"Ítem inválido: ID={producto_id}, Cant={cantidad}, Precio={precio_unitario}")

            detalle_data.append((
                pedido_id,
                producto_id,
                cantidad,
                float(precio_unitario),
                float(subtotal)
            ))

        if detalle_data:
            cursor.executemany("""
                INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, detalle_data)

        conn.commit()
        return True, f"✅ Pedido #{pedido_id} registrado. Total: ${total:.2f}"

    except ValueError as ve:
        if conn:
            conn.rollback()
        logger.warning(f"Validación fallida al registrar pedido: {ve}")
        return False, f"❌ Datos inválidos: {ve}"
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error MySQL al registrar pedido: {e}")
        return False, f"❌ Error al registrar pedido: {e.msg}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al registrar pedido")
        return False, "❌ Error inesperado. Consulte al administrador."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def actualizar_estado_pedido(pedido_id, nuevo_estado):
    """Actualiza el estado de un pedido. Si es 'Recibido', actualiza stock en la misma transacción."""
    conn = None
    cursor = None
    try:
        pedido_id = _safe_int(pedido_id)
        if not pedido_id:
            return False, "❌ ID de pedido inválido."

        if nuevo_estado not in ['Pendiente', 'Recibido', 'Cancelado']:
            return False, "❌ Estado no válido."

        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        cursor.execute("""
            SELECT id, estado, proveedor_id FROM pedidos WHERE id = %s FOR UPDATE
        """, (pedido_id,))
        pedido = cursor.fetchone()

        if not pedido:
            return False, "❌ Pedido no encontrado."

        estado_actual = pedido['estado']
        if estado_actual == nuevo_estado:
            return True, f"ℹ️ El pedido ya está en estado '{nuevo_estado}'."

        if estado_actual == 'Recibido' and nuevo_estado == 'Recibido':
            return False, "❌ El pedido ya fue recibido. No se puede procesar doblemente."

        cursor.execute("""
            UPDATE pedidos SET estado = %s WHERE id = %s
        """, (nuevo_estado, pedido_id))

        if nuevo_estado == 'Recibido':
            cursor.execute("""
                SELECT producto_id, cantidad 
                FROM detalle_pedido 
                WHERE pedido_id = %s
            """, (pedido_id,))
            items = cursor.fetchall()

            if not items:
                logger.warning(f"Pedido {pedido_id} marcado como recibido sin ítems.")

            for item in items:
                cursor.execute("""
                    UPDATE productos
                    SET stock = stock + %s
                    WHERE id = %s
                """, (item['cantidad'], item['producto_id']))

        conn.commit()
        return True, f"✅ Pedido #{pedido_id} actualizado a '{nuevo_estado}'."

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error MySQL al actualizar estado: {e}")
        return False, f"❌ Error al actualizar estado: {e.msg}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al actualizar estado")
        return False, "❌ Error inesperado. Consulte al administrador."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def eliminar_pedido(pedido_id):
    """Elimina un pedido y sus detalles (solo si está 'Pendiente' o 'Cancelado')."""
    conn = None
    cursor = None
    try:
        pedido_id = _safe_int(pedido_id)
        if not pedido_id:
            return False, "❌ ID inválido."

        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión."

        cursor = conn.cursor()
        cursor.execute("""
            DELETE dp, p 
            FROM pedidos p
            LEFT JOIN detalle_pedido dp ON p.id = dp.pedido_id
            WHERE p.id = %s AND p.estado IN ('Pendiente', 'Cancelado')
        """, (pedido_id,))

        if cursor.rowcount == 0:
            return False, "❌ Pedido no encontrado o ya fue recibido (no se puede eliminar)."

        conn.commit()
        return True, f"✅ Pedido #{pedido_id} eliminado."

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error al eliminar pedido {pedido_id}: {e}")
        return False, f"❌ Error al eliminar: {e.msg}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error inesperado al eliminar pedido")
        return False, "❌ Error inesperado."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()