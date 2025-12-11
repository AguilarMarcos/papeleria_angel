#Dashboard_View.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Importaciones inmediatas (seguras)
from products_view import ProductsView
from user_view import UserView
from suppliers_view import ProveedoresView
from sales_view import VentasView
from sales_history_view import SalesHistoryView


class DashboardView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.active_subwindow = None  
        self.loading_overlay = None

        self.root.title(f"📦 Papelería Ángel - Dashboard | {usuario['nombre']}")
        self.root.geometry("1080x680")
        self.root.configure(bg="#f5f7fa")
        self.root.minsize(900, 600)

        header = tk.Frame(root, bg="#2c3e50", height=80)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"👋 Bienvenido, {usuario['nombre']} ({usuario['rol'].capitalize()})",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2c3e50"
        ).pack(side="left", padx=20, pady=20)

        tk.Button(
            header,
            text="🚪 Cerrar Sesión",
            command=self.logout,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=10,
            width=12
        ).pack(side="right", padx=20, pady=20)

        content = tk.Frame(root, bg="#f5f7fa")
        content.pack(fill="both", expand=True, padx=40, pady=30)

        for i in range(2):
            content.grid_columnconfigure(i, weight=1)

        buttons = [
            ("📦 Productos", self.open_products, "#3498db"),
            ("💰 Ventas", self.show_sales, "#2ecc71"),
            ("👥 Clientes", self.open_clients, "#1abc9c"),
            ("📝 Pedidos Clientes (Abonos)", self.open_client_orders, "#f1c40f"),
            ("📜 Historial de Ventas", self.show_sales_history, "#f39c12")
        ]

        if usuario['rol'] == 'admin':
            buttons.extend([
                ("🏭 Proveedores", self.open_suppliers, "#9b59b6"),
                ("⚙️ Administración de Usuarios", self.open_users, "#e67e22")
            ])

        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(
                content,
                text=text,
                command=command,
                bg=color,
                fg="white",
                font=("Arial", 13, "bold"),
                height=2,
                relief="flat",
                activebackground=self._lighten_color(color),
                cursor="hand2"
            )
            row = i // 2
            col = i % 2
            btn.grid(row=row, column=col, padx=15, pady=12, sticky="ew")

        footer = tk.Label(
            root,
            text="Papelería Ángel © 2025 - Sistema de Gestión Digital",
            bg="#ecf0f1",
            fg="#7f8c8d",
            font=("Arial", 10)
        )
        footer.pack(side="bottom", fill="x", ipady=8)

    def _lighten_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _show_loading(self):
        if self.loading_overlay:
            return
        self.loading_overlay = tk.Toplevel(self.root)
        self.loading_overlay.geometry(self.root.geometry())
        self.loading_overlay.overrideredirect(True)
        self.loading_overlay.attributes("-alpha", 0.8)
        self.loading_overlay.configure(bg="white")

        tk.Label(
            self.loading_overlay,
            text="⏳ Cargando vista...\nPor favor, espere.",
            font=("Arial", 16),
            bg="white",
            fg="#2c3e50"
        ).place(relx=0.5, rely=0.5, anchor="center")

        self.root.update_idletasks()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.loading_overlay.geometry(f"+{x}+{y}")

    def _hide_loading(self):
        if self.loading_overlay:
            self.loading_overlay.destroy()
            self.loading_overlay = None

    def _open_view_safe(self, ViewClass, module_name=""):
        if self.active_subwindow:
            messagebox.showinfo("ℹ️ Información", "Ya hay una ventana abierta. Ciérrela primero.", parent=self.root)
            return

        self._show_loading()
        self.root.update_idletasks()

        window = None

        def load_in_thread():
            nonlocal window
            try:
                window = tk.Toplevel(self.root)
                window.title(f"{ViewClass.__name__} - Papelería Ángel")
                window.geometry("1000x700")
                window.minsize(800, 500)

                window.protocol("WM_DELETE_WINDOW", lambda: self._on_close_window(window))

                self.root.withdraw()
                self.active_subwindow = window

                ViewClass(window, self.usuario)

                self.root.after(1, lambda: self._finalize_view_display(window))

            except Exception as e:
                messagebox.showerror(
                    "❌ Error al cargar vista",
                    f"No se pudo abrir {module_name or ViewClass.__name__}:\n{e}",
                    parent=self.root
                )
                if window:
                    self._on_close_window(window)
                self.root.after(100, self._hide_loading)

        threading.Thread(target=load_in_thread, daemon=True).start()

    def _finalize_view_display(self, window):
        if window and window.winfo_exists():
            window.lift()
            window.focus_force()

        self._hide_loading()

    def _on_close_window(self, window):
        """Cierre seguro de la ventana con limpieza."""
        try:
            if window and window.winfo_exists():
                window.destroy()
        except:
            pass

        # Limpieza en el hilo principal
        self.root.after(20, self._window_closed_cleanup)

    def _window_closed_cleanup(self):
        self.active_subwindow = None
        self.root.deiconify()

    # ---------------------
    # APERTURA DE VISTAS
    # ---------------------

    def open_products(self):
        self._open_view_safe(ProductsView, "Productos")

    def open_users(self):
        self._open_view_safe(UserView, "Usuarios")

    def open_suppliers(self):
        self._open_view_safe(ProveedoresView, "Proveedores")

    def show_sales(self):
        self._open_view_safe(VentasView, "Ventas")

    def open_clients(self):
        try:
            from clientes_view import ClientsView
            self._open_view_safe(ClientsView, "Clientes")
        except ImportError as e:
            self._hide_loading()
            messagebox.showerror("❌ Módulo faltante", f"No se encontró 'clientes_view.py':\n{e}")

    def open_client_orders(self):
        try:
            from client_orders_view import ClientOrdersView
            self._open_view_safe(ClientOrdersView, "Pedidos a Clientes")
        except ImportError as e:
            self._hide_loading()
            messagebox.showerror("❌ Módulo faltante", f"No se encontró 'client_orders_view.py':\n{e}")

    def show_sales_history(self):
        self._open_view_safe(SalesHistoryView, "Historial de Ventas")

    def logout(self):
        if messagebox.askyesno("❓ Cerrar sesión", "¿Está seguro que desea cerrar sesión?", parent=self.root):
            self.root.destroy()
            try:
                from login import LoginView
                root = tk.Tk()
                LoginView(root)
                root.mainloop()
            except Exception as e:
                messagebox.showerror("❌ Error", f"No se pudo abrir login:\n{e}")
