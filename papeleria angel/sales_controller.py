# sales_controller.py
from database import conectar
from datetime import datetime
import mysql.connector
import logging

# Configurar logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def obtener_productos_activos():
    """Obtiene productos con stock > 0."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT id, nombre, precio_venta, stock
        FROM productos
        WHERE activo = 1 AND stock > 0
        ORDER BY nombre ASC
        """
        cursor.execute(query)
        productos = cursor.fetchall()

        # Asegurar tipos numéricos
        for p in productos:
            p['precio_venta'] = float(p.get('precio_venta', 0))
            p['stock'] = int(p.get('stock', 0))

        return productos
    except Exception as e:
        logger.error(f"Error al obtener productos activos: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def registrar_venta_completa(producto_id, usuario_id, cantidad, precio_unitario):
    """Registra venta Y actualiza stock en una sola transacción atómica."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor()
        conn.start_transaction()

        total = float(precio_unitario) * int(cantidad)
        fecha_venta = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 1. Registrar la venta
        cursor.execute("""
            INSERT INTO ventas (producto_id, usuario_id, cantidad, total, fecha_venta)
            VALUES (%s, %s, %s, %s, %s)
        """, (producto_id, usuario_id, cantidad, total, fecha_venta))

        # 2. Actualizar stock (en la misma transacción)
        cursor.execute("""
            UPDATE productos 
            SET stock = stock - %s 
            WHERE id = %s AND stock >= %s
        """, (cantidad, producto_id, cantidad))

        if cursor.rowcount == 0:
            conn.rollback()
            return False, "❌ Stock insuficiente. Venta cancelada para mantener consistencia."

        conn.commit()
        return True, "✅ Venta registrada y stock actualizado correctamente."

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error en venta atómica")
        return False, f"❌ Error al registrar venta: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def registrar_venta(usuario_id, items_vendidos):
    """Registra una venta compuesta por varios items y actualiza el stock en una transacción."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."

        cursor = conn.cursor()
        conn.start_transaction()

        total = 0.0
        for it in items_vendidos:
            total += float(it.get('subtotal', 0))

        fecha_venta = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insertar venta principal
        # Algunas bases de datos esperan un producto_id en la tabla ventas (esquema legado),
        # así que llenamos ese campo con el primer producto del pedido y la cantidad total.
        first_producto_id = None
        total_cantidad = 0
        if items_vendidos:
            first_producto_id = items_vendidos[0].get('producto_id')
            for it in items_vendidos:
                try:
                    total_cantidad += int(it.get('cantidad', 0))
                except Exception:
                    total_cantidad += 0

        cursor.execute(
            "INSERT INTO ventas (producto_id, usuario_id, cantidad, total, fecha_venta) VALUES (%s, %s, %s, %s, %s)",
            (first_producto_id, usuario_id, total_cantidad, total, fecha_venta)
        )
        venta_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None

        # Insertar detalle y actualizar stock por cada item
        try:
            for it in items_vendidos:
                producto_id = it.get('producto_id')
                cantidad = int(it.get('cantidad', 0))
                precio_unitario = float(it.get('precio_unitario', 0))
                subtotal = float(it.get('subtotal', precio_unitario * cantidad))

                cursor.execute(
                    "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                )

                cursor.execute(
                    "UPDATE productos SET stock = stock - %s WHERE id = %s AND stock >= %s",
                    (cantidad, producto_id, cantidad)
                )

                if cursor.rowcount == 0:
                    conn.rollback()
                    return False, f"❌ Stock insuficiente para el producto {producto_id}."
        except mysql.connector.errors.ProgrammingError as pe:
            # Si la tabla detalle_venta no existe, hacemos fallback al esquema legado
            if getattr(pe, 'errno', None) == 1146:
                conn.rollback()
                for it in items_vendidos:
                    producto_id = it.get('producto_id')
                    cantidad = int(it.get('cantidad', 0))
                    precio_unitario = float(it.get('precio_unitario', 0))
                    ok, msg = registrar_venta_completa(producto_id, usuario_id, cantidad, precio_unitario)
                    if not ok:
                        return False, msg
            else:
                raise

        conn.commit()
        return True, "✅ Venta registrada y stock actualizado correctamente."

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error al registrar venta compuesta")
        return False, f"❌ Error al registrar la venta: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn and hasattr(conn, 'is_connected') and conn.is_connected():
            conn.close()