# suppliers_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from suppliers_controller import obtener_todos_proveedores, agregar_proveedor, actualizar_proveedor, eliminar_proveedor

class ProveedoresView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("🏭 Gestión de Proveedores - Papelería Ángel")
        self.root.geometry("1000x600")
        self.root.configure(bg="#f5f7fa")

        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🏭 Gestión de Proveedores", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)

        back_btn = tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10))
        back_btn.pack(anchor="nw", padx=20, pady=10)

        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        form_frame = ttk.LabelFrame(main_frame, text="Agregar Nuevo Proveedor", padding="15")
        form_frame.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(form_frame, text="Nombre Empresa:", bg="#f5f7fa", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
        self.nombre_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.nombre_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Contacto:", bg="#f5f7fa", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
        self.contacto_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.contacto_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Teléfono:", bg="#f5f7fa", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=5)
        self.telefono_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.telefono_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Correo:", bg="#f5f7fa", font=("Arial", 11)).grid(row=3, column=0, sticky="w", pady=5)
        self.correo_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.correo_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Button(form_frame, text="➕ Agregar Proveedor", command=self.agregar_proveedor, bg="#2ecc71", fg="white", font=("Arial", 11)).grid(row=4, column=0, columnspan=2, pady=15)

        table_frame = ttk.Frame(main_frame)
        table_frame.pack(side="right", fill="both", expand=True)

        columns = ("ID", "Nombre Empresa", "Contacto", "Teléfono", "Correo", "Editar", "Eliminar")
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
        tk.Button(btn_frame, text="🔄 Actualizar", command=self.cargar_proveedores, bg="#3498db", fg="white", font=("Arial", 11)).pack(side="left", padx=5)

        self.cargar_proveedores()

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if item and column in ("#6", "#7"):
                values = self.tree.item(item, "values")
                proveedor_id = values[0]
                if column == "#6":  # Editar
                    self.editar_directo(proveedor_id)
                elif column == "#7":  # Eliminar
                    self.eliminar_directo(proveedor_id)

    def cargar_proveedores(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        proveedores = obtener_todos_proveedores()
        for p in proveedores:
            self.tree.insert("", "end", values=(p['id'], p['nombre_empresa'], p['contacto'], p['telefono'], p['correo'], "✏️", "🗑️"))

    def agregar_proveedor(self):
        nombre = self.nombre_entry.get().strip()
        contacto = self.contacto_entry.get().strip()
        telefono = self.telefono_entry.get().strip()
        correo = self.correo_entry.get().strip()

        if not nombre or not telefono:
            messagebox.showwarning("⚠️ Campos obligatorios", "Nombre y Teléfono son obligatorios.")
            return

        success, msg = agregar_proveedor(nombre, contacto, telefono, correo)
        if success:
            messagebox.showinfo("✅ Éxito", msg)
            self.nombre_entry.delete(0, tk.END)
            self.contacto_entry.delete(0, tk.END)
            self.telefono_entry.delete(0, tk.END)
            self.correo_entry.delete(0, tk.END)
            self.cargar_proveedores()
        else:
            messagebox.showerror("❌ Error", msg)

    def editar_directo(self, proveedor_id):
        proveedores = obtener_todos_proveedores()
        proveedor = next((p for p in proveedores if str(p['id']) == str(proveedor_id)), None)
        if not proveedor:
            messagebox.showerror("❌ Error", "Proveedor no encontrado.")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Editar Proveedor ID: {proveedor_id}")
        edit_window.geometry("450x450")
        edit_window.configure(bg="#f5f7fa")

        tk.Label(edit_window, text=f"Editar Proveedor: {proveedor['nombre_empresa']}", font=("Arial", 16, "bold"), bg="#f5f7fa").pack(pady=15)

        form = tk.Frame(edit_window, bg="#f5f7fa")
        form.pack(padx=20, pady=10)

        tk.Label(form, text="Nombre Empresa:", bg="#f5f7fa", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
        nombre_entry = tk.Entry(form, font=("Arial", 12), width=25)
        nombre_entry.insert(0, proveedor['nombre_empresa'])
        nombre_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(form, text="Contacto:", bg="#f5f7fa", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
        contacto_entry = tk.Entry(form, font=("Arial", 12), width=25)
        contacto_entry.insert(0, proveedor['contacto'])
        contacto_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(form, text="Teléfono:", bg="#f5f7fa", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=5)
        telefono_entry = tk.Entry(form, font=("Arial", 12), width=25)
        telefono_entry.insert(0, proveedor['telefono'])
        telefono_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(form, text="Correo:", bg="#f5f7fa", font=("Arial", 11)).grid(row=3, column=0, sticky="w", pady=5)
        correo_entry = tk.Entry(form, font=("Arial", 12), width=25)
        correo_entry.insert(0, proveedor['correo'])
        correo_entry.grid(row=3, column=1, padx=10, pady=5)

        def save_changes():
            nombre = nombre_entry.get().strip()
            contacto = contacto_entry.get().strip()
            telefono = telefono_entry.get().strip()
            correo = correo_entry.get().strip()

            if not nombre or not telefono:
                messagebox.showwarning("⚠️ Campos obligatorios", "Nombre y Teléfono son obligatorios.", parent=edit_window)
                return

            success, msg = actualizar_proveedor(proveedor_id, nombre, contacto, telefono, correo)
            if success:
                messagebox.showinfo("✅ Éxito", "Proveedor actualizado exitosamente.", parent=edit_window)
                edit_window.destroy()
                self.cargar_proveedores()
            else:
                messagebox.showerror("❌ Error", msg, parent=edit_window)

        btn_frame = tk.Frame(edit_window, bg="#f5f7fa")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Guardar Cambios", command=save_changes, bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancelar", command=edit_window.destroy, bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), width=10).pack(side="left", padx=5)

    def eliminar_directo(self, proveedor_id):
        if messagebox.askyesno("❓ Confirmar eliminación", f"¿Está seguro de eliminar este proveedor?", parent=self.root):
            success, msg = eliminar_proveedor(proveedor_id)
            if success:
                messagebox.showinfo("✅ Éxito", msg, parent=self.root)
                self.cargar_proveedores()
            else:
                messagebox.showerror("❌ Error", msg, parent=self.root)
        else:
            messagebox.showinfo("ℹ️ Cancelado", "No se ha eliminado ningún proveedor.", parent=self.root)

    def back_to_dashboard(self):
        self.root.destroy()
        from dashboard_view import DashboardView
        new_root = tk.Tk()
        DashboardView(new_root, self.usuario)
        new_root.mainloop()