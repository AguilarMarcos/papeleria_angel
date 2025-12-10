# suppliers_controller.py
from database import conectar
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def obtener_todos_proveedores():
    conn = conectar()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM proveedores ORDER BY nombre_empresa ASC"
    try:
        cursor.execute(query)
        proveedores = cursor.fetchall()
        return proveedores
    except Exception as e:
        logger.error(f"Error al obtener proveedores: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def agregar_proveedor(nombre_empresa, contacto, telefono, correo):
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    cursor = conn.cursor()
    query = """INSERT INTO proveedores (nombre_empresa, contacto, telefono, correo) VALUES (%s, %s, %s, %s)"""
    try:
        cursor.execute(query, (nombre_empresa, contacto, telefono, correo))
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Proveedor agregado exitosamente"
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, f"Error al agregar: {str(e)}"

def actualizar_proveedor(id_proveedor, nombre_empresa, contacto, telefono, correo):
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    cursor = conn.cursor()
    query = """UPDATE proveedores SET nombre_empresa = %s, contacto = %s, telefono = %s, correo = %s WHERE id = %s"""
    try:
        cursor.execute(query, (nombre_empresa, contacto, telefono, correo, id_proveedor))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Proveedor no encontrado."
        cursor.close()
        conn.close()
        return True, "Proveedor actualizado exitosamente"
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, f"Error al actualizar: {str(e)}"

def eliminar_proveedor(id_proveedor):
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    cursor = conn.cursor()
    try:
        # Verificar si hay productos asociados
        cursor.execute("SELECT COUNT(*) AS total FROM productos WHERE proveedor_id = %s", (id_proveedor,))
        resultado = cursor.fetchone()
        if resultado['total'] > 0:
            return False, "No se puede eliminar: hay productos asociados a este proveedor."

        cursor.execute("DELETE FROM proveedores WHERE id = %s", (id_proveedor,))
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Proveedor eliminado exitosamente"
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, f"Error al eliminar: {str(e)}"