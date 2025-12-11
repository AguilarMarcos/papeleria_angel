# sales_controller.py - VERSIÓN PERFECCIONADA

from database import conectar
from datetime import datetime
import mysql.connector
import logging

# Configurar logging para registrar errores en un archivo o consola
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def obtener_productos_activos():
    """Obtiene productos activos con stock > 0 para la venta, asegurando tipos numéricos."""
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

        # Asegurar tipos numéricos para evitar errores en la interfaz
        for p in productos:
            p['precio_venta'] = float(p.get('precio_venta', 0))
            p['stock'] = int(p.get('stock', 0))

        return productos
    except Exception as e:
        logger.error(f"Error al obtener productos activos: {e}")
        return []
    finally:
        # Cerrar la conexión y el cursor de forma segura
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def registrar_venta(usuario_id, items_vendidos, cliente_id=None):
    """
    Registra una venta con múltiples ítems, actualiza el stock y maneja la transacción.

    Args:
        usuario_id (int): ID del usuario/cajero.
        items_vendidos (list): Lista de dicts con {'producto_id', 'cantidad', 'precio_unitario', 'subtotal'}.
        cliente_id (int, optional): ID del cliente. Defaults to None (público general).

    Returns:
        (bool, str): (éxito, mensaje)
    """
    if not items_vendidos:
        return False, "❌ La venta no tiene ítems."

    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."
        
        cursor = conn.cursor()

        # 1. Validar Stock antes de la transacción: Chequeo preventivo
        for item in items_vendidos:
            producto_id = item['producto_id']
            cantidad_solicitada = item['cantidad']

            cursor.execute("SELECT stock, nombre FROM productos WHERE id = %s AND activo = 1", (producto_id,))
            producto = cursor.fetchone()
            
            if not producto:
                return False, f"❌ Producto con ID {producto_id} no encontrado o inactivo."
            
            stock_actual = producto[0]
            nombre_producto = producto[1]

            if stock_actual < cantidad_solicitada:
                # Retorna error sin hacer rollback, ya que no se inició la transacción
                return False, f"❌ Stock insuficiente para {nombre_producto}. Disponible: {stock_actual}, Solicitado: {cantidad_solicitada}."

        # 2. Registrar la venta principal (ventas)
        total_venta = sum(item['subtotal'] for item in items_vendidos)
        fecha_venta = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query_venta = """
        INSERT INTO ventas (usuario_id, cliente_id, fecha_venta, total)
        VALUES (%s, %s, %s, %s)
        """
        # Usar cliente_id (puede ser NULL si es público general)
        cursor.execute(query_venta, (usuario_id, cliente_id, fecha_venta, total_venta))
        venta_id = cursor.lastrowid
        
        detalle_data = []
        
        # 3. Registrar el detalle y actualizar stock
        for item in items_vendidos:
            producto_id = item['producto_id']
            cantidad = item['cantidad']
            precio = item['precio_unitario']
            subtotal = item['subtotal']

            detalle_data.append((venta_id, producto_id, cantidad, precio, subtotal))

            # Actualizar stock
            query_stock = "UPDATE productos SET stock = stock - %s WHERE id = %s"
            cursor.execute(query_stock, (cantidad, producto_id))

        query_detalle = """
        INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.executemany(query_detalle, detalle_data)

        # Confirmar todos los cambios
        conn.commit()
        return True, f"✅ Venta {venta_id} registrada con éxito. Total: ${total_venta:.2f}"
        
    except mysql.connector.Error as e:
        # En caso de error de MySQL, se realiza un rollback
        if conn:
            conn.rollback()
        logger.error(f"Error de base de datos al registrar venta: {str(e)}", exc_info=True)
        return False, f"❌ Error de base de datos al registrar venta. Consulte logs para detalles."
    except Exception as e:
        # En caso de cualquier otro error, se realiza un rollback
        if conn:
            conn.rollback()
        logger.error(f"Error inesperado al registrar venta: {str(e)}", exc_info=True)
        return False, f"❌ Error inesperado al registrar venta. Error: {str(e)}"
    finally:
        # Asegurar el cierre de la conexión y el cursor
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()