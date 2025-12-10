# sales_history_controller.py
from database import conectar
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def get_sales_history_simple():
    """Versión simple para compatibilidad con tu vista actual."""
    # Por defecto: últimos 30 días, máximo 1000 registros
    hoy = datetime.now().date()
    hace_30 = hoy - timedelta(days=30)

    return get_sales_history(
        fecha_inicio=hace_30.strftime('%Y-%m-%d'),
        fecha_fin=hoy.strftime('%Y-%m-%d'),
        limit=1000
    )

def get_sales_history(fecha_inicio=None, fecha_fin=None, limit=1000, offset=0):
    """
    Obtiene el historial de ventas con soporte para filtrado y paginación.
    """
    conn = None
    cursor = None

    try:
        conn = conectar()
        if not conn:
            return False, "❌ Error: No se pudo conectar a la base de datos."

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                v.id AS venta_id,
                v.fecha_venta,
                p.nombre AS producto_nombre,
                v.cantidad,
                v.total,
                'Público General' AS cliente_nombre,  -- Mostrará 'Público General' para todas las ventas
                u.nombre AS usuario_nombre
            FROM ventas v
            INNER JOIN productos p ON v.producto_id = p.id
            INNER JOIN usuarios u ON v.usuario_id = u.id
            WHERE 1=1
        """

        params = []

        if fecha_inicio:
            query += " AND v.fecha_venta >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            query += " AND v.fecha_venta < %s"
            params.append(f"{fecha_fin} 23:59:59")

        query += " ORDER BY v.fecha_venta DESC"

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)
        if offset:
            query += " OFFSET %s"
            params.append(offset)

        cursor.execute(query, params)
        ventas = cursor.fetchall()

        return True, ventas

    except Exception as e:
        logger.exception("Error inesperado en get_sales_history")
        return False, f"❌ Error al cargar el historial: {str(e)}"
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn and conn.is_connected():
            try:
                conn.close()
            except:
                pass