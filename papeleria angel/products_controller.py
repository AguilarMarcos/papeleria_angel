# products_controller.py
from database import conectar
import logging

# Configura logging (en producción, usa un archivo)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def get_all_products():
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
        if conn:
            conn.close()


def add_product(nombre, descripcion, precio_compra, precio_venta, stock, categoria, proveedor_id, fecha_ingreso):
    conn = None
    cursor = None
    try:
        # Validación básica: stock debe ser un número entero no negativo
        try:
            stock_int = int(stock)
            if stock_int < 0:
                return False, "El stock no puede ser negativo."
        except (ValueError, TypeError):
            return False, "Stock inválido. Debe ser un número entero."

        conn = conectar()
        if not conn:
            return False, "No se pudo conectar a la base de datos."

        cursor = conn.cursor()
        query = """
            INSERT INTO productos (
                nombre, descripcion, precio_compra, precio_venta, 
                stock, categoria, proveedor_id, fecha_ingreso
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Usamos stock_int en lugar de stock para asegurar que sea un entero
        cursor.execute(query, (
            nombre, descripcion, float(precio_compra), float(precio_venta),
            stock_int, categoria, proveedor_id, fecha_ingreso
        ))
        conn.commit()
        return True, "Producto agregado exitosamente."

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error al agregar producto")
        return False, "Error al agregar el producto. Intente nuevamente."
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_product(producto_id, nombre, descripcion, precio_compra, precio_venta, stock, categoria, proveedor_id):
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "No se pudo conectar a la base de datos."

        cursor = conn.cursor()
        # 🔒 Solo actualiza si el producto existe Y está activo (evita reactivar por error)
        query = """
            UPDATE productos 
            SET 
                nombre = %s, 
                descripcion = %s, 
                precio_compra = %s, 
                precio_venta = %s, 
                stock = %s, 
                categoria = %s, 
                proveedor_id = %s,
                fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = %s AND activo = 1
        """
        cursor.execute(query, (
            nombre, descripcion, precio_compra, precio_venta,
            stock, categoria, proveedor_id, producto_id
        ))
        conn.commit()
        return True, "Producto actualizado exitosamente."

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error al actualizar producto")
        return False, "Error al actualizar el producto. Intente nuevamente."
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_product(producto_id):
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "No se pudo conectar a la base de datos."

        cursor = conn.cursor()
        # 🛑 Solo desactiva si está activo (evita doble eliminación)
        query = "UPDATE productos SET activo = 0 WHERE id = %s AND activo = 1"
        cursor.execute(query, (producto_id,))
        
        if cursor.rowcount == 0:
            return False, "Producto no encontrado o ya eliminado."
        
        conn.commit()
        return True, "Producto eliminado correctamente."

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception("Error al eliminar producto")
        return False, "Error al eliminar el producto. Intente nuevamente."
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()