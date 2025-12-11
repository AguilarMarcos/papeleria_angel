# sales_history_view.py - CÓDIGO PERFECCIONADO
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from export_controller import exportar_a_csv, generar_ruta_csv
# Importamos la función principal para poder usar filtros
from sales_history_controller import get_sales_history 
from datetime import datetime, timedelta

class SalesHistoryView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("📜 Historial de Ventas")
        self.root.geometry("1300x750") 
        self.root.configure(bg="#f5f7fa")
        self.root.minsize(1150, 600)

        # Variables de filtro (30 días por defecto)
        hoy = datetime.now().strftime('%Y-%m-%d')
        hace_30 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        self.fecha_inicio_var = tk.StringVar(value=hace_30)
        self.fecha_fin_var = tk.StringVar(value=hoy)
        self.all_sales_data = [] # Para almacenar los datos cargados para exportación

        style = ttk.Style()
        style.configure("T.Green.TButton", background="#2ecc71", foreground="white", font=("Arial", 10, "bold"))
        style.configure("T.Blue.TButton", background="#3498db", foreground="white", font=("Arial", 10, "bold"))
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#d3e0e7", foreground="#2c3e50")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)

        # --- Barra superior ---
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="📜 Historial de Ventas", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)
        
        back_btn = tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10))
        back_btn.pack(anchor="nw", padx=20, pady=(10, 0))

        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Filtros y Botones de Acción ---
        filter_frame = ttk.LabelFrame(main_frame, text="🔍 Opciones de Filtro y Acción", padding="10")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        # Filtro de Fecha Inicio
        ttk.Label(filter_frame, text="Fecha Inicio (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(filter_frame, textvariable=self.fecha_inicio_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Filtro de Fecha Fin
        ttk.Label(filter_frame, text="Fecha Fin (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(filter_frame, textvariable=self.fecha_fin_var, width=15).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Botón de Cargar
        ttk.Button(filter_frame, text="🔄 Cargar / Aplicar Filtros", command=self.load_history, style="T.Blue.TButton").grid(row=0, column=4, padx=15, pady=5, sticky="w")
        
        # Botón de Exportar
        ttk.Button(filter_frame, text="📄 Exportar a CSV", command=self.export_data, style="T.Green.TButton").grid(row=0, column=5, padx=15, pady=5, sticky="w")

        # --- Treeview de Historial ---
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True)

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        # Columnas del Treeview
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=("ID", "Fecha", "Producto", "Cantidad", "Subtotal Item", "Vendedor"),
            show="headings", 
            yscrollcommand=tree_scroll.set
        )
        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Definición de encabezados
        self.tree.heading("ID", text="ID Venta", anchor=tk.W)
        self.tree.heading("Fecha", text="Fecha y Hora", anchor=tk.W)
        self.tree.heading("Producto", text="Producto", anchor=tk.W)
        self.tree.heading("Cantidad", text="Cantidad", anchor=tk.W)
        self.tree.heading("Subtotal Item", text="Subtotal Item", anchor=tk.E) 
        self.tree.heading("Vendedor", text="Vendedor", anchor=tk.W)
        
        # Ajuste de columnas
        self.tree.column("ID", width=80, stretch=tk.NO)
        self.tree.column("Fecha", width=150, stretch=tk.NO)
        self.tree.column("Producto", width=350, anchor=tk.W)
        self.tree.column("Cantidad", width=80, stretch=tk.NO, anchor=tk.CENTER)
        self.tree.column("Subtotal Item", width=120, stretch=tk.NO, anchor=tk.E)
        self.tree.column("Vendedor", width=150, stretch=tk.NO, anchor=tk.W)
        
        # Cargar datos iniciales
        self.load_history()

    def load_history(self):
        """Carga el historial de ventas aplicando los filtros de fecha."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        fecha_inicio = self.fecha_inicio_var.get().strip()
        fecha_fin = self.fecha_fin_var.get().strip()
        
        if not self._validate_date_format(fecha_inicio) or not self._validate_date_format(fecha_fin):
            messagebox.showerror("❌ Error de Filtro", "El formato de fecha debe ser YYYY-MM-DD.")
            return

        # Usar la función principal del controlador con filtros
        success, data = get_sales_history(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limit=None)
        self.all_sales_data = data # Guardar la data para la exportación
        
        if success:
            for venta in data:
                # venta['total'] es ahora el subtotal del item
                self.tree.insert("", "end", values=(
                    venta['venta_id'],
                    venta['fecha_venta'],
                    venta['producto_nombre'],
                    venta['cantidad'],
                    f"${venta['total']:.2f}", # Subtotal Item formateado
                    venta['usuario_nombre']
                ))
            if not data:
                messagebox.showinfo("ℹ️ Sin Resultados", "No se encontraron ventas para el período seleccionado.")
        else:
            messagebox.showerror("❌ Error de Carga", data)

    def _validate_date_format(self, date_str):
        """Valida que la cadena tenga formato YYYY-MM-DD."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def export_data(self):
        """Exporta los datos actualmente cargados a un archivo CSV."""
        data = self.all_sales_data
        
        if not data:
            messagebox.showwarning("⚠️ Advertencia", "No hay datos de ventas para exportar. Por favor, cargue la información primero.")
            return

        # Definir el mapeo de keys del diccionario a nombres de columnas en español para el CSV
        export_map = {
            "venta_id": "ID_Venta",
            "fecha_venta": "Fecha_y_Hora",
            "producto_nombre": "Producto",
            "cantidad": "Cantidad",
            "total": "Subtotal_Item",
            "usuario_nombre": "Vendedor",
            "cliente_nombre": "Cliente"
        }
        
        # Crear la lista de diccionarios para exportar con los encabezados en español
        data_to_export = []
        raw_keys = list(export_map.keys())
        encabezados_csv = list(export_map.values())
        
        for row in data:
            new_row = {export_map[key]: row[key] for key in raw_keys}
            data_to_export.append(new_row)

        ruta_sugerida = generar_ruta_csv("Reporte_Ventas")
        
        ruta_guardado = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=ruta_sugerida,
            filetypes=[("Archivos CSV", "*.csv")]
        )

        if ruta_guardado:
            # Ahora usamos data_to_export con los encabezados en español
            exito, mensaje = exportar_a_csv(data_to_export, ruta_guardado, encabezados_csv)
            
            if exito:
                messagebox.showinfo("✅ Exportación Exitosa", mensaje)
            else:
                messagebox.showerror("❌ Error de Exportación", mensaje)

    def back_to_dashboard(self):
        self.root.destroy()
        # Se requiere la importación dentro de la función o fuera de la clase para evitar dependencia circular
        from dashboard_view import DashboardView
        root = tk.Tk()
        DashboardView(root, self.usuario)
        root.mainloop()