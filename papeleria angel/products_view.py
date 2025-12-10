# products_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from products_controller import get_all_products, add_product, update_product, delete_product
from suppliers_controller import obtener_todos_proveedores
from datetime import datetime


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


class ProductsView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("📦 Gestión de Productos - Papelería Ángel")
        self.root.geometry("1250x700")
        self.root.configure(bg="#f5f7fa")

        # Barra superior
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="📦 Gestión de Productos", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(
            side="left", padx=20, pady=10
        )
        tk.Button(
            top_bar,
            text="🚪 Cerrar Sesión",
            command=self.confirmar_cierre,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=10,
        ).pack(side="right", padx=20, pady=10)

        # Botón volver
        back_btn = tk.Button(
            root,
            text="← Volver al Dashboard",
            command=self.back_to_dashboard,
            bg="#6c757d",
            fg="white",
            font=("Arial", 10),
        )
        back_btn.pack(anchor="nw", padx=20, pady=10)

        # Frame principal
        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Formulario
        self.create_form(main_frame)

        # Tabla
        self.create_table(main_frame)

        self.load_products()

    def create_form(self, parent):
        form_frame = tk.LabelFrame(
            parent,
            text="Agregar Nuevo Producto",
            font=("Arial", 12, "bold"),
            bg="#f5f7fa",
            padx=15,
            pady=15,
        )
        form_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Entradas
        labels = [
            "Nombre:",
            "Descripción:",
            "Precio Compra:",
            "Precio Venta:",
            "Stock:",
            "Categoría:",
            "Proveedor:",
            "Fecha Ingreso:",
        ]
        self.entries = {}
        for i, text in enumerate(labels):
            tk.Label(form_frame, text=text, bg="#f5f7fa", font=("Arial", 11)).grid(
                row=i, column=0, sticky="w", pady=5
            )

        # Campos específicos
        self.name_entry = tk.Entry(form_frame, font=("Arial", 12), width=30, relief="solid", bd=1)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        self.desc_entry = tk.Entry(form_frame, font=("Arial", 12), width=30, relief="solid", bd=1)
        self.desc_entry.grid(row=1, column=1, padx=10, pady=5)

        self.buy_price_entry = tk.Entry(form_frame, font=("Arial", 12), width=15, relief="solid", bd=1)
        self.buy_price_entry.grid(row=2, column=1, padx=10, pady=5)

        self.sell_price_entry = tk.Entry(form_frame, font=("Arial", 12), width=15, relief="solid", bd=1)
        self.sell_price_entry.grid(row=3, column=1, padx=10, pady=5)

        self.stock_entry = tk.Entry(form_frame, font=("Arial", 12), width=15, relief="solid", bd=1)
        self.stock_entry.grid(row=4, column=1, padx=10, pady=5)

        self.category_entry = tk.Entry(form_frame, font=("Arial", 12), width=30, relief="solid", bd=1)
        self.category_entry.grid(row=5, column=1, padx=10, pady=5)

        # Proveedor (Combobox)
        try:
            proveedores = obtener_todos_proveedores()
            if proveedores is None:
                proveedores = []
            self.lista_proveedores = [f"{p['id']} - {p['nombre_empresa']}" for p in proveedores]
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los proveedores:\n{e}", parent=self.root)
            self.lista_proveedores = []

        self.proveedor_var = tk.StringVar()
        self.proveedor_combo = ttk.Combobox(
            form_frame,
            textvariable=self.proveedor_var,
            values=self.lista_proveedores,
            state="readonly",
            width=28,
        )
        self.proveedor_combo.grid(row=6, column=1, padx=10, pady=5)
        if self.lista_proveedores:
            self.proveedor_combo.set(self.lista_proveedores[0])
        else:
            self.proveedor_combo.set("")

        # Fecha
        self.date_entry = tk.Entry(form_frame, font=("Arial", 12), width=15, relief="solid", bd=1)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=7, column=1, padx=10, pady=5)

        # Botón
        add_btn = tk.Button(
            form_frame,
            text="➕ Agregar Producto",
            command=self.add_product,
            bg="#2ecc71",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        add_btn.grid(row=8, column=0, columnspan=2, pady=15)

    def create_table(self, parent):
        table_frame = tk.LabelFrame(
            parent,
            text="Lista de Productos",
            font=("Arial", 12, "bold"),
            bg="#f5f7fa",
            padx=15,
            pady=15,
        )
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        columns = ("ID", "Nombre", "Descripción", "Compra", "Venta", "Stock", "Categoría", "Proveedor", "Fecha", "Editar", "Eliminar")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        col_widths = {
            "ID": 60,
            "Nombre": 150,
            "Descripción": 200,
            "Compra": 80,
            "Venta": 80,
            "Stock": 60,
            "Categoría": 100,
            "Proveedor": 120,
            "Fecha": 100,
            "Editar": 60,
            "Eliminar": 60,
        }

        for col in columns:
            self.tree.heading(col, text=col)
            width = col_widths.get(col, 100)
            anchor = "center" if col in ("Editar", "Eliminar", "ID", "Stock") else "w"
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

        btn_frame = tk.Frame(table_frame, bg="#f5f7fa")
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame,
            text="🔄 Actualizar",
            command=self.load_products,
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
        ).pack()

    def extract_proveedor_id(self, proveedor_str):
        """Extrae el ID del proveedor desde el string 'ID - Nombre'."""
        if not proveedor_str.strip():
            return None
        try:
            return int(proveedor_str.split(" - ")[0])
        except (ValueError, IndexError):
            return None

    def validate_inputs(self, nombre, precio_compra, precio_venta, stock, proveedor_str, categoria, fecha="", is_edit=False):
        # Campos obligatorios
        required = [nombre, precio_compra, precio_venta, stock, proveedor_str, categoria]
        if not all(required):
            return False, "Los campos Nombre, Precio Compra, Precio Venta, Stock, Categoría y Proveedor son obligatorios."

        # Conversión numérica
        try:
            precio_compra = float(precio_compra)
            precio_venta = float(precio_venta)
            stock = int(stock)
        except ValueError:
            return False, "Precio Compra, Precio Venta y Stock deben ser números válidos."

        # Proveedor ID
        proveedor_id = self.extract_proveedor_id(proveedor_str)
        if proveedor_id is None:
            return False, "Proveedor inválido. Seleccione uno de la lista."

        # Fecha (solo en alta)
        if not is_edit:
            if not validate_date(fecha):
                return False, "La fecha debe tener formato YYYY-MM-DD."

        return True, (nombre, precio_compra, precio_venta, stock, categoria, proveedor_id, fecha if not is_edit else None)

    def add_product(self):
        nombre = self.name_entry.get().strip()
        descripcion = self.desc_entry.get().strip()
        precio_compra = self.buy_price_entry.get().strip()
        precio_venta = self.sell_price_entry.get().strip()
        stock = self.stock_entry.get().strip()
        categoria = self.category_entry.get().strip()
        proveedor_seleccionado = self.proveedor_var.get().strip()
        fecha_ingreso = self.date_entry.get().strip()

        if not nombre or not precio_compra or not precio_venta or not stock or not proveedor_seleccionado:
            messagebox.showwarning("⚠️ Campos obligatorios", "Los campos Nombre, Precio Compra, Precio Venta, Stock, Categoría y Proveedor son obligatorios.")
            return
        try:
            precio_compra = float(precio_compra)
            precio_venta = float(precio_venta)
            # Convertir stock a entero
            stock_int = int(stock)
        except ValueError:
            messagebox.showerror("❌ Formato inválido", "Precio y stock deben ser números válidos.")
            return

        # 3. 🟢 CORRECCIÓN: Asegurar que el valor del Combobox también se limpie de espacios
        try:
            # Si el proveedor_seleccionado está vacío, la validación 1 ya lo atrapó.
            # Pero si no tiene el formato 'ID - Nombre', el split fallará.
            proveedor_id = int(proveedor_seleccionado.split(" - ")[0])
        except Exception:
            # Este mensaje es más informativo si el usuario no tiene proveedores
            messagebox.showerror("❌ Proveedor Inválido", "No se pudo obtener el ID del proveedor. Asegúrese de que ha seleccionado un proveedor de la lista y que existen proveedores registrados.")
            return

        # 4. Llamada al controlador
        success, msg = add_product(nombre, descripcion, precio_compra, precio_venta, stock_int, categoria, proveedor_id, fecha_ingreso)
        if success:
            messagebox.showinfo("✅ Éxito", msg)
            self.clear_form()
            self.load_products()
        else:
            messagebox.showerror("❌ Error", msg)

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.buy_price_entry.delete(0, tk.END)
        self.sell_price_entry.delete(0, tk.END)
        self.stock_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        if self.lista_proveedores:
            self.proveedor_combo.set(self.lista_proveedores[0])
        else:
            self.proveedor_var.set("")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def load_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            productos = get_all_products()
            if productos is None:
                productos = []
            for p in productos:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        p["id"],
                        p["nombre"],
                        p["descripcion"],
                        f"${p['precio_compra']:.2f}",
                        f"${p['precio_venta']:.2f}",
                        p["stock"],
                        p["categoria"],
                        p.get("proveedor_nombre", "—"),
                        p["fecha_ingreso"],
                        "✏️",
                        "🗑️",
                    ),
                )
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los productos:\n{e}")

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, "values")
        if not values:
            return
        producto_id = values[0]
        if column == "#10":  # Editar
            self.edit_selected_direct(producto_id)
        elif column == "#11":  # Eliminar
            self.delete_selected_direct(producto_id)

    def edit_selected_direct(self, producto_id):
        try:
            productos = get_all_products()
            producto = next((p for p in productos if str(p["id"]) == str(producto_id)), None)
        except Exception:
            producto = None

        if not producto:
            messagebox.showerror("❌ Error", "Producto no encontrado.")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Editar Producto ID: {producto_id}")
        edit_window.geometry("450x500")
        edit_window.configure(bg="#f5f7fa")
        edit_window.transient(self.root)
        edit_window.grab_set()

        tk.Label(edit_window, text=f"Editar Producto: {producto['nombre']}", font=("Arial", 14, "bold"), bg="#f5f7fa").pack(pady=10)

        form = tk.Frame(edit_window, bg="#f5f7fa")
        form.pack(padx=20, pady=10, fill="x")

        fields = [
            ("Nombre:", producto["nombre"]),
            ("Descripción:", producto["descripcion"]),
            ("Precio Compra:", producto["precio_compra"]),
            ("Precio Venta:", producto["precio_venta"]),
            ("Stock:", producto["stock"]),
            ("Categoría:", producto["categoria"]),
        ]

        entries = {}
        for i, (label, value) in enumerate(fields):
            tk.Label(form, text=label, bg="#f5f7fa", font=("Arial", 11)).grid(row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(form, font=("Arial", 12), width=30, relief="solid", bd=1)
            entry.insert(0, str(value))
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[label] = entry

        # Proveedor
        tk.Label(form, text="Proveedor:", bg="#f5f7fa", font=("Arial", 11)).grid(row=6, column=0, sticky="w", pady=5)
        try:
            proveedores = obtener_todos_proveedores() or []
            lista = [f"{p['id']} - {p['nombre_empresa']}" for p in proveedores]
        except Exception:
            lista = []
        proveedor_var = tk.StringVar()
        combo = ttk.Combobox(form, textvariable=proveedor_var, values=lista, state="readonly", width=28)
        combo.grid(row=6, column=1, padx=10, pady=5)
        # Set current
        current = f"{producto['proveedor_id']} - {producto.get('proveedor_nombre', 'Desconocido')}"
        if current in lista:
            combo.set(current)
        elif lista:
            combo.set(lista[0])

        def save_changes():
            nombre = entries["Nombre:"].get().strip()
            descripcion = entries["Descripción:"].get().strip()
            precio_compra = entries["Precio Compra:"].get().strip()
            precio_venta = entries["Precio Venta:"].get().strip()
            stock = entries["Stock:"].get().strip()
            categoria = entries["Categoría:"].get().strip()
            proveedor_str = proveedor_var.get()

            valid, result = self.validate_inputs(
                nombre, precio_compra, precio_venta, stock, proveedor_str, categoria, is_edit=True
            )
            if not valid:
                messagebox.showwarning("⚠️ Validación", result, parent=edit_window)
                return

            success, msg = update_product(producto_id, *result[:5], descripcion, result[5])  # id, nombre, pc, pv, stock, cat, descr, prov_id
            if success:
                messagebox.showinfo("✅ Éxito", "Producto actualizado correctamente.", parent=edit_window)
                edit_window.destroy()
                self.load_products()
            else:
                messagebox.showerror("❌ Error", msg, parent=edit_window)

        btn_frame = tk.Frame(edit_window, bg="#f5f7fa")
        btn_frame.pack(pady=20)
        tk.Button(
            btn_frame,
            text="💾 Guardar",
            command=save_changes,
            bg="#2ecc71",
            fg="white",
            font=("Arial", 11, "bold"),
            width=12,
        ).pack(side="left", padx=5)
        tk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=edit_window.destroy,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            width=10,
        ).pack(side="left", padx=5)

    def delete_selected_direct(self, producto_id):
        if messagebox.askyesno(
            "❓ Confirmar eliminación",
            f"¿Está seguro de eliminar el producto ID {producto_id}?\n⚠️ Esta acción lo ocultará del inventario.",
            parent=self.root,
        ):
            success, msg = delete_product(producto_id)
            if success:
                messagebox.showinfo("✅ Éxito", "Producto eliminado correctamente.", parent=self.root)
                self.load_products()
            else:
                messagebox.showerror("❌ Error", msg, parent=self.root)

    # 🔴 Importante: No crear Tk() dentro de Tk()
    def back_to_dashboard(self):
        from dashboard_view import DashboardView
        self.root.destroy()
        # Ideal: que el main.py o app.py gestione esto.
        # Por ahora, asumimos que el dashboard espera un root nuevo.
        root = tk.Tk()
        DashboardView(root, self.usuario)
        root.mainloop()

    def confirmar_cierre(self):
        if messagebox.askyesno(
            "❓ Cerrar sesión",
            f"¿Está seguro que desea cerrar sesión como {self.usuario.get('nombre', 'Usuario')}?",
        ):
            from login import LoginView
            self.root.destroy()
            root = tk.Tk()
            LoginView(root)
            root.mainloop()
        else:
            messagebox.showinfo("ℹ️ Información", "Se ha cancelado el cierre de sesión.")