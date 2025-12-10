#auth_controller.py
from database import conectar
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(correo, contraseña):
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    cursor = conn.cursor(dictionary=True)
    hashed_pass = hash_password(contraseña)
    
    query = "SELECT * FROM usuarios WHERE correo = %s AND contraseña = %s"
    cursor.execute(query, (correo, hashed_pass))
    usuario = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if usuario:
        return True, usuario
    else:
        return False, "Correo o contraseña incorrectos"

def registrar_usuario(nombre, correo, contraseña, rol="cajero"):
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    cursor = conn.cursor()
    hashed_pass = hash_password(contraseña)
    
    query = """
    INSERT INTO usuarios (nombre, correo, contraseña, rol)
    VALUES (%s, %s, %s, %s)
    """
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