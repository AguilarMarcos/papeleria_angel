# sales_view.py - POS con carrito y control de ventana única

import tkinter as tk
from tkinter import ttk, messagebox
try:
    from clientes_controller import obtener_todos_clientes 
except ImportError:
    def obtener_todos_clientes(): return []

from sales_controller import registrar_venta, obtener_productos_activos

class VentasView:
    ventana_abierta = False  # 🔹 Control de ventana única

    def __init__(self, root, usuario):
        if VentasView.ventana_abierta:
            messagebox.showwarning("⚠️ Ventana Abierta", "Ya hay una ventana de ventas abierta. Ciérrela primero.")
            root.destroy()
            return

        VentasView.ventana_abierta = True
        self.root = root
        self.usuario = usuario
        self.root.title("💰 Punto de Venta (POS) - Papelería Ángel")
        self.root.geometry("1000x650")
        self.root.configure(bg="#f5f7fa")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.volver_dashboard)

        # --- Datos ---
        self.productos_list = []
        self.producto_id_map = {}
        self.carrito = {}
        self.total_venta = tk.DoubleVar(value=0.00)
        self.registrando = False

        self.cargar_productos()
        self.clientes_list = self.cargar_clientes()
        self.cliente_seleccionado = tk.StringVar(value="Público General")
        self.cliente_id_map = {f"{c.get('nombre', '')} {c.get('apellido', '')}".strip(): c['id'] for c in self.clientes_list}
        self.cliente_id_map["Público General"] = None

        self._setup_ui()

    # -------------------- UI --------------------
    def _setup_ui(self):
        # Estilos
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10, "bold"), padding=6)
        style.configure("Red.TButton", background="#e74c3c", foreground="white")
        style.configure("Green.TButton", background="#2ecc71", foreground="white")
        style.configure("Blue.TButton", background="#3498db", foreground="white")

        # Top bar
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="💰 Punto de Venta", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)
        tk.Button(top_bar, text="🚪 Cerrar Sesión", command=self.confirmar_cierre, bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=10).pack(side="right", padx=20, pady=10)

        # Frames principales
        main_frame = tk.Frame(self.root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        left_frame = ttk.LabelFrame(main_frame, text="Detalle de Producto", padding="10")
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        right_frame = ttk.LabelFrame(main_frame, text="Carrito de Compras", padding="10")
        right_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Combobox de productos
        self.product_combobox = self._create_combobox(left_frame, "Producto:", 0, list(self.producto_id_map.keys()))
        self.product_combobox.bind("<<ComboboxSelected>>", self.on_product_selected)

        self.stock_label = ttk.Label(left_frame, text="Stock Disponible: 0")
        self.stock_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.precio_unitario = tk.DoubleVar(value=0.00)
        ttk.Label(left_frame, text="Precio Unitario:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(left_frame, textvariable=self.precio_unitario, font=("Arial", 12, "bold"), foreground="#00796b").grid(row=3, column=1, sticky="w", padx=5, pady=5)

        self.cantidad_entry_var = tk.StringVar(value="1")
        self._create_input(left_frame, "Cantidad:", 4, self.cantidad_entry_var)

        self.add_btn = ttk.Button(left_frame, text="➕ Añadir al Carrito", command=self.add_to_cart, style="Blue.TButton")
        self.add_btn.grid(row=5, column=0, columnspan=2, pady=15, sticky="ew")

        # Cliente
        ttk.Label(left_frame, text="Cliente:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.client_combobox = ttk.Combobox(left_frame, textvariable=self.cliente_seleccionado, width=27, state="readonly")
        self.client_combobox['values'] = ["Público General"] + sorted(list(self.cliente_id_map.keys())[1:])
        self.client_combobox.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        # Carrito Treeview
        columns = ("ID", "Producto", "Cantidad", "P. Unitario", "Subtotal")
        self.cart_tree = ttk.Treeview(right_frame, columns=columns, show="headings")
        self.cart_tree.pack(fill="both", expand=True)
        for col in columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, anchor="center", width=100 if col not in ("Producto", "P. Unitario") else (200 if col=="Producto" else 80))

        bottom_frame = tk.Frame(right_frame, bg="#f5f7fa")
        bottom_frame.pack(fill="x", pady=10)
        tk.Label(bottom_frame, text="TOTAL:", font=("Arial", 16, "bold"), fg="#2c3e50", bg="#f5f7fa").pack(side="left", padx=10)
        tk.Label(bottom_frame, textvariable=self.total_venta, font=("Arial", 18, "bold"), fg="#e74c3c", bg="#f5f7fa").pack(side="left")
        tk.Label(bottom_frame, text=" $", font=("Arial", 18, "bold"), fg="#e74c3c", bg="#f5f7fa").pack(side="left")

        self.registrar_btn = ttk.Button(bottom_frame, text="✅ Registrar Venta", command=self.registrar_venta_action, style="Green.TButton")
        self.registrar_btn.pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="🗑️ Vaciar Carrito", command=self.clear_cart, style="Red.TButton").pack(side="right", padx=5)

        self.cart_tree.bind('<Delete>', self.remove_selected_from_cart)

    # -------------------- Métodos generales --------------------
    def volver_dashboard(self):
        VentasView.ventana_abierta = False
        self.root.destroy()
        try:
            from dashboard_view import DashboardView
            new_root = tk.Toplevel(self.root.master) if hasattr(self.root, 'master') else tk.Tk()
            DashboardView(new_root, self.usuario)
        except Exception:
            pass

    def confirmar_cierre(self):
        if messagebox.askyesno("❓ Cerrar sesión", f"¿Desea cerrar sesión como {self.usuario.get('nombre', 'Usuario')}?"):
            VentasView.ventana_abierta = False
            self.root.destroy()
            try:
                from login import LoginView
                root = tk.Tk()
                LoginView(root)
                root.mainloop()
            except Exception:
                pass

    # -------------------- Métodos de utilidad --------------------
    def _create_combobox(self, parent, label, row, values):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        cb = ttk.Combobox(parent, values=values, state="readonly", width=27)
        cb.grid(row=row, column=1, padx=5, pady=5)
        return cb

    def _create_input(self, parent, label, row, var):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        entry = ttk.Entry(parent, textvariable=var, width=30)
        entry.grid(row=row, column=1, padx=5, pady=5)
        return entry

    def cargar_productos(self):
        productos = obtener_productos_activos()
        self.productos_list = productos
        self.producto_id_map = {p['nombre']: p for p in productos}
        if hasattr(self, 'product_combobox'):
            nombres = sorted(list(self.producto_id_map.keys()))
            self.product_combobox['values'] = nombres
            if nombres:
                self.product_combobox.set(nombres[0])
                self.on_product_selected()
            else:
                self.product_combobox.set("")
                self.stock_label.config(text="Stock Disponible: 0")
                self.precio_unitario.set(0.00)

    def cargar_clientes(self):
        try:
            return obtener_todos_clientes()
        except Exception:
            return []
