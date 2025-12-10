# user_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from user_controller import get_all_users, add_user, update_user, delete_user

class UserView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("⚙️ Administración de Usuarios - Papelería Ángel")
        self.root.geometry("1000x600")
        self.root.configure(bg="#f5f7fa")

        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="⚙️ Administración de Usuarios", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)

        back_btn = tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10))
        back_btn.pack(anchor="nw", padx=20, pady=10)

        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        form_frame = ttk.LabelFrame(main_frame, text="Agregar Nuevo Usuario", padding="15")
        form_frame.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(form_frame, text="Nombre:", bg="#f5f7fa", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Correo:", bg="#f5f7fa", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
        self.email_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.email_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Contraseña:", bg="#f5f7fa", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(form_frame, show="*", font=("Arial", 12), width=25)
        self.password_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Rol:", bg="#f5f7fa", font=("Arial", 11)).grid(row=3, column=0, sticky="w", pady=5)
        self.rol_var = tk.StringVar(value="cajero")
        ttk.Combobox(form_frame, textvariable=self.rol_var, values=["cajero", "admin"], state="readonly", width=23).grid(row=3, column=1, padx=10, pady=5)

        tk.Button(form_frame, text="➕ Agregar Usuario", command=self.add_user, bg="#2ecc71", fg="white", font=("Arial", 11)).grid(row=4, column=0, columnspan=2, pady=15)

        table_frame = ttk.Frame(main_frame)
        table_frame.pack(side="right", fill="both", expand=True)

        columns = ("ID", "Nombre", "Correo", "Rol", "Editar", "Eliminar")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="w")
        self.tree.column("Editar", width=60, anchor="center")
        self.tree.column("Eliminar", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

        btn_frame = tk.Frame(table_frame, bg="#f5f7fa")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="🔄 Actualizar", command=self.load_users, bg="#3498db", fg="white", font=("Arial", 11)).pack(side="left", padx=5)

        self.load_users()

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if item and column in ("#6", "#7"):
                values = self.tree.item(item, "values")
                user_id = values[0]
                if column == "#6":  # Editar
                    self.edit_user_direct(user_id)
                elif column == "#7":  # Eliminar
                    self.delete_user_direct(user_id)

    def load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        usuarios = get_all_users()
        for u in usuarios:
            self.tree.insert("", "end", values=(u['id'], u['nombre'], u['correo'], u['rol'], "✏️", "🗑️"))

    def add_user(self):
        nombre = self.name_entry.get().strip()
        correo = self.email_entry.get().strip()
        contraseña = self.password_entry.get()
        rol = self.rol_var.get()

        if not nombre or not correo or not contraseña:
            messagebox.showwarning("⚠️ Campos obligatorios", "Todos los campos son obligatorios.")
            return

        if "@" not in correo or "." not in correo:
            messagebox.showwarning("⚠️ Correo inválido", "El correo debe tener un formato válido.")
            return

        if len(contraseña) < 6:
            messagebox.showwarning("⚠️ Contraseña débil", "La contraseña debe tener al menos 6 caracteres.")
            return

        success, msg = add_user(nombre, correo, contraseña, rol)
        if success:
            messagebox.showinfo("✅ Éxito", msg)
            self.clear_form()
            self.load_users()
        else:
            messagebox.showerror("❌ Error", msg)

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.rol_var.set("cajero")

    def edit_user_direct(self, user_id):
        usuarios = get_all_users()
        user = next((u for u in usuarios if str(u['id']) == str(user_id)), None)
        if not user:
            messagebox.showerror("❌ Error", "Usuario no encontrado.")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Editar Usuario ID: {user_id}")
        edit_window.geometry("400x300")
        edit_window.configure(bg="#f5f7fa")

        tk.Label(edit_window, text=f"Editar Usuario: {user['nombre']}", font=("Arial", 16, "bold"), bg="#f5f7fa").pack(pady=15)

        form = tk.Frame(edit_window, bg="#f5f7fa")
        form.pack(padx=20, pady=10)

        tk.Label(form, text="Nombre:", bg="#f5f7fa", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
        name_entry = tk.Entry(form, font=("Arial", 12), width=25)
        name_entry.insert(0, user['nombre'])
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(form, text="Correo:", bg="#f5f7fa", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
        email_entry = tk.Entry(form, font=("Arial", 12), width=25)
        email_entry.insert(0, user['correo'])
        email_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(form, text="Rol:", bg="#f5f7fa", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=5)
        rol_var = tk.StringVar(value=user['rol'])
        ttk.Combobox(form, textvariable=rol_var, values=["cajero", "admin"], state="readonly", width=23).grid(row=2, column=1, padx=10, pady=5)

        def save_changes():
            nombre = name_entry.get().strip()
            correo = email_entry.get().strip()
            rol = rol_var.get()

            if not nombre or not correo:
                messagebox.showwarning("⚠️ Campos obligatorios", "Nombre y correo son obligatorios.", parent=edit_window)
                return

            success, msg = update_user(user_id, nombre, correo, rol)
            if success:
                messagebox.showinfo("✅ Éxito", "Usuario actualizado exitosamente.", parent=edit_window)
                edit_window.destroy()
                self.load_users()
            else:
                messagebox.showerror("❌ Error", msg, parent=edit_window)

        btn_frame = tk.Frame(edit_window, bg="#f5f7fa")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Guardar Cambios", command=save_changes, bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancelar", command=edit_window.destroy, bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), width=10).pack(side="left", padx=5)

    def delete_user_direct(self, user_id):
        if messagebox.askyesno("❓ Confirmar eliminación", f"¿Está seguro de eliminar este usuario?", parent=self.root):
            success, msg = delete_user(user_id)
            if success:
                messagebox.showinfo("✅ Éxito", msg, parent=self.root)
                self.load_users()
            else:
                messagebox.showerror("❌ Error", msg, parent=self.root)
        else:
            messagebox.showinfo("ℹ️ Cancelado", "No se ha eliminado ningún usuario.", parent=self.root)

    def back_to_dashboard(self):
        self.root.destroy()
        from dashboard_view import DashboardView
        new_root = tk.Tk()
        DashboardView(new_root, self.usuario)
        new_root.mainloop()