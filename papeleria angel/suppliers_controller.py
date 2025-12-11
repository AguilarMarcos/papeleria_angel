# suppliers_controller.py - VERSIÓN PERFECTA
import mysql.connector
from database import conectar
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def obtener_todos_proveedores():
    """
    Obtiene todos los proveedores de la base de datos.

    Returns:
        list: Lista de diccionarios con la información de los proveedores.
    """
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            logger.error("No se pudo conectar a la base de datos.")
            return []
            
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM proveedores ORDER BY nombre_empresa ASC"
        cursor.execute(query)
        proveedores = cursor.fetchall()
        return proveedores
        
    except Exception as e:
        logger.exception("Error al obtener proveedores")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def agregar_proveedor(nombre_empresa, contacto, telefono, correo):
    """
    Inserta un nuevo proveedor en la base de datos.

    Returns:
        (bool, str): (éxito, mensaje)
    """
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."
            
        cursor = conn.cursor()
        query = """
        INSERT INTO proveedores (nombre_empresa, contacto, telefono, correo) 
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (nombre_empresa, contacto, telefono, correo))
        conn.commit()
        return True, "✅ Proveedor agregado exitosamente."
        
    except mysql.connector.Error as e:
        if conn: conn.rollback()
        logger.exception("Error al agregar proveedor")
        # Capturar error de duplicidad, si aplica
        if e.errno == 1062: # Código de error de duplicidad en MySQL
            return False, "❌ Error: Ya existe un proveedor con esa información (nombre/correo)."
        return False, f"❌ Error de base de datos al agregar: {str(e)}"
    except Exception as e:
        if conn: conn.rollback()
        logger.exception("Error desconocido al agregar proveedor")
        return False, f"❌ Error inesperado: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


def actualizar_proveedor(id_proveedor, nombre_empresa, contacto, telefono, correo):
    """
    Actualiza la información de un proveedor existente.

    Returns:
        (bool, str): (éxito, mensaje)
    """
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."
            
        cursor = conn.cursor()
        query = """
        UPDATE proveedores 
        SET nombre_empresa = %s, contacto = %s, telefono = %s, correo = %s 
        WHERE id = %s
        """
        cursor.execute(query, (nombre_empresa, contacto, telefono, correo, id_proveedor))
        
        if cursor.rowcount == 0:
            # No se actualizó ninguna fila (ID no encontrado o datos idénticos)
            conn.rollback() 
            return False, "❌ No se encontró el proveedor para actualizar o no hubo cambios."
        
        conn.commit()
        return True, "✅ Proveedor actualizado exitosamente."
        
    except mysql.connector.Error as e:
        if conn: conn.rollback()
        logger.exception("Error al actualizar proveedor")
        return False, f"❌ Error de base de datos al actualizar: {str(e)}"
    except Exception as e:
        if conn: conn.rollback()
        logger.exception("Error desconocido al actualizar proveedor")
        return False, f"❌ Error inesperado: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


def eliminar_proveedor(id_proveedor):
    """
    Elimina un proveedor de la base de datos, verificando que no tenga productos asociados.

    Returns:
        (bool, str): (éxito, mensaje)
    """
    conn = None
    cursor = None
    try:
        conn = conectar()
        if not conn:
            return False, "❌ Error de conexión a la base de datos."
            
        cursor = conn.cursor(dictionary=True) # Usamos dictionary=True para la verificación de productos
        
        # 1. Verificar si hay productos asociados
        cursor.execute("SELECT COUNT(*) AS total FROM productos WHERE proveedor_id = %s AND activo = 1", (id_proveedor,))
        resultado = cursor.fetchone()
        
        if resultado and resultado.get('total', 0) > 0:
            conn.rollback()
            return False, f"❌ No se puede eliminar: hay {resultado['total']} productos activos asociados a este proveedor."

        # 2. Eliminar el proveedor
        # Se requiere un nuevo cursor si el anterior era dictionary=True (depende de la implementación de conectar)
        # Para mayor seguridad y compatibilidad, cierro el anterior y abro uno simple
        cursor.close() 
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM proveedores WHERE id = %s", (id_proveedor,))
        
        if cursor.rowcount == 0:
            conn.rollback()
            return False, "❌ Proveedor no encontrado."
            
        conn.commit()
        return True, "✅ Proveedor eliminado exitosamente."
        
    except Exception as e:
        if conn: conn.rollback()
        logger.exception("Error al eliminar proveedor")
        return False, f"❌ Error al eliminar proveedor: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()