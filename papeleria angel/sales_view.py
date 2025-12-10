import tkinter as tk
from tkinter import ttk, messagebox
from sales_controller import registrar_venta_completa, obtener_productos_activos
import sys
import os


class VentasView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("💰 Registrar Venta - Papelería Ángel")
        self.root.geometry("650x550")
        self.root.configure(bg="#f5f7fa")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.volver_dashboard)

        # Estado
        self.producto_id_map = {}  # {"Display Text": product_id}
        self.registrando = False

        # --- Barra superior ---
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="💰 Registrar Nueva Venta", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)
        tk.Button(
            top_bar,
            text="🚪 Cerrar Sesión",
            command=self.confirmar_cierre,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=10
        ).pack(side="right", padx=20, pady=20)

        back_btn = tk.Button(root, text="← Volver al Dashboard", command=self.volver_dashboard, bg="#6c757d", fg="white", font=("Arial", 10))
        back_btn.pack(anchor="nw", padx=20, pady=10)

        # --- Formulario ---
        form_frame = tk.Frame(root, bg="#f5f7fa", padx=30, pady=20)
        form_frame.pack(fill="both", expand=True)

        tk.Label(form_frame, text="Selecciona un producto:", bg="#f5f7fa", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))

        self.cargar_productos()
        if not self.producto_id_map:
            messagebox.showwarning("⚠️ Sin productos", "No hay productos disponibles para vender.", parent=root)
            self.root.after(500, self.volver_dashboard)
            return

        # ✅ ID-based mapping (no more .index()!)
        self.producto_var = tk.StringVar()
        self.producto_combo = ttk.Combobox(
            form_frame,
            textvariable=self.producto_var,
            values=list(self.producto_id_map.keys()),
            state="readonly",
            width=45,
            font=("Arial", 11)
        )
        self.producto_combo.pack(pady=5)
        self.producto_combo.current(0)
        self.producto_combo.bind("<<ComboboxSelected>>", self.actualizar_datos_producto)

        # Precio y cantidad
        tk.Label(form_frame, text="Precio unitario:", bg="#f5f7fa", font=("Arial", 12)).pack(anchor="w", pady=(15, 5))
        self.precio_label = tk.Label(form_frame, text="$0.00", bg="#f5f7fa", font=("Arial", 12, "bold"), fg="#27ae60")
        self.precio_label.pack(anchor="w")

        tk.Label(form_frame, text="Cantidad (máx. stock disponible):", bg="#f5f7fa", font=("Arial", 12, "bold")).pack(anchor="w", pady=(15, 5))
        self.cantidad_entry = tk.Entry(form_frame, font=("Arial", 12), width=10, relief="solid", bd=1)
        self.cantidad_entry.pack(anchor="w", pady=5)
        self.cantidad_entry.insert(0, "1")
        self.cantidad_entry.bind("<KeyRelease>", self.actualizar_total)
        
        # Stock actual (dinámico)
        self.stock_label = tk.Label(form_frame, text="📦 Stock: —", bg="#f5f7fa", font=("Arial", 10), fg="#8e44ad")
        self.stock_label.pack(anchor="w", pady=(2, 5))

        tk.Label(form_frame, text="Total:", bg="#f5f7fa", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))
        self.total_label = tk.Label(form_frame, text="$0.00", bg="#f5f7fa", font=("Arial", 14, "bold"), fg="#27ae60")
        self.total_label.pack(anchor="w")

        # Botones
        btn_frame = tk.Frame(form_frame, bg="#f5f7fa")
        btn_frame.pack(pady=25)
        
        self.registrar_btn = tk.Button(
            btn_frame,
            text="✅ Registrar Venta",
            command=self.registrar_venta,
            bg="#2ecc71",
            fg="white",
            font=("Arial", 12, "bold"),
            width=18
        )
        self.registrar_btn.pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=self.volver_dashboard,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 12, "bold"),
            width=12
        ).pack(side="left", padx=5)

        # Inicializar
        self.actualizar_datos_producto(None)

    def cargar_productos(self):
        """Carga productos y crea mapeo ID seguro."""
        try:
            productos = self.obtener_productos_actualizados()
            self.producto_id_map = {}
            for p in productos:
                # ✅ Seguro contra cambios en formato
                display = f"{p['nombre']} (ID: {p['id']}) - ${p['precio_venta']:.2f} | Stock: {p['stock']}"
                self.producto_id_map[display] = {
                    'id': p['id'],
                    'nombre': p['nombre'],
                    'precio': float(p['precio_venta']),
                    'stock': int(p['stock'])
                }
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los productos:\n{e}")

    def obtener_productos_actualizados(self):
        """Hook para sobrescribir en testing."""
        productos = obtener_productos_activos()
        # Asegurar tipos numéricos
        for p in productos:
            p['precio_venta'] = float(p.get('precio_venta', 0))
            p['stock'] = int(p.get('stock', 0))
        return productos

    def actualizar_datos_producto(self, event):
        """Actualiza precio, stock y total al cambiar producto."""
        display = self.producto_var.get()
        producto = self.producto_id_map.get(display)
        if producto:
            self.precio_label.config(text=f"${producto['precio']:.2f}")
            self.stock_label.config(text=f"📦 Stock actual: {producto['stock']} unidades")
            self.actualizar_total(None)

    def actualizar_total(self, event):
        """Calcula total y valida cantidad."""
        try:
            cantidad = int(self.cantidad_entry.get() or 1)
        except ValueError:
            cantidad = 1

        display = self.producto_var.get()
        producto = self.producto_id_map.get(display)
        if producto:
            # Asegurar cantidad válida
            if cantidad < 1:
                cantidad = 1
            elif cantidad > producto['stock']:
                messagebox.showinfo(
                    "ℹ️ Stock máximo",
                    f"Solo hay {producto['stock']} unidades disponibles.\nAjustando cantidad.",
                    parent=self.root
                )
                cantidad = producto['stock']

            self.cantidad_entry.delete(0, tk.END)
            self.cantidad_entry.insert(0, str(cantidad))

            total = producto['precio'] * cantidad
            self.total_label.config(text=f"${total:.2f}")

    def registrar_venta(self):
        if self.registrando:
            return  # Evita doble clic

        display = self.producto_var.get()
        producto = self.producto_id_map.get(display)
        if not producto:
            messagebox.showwarning("⚠️ Selección inválida", "Seleccione un producto de la lista.", parent=self.root)
            return

        try:
            cantidad = int(self.cantidad_entry.get())
            if cantidad <= 0 or cantidad > producto['stock']:
                messagebox.showerror("❌ Cantidad inválida", f"Ingrese una cantidad entre 1 y {producto['stock']}.", parent=self.root)
                return

            # 🔒 Bloquear UI
            self.registrando = True
            self.registrar_btn.config(state="disabled", text="⏳ Procesando...")
            self.root.update_idletasks()

            # ✅ Llamada ATÓMICA (venta + stock en una transacción)
            exito, mensaje = registrar_venta_completa(
                producto_id=producto['id'],
                usuario_id=self.usuario['id'],
                cantidad=cantidad,
                precio_unitario=producto['precio']
            )

            if exito:
                messagebox.showinfo(
                    "✅ ¡Venta Exitosa!",
                    f"Producto: {producto['nombre']}\nCantidad: {cantidad}\nTotal: ${producto['precio'] * cantidad:.2f}",
                    parent=self.root
                )
                self.root.after(300, self.volver_dashboard)
            else:
                messagebox.showerror("❌ Error", mensaje, parent=self.root)
                self.registrando = False
                self.registrar_btn.config(state="normal", text="✅ Registrar Venta")

        except Exception as e:
            messagebox.showerror("❌ Error inesperado", f"No se pudo registrar la venta:\n{e}", parent=self.root)
            self.registrando = False
            self.registrar_btn.config(state="normal", text="✅ Registrar Venta")

    def volver_dashboard(self):
        self.root.destroy()
        try:
            from dashboard_view import DashboardView
            root = tk.Tk()
            DashboardView(root, self.usuario)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo abrir el dashboard:\n{e}")

    def confirmar_cierre(self):
        if messagebox.askyesno("❓ Cerrar sesión", f"¿Cerrar sesión como {self.usuario.get('nombre', 'Usuario')}?"):
            self.root.destroy()
            try:
                from login import LoginView
                root = tk.Tk()
                LoginView(root)
                root.mainloop()
            except Exception as e:
                messagebox.showerror("❌ Error", f"No se pudo abrir el login:\n{e}")