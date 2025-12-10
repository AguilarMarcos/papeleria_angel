#clientes_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from clientes_controller import add_client, obtener_todos_clientes, update_client, delete_client
import re


class ClientsView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("👤 Gestión de Clientes - Papelería Ángel")
        self.root.geometry("1150x680")
        self.root.configure(bg="#f5f7fa")
        self.root.minsize(900, 600)

        # Estado
        self.active_edit_window = None
        self.clients_data = []

        # --- Estilos ---
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#d3e0e7")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.configure("T.Red.TButton", background="#e74c3c", foreground="white", font=("Arial", 10, "bold"))
        style.configure("T.Blue.TButton", background="#3498db", foreground="white", font=("Arial", 10, "bold"))

        # --- Barra superior ---
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="👤 Gestión de Clientes", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)
        tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10)).pack(anchor="nw", padx=20, pady=10)

        # --- Frame principal ---
        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Formulario (izquierda) ---
        form_frame = ttk.LabelFrame(main_frame, text="Registrar Nuevo Cliente", padding="15")
        form_frame.pack(side="left", fill="y", padx=(0, 10))

        self.nombre_var = tk.StringVar()
        self.apellido_var = tk.StringVar()
        self.telefono_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.direccion_var = tk.StringVar()

        self._create_input_field(form_frame, "Nombre *:", self.nombre_var, 0)
        self._create_input_field(form_frame, "Apellido:", self.apellido_var, 1)
        self._create_input_field(form_frame, "Teléfono *:", self.telefono_var, 2)
        self._create_input_field(form_frame, "Email:", self.email_var, 3)
        self._create_input_field(form_frame, "Dirección:", self.direccion_var, 4)

        ttk.Button(
            form_frame,
            text="✅ Agregar Cliente",
            command=self.add_client_action,
            style="T.Blue.TButton",
            width=25
        ).grid(row=5, column=0, columnspan=2, pady=20)

        # --- Tabla (derecha) ---
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(side="right", fill="both", expand=True)

        # Barra de búsqueda (opcional pero útil)
        search_frame = ttk.Frame(table_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(search_frame, text="🔍 Buscar:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left")
        self.search_var.trace("w", lambda *args: self.filter_clients())

        # Tabla
        columns = ("ID", "Nombre", "Apellido", "Teléfono", "Email", "Dirección")
        self.clients_tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        col_widths = {
            "ID": 50,
            "Nombre": 130,
            "Apellido": 120,
            "Teléfono": 110,
            "Email": 150,
            "Dirección": 180
        }
        for col in columns:
            self.clients_tree.heading(col, text=col)
            self.clients_tree.column(col, width=col_widths[col], anchor="w" if col in ("Nombre", "Apellido", "Dirección", "Email") else "center")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.clients_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.clients_tree.xview)
        self.clients_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.clients_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # Etiqueta vacía
        self.empty_label = tk.Label(
            table_frame,
            text="👋 No hay clientes registrados.\nUse el formulario para agregar uno.",
            bg="#f5f7fa",
            fg="#7f8c8d",
            font=("Arial", 12, "italic")
        )
        self.empty_label.pack_forget()

        # Botones de acción
        btn_frame = tk.Frame(table_frame, bg="#f5f7fa")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="✏️ Editar", command=self.edit_client_action, style="T.Blue.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Eliminar", command=self.delete_client_action, style="T.Red.TButton").pack(side="left", padx=5)

        # Cargar datos
        self.load_clients()

    def _create_input_field(self, parent, label_text, var, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=8, sticky="w")
        entry = ttk.Entry(parent, textvariable=var, width=30)
        entry.grid(row=row, column=1, padx=5, pady=8)
        if "Teléfono" in label_text:
            entry.bind("<KeyRelease>", self._format_phone)
        return entry

    def _format_phone(self, event):
        """Formatea teléfono: 1234567890 → (123) 456-7890"""
        val = self.telefono_var.get().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if val.isdigit() and len(val) >= 10:
            val = f"({val[:3]}) {val[3:6]}-{val[6:10]}"
        self.telefono_var.set(val[:14])  # Máx 14 chars

    def _validate_inputs(self, nombre, telefono, email=""):
        """Valida datos antes de enviar."""
        if not nombre.strip():
            return False, "El nombre es obligatorio."
        if not telefono.strip():
            return False, "El teléfono es obligatorio."
        
        # Validar teléfono: debe tener 10+ dígitos
        clean_phone = re.sub(r'\D', '', telefono)
        if len(clean_phone) < 10:
            return False, "El teléfono debe tener al menos 10 dígitos."

        # Validar email (básico)
        if email.strip() and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False, "El email tiene un formato inválido."

        return True, ""

    def load_clients(self):
        """Carga clientes y actualiza UI."""
        try:
            self.clients_data = obtener_todos_clientes() or []
            self.filter_clients()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los clientes:\n{e}")

    def filter_clients(self, query=None):
        """Filtra clientes por búsqueda (case-insensitive)."""
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)

        query = (self.search_var.get() or "").lower().strip()

        filtered = []
        for c in self.clients_data:
            # Busca en nombre, apellido, teléfono, email
            search_text = f"{c.get('nombre','')} {c.get('apellido','')} {c.get('telefono','')} {c.get('email','')}".lower()
            if query in search_text:
                filtered.append(c)

        if filtered:
            self.empty_label.pack_forget()
            for c in filtered:
                self.clients_tree.insert("", tk.END, values=(
                    c['id'],
                    c.get('nombre', ''),
                    c.get('apellido', ''),
                    c.get('telefono', ''),
                    c.get('email', ''),
                    c.get('direccion', '')
                ))
        else:
            self.clients_tree.pack_forget()
            self.empty_label.pack(pady=40)

    def add_client_action(self):
        nombre = self.nombre_var.get().strip()
        apellido = self.apellido_var.get().strip()
        telefono = self.telefono_var.get().strip()
        email = self.email_var.get().strip()
        direccion = self.direccion_var.get().strip()

        valido, mensaje = self._validate_inputs(nombre, telefono, email)
        if not valido:
            messagebox.showerror("❌ Validación", mensaje)
            return

        try:
            exito, msg = add_client(nombre, apellido, telefono, email, direccion)
            if exito:
                messagebox.showinfo("✅ Éxito", msg)
                # ✅ Solo limpiar si éxito
                self.nombre_var.set("")
                self.apellido_var.set("")
                self.telefono_var.set("")
                self.email_var.set("")
                self.direccion_var.set("")
                self.load_clients()
                # Enfocar nombre para siguiente cliente
                self.root.focus_set()
            else:
                messagebox.showerror("❌ Error", msg)
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al registrar cliente:\n{e}")

    def edit_client_action(self):
        if self.active_edit_window:
            self.active_edit_window.focus()
            return

        selected = self.clients_tree.focus()
        if not selected:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un cliente para editar.")
            return

        values = self.clients_tree.item(selected, 'values')
        try:
            client_id = values[0]
            self.open_edit_window(
                client_id=client_id,
                nombre=values[1],
                apellido=values[2],
                telefono=values[3],
                email=values[4],
                direccion=values[5]
            )
        except IndexError:
            messagebox.showerror("❌ Error", "Datos del cliente incompletos.")

    def open_edit_window(self, client_id, nombre, apellido, telefono, email, direccion):
        if self.active_edit_window:
            self.active_edit_window.focus()
            return

        edit_window = tk.Toplevel(self.root)
        self.active_edit_window = edit_window
        edit_window.title(f"✏️ Editar Cliente ID: {client_id}")
        edit_window.geometry("450x380")
        edit_window.resizable(False, False)
        edit_window.grab_set()

        def on_close():
            self.active_edit_window = None
            edit_window.destroy()
        edit_window.protocol("WM_DELETE_WINDOW", on_close)

        frame = ttk.Frame(edit_window, padding="15")
        frame.pack(fill="both", expand=True)

        vars = {
            'nombre': tk.StringVar(value=nombre),
            'apellido': tk.StringVar(value=apellido),
            'telefono': tk.StringVar(value=telefono),
            'email': tk.StringVar(value=email),
            'direccion': tk.StringVar(value=direccion)
        }

        self._create_edit_field(frame, "Nombre *:", vars['nombre'], 0)
        self._create_edit_field(frame, "Apellido:", vars['apellido'], 1)
        tel_entry = self._create_edit_field(frame, "Teléfono *:", vars['telefono'], 2)
        tel_entry.bind("<KeyRelease>", self._format_phone)
        self._create_edit_field(frame, "Email:", vars['email'], 3)
        self._create_edit_field(frame, "Dirección:", vars['direccion'], 4)

        def save_changes():
            n = vars['nombre'].get().strip()
            a = vars['apellido'].get().strip()
            t = vars['telefono'].get().strip()
            e = vars['email'].get().strip()
            d = vars['direccion'].get().strip()

            valido, msg = self._validate_inputs(n, t, e)
            if not valido:
                messagebox.showerror("❌ Validación", msg, parent=edit_window)
                return

            try:
                exito, mensaje = update_client(client_id, n, a, t, d, e)
                if exito:
                    messagebox.showinfo("✅ Éxito", mensaje, parent=edit_window)
                    edit_window.destroy()
                    self.load_clients()
                else:
                    messagebox.showerror("❌ Error", mensaje, parent=edit_window)
            except Exception as ex:
                messagebox.showerror("❌ Error", f"Error al actualizar:\n{ex}", parent=edit_window)

        ttk.Button(
            frame,
            text="💾 Guardar Cambios",
            command=save_changes,
            style="T.Blue.TButton",
            width=20
        ).grid(row=5, column=0, columnspan=2, pady=20)

    def _create_edit_field(self, parent, label_text, var, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=8, sticky="w")
        entry = ttk.Entry(parent, textvariable=var, width=35)
        entry.grid(row=row, column=1, padx=5, pady=8)
        return entry

    def delete_client_action(self):
        selected = self.clients_tree.focus()
        if not selected:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un cliente para eliminar.")
            return

        values = self.clients_tree.item(selected, 'values')
        client_id, nombre = values[0], values[1]

        if not messagebox.askyesno(
            "❓ Confirmar eliminación",
            f"¿Eliminar cliente '{nombre}' (ID: {client_id})?\n⚠️ Esta acción es irreversible.",
            parent=self.root
        ):
            return

        try:
            exito, mensaje = delete_client(client_id)
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje)
                self.load_clients()
            else:
                messagebox.showerror("❌ Error", mensaje)
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al eliminar cliente:\n{e}")

    def back_to_dashboard(self):
        self.root.destroy()
        try:
            from dashboard_view import DashboardView
            root = tk.Tk()
            DashboardView(root, self.usuario)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo abrir el dashboard:\n{e}")