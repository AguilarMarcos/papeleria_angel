import mysql.connector
from database import conectar
import logging
from datetime import datetime

# Configuración básica de logging para registrar errores
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def get_all_products():
    """Obtiene todos los productos activos, incluyendo el nombre del proveedor."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            logger.error("No se pudo conectar a la base de datos en get_all_products")
            return []

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                p.id,
                p.nombre,
                p.descripcion,
                p.precio_compra,
                p.precio_venta,
                p.stock,
                p.categoria,
                p.proveedor_id,
                p.fecha_ingreso,
                pr.nombre_empresa AS proveedor_nombre
            FROM productos p
            INNER JOIN proveedores pr ON p.proveedor_id = pr.id
            WHERE p.activo = 1
            ORDER BY p.nombre ASC
        """
        cursor.execute(query)
        productos = cursor.fetchall()
        return productos

    except Exception as e:
        logger.exception("Error al obtener productos")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def add_product(nombre, descripcion, precio_compra, precio_venta, stock, categoria, proveedor_id, fecha_ingreso):
    """Inserta un nuevo producto en la base de datos."""
    if stock < 0:
        return False, "El stock inicial no puede ser negativo."
    
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ No se pudo conectar a la base de datos."
        
        cursor = conn.cursor()
        query = """
        INSERT INTO productos (nombre, descripcion, precio_compra, precio_venta, stock, categoria, proveedor_id, fecha_ingreso, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
        """
        cursor.execute(query, (nombre, descripcion, precio_compra, precio_venta, stock, categoria, proveedor_id, fecha_ingreso))
        conn.commit()
        return True, "✅ Producto agregado exitosamente."
        
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.exception("Error al agregar producto")
        # Captura errores de MySQL como FK no encontrada o duplicados
        return False, f"❌ Error de base de datos al agregar el producto: {str(e)}"
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error al agregar producto")
        return False, f"❌ Error al agregar el producto: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_product(producto_id, nombre, descripcion, precio_compra, precio_venta, stock, categoria, proveedor_id):
    """Actualiza la información de un producto existente."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ No se pudo conectar a la base de datos."
        
        cursor = conn.cursor()
        query = """
        UPDATE productos SET nombre=%s, descripcion=%s, precio_compra=%s, precio_venta=%s, stock=%s, categoria=%s, proveedor_id=%s
        WHERE id=%s
        """
        cursor.execute(query, (nombre, descripcion, precio_compra, precio_venta, stock, categoria, proveedor_id, producto_id))
        
        if cursor.rowcount == 0:
            conn.rollback()
            return False, "❌ No se encontró el producto para actualizar o los datos eran idénticos."

        conn.commit()
        return True, "✅ Producto actualizado exitosamente."
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error al actualizar producto")
        return False, f"❌ Error al actualizar el producto: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def delete_product(producto_id):
    """Desactiva un producto (soft delete)."""
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ No se pudo conectar a la base de datos."

        cursor = conn.cursor()
        # Solo desactiva si está activo (evita doble eliminación)
        query = "UPDATE productos SET activo = 0 WHERE id = %s AND activo = 1"
        cursor.execute(query, (producto_id,))
        
        if cursor.rowcount == 0:
            conn.rollback()
            return False, "❌ Producto no encontrado o ya fue eliminado."
        
        conn.commit()
        return True, "✅ Producto eliminado correctamente."

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error al eliminar producto")
        return False, f"❌ Error al eliminar el producto: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()