from database import conectar
import re
import logging
from email.utils import parseaddr
import mysql.connector

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

TABLE_NAME = "clientes"

# --- Funciones de Utilidad y Validación ---

def _sanitize_input(value):
    """Sanitiza entrada básica (evita HTML/JS en datos)."""
    if not isinstance(value, str):
        return value
    # Elimina etiquetas HTML/JS (básico)
    return re.sub(r'<[^>]+>', '', value).strip()

def _validate_client_data(nombre, telefono):
    """Validación mínima de datos esenciales."""
    nombre = _sanitize_input(nombre)
    if not nombre or len(nombre.strip()) < 2:
        return False, "❌ El nombre debe tener al menos 2 caracteres."

    telefono = _sanitize_input(telefono)
    clean_phone = re.sub(r'\D', '', telefono or '')
    if len(clean_phone) < 10:
        return False, "❌ El teléfono debe tener al menos 10 dígitos."

    return True, ""

def _is_valid_email(email):
    """Validación razonable de email."""
    if not email:
        return True  # Email opcional

    email = email.strip()

    # Usar parseaddr correctamente
    name, addr = parseaddr(email)

    # Validación básica
    if '@' not in addr or '.' not in addr:
        return False

    # Validar que addr sea igual al email original
    return addr == email

# --- Funciones CRUD ---

def add_client(nombre, apellido, telefono, direccion, email):
    """Inserta un nuevo cliente en la base de datos con validación."""
    
    # 1. Validación de Negocio
    valido, mensaje_val = _validate_client_data(nombre, telefono)
    if not valido:
        return False, mensaje_val
        
    if not _is_valid_email(email):
        return False, "❌ El formato del correo electrónico no es válido."
        
    # 2. Sanitización de Inputs antes de DB
    nombre, apellido, telefono, direccion, email = map(_sanitize_input, (nombre, apellido, telefono, direccion, email))
    
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        if not conexion:
            return False, "❌ Error de conexión a la base de datos."
        
        cursor = conexion.cursor()
        query = f"""
        INSERT INTO {TABLE_NAME} (nombre, apellido, telefono, direccion, email)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (nombre, apellido, telefono, direccion, email))
        conexion.commit()
        return True, "✅ Cliente agregado exitosamente."
        
    except mysql.connector.Error as e:
        if conexion:
            conexion.rollback()
        logger.exception("Error al agregar cliente")
        # 1062 es código de error para duplicado (e.g., email único)
        if e.errno == 1062:
            return False, "❌ Error: Ya existe un cliente con ese correo o teléfono."
        return False, f"❌ Error al agregar cliente: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conexion and conexion.is_connected(): conexion.close()

def obtener_todos_clientes():
    """Obtiene todos los clientes de la base de datos, retornando diccionarios."""
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        if not conexion:
            return [] 
        
        cursor = conexion.cursor(dictionary=True) 
        query = f"SELECT id, nombre, apellido, telefono, direccion, email FROM {TABLE_NAME} ORDER BY nombre, apellido ASC"
        cursor.execute(query)
        clientes = cursor.fetchall()
        return clientes 
        
    except Exception as e:
        logger.exception("Error al obtener todos los clientes")
        return []
    finally:
        if cursor: cursor.close()
        if conexion and conexion.is_connected(): conexion.close()
        
def update_client(client_id, nombre, apellido, telefono, direccion, email):
    """Actualiza un cliente existente con validación."""
    
    # 1. Validación de Negocio
    valido, mensaje_val = _validate_client_data(nombre,telefono)
    if not valido:
        return False, mensaje_val
        
    if not _is_valid_email(email):
        return False, "❌ El formato del correo electrónico no es válido."

    # 2. Sanitización de Inputs
    nombre, apellido, telefono, direccion, email = map(_sanitize_input, (nombre, apellido, telefono, direccion, email))

    conexion = None
    cursor = None
    try:
        conexion = conectar()
        if not conexion:
            return False, "❌ Error de conexión a la base de datos."
        
        cursor = conexion.cursor()
        query = f"""
        UPDATE {TABLE_NAME} SET 
            nombre = %s, apellido = %s, telefono = %s, direccion = %s, email = %s
        WHERE id = %s
        """
        cursor.execute(query, (nombre, apellido, telefono, direccion, email, client_id))
        conexion.commit()
        
        if cursor.rowcount == 0:
            return False, "❌ No se encontró el cliente con ese ID para actualizar."

        return True, "✅ Cliente actualizado exitosamente."
    except mysql.connector.Error as e:
        if conexion:
            conexion.rollback()
        logger.exception("Error al actualizar cliente")
        if e.errno == 1062:
            return False, "❌ Error: Ya existe otro cliente con ese correo o teléfono."
        return False, f"❌ Error al actualizar cliente: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conexion and conexion.is_connected(): conexion.close()

def delete_client(client_id):
    """Elimina un cliente de la base de datos usando su ID, verificando dependencias."""
    if not client_id or not str(client_id).isdigit():
        return False, "❌ ID de cliente inválido."

    conexion = None
    cursor = None
    try:
        conexion = conectar()
        if not conexion:
            return False, "❌ Error de conexión."

        cursor = conexion.cursor()

        # 🔒 Revisar si tiene pedidos asociados (Integridad referencial)
        # Asumo que tienes una tabla 'pedidos_cliente' o una columna 'cliente_id' en 'ventas'
        try:
            # (Si no existe 'pedidos_cliente', puedes comentar o cambiar esta sección)
            cursor.execute("SELECT COUNT(*) FROM ventas WHERE cliente_id = %s", (client_id,))
            tiene_ventas = cursor.fetchone()[0] > 0
            if tiene_ventas:
                return False, "❌ No se puede eliminar: el cliente tiene ventas registradas. Considere desactivarlo en su lugar."
        except Exception:
             # Si la tabla 'ventas' no tiene 'cliente_id', continúa.
             pass 

        query = f"DELETE FROM {TABLE_NAME} WHERE id = %s"
        cursor.execute(query, (client_id,))

        if cursor.rowcount == 0:
            return False, "❌ Cliente no encontrado."

        conexion.commit()
        return True, "✅ Cliente eliminado con éxito."

    except Exception as e:
        if conexion: conexion.rollback()
        logger.exception("Error al eliminar cliente")
        return False, f"❌ Error al eliminar: {str(e)}"
    finally:
        # Cerrado robusto de conexión y cursor
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conexion:
            try: 
                if conexion.is_connected(): conexion.close()
            except Exception: pass