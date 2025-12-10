import pytest
import mysql.connector
from datetime import datetime
import random
import time
from database import conectar, cerrar_conexion

# Importar funciones de los controladores (Asegúrate de que los nombres coincidan)
from clientes_controller import add_client, obtener_todos_clientes, delete_client
from products_controller import add_product
from sales_controller import registrar_venta, obtener_productos_activos


# =======================================================
# CONFIGURACIÓN Y FUNCIONES AUXILIARES
# =======================================================

@pytest.fixture(scope="module")
def db_conn():
    """Fixture para proporcionar y cerrar la conexión de la base de datos."""
    conn = conectar()
    if not conn:
        pytest.skip("No se pudo conectar a la base de datos de prueba.")
    yield conn
    cerrar_conexion(conn)

def clean_data(conn, table, id_field, id_value):
    """Función auxiliar para limpiar datos después de una prueba."""
    if not conn: return
    cursor = conn.cursor()
    try:
        query = f"DELETE FROM {table} WHERE {id_field} = %s"
        cursor.execute(query, (id_value,))
        conn.commit()
    except Exception as e:
        print(f"\nAdvertencia: No se pudo limpiar la tabla {table}. Error: {e}")
    finally:
        cursor.close()

# Variables Globales de Prueba (Asegúrate que existan en tu DB)
USUARIO_ID_PRUEBA = 1
PROVEEDOR_ID_PRUEBA = 1 
FECHA_PRUEBA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# =======================================================
# PRUEBAS DE CLIENTES
# =======================================================

def test_add_client_success(db_conn):
    """Prueba que un cliente se agregue correctamente y luego se elimine."""
    nombre = f"Test_{random.randint(1, 1000)}"
    telefono = f"55{random.randint(10000000, 99999999)}"
    
    # 1. Ejecutar la función de agregar
    exito, mensaje = add_client(nombre, "Unitario", telefono, "Direccion Test", f"test.{nombre}@test.com")
    assert exito is True, f"Fallo al agregar cliente: {mensaje}"

    # 2. Verificar que se agregó y obtener ID para limpieza
    clientes = obtener_todos_clientes()
    nuevo_cliente = next((c for c in clientes if c['nombre'] == nombre), None)
    
    assert nuevo_cliente is not None, "El cliente no fue encontrado después de la inserción."
    
    # 3. Limpieza de datos (Teardown)
    exito_del, mensaje_del = delete_client(nuevo_cliente['id'])
    assert exito_del is True, f"Fallo en la limpieza (delete_client): {mensaje_del}"


# =======================================================
# PRUEBAS DE PRODUCTOS
# =======================================================

def test_add_product_validation_failure():
    """Prueba que la lógica de negocio (validación de stock negativo) funcione."""
    
    # Intentar agregar stock negativo
    # ARGUMENTOS CORREGIDOS: Se añadieron 'categoria' y 'fecha_ingreso'
    exito, mensaje = add_product("Producto Fail", "Desc", 1.0, 2.0, -10, "Papeleria", PROVEEDOR_ID_PRUEBA, FECHA_PRUEBA)
    
    assert exito is False, "El controlador aceptó stock negativo."
    assert "no puede ser negativo" in mensaje, "El mensaje de error no es el esperado."


def test_add_product_success(db_conn):
    """Prueba que un producto se agregue correctamente."""
    nombre = f"Prod_{random.randint(1, 1000)}"
    
    # 1. Ejecutar la función de agregar
    # ARGUMENTOS CORREGIDOS: Se añadieron 'categoria' y 'fecha_ingreso'
    exito, mensaje = add_product(
        nombre=nombre,
        descripcion="Prueba Unit",
        precio_compra=5.0,
        precio_venta=10.0,
        stock=5,
        categoria="Escolar", # Argumento faltante
        proveedor_id=PROVEEDOR_ID_PRUEBA,
        fecha_ingreso=FECHA_PRUEBA # Argumento faltante
    )
    assert exito is True, f"Fallo al agregar producto: {mensaje}"

    # 2. Limpieza de datos (Teardown)
    cursor = db_conn.cursor(dictionary=True)
    query_find = "SELECT id FROM productos WHERE nombre = %s"
    cursor.execute(query_find, (nombre,))
    
    # Manejo de caso donde la inserción falló silenciosamente (aunque assert ya lo cubrió)
    producto_data = cursor.fetchone()
    if producto_data:
        producto_id = producto_data['id']
        cursor.close()
        clean_data(db_conn, "productos", "id", producto_id)
    else:
        cursor.close()
        # Si la inserción fue exitosa pero no se pudo encontrar, es un fallo crítico
        raise AssertionError("Producto insertado pero no encontrado para limpieza.")


# =======================================================
# PRUEBAS DE VENTAS
# =======================================================

def test_registrar_venta_success(db_conn):
    """Prueba el registro completo de una venta."""
    # --- SETUP: Insertar producto temporal ---
    nombre_prod = f"Temp_{random.randint(1, 1000)}"
    
    # ARGUMENTOS CORREGIDOS: Se añadieron 'categoria' y 'fecha_ingreso'
    exito_setup, msg_setup = add_product(nombre_prod, "Venta Test", 20.0, 30.0, 10, "Oficina", PROVEEDOR_ID_PRUEBA, FECHA_PRUEBA)
    assert exito_setup is True, f"Fallo en el setup (add_product): {msg_setup}"
    
    productos_activos = obtener_productos_activos()
    test_producto = next((p for p in productos_activos if p['nombre'] == nombre_prod), None)
    
    assert test_producto is not None, "Fallo en el setup: Producto no encontrado para la venta."
    producto_id = test_producto['id']
    stock_inicial = test_producto['stock']
    
    # --- PRUEBA: Registrar venta ---
    cantidad_vendida = 3
    items_vendidos = [{
        'producto_id': producto_id,
        'cantidad': cantidad_vendida,
        'precio_unitario': 30.0,
        'subtotal': 90.0
    }]
    
    exito, mensaje = registrar_venta(USUARIO_ID_PRUEBA, items_vendidos)
    assert exito is True, f"Fallo al registrar la venta: {mensaje}"
    
    # --- VERIFICACIÓN ADICIONAL: Stock ---
    productos_post_venta = obtener_productos_activos()
    stock_final = next((p for p in productos_post_venta if p['id'] == producto_id), None)['stock']
    assert stock_final == (stock_inicial - cantidad_vendida), "El stock no se actualizó correctamente después de la venta."
    
    # --- TEARDOWN: Limpieza de Producto y Venta ---
    cursor = db_conn.cursor()
    
    # Obtener el ID de la venta más reciente (la que acabamos de hacer)
    cursor.execute("SELECT id FROM ventas ORDER BY id DESC LIMIT 1")
    venta_id_data = cursor.fetchone()
    
    if venta_id_data:
        venta_id = venta_id_data[0]
        clean_data(db_conn, "detalle_venta", "venta_id", venta_id)
        clean_data(db_conn, "ventas", "id", venta_id)

    # Limpiar producto
    clean_data(db_conn, "productos", "id", producto_id)
    cursor.close()