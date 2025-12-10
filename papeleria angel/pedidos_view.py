#pedidos_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# IMPORTS CENTRALES
from pedidos_controller import (
    obtener_pedidos, obtener_detalle_pedido, registrar_pedido,
    actualizar_estado_pedido, eliminar_pedido,
    obtener_pedido_por_id, update_pedido_details
)
import suppliers_controller
import products_controller


def validar_fecha(fecha_str):
    """Valida y normaliza fecha en formato YYYY-MM-DD."""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


class PedidosView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("🛒 Gestión de Pedidos (Órdenes de Compra)")
        self.root.geometry("1300x700")
        self.root.configure(bg="#f5f7fa")

        # Estado de ventanas abiertas
        self.add_pedido_window = None
        self.edit_pedido_window = None
        self.detail_window = None

        # Caché de datos (carga una vez)
        self.proveedor_id_map = {}
        self.product_map = {}
        self._load_all_data()  # ← Carga inicial

        # --- Estilos ---
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#d3e0e7", foreground="#2c3e50")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.map("TButton", background=[("active", "#3498db")])
        style.configure("T.Blue.TButton", background="#3498db", foreground="white", font=("Arial", 10, "bold"))
        style.configure("T.Red.TButton", background="#e74c3c", foreground="white", font=("Arial", 10, "bold"))

        # --- Barra superior ---
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🛒 Órdenes de Compra a Proveedores", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)
        tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10)).pack(anchor="nw", padx=20, pady=10)

        # --- Frame principal ---
        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Tabla de pedidos ---
        list_frame = ttk.LabelFrame(main_frame, text="Listado de Órdenes", padding="10")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("ID", "Proveedor", "Fecha Pedido", "Total", "Estado")
        self.pedidos_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        for col in columns:
            self.pedidos_tree.heading(col, text=col)
            self.pedidos_tree.column(col, width=150, anchor=tk.CENTER)
        self.pedidos_tree.column("Proveedor", width=250, anchor=tk.W)
        self.pedidos_tree.pack(fill="both", expand=True)

        # Tags de estado
        self.pedidos_tree.tag_configure('pendiente', background='#fcf8e3')  # Amarillo
        self.pedidos_tree.tag_configure('recibido', background='#d4edda')   # Verde
        self.pedidos_tree.tag_configure('cancelado', background='#f8d7da')  # Rojo

        # --- Botones ---
        btn_frame = tk.Frame(main_frame, bg="#f5f7fa")
        btn_frame.pack(fill="x", pady=10, padx=10)
        ttk.Button(btn_frame, text="➕ Nuevo Pedido", command=self.open_add_pedido_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔍 Ver Detalle", command=self.show_detalle_pedido).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Editar Pedido", command=self.open_edit_pedido_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Marcar como Recibido", command=lambda: self.update_status('Recibido')).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Eliminar Pedido", command=self.delete_pedido_action, style="T.Red.TButton").pack(side="left", padx=5)

        self.load_pedidos()

    def _load_all_data(self):
        """Carga proveedores y productos una sola vez (al inicio)."""
        try:
            # Proveedores
            proveedores = suppliers_controller.obtener_todos_proveedores() or []
            self.proveedor_id_map = {p['nombre_empresa']: p['id'] for p in proveedores}
            if not self.proveedor_id_map:
                print("⚠️ Advertencia: No se encontraron proveedores.")

            # Productos
            productos = products_controller.get_all_products() or []
            self.product_map = {}
            for p in productos:
                key = f"{p['nombre']} (ID: {p['id']})"
                self.product_map[key] = {
                    'id': p['id'],
                    'precio_compra': float(p.get('precio_compra', 0)),
                    'stock_actual': p.get('stock', 0)
                }
            if not self.product_map:
                print("⚠️ Advertencia: No se encontraron productos.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar datos maestros:\n{e}")

    def is_window_open(self, window_ref):
        """Verifica si una ventana Toplevel está abierta."""
        return window_ref and window_ref.winfo_exists()

    def load_pedidos(self):
        for item in self.pedidos_tree.get_children():
            self.pedidos_tree.delete(item)

        try:
            pedidos = obtener_pedidos() or []
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los pedidos:\n{e}")
            return

        for p in pedidos:
            estado = str(p.get('estado', 'Pendiente')).lower()
            self.pedidos_tree.insert("", tk.END, values=(
                p['id'],
                p.get('proveedor', '—') or '—',
                p.get('fecha_pedido', '—'),
                f"${p.get('total', 0):.2f}",
                p.get('estado', 'Pendiente')
            ), tags=(estado,))

    def show_detalle_pedido(self):
        if self.is_window_open(self.detail_window):
            self.detail_window.focus()
            return

        selected_item = self.pedidos_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido para ver el detalle.")
            return

        pedido_id = self.pedidos_tree.item(selected_item, 'values')[0]
        try:
            detalle = obtener_detalle_pedido(pedido_id) or []
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo cargar el detalle:\n{e}")
            return

        if not detalle:
            messagebox.showinfo("ℹ️ Información", f"El pedido {pedido_id} no tiene productos registrados.")
            return

        detail_window = tk.Toplevel(self.root)
        self.detail_window = detail_window
        detail_window.title(f"🔍 Detalle del Pedido #{pedido_id}")
        detail_window.geometry("650x400")
        detail_window.transient(self.root)
        detail_window.grab_set()

        def on_close():
            self.detail_window = None
            detail_window.destroy()
        detail_window.protocol("WM_DELETE_WINDOW", on_close)

        frame = ttk.LabelFrame(detail_window, text=f"Productos en Pedido #{pedido_id}", padding="10")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Nombre", "Cantidad", "Precio Unit.", "Subtotal")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)
        tree.column("Nombre", width=200, anchor=tk.W)

        for d in detalle:
            tree.insert("", tk.END, values=(
                d.get('producto_id', '—'),
                d.get('producto_nombre', '—'),
                d.get('cantidad', 0),
                f"${d.get('precio_unitario', 0):.2f}",
                f"${d.get('subtotal', 0):.2f}"
            ))

        tree.pack(fill="both", expand=True)
        detail_window.wait_window()

    def open_add_pedido_window(self):
        if self.is_window_open(self.add_pedido_window):
            self.add_pedido_window.focus()
            return

        if not self.proveedor_id_map:
            messagebox.showerror("❌ Error", "No hay proveedores registrados. Registre al menos uno.")
            return
        if not self.product_map:
            messagebox.showerror("❌ Error", "No hay productos registrados. Registre al menos uno.")
            return

        add_window = tk.Toplevel(self.root)
        self.add_pedido_window = add_window
        add_window.title("➕ Nuevo Pedido de Compra")
        add_window.geometry("850x600")
        add_window.transient(self.root)
        add_window.grab_set()

        def on_close():
            self.add_pedido_window = None
            add_window.destroy()
        add_window.protocol("WM_DELETE_WINDOW", on_close)

        self.new_pedido_items = []

        # --- Datos generales ---
        input_frame = ttk.LabelFrame(add_window, text="Datos del Pedido", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Proveedor: *").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.proveedor_var = tk.StringVar()
        combo_prov = ttk.Combobox(input_frame, textvariable=self.proveedor_var, values=list(self.proveedor_id_map.keys()), state="readonly", width=40)
        combo_prov.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        combo_prov.current(0)

        ttk.Label(input_frame, text="Fecha Entrega Estimada (YYYY-MM-DD): *").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.fecha_estimada_entry = ttk.Entry(input_frame, width=30)
        self.fecha_estimada_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.fecha_estimada_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        # --- Añadir productos ---
        product_frame = ttk.LabelFrame(add_window, text="Añadir Productos", padding="10")
        product_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(product_frame, text="Producto: *").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.producto_var = tk.StringVar()
        self.producto_combobox = ttk.Combobox(product_frame, textvariable=self.producto_var, values=list(self.product_map.keys()), state="readonly", width=35)
        self.producto_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # ✅ Autocompletar precio al seleccionar producto
        def on_product_select(event):
            prod_key = self.producto_var.get()
            prod = self.product_map.get(prod_key)
            if prod:
                self.precio_unitario_entry.delete(0, tk.END)
                self.precio_unitario_entry.insert(0, f"{prod['precio_compra']:.2f}")
                # Opcional: mostrar stock actual
                self.stock_label.config(text=f"Stock actual: {prod['stock_actual']}")
        self.producto_combobox.bind("<<ComboboxSelected>>", on_product_select)

        ttk.Label(product_frame, text="Cantidad: *").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.cantidad_entry = ttk.Entry(product_frame, width=10)
        self.cantidad_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.cantidad_entry.insert(0, "1")

        ttk.Label(product_frame, text="Precio Unit. Compra ($): *").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.precio_unitario_entry = ttk.Entry(product_frame, width=15)
        self.precio_unitario_entry.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        self.stock_label = ttk.Label(product_frame, text="Stock actual: —", foreground="#6c757d")
        self.stock_label.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Button(product_frame, text="⊕ Agregar Ítem", command=self.add_item_to_pedido).grid(row=0, column=6, padx=10, pady=5)

        # --- Ítems actuales ---
        items_frame = ttk.LabelFrame(add_window, text="Ítems del Pedido", padding="10")
        items_frame.pack(fill="both", expand=True, padx=10, pady=5)

        items_columns = ("ID", "Nombre", "Cantidad", "Precio Unit.", "Subtotal")
        self.items_tree = ttk.Treeview(items_frame, columns=items_columns, show="headings")
        for col in items_columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=100, anchor=tk.CENTER)
        self.items_tree.column("Nombre", width=180, anchor=tk.W)
        self.items_tree.pack(fill="both", expand=True)

        ttk.Button(items_frame, text="➖ Quitar Ítem", command=self.remove_item_from_pedido).pack(pady=5)

        # --- Botón final ---
        ttk.Button(add_window, text="💾 Registrar Pedido", command=self.final_register_pedido, style="T.Blue.TButton").pack(pady=10)

    def open_edit_pedido_window(self):
        if self.is_window_open(self.edit_pedido_window):
            self.edit_pedido_window.focus()
            return

        selected_item = self.pedidos_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido para editar.")
            return

        pedido_id = self.pedidos_tree.item(selected_item, 'values')[0]
        try:
            pedido = obtener_pedido_por_id(pedido_id)
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo cargar el pedido:\n{e}")
            return

        if not pedido:
            messagebox.showerror("❌ Error", "Pedido no encontrado.")
            return

        edit_window = tk.Toplevel(self.root)
        self.edit_pedido_window = edit_window
        edit_window.title(f"✏️ Editar Pedido #{pedido_id}")
        edit_window.geometry("500x220")
        edit_window.transient(self.root)
        edit_window.grab_set()

        def on_close():
            self.edit_pedido_window = None
            edit_window.destroy()
        edit_window.protocol("WM_DELETE_WINDOW", on_close)

        frame = ttk.LabelFrame(edit_window, text="Editar Datos Generales", padding="10")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Proveedor
        ttk.Label(frame, text="Proveedor: *").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.edit_proveedor_var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=self.edit_proveedor_var, values=list(self.proveedor_id_map.keys()), state="readonly", width=35)
        combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        # Set current
        current_prov_name = pedido.get('proveedor_nombre')
        if current_prov_name in self.proveedor_id_map:
            combo.set(current_prov_name)
        else:
            combo.set(list(self.proveedor_id_map.keys())[0] if self.proveedor_id_map else "")

        # Fecha
        ttk.Label(frame, text="Fecha Entrega Estimada (YYYY-MM-DD): *").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        current_fecha = str(pedido.get('fecha_entrega_estimada') or '')
        self.edit_fecha_entrega_var = tk.StringVar(value=current_fecha)
        fecha_entry = ttk.Entry(frame, textvariable=self.edit_fecha_entrega_var, width=30)
        fecha_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # ⚠️ Mensaje explicativo
        ttk.Label(frame, text="⚠️ Nota: Solo se pueden editar datos generales.\nPara modificar productos, cancele este pedido y cree uno nuevo.",
                  foreground="#e74c3c", font=("Arial", 9)).grid(row=2, column=0, columnspan=2, pady=5)

        def save_changes():
            try:
                new_prov_name = self.edit_proveedor_var.get().strip()
                new_fecha = self.edit_fecha_entrega_var.get().strip()

                if not new_prov_name or not new_fecha:
                    messagebox.showerror("❌ Error", "Complete todos los campos obligatorios.", parent=edit_window)
                    return

                proveedor_id = self.proveedor_id_map.get(new_prov_name)
                if not proveedor_id:
                    messagebox.showerror("❌ Error", "Proveedor seleccionado inválido.", parent=edit_window)
                    return

                fecha_valida = validar_fecha(new_fecha)
                if not fecha_valida:
                    messagebox.showerror("❌ Error", "Formato de fecha inválido. Use YYYY-MM-DD.", parent=edit_window)
                    return

                exito, mensaje = update_pedido_details(pedido_id, proveedor_id, fecha_valida)
                if exito:
                    messagebox.showinfo("✅ Éxito", mensaje, parent=edit_window)
                    self.load_pedidos()
                    edit_window.destroy()
                else:
                    messagebox.showerror("❌ Error", mensaje, parent=edit_window)

            except Exception as e:
                messagebox.showerror("❌ Error", f"Error al guardar:\n{e}", parent=edit_window)

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="💾 Guardar", command=save_changes, style="T.Blue.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=edit_window.destroy).pack(side="left", padx=5)

    # --- Funciones de ítems ---
    def add_item_to_pedido(self):
        try:
            prod_key = self.producto_var.get().strip()
            if not prod_key:
                messagebox.showerror("❌ Error", "Seleccione un producto.")
                return

            cantidad_str = self.cantidad_entry.get().strip()
            precio_str = self.precio_unitario_entry.get().strip()

            if not cantidad_str or not precio_str:
                messagebox.showerror("❌ Error", "Complete Cantidad y Precio.")
                return

            cantidad = int(cantidad_str)
            precio = float(precio_str.replace(',', '.'))

            if cantidad <= 0:
                messagebox.showerror("❌ Error", "La cantidad debe ser mayor a cero.")
                return
            if precio <= 0:
                messagebox.showerror("❌ Error", "El precio debe ser mayor a cero.")
                return

            producto = self.product_map.get(prod_key)
            if not producto:
                messagebox.showerror("❌ Error", "Producto seleccionado inválido.")
                return

            subtotal = round(cantidad * precio, 2)
            item = {
                'producto_id': producto['id'],
                'producto_nombre': prod_key.split(' (')[0],
                'cantidad': cantidad,
                'precio_unitario': precio,
                'subtotal': subtotal
            }

            self.new_pedido_items.append(item)
            self.update_items_tree()

            # Limpiar campos, pero mantener producto seleccionado para seguir añadiendo
            self.cantidad_entry.delete(0, tk.END)
            self.cantidad_entry.insert(0, "1")
            self.precio_unitario_entry.focus()

        except ValueError:
            messagebox.showerror("❌ Error", "Cantidad y Precio deben ser números válidos.")

    def remove_item_from_pedido(self):
        selected = self.items_tree.focus()
        if not selected:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un ítem para eliminar.")
            return

        idx = self.items_tree.index(selected)
        if 0 <= idx < len(self.new_pedido_items):
            self.new_pedido_items.pop(idx)
            self.update_items_tree()

    def update_items_tree(self):
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        for item in self.new_pedido_items:
            self.items_tree.insert("", tk.END, values=(
                item['producto_id'],
                item['producto_nombre'],
                item['cantidad'],
                f"${item['precio_unitario']:.2f}",
                f"${item['subtotal']:.2f}"
            ))

    # --- Registro final ---
    def final_register_pedido(self):
        if not self.new_pedido_items:
            messagebox.showerror("❌ Error", "Debe agregar al menos un producto al pedido.")
            return

        proveedor_name = self.proveedor_var.get().strip()
        if not proveedor_name:
            messagebox.showerror("❌ Error", "Seleccione un proveedor.")
            return

        fecha_estimada = self.fecha_estimada_entry.get().strip()
        fecha_valida = validar_fecha(fecha_estimada)
        if not fecha_valida:
            messagebox.showerror("❌ Error", "Fecha de entrega inválida. Use formato YYYY-MM-DD.")
            return

        try:
            proveedor_id = self.proveedor_id_map[proveedor_name]
            items = [
                {
                    'producto_id': item['producto_id'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'subtotal': item['subtotal']
                }
                for item in self.new_pedido_items
            ]

            exito, mensaje = registrar_pedido(proveedor_id, items, fecha_valida)
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje)
                self.load_pedidos()
                self.add_pedido_window.destroy()
                self.add_pedido_window = None
            else:
                messagebox.showerror("❌ Error", mensaje)

        except KeyError:
            messagebox.showerror("❌ Error", "Proveedor seleccionado inválido.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al registrar pedido:\n{e}")

    # --- Otras acciones ---
    def update_status(self, new_status):
        selected = self.pedidos_tree.focus()
        if not selected:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido.")
            return

        values = self.pedidos_tree.item(selected, 'values')
        pedido_id = values[0]
        estado_actual = values[4]

        if estado_actual == new_status:
            messagebox.showinfo("ℹ️ Información", f"El pedido ya está en estado '{new_status}'.")
            return

        if new_status == 'Recibido':
            if not messagebox.askyesno("❓ Confirmar Recepción",
                f"¿Confirma que ha recibido el Pedido #{pedido_id}?\n"
                "⚠️ Esto aumentará el stock de los productos incluidos.",
                parent=self.root):
                return

        try:
            exito, mensaje = actualizar_estado_pedido(pedido_id, new_status)
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje)
                self.load_pedidos()
            else:
                messagebox.showerror("❌ Error", mensaje)
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al actualizar estado:\n{e}")

    def delete_pedido_action(self):
        selected = self.pedidos_tree.focus()
        if not selected:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido.")
            return

        values = self.pedidos_tree.item(selected, 'values')
        pedido_id, proveedor = values[0], values[1]

        if not messagebox.askyesno("❓ Confirmar Eliminación",
            f"¿Eliminar el Pedido #{pedido_id} al proveedor {proveedor}?\n"
            "⚠️ Esta acción es irreversible.",
            parent=self.root):
            return

        try:
            exito, mensaje = eliminar_pedido(pedido_id)
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje)
                self.load_pedidos()
            else:
                messagebox.showerror("❌ Error", mensaje)
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al eliminar:\n{e}")

    def back_to_dashboard(self):
        self.root.destroy()
        try:
            from dashboard_view import DashboardView
            root = tk.Tk()
            DashboardView(root, self.usuario)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo abrir el dashboard:\n{e}")