from database import conectar
import re
import logging
from email.utils import parseaddr

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

TABLE_NAME = "clientes"


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
        return False, "El nombre debe tener al menos 2 caracteres."

    telefono = _sanitize_input(telefono)
    clean_phone = re.sub(r'\D', '', telefono or '')
    if len(clean_phone) < 10:
        return False, "El teléfono debe tener al menos 10 dígitos."

    return True, ""


def _is_valid_email(email):
    """Validación razonable de email usando parseaddr y una comprobación simple."""
    if not email:
        return True
    email = email.strip()
    name, addr = parseaddr(email)
    # parseaddr devuelve '' si no hay dirección; comprobamos formato básico con regex
    if not addr:
        return False
    # Requiere algo@algo.algo sin espacios
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', addr))


def add_client(nombre, apellido, telefono, direccion, email):
    """Inserta un nuevo cliente en la base de datos."""
    conexion = None
    cursor = None
    try:
        # ✅ Validación en capa de negocio
        valido, msg = _validate_client_data(nombre, telefono)
        if not valido:
            return False, f"❌ Datos inválidos: {msg}"

        if email and not _is_valid_email(email):
            return False, "❌ El correo electrónico tiene un formato inválido."

        conexion = conectar()
        if not conexion:
            return False, "❌ Error: No se pudo conectar a la base de datos."

        cursor = conexion.cursor()

        # ✅ Sanitización
        nombre = _sanitize_input(nombre)
        apellido = _sanitize_input(apellido or '')
        telefono = _sanitize_input(telefono)
        email = _sanitize_input(email or '')
        direccion = _sanitize_input(direccion or '').lower()

        # Asegurar que el orden de valores coincide con las columnas
        query = f"""
        INSERT INTO {TABLE_NAME} (nombre, apellido, telefono, direccion, email, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, CURDATE())
        """
        cursor.execute(query, (nombre, apellido, telefono, direccion, email))
        conexion.commit()
        return True, f"✅ Cliente '{nombre}' agregado con éxito."

    except Exception as e:
        if conexion:
            try:
                conexion.rollback()
            except Exception:
                pass
        logger.exception("Error al agregar cliente")
        return False, f"❌ Error al agregar cliente: {str(e)}"
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conexion:
            try:
                if hasattr(conexion, "is_connected"):
                    if conexion.is_connected():
                        conexion.close()
                else:
                    conexion.close()
            except Exception:
                pass


def obtener_todos_clientes():
    """Obtiene todos los clientes (ordenados por nombre)."""
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        if not conexion:
            return []

        cursor = conexion.cursor(dictionary=True)
        query = f"""
        SELECT id, nombre, apellido, telefono, direccion, email, fecha_registro
        FROM {TABLE_NAME}
        ORDER BY nombre, apellido
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error al obtener clientes: {e}")
        return []
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conexion:
            try:
                if hasattr(conexion, "is_connected"):
                    if conexion.is_connected():
                        conexion.close()
                else:
                    conexion.close()
            except Exception:
                pass


def update_client(client_id, nombre, apellido, telefono, email, direccion):
    """Actualiza un cliente existente."""
    conexion = None
    cursor = None
    try:
        if not client_id:
            return False, "❌ ID de cliente inválido."

        valido, msg = _validate_client_data(nombre, telefono)
        if not valido:
            return False, f"❌ Datos inválidos: {msg}"

        if email and not _is_valid_email(email):
            return False, "❌ Correo electrónico inválido."

        conexion = conectar()
        if not conexion:
            return False, "❌ Error de conexión."

        cursor = conexion.cursor()

        nombre = _sanitize_input(nombre)
        apellido = _sanitize_input(apellido or '')
        telefono = _sanitize_input(telefono)
        email = _sanitize_input(email or '')
        direccion = _sanitize_input(direccion or '').lower()

        query = f"""
        UPDATE {TABLE_NAME}
        SET nombre = %s, apellido = %s, telefono = %s, direccion = %s, email = %s
        WHERE id = %s
        """
        cursor.execute(query, (nombre, apellido, telefono, direccion, email, client_id))

        if cursor.rowcount == 0:
            return False, "❌ Cliente no encontrado."

        conexion.commit()
        return True, f"✅ Cliente '{nombre}' actualizado con éxito."

    except Exception as e:
        if conexion:
            try:
                conexion.rollback()
            except Exception:
                pass
        logger.exception("Error al actualizar cliente")
        return False, f"❌ Error al actualizar: {str(e)}"
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conexion:
            try:
                if hasattr(conexion, "is_connected"):
                    if conexion.is_connected():
                        conexion.close()
                else:
                    conexion.close()
            except Exception:
                pass


def delete_client(client_id):
    """Elimina un cliente (soft delete recommended, but hard delete implemented)."""
    conexion = None
    cursor = None
    try:
        if not client_id:
            return False, "❌ ID de cliente inválido."

        conexion = conectar()
        if not conexion:
            return False, "❌ Error de conexión."

        cursor = conexion.cursor()

        # 🔒 Opcional: verificar que no tenga pedidos/ventas (evita inconsistencia)
        cursor.execute("SELECT COUNT(*) FROM pedidos_cliente WHERE cliente_id = %s", (client_id,))
        tiene_pedidos = cursor.fetchone()[0] > 0

        if tiene_pedidos:
            return False, "❌ No se puede eliminar: el cliente tiene pedidos registrados."

        query = f"DELETE FROM {TABLE_NAME} WHERE id = %s"
        cursor.execute(query, (client_id,))

        if cursor.rowcount == 0:
            return False, "❌ Cliente no encontrado."

        conexion.commit()
        return True, "✅ Cliente eliminado con éxito."

    except Exception as e:
        if conexion:
            try:
                conexion.rollback()
            except Exception:
                pass
        logger.exception("Error al eliminar cliente")
        return False, f"❌ Error al eliminar: {str(e)}"
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conexion:
            try:
                if hasattr(conexion, "is_connected"):
                    if conexion.is_connected():
                        conexion.close()
                else:
                    conexion.close()
            except Exception:
                pass
