# export_controller.py
import csv
import os
from pathlib import Path
from datetime import datetime
import sys


def _get_safe_documents_path():
    """Obtiene una ruta segura en la carpeta de Documentos del usuario."""
    try:
        if sys.platform == "win32":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                documentos = winreg.QueryValueEx(key, "{F42EE2D3-909F-4907-8871-4C22FC0BF756}")[0]
        elif sys.platform == "darwin":  # macOS
            documentos = os.path.expanduser("~/Documents")
        else:  # Linux
            documentos = os.path.expanduser("~/Documentos")
            if not os.path.exists(documentos):
                documentos = os.path.expanduser("~/Documents")

        Path(documentos).mkdir(parents=True, exist_ok=True)
        return documentos
    except Exception:
        return os.getcwd()


def generar_ruta_csv(nombre_base, extension="csv"):
    """Genera una ruta segura en Documentos con timestamp."""
    nombre_limpio = "".join(c if c.isalnum() or c in "._- " else "_" for c in str(nombre_base))
    nombre_limpio = nombre_limpio.strip().replace(" ", "_")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{nombre_limpio}_{timestamp}.{extension}"
    
    documentos = _get_safe_documents_path()
    return os.path.join(documentos, nombre_archivo)


def exportar_a_csv(datos, ruta_archivo, encabezados):
    """
    Exporta datos a CSV con soporte completo para Excel (Windows/macOS/Linux).
    """
    if not datos:
        return False, "⚠️ No hay datos para exportar."

    try:
        with open(ruta_archivo, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(
                file,
                fieldnames=encabezados,
                extrasaction='ignore',
                quoting=csv.QUOTE_MINIMAL,
                escapechar='\\'
            )
            writer.writeheader()
            
            filas_limpias = []
            for fila in datos:
                fila_limpia = {}
                for k, v in fila.items():
                    if v is None:
                        fila_limpia[k] = ""
                    elif isinstance(v, (int, float)):
                        if isinstance(v, float):
                            fila_limpia[k] = f"{v:.2f}"
                        else:
                            fila_limpia[k] = str(v)
                    elif hasattr(v, 'strftime'):  # datetime
                        fila_limpia[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        fila_limpia[k] = str(v).strip()
                filas_limpias.append(fila_limpia)
            
            writer.writerows(filas_limpias)
        
        if os.path.exists(ruta_archivo) and os.path.getsize(ruta_archivo) > 0:
            return True, f"✅ Exportado exitosamente:\n{ruta_archivo}"
        else:
            return False, "❌ Error: El archivo CSV está vacío o no se creó."

    except PermissionError:
        return False, (
            "❌ Acceso denegado.\n"
            "→ Asegúrese de que el archivo no esté abierto en Excel.\n"
            "→ Intente guardar en otra carpeta (ej. Escritorio)."
        )
    except Exception as e:
        return False, f"❌ Error al exportar:\n{str(e)}"