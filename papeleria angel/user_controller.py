# user_controller.py
from database import conectar
from hashlib import sha256
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def hash_password(password):
    return sha256(password.encode('utf-8')).hexdigest()

def get_all_users():
    conn = conectar()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM usuarios ORDER BY nombre ASC"
    try:
        cursor.execute(query)
        usuarios = cursor.fetchall()
        return usuarios
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def add_user(nombre, correo, contraseña, rol="cajero"):
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    cursor = conn.cursor()
    hashed_pass = hash_password(contraseña)
    query = """INSERT INTO usuarios (nombre, correo, contraseña, rol) VALUES (%s, %s, %s, %s)"""
    try:
        cursor.execute(query, (nombre, correo, hashed_pass, rol))
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Usuario registrado exitosamente"
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, f"Error al registrar: {str(e)}"

def update_user(user_id, nombre, correo, rol):
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    cursor = conn.cursor()
    query = """UPDATE usuarios SET nombre = %s, correo = %s, rol = %s WHERE id = %s"""
    try:
        cursor.execute(query, (nombre, correo, rol, user_id))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Usuario no encontrado."
        cursor.close()
        conn.close()
        return True, "Usuario actualizado exitosamente"
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, f"Error al actualizar: {str(e)}"

def delete_user(user_id):
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    cursor = conn.cursor()
    query = "DELETE FROM usuarios WHERE id = %s"
    try:
        cursor.execute(query, (user_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Usuario no encontrado."
        cursor.close()
        conn.close()
        return True, "Usuario eliminado exitosamente"
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, f"Error al eliminar: {str(e)}"