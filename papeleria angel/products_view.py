import tkinter as tk
from tkinter import ttk, messagebox
from products_controller import get_all_products, add_product, update_product, delete_product
from suppliers_controller import obtener_todos_proveedores
from datetime import datetime
from export_controller import exportar_a_csv


class ProductsView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("📦 Gestión de Productos - Papelería Ángel")
        self.root.geometry("1250x700")
        self.root.configure(bg="#f5f7fa")

        # ---- TOP BAR ----
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="📦 Gestión de Productos",
                 font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(
            side="left", padx=20, pady=10
        )

        tk.Button(
            top_bar, text="🚪 Cerrar Sesión", command=self.confirmar_cierre,
            bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=10
        ).pack(side="right", padx=20, pady=10)

        # ---- BOTÓN VOLVER ----
        tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard,
                  bg="#6c757d", fg="white", font=("Arial", 10)).pack(anchor="nw", padx=20, pady=10)

        # ---- FRAME PRINCIPAL ----
        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ---- BOTONES ----
        buttons = tk.Frame(main_frame, bg="#f5f7fa")
        buttons.pack(fill="x", pady=(0, 10))

        ttk.Button(buttons, text="➕ Agregar Producto",
                   command=self.open_add_product_window).pack(side="left", padx=5)
        ttk.Button(buttons, text="✏️ Editar Producto",
                   command=self.open_edit_product_window).pack(side="left", padx=5)
        ttk.Button(buttons, text="🗑️ Eliminar Producto",
                   command=self.delete_selected_product).pack(side="left", padx=5)
        ttk.Button(buttons, text="⬇️ Exportar CSV",
                   command=self.export_to_csv).pack(side="right", padx=5)

        # ---- TABLA ----
        self.products_tree = ttk.Treeview(
            main_frame,
            columns=("ID", "Nombre", "Descripción", "P. Compra", "P. Venta",
                     "Stock", "Categoría", "Proveedor", "F. Ingreso"),
            show="headings"
        )
        self.products_tree.pack(fill="both", expand=True)

        col_widths = {
            "ID": 40, "Nombre": 180, "Descripción": 200,
            "P. Compra": 90, "P. Venta": 90,
            "Stock": 60, "Categoría": 100,
            "Proveedor": 120, "F. Ingreso": 100
        }

        for col, width in col_widths.items():
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=width, anchor=tk.CENTER)

        self.products_tree.bind("<Double-1>", self._on_double_click)

        self.load_products()

    # -------------------------------------------------------------------
    # Cargar productos en tabla
    # -------------------------------------------------------------------
    def load_products(self):
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        productos = get_all_products()
        if not productos:
            return

        for p in productos:
            fecha = p["fecha_ingreso"]

            if isinstance(fecha, datetime):
                fecha = fecha.strftime("%Y-%m-%d")

            self.products_tree.insert("", "end", values=(
                p["id"],
                p["nombre"],
                p["descripcion"][:30] + "..." if len(p["descripcion"]) > 30 else p["descripcion"],
                f"${p['precio_compra']:.2f}",
                f"${p['precio_venta']:.2f}",
                p["stock"],
                p["categoria"],
                p["proveedor_nombre"],
                fecha if fecha else "N/A"
            ))

    # -------------------------------------------------------------------
    # Obtener producto seleccionado
    # -------------------------------------------------------------------
    def _get_selected_product_id(self):
        selected = self.products_tree.focus()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto.")
            return None
        return self.products_tree.item(selected, "values")[0]

    # -------------------------------------------------------------------
    # Agregar producto
    # -------------------------------------------------------------------
    def open_add_product_window(self):
        self._open_product_form(mode="add")

    # -------------------------------------------------------------------
    # Editar producto
    # -------------------------------------------------------------------
    def open_edit_product_window(self):
        producto_id = self._get_selected_product_id()
        if not producto_id:
            return
        self._open_product_form(mode="edit", producto_id=producto_id)

    # -------------------------------------------------------------------
    # Formulario add/edit (reutilizable)
    # -------------------------------------------------------------------
    def _open_product_form(self, mode, producto_id=None):
        productos = get_all_products()
        producto = None

        if mode == "edit":
            producto = next((p for p in productos if str(p["id"]) == str(producto_id)), None)
            if not producto:
                messagebox.showerror("Error", "Producto no encontrado.")
                return

        win = tk.Toplevel(self.root)
        win.title("Agregar Producto" if mode == "add" else "Editar Producto")
        win.geometry("400x550")
        win.grab_set()

        proveedores = obtener_todos_proveedores()
        proveedor_dict = {p["nombre_empresa"]: p["id"] for p in proveedores}

        campos = ["Nombre", "Descripción", "Precio Compra", "Precio Venta",
                  "Stock", "Categoría", "Proveedor", "Fecha Ingreso (YYYY-MM-DD)"]

        entries = {}

        for campo in campos:
            tk.Label(win, text=campo).pack()
            if campo == "Proveedor":
                cb = ttk.Combobox(win, values=list(proveedor_dict.keys()))
                if mode == "edit":
                    cb.set(producto.get("proveedor_nombre", ""))
                cb.pack()
                entries[campo] = cb
            else:
                e = tk.Entry(win)
                if mode == "edit":
                    key_map = {
                        "Nombre": "nombre",
                        "Descripción": "descripcion",
                        "Precio Compra": "precio_compra",
                        "Precio Venta": "precio_venta",
                        "Stock": "stock",
                        "Categoría": "categoria",
                        "Fecha Ingreso (YYYY-MM-DD)": "fecha_ingreso"
                    }
                    valor = producto.get(key_map[campo], "")
                    if isinstance(valor, datetime):
                        valor = valor.strftime("%Y-%m-%d")
                    e.insert(0, valor)
                else:
                    if campo == "Fecha Ingreso (YYYY-MM-DD)":
                        e.insert(0, datetime.now().strftime("%Y-%m-%d"))
                e.pack()
                entries[campo] = e

        def guardar():
            try:
                nombre = entries["Nombre"].get()
                descripcion = entries["Descripción"].get()
                precio_compra = float(entries["Precio Compra"].get())
                precio_venta = float(entries["Precio Venta"].get())
                stock = int(entries["Stock"].get())
                categoria = entries["Categoría"].get()
                prov_nom = entries["Proveedor"].get()
                fecha = entries["Fecha Ingreso (YYYY-MM-DD)"].get()

                if prov_nom not in proveedor_dict:
                    messagebox.showerror("Error", "Proveedor inválido.")
                    return
                prov_id = proveedor_dict[prov_nom]

                if mode == "add":
                    ok, msg = add_product(nombre, descripcion, precio_compra,
                                          precio_venta, stock, categoria, prov_id, fecha)
                else:
                    # Corregido: solo 8 argumentos para update_product
                    ok, msg = update_product(producto_id, nombre, descripcion,
                                             precio_compra, precio_venta,
                                             stock, categoria, prov_id)

                if ok:
                    messagebox.showinfo("Éxito", msg)
                    win.destroy()
                    self.load_products()
                else:
                    messagebox.showerror("Error", msg)

            except ValueError:
                messagebox.showerror("Error", "Revise los valores numéricos.")

        tk.Button(win, text="Guardar", bg="#27ae60", fg="white",
                  command=guardar).pack(pady=10)

    # -------------------------------------------------------------------
    # Eliminar
    # -------------------------------------------------------------------
    def delete_selected_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Selección requerida", "Seleccione un producto para eliminar.")
            return

        item = self.products_tree.item(selected[0])
        product_id = item["values"][0]

        if messagebox.askyesno("🗑 Eliminar", "¿Desea eliminar este producto?"):
            success, msg = delete_product(product_id)
            if success:
                messagebox.showinfo("✅ Eliminado", msg)
                self.load_products()
            else:
                messagebox.showerror("❌ Error", msg)

    # -------------------------------------------------------------------
    # Exportar CSV
    # -------------------------------------------------------------------
    def export_to_csv(self):
        exportar_a_csv()
        messagebox.showinfo("Éxito", "Archivo CSV generado correctamente.")

    # -------------------------------------------------------------------
    # Cerrar ventana
    # -------------------------------------------------------------------
    def confirmar_cierre(self):
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?"):
            self.root.destroy()

    # -------------------------------------------------------------------
    # Volver al dashboard
    # -------------------------------------------------------------------
    def back_to_dashboard(self):
        from dashboard_view import DashboardView
        self.root.destroy()
        root = tk.Tk()
        DashboardView(root, self.usuario)
        root.mainloop()

    # -------------------------------------------------------------------
    # Doble clic → editar
    # -------------------------------------------------------------------
    def _on_double_click(self, event):
        self.open_edit_product_window()
