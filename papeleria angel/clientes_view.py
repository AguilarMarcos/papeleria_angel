import tkinter as tk
from tkinter import ttk, messagebox
from clientes_controller import add_client, obtener_todos_clientes, update_client, delete_client

class ClientsView:
    # 🔹 Bandera para controlar si hay una ventana de clientes abierta
    ventana_abierta = False

    def __init__(self, root, usuario):
        if ClientsView.ventana_abierta:
            messagebox.showwarning("⚠️ Ventana Abierta", "Ya hay una ventana de Clientes abierta. Ciérrela primero.")
            root.destroy()
            return

        ClientsView.ventana_abierta = True  # Marcar la ventana como abierta

        self.root = root
        self.usuario = usuario
        self.root.title("👤 Gestión de Clientes - Papelería Ángel")
        self.root.geometry("1150x680")
        self.root.configure(bg="#f5f7fa")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.back_to_dashboard)
        
        self.active_edit_window = None
        
        self._setup_styles()
        self._setup_ui()
        self.load_clients()

    # ------------------- Estilos -------------------
    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#d3e0e7", foreground="#2c3e50")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.configure("T.Red.TButton", background="#e74c3c", foreground="white", font=("Arial", 10, "bold"))
        style.configure("T.Blue.TButton", background="#3498db", foreground="white", font=("Arial", 10, "bold"))
        style.configure("T.Green.TButton", background="#2ecc71", foreground="white", font=("Arial", 10, "bold"))

    # ------------------- Interfaz -------------------
    def _setup_ui(self):
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="👤 Gestión de Clientes", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)
        
        tk.Button(self.root, text="← Volver al Dashboard", command=self.back_to_dashboard,
                  bg="#6c757d", fg="white", font=("Arial", 10)).pack(anchor="nw", padx=20, pady=10)

        main_frame = tk.Frame(self.root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Formulario de clientes
        form_frame = ttk.LabelFrame(main_frame, text="Nuevo Cliente", padding="10 10 10 10")
        form_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.vars = {
            'nombre': tk.StringVar(),
            'apellido': tk.StringVar(),
            'telefono': tk.StringVar(),
            'direccion': tk.StringVar(),
            'email': tk.StringVar()
        }

        self._create_field(form_frame, "Nombre:", self.vars['nombre'], 0)
        self._create_field(form_frame, "Apellido:", self.vars['apellido'], 1)
        self._create_field(form_frame, "Teléfono (Mín. 10 dig.):", self.vars['telefono'], 2)
        self._create_field(form_frame, "Dirección:", self.vars['direccion'], 3)
        self._create_field(form_frame, "Email (Opcional):", self.vars['email'], 4)

        ttk.Button(form_frame, text="➕ Agregar Cliente", command=self.add_client_action, style="T.Green.TButton").grid(
            row=5, column=0, columnspan=2, pady=15, sticky="ew"
        )

        # Tabla de clientes
        table_frame = tk.Frame(main_frame, bg="#f5f7fa")
        table_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.clients_tree = self._create_treeview(table_frame)
        
        # Botones de acción
        action_frame = tk.Frame(table_frame, bg="#f5f7fa")
        action_frame.pack(fill="x", pady=10)
        ttk.Button(action_frame, text="✏️ Editar Seleccionado", command=self.edit_client_action, style="T.Blue.TButton").pack(side="left", padx=5)
        ttk.Button(action_frame, text="🗑️ Eliminar Seleccionado", command=self.delete_client_action, style="T.Red.TButton").pack(side="left", padx=5)

    # ------------------- Campos -------------------
    def _create_field(self, parent, label_text, var, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=8, sticky="w")
        entry = ttk.Entry(parent, textvariable=var, width=35)
        entry.grid(row=row, column=1, padx=5, pady=8)
        return entry

    def _create_treeview(self, parent):
        cols = ("ID", "Nombre", "Apellido", "Teléfono", "Dirección", "Email")
        tree = ttk.Treeview(parent, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100 if col != "ID" else 40, anchor="center")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        return tree

    # ------------------- Funciones de clientes -------------------
    def load_clients(self):
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
        clientes = obtener_todos_clientes()
        if clientes is None:
            messagebox.showerror("❌ Error de Carga", "No se pudo cargar los clientes.", parent=self.root)
            return
        for c in clientes:
            self.clients_tree.insert("", "end", values=(c['id'], c['nombre'], c['apellido'], c['telefono'], c['direccion'], c['email']))

    def add_client_action(self):
        nombre = self.vars['nombre'].get().strip()
        apellido = self.vars['apellido'].get().strip()
        telefono = self.vars['telefono'].get().strip()
        direccion = self.vars['direccion'].get().strip()
        email = self.vars['email'].get().strip()
        if not nombre or not telefono:
            messagebox.showwarning("⚠️ Campos Incompletos", "Los campos Nombre y Teléfono son obligatorios.", parent=self.root)
            return
        exito, mensaje = add_client(nombre, apellido, telefono, direccion, email)
        if exito:
            messagebox.showinfo("✅ Éxito", mensaje, parent=self.root)
            self.load_clients()
            for var in self.vars.values():
                var.set("")
        else:
            messagebox.showerror("❌ Error al Agregar", mensaje, parent=self.root)

    def edit_client_action(self):
        selected_item = self.clients_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un cliente para editar.", parent=self.root)
            return
        if self.active_edit_window and self.active_edit_window.winfo_exists():
            self.active_edit_window.focus()
            messagebox.showwarning("⚠️ Advertencia", "Ya hay una ventana de edición abierta.", parent=self.root)
            return
        values = self.clients_tree.item(selected_item, 'values')
        client_id = values[0]

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"✏️ Editar Cliente ID: {client_id}")
        edit_window.geometry("450x380")
        edit_window.configure(bg="#f5f7fa")
        edit_window.transient(self.root)
        edit_window.grab_set()
        self.active_edit_window = edit_window
        edit_window.protocol("WM_DELETE_WINDOW", lambda: self._close_edit_window(edit_window))

        frame = ttk.LabelFrame(edit_window, text="Detalles del Cliente", padding="15")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        edit_vars = {
            'nombre': tk.StringVar(value=values[1]),
            'apellido': tk.StringVar(value=values[2]),
            'telefono': tk.StringVar(value=values[3]),
            'direccion': tk.StringVar(value=values[4]),
            'email': tk.StringVar(value=values[5])
        }

        for i, (label, var) in enumerate(edit_vars.items()):
            self._create_edit_field(frame, label.capitalize() + ":", var, i)

        def save_changes():
            nombre = edit_vars['nombre'].get().strip()
            telefono = edit_vars['telefono'].get().strip()
            if not nombre or not telefono:
                messagebox.showwarning("⚠️ Campos Incompletos", "Los campos Nombre y Teléfono son obligatorios.", parent=edit_window)
                return
            exito, mensaje = update_client(client_id,
                                           edit_vars['nombre'].get(),
                                           edit_vars['apellido'].get(),
                                           edit_vars['telefono'].get(),
                                           edit_vars['direccion'].get(),
                                           edit_vars['email'].get())
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje, parent=edit_window)
                self.load_clients()
                self._close_edit_window(edit_window)
            else:
                messagebox.showerror("❌ Error al Actualizar", mensaje, parent=edit_window)

        ttk.Button(frame, text="💾 Guardar Cambios", command=save_changes, style="T.Blue.TButton").grid(row=5, column=0, columnspan=2, pady=15)

    def _create_edit_field(self, parent, label_text, var, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=8, sticky="w")
        entry = ttk.Entry(parent, textvariable=var, width=35)
        entry.grid(row=row, column=1, padx=5, pady=8)
        return entry

    def _close_edit_window(self, window):
        window.grab_release()
        window.destroy()
        self.active_edit_window = None

    def delete_client_action(self):
        selected_item = self.clients_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un cliente para eliminar.", parent=self.root)
            return
        values = self.clients_tree.item(selected_item, 'values')
        client_id, nombre = values[0], values[1]
        if not messagebox.askyesno("❓ Confirmar eliminación", f"¿Eliminar cliente '{nombre}' (ID: {client_id})?", parent=self.root):
            return
        exito, mensaje = delete_client(client_id)
        if exito:
            messagebox.showinfo("✅ Éxito", mensaje, parent=self.root)
            self.load_clients()
        else:
            messagebox.showerror("❌ Error", mensaje, parent=self.root)

    # ------------------- Dashboard -------------------
    def back_to_dashboard(self):
        """Vuelve al Dashboard y destruye la ventana actual"""
        ClientsView.ventana_abierta = False  # 🔹 Liberar bandera
        from dashboard_view import DashboardView
        self.root.destroy()
        root = tk.Tk()
        DashboardView(root, self.usuario)
        root.mainloop()
