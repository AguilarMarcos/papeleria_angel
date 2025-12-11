# sales_history_controller.py - CÓDIGO PERFECCIONADO
from database import conectar
from datetime import datetime, timedelta
import logging

# Configura logging para mejor manejo de errores
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def get_sales_history(fecha_inicio=None, fecha_fin=None, limit=None, offset=0):
    """
    Obtiene el historial de ventas, listando cada producto vendido como una línea (detalle_venta).
    Soporta filtrado por fecha, límite y paginación.
    """
    conn = None
    cursor = None
    
    # Manejo de límite por defecto si no se especifica
    if limit is None:
        limit = 1000

    try:
        conn = conectar()
        if not conn:
            return False, "❌ Error: No se pudo conectar a la base de datos."

        cursor = conn.cursor(dictionary=True)

        # Consulta corregida: Une ventas con detalle_venta y productos para obtener el historial de items
        query = """
            SELECT
                v.id AS venta_id,
                v.fecha_venta,
                p.nombre AS producto_nombre,
                dv.cantidad,                                  -- Cantidad de este producto
                dv.subtotal AS total,                         -- Subtotal (precio * cantidad) de este item vendido
                u.nombre AS usuario_nombre,
                'Público General' AS cliente_nombre           -- Asume cliente genérico si no hay un sistema de clientes en ventas
            FROM
                ventas v
            INNER JOIN
                detalle_venta dv ON v.id = dv.venta_id
            INNER JOIN
                productos p ON dv.producto_id = p.id
            INNER JOIN
                usuarios u ON v.usuario_id = u.id
            WHERE 1=1
        """

        params = []

        if fecha_inicio:
            # Filtra por la fecha de inicio (solo el día)
            query += " AND DATE(v.fecha_venta) >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            # Filtra hasta el final del día de la fecha final (más robusto)
            query += " AND v.fecha_venta <= %s" 
            params.append(f"{fecha_fin} 23:59:59")

        query += " ORDER BY v.fecha_venta DESC"

        # Paginación/Límite
        if limit > 0:
            query += " LIMIT %s"
            params.append(limit)
        if offset and offset > 0:
            query += " OFFSET %s"
            params.append(offset)
            
        cursor.execute(query, params)
        ventas = cursor.fetchall()

        return True, ventas

    except Exception as e:
        logger.exception(f"Error al cargar el historial de ventas: {e}")
        return False, f"❌ Error al cargar el historial: {str(e)}"
    finally:
        # Asegurar el cierre de recursos
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn and hasattr(conn, 'is_connected') and conn.is_connected():
            try:
                conn.close()
            except Exception:
                pass


def get_sales_history_simple():
    """Función para cargar datos por defecto (últimos 30 días, 1000 registros)."""
    hace_30 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    hoy = datetime.now().strftime('%Y-%m-%d')

    return get_sales_history(
        fecha_inicio=hace_30,
        fecha_fin=hoy,
        limit=1000
    )