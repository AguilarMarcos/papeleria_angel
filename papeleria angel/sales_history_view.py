# sales_history_view.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from export_controller import exportar_a_csv, generar_ruta_csv
from sales_history_controller import get_sales_history_simple

class SalesHistoryView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("📜 Historial de Ventas")
        self.root.geometry("1150x700")
        self.root.configure(bg="#f5f7fa")

        style = ttk.Style()
        style.configure("T.Green.TButton", background="#2ecc71", foreground="white", font=("Arial", 10, "bold"))

        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="📜 Historial de Ventas", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)

        back_btn = tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10))
        back_btn.pack(anchor="nw", padx=20, pady=10)

        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        action_frame = tk.Frame(main_frame, bg="#f5f7fa")
        action_frame.pack(fill="x", pady=5)

        ttk.Button(
            action_frame,
            text="📄 Exportar a CSV",
            command=self.exportar_historial,
            style="T.Green.TButton"
        ).pack(side="left", padx=5)

        columns = ("ID Venta", "Fecha", "Producto", "Cantidad", "Total", "Cliente", "Vendedor")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        self.tree.column("Fecha", width=180, anchor="center")
        self.tree.column("Producto", width=250, anchor="w")
        self.tree.column("Total", width=100, anchor="e")

        self.tree.pack(fill="both", expand=True)

        self.load_history()

    def exportar_historial(self):
        success, data = get_sales_history_simple()

        if not success or not data:
            messagebox.showwarning("Advertencia", "No hay datos de historial para exportar.")
            return

        raw_keys = list(data[0].keys())

        ruta_sugerida = generar_ruta_csv("Reporte_Ventas")

        ruta_guardado = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=ruta_sugerida,
            filetypes=[("Archivos CSV", "*.csv")]
        )

        if ruta_guardado:
            exito, mensaje = exportar_a_csv(data, ruta_guardado, raw_keys)

            if exito:
                messagebox.showinfo("✅ Exportación Exitosa", mensaje)
            else:
                messagebox.showerror("❌ Error de Exportación", mensaje)

    def load_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        success, data = get_sales_history_simple()

        if success:
            for venta in data:
                self.tree.insert("", "end", values=(
                    venta['venta_id'],
                    venta['fecha_venta'],
                    venta['producto_nombre'],
                    venta['cantidad'],
                    f"${venta['total']:.2f}",
                    venta.get('cliente_nombre', 'N/A'),
                    venta['usuario_nombre']
                ))
        else:
            messagebox.showerror("❌ Error de Carga", data)

    def back_to_dashboard(self):
        self.root.destroy()
        from dashboard_view import DashboardView
        new_root = tk.Tk()
        DashboardView(new_root, self.usuario)
        new_root.mainloop()