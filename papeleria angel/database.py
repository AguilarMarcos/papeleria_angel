# database.py
import mysql.connector
from mysql.connector import Error
import os

def conectar():
    """Establece una conexión a la base de datos MySQL."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 3306),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'papeleria_angel')
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al conectar: {e}")
        return None


def cerrar_conexion(conn):
    """Cierra de forma segura una conexión a la base de datos si existe."""
    try:
        if conn:
            try:
                # Algunas conexiones (mysql.connector) tienen is_connected()
                if hasattr(conn, 'is_connected') and conn.is_connected():
                    conn.close()
                else:
                    conn.close()
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
    except Exception:
        pass