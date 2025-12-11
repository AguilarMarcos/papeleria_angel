# suppliers_view.py - VERSIÓN PERFECTA
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from suppliers_controller import obtener_todos_proveedores, agregar_proveedor, actualizar_proveedor, eliminar_proveedor
# Importamos utilidades de exportación (asumiendo que las tienes)
from export_controller import exportar_a_csv, generar_ruta_csv 


class ProveedoresView:
    def __init__(self, root, usuario):
        self.root = root  # Este es el tk.Toplevel (la ventana de Proveedores)
        self.usuario = usuario
        self.root.title("🏭 Gestión de Proveedores - Papelería Ángel")
        self.root.geometry("1000x650")
        self.root.configure(bg="#f5f7fa")
        
        # Configuración de estilos
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#d3e0e7", foreground="#2c3e50")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.configure("T.Blue.TButton", font=("Arial", 10, "bold"), background="#3498db", foreground="white")
        style.configure("T.Red.TButton", font=("Arial", 10, "bold"), background="#e74c3c", foreground="white")
        style.configure("T.Green.TButton", font=("Arial", 10, "bold"), background="#2ecc71", foreground="white")

        # Barra superior
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🏭 Gestión de Proveedores", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(
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

        # Botón Volver al Dashboard (Navegación Corregida)
        back_btn = tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10))
        back_btn.pack(anchor="nw", padx=20, pady=10)

        # Frame principal para el contenido
        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Frame de botones (CRUD)
        button_frame = tk.Frame(main_frame, bg="#f5f7fa")
        button_frame.pack(fill="x", pady=(0, 10))

        # Botones CRUD
        ttk.Button(button_frame, text="➕ Agregar Proveedor", command=self.open_add_proveedor_window, style="T.Blue.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="✏️ Editar Proveedor", command=self.open_edit_proveedor_window, style="T.Blue.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="🗑️ Eliminar Proveedor", command=self.eliminar_proveedor_action, style="T.Red.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="⬇️ Exportar CSV", command=self.export_to_csv, style="T.Green.TButton").pack(side="right", padx=5)


        # Treeview para mostrar proveedores
        self.proveedores_tree = ttk.Treeview(main_frame, columns=("ID", "Empresa", "Contacto", "Teléfono", "Correo"), show="headings")
        self.proveedores_tree.pack(fill="both", expand=True)

        # Configuración de columnas
        col_widths = {"ID": 50, "Empresa": 200, "Contacto": 180, "Teléfono": 120, "Correo": 250}
        for col, width in col_widths.items():
            self.proveedores_tree.heading(col, text=col)
            self.proveedores_tree.column(col, width=width, anchor=tk.CENTER)

        self.cargar_proveedores()
        
        # Enlazar doble clic para editar
        self.proveedores_tree.bind("<Double-1>", self._on_double_click)


    # --- Métodos de Lógica y UI ---

    def _get_selected_proveedor_data(self):
        """Retorna el ID y el nombre de la empresa del proveedor seleccionado, o None."""
        selected_item = self.proveedores_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un proveedor primero.", parent=self.root)
            return None, None
        
        values = self.proveedores_tree.item(selected_item, 'values')
        return values[0], values[1] # ID, Nombre Empresa


    def cargar_proveedores(self):
        """Carga y muestra los proveedores en el Treeview."""
        for item in self.proveedores_tree.get_children():
            self.proveedores_tree.delete(item)

        proveedores = obtener_todos_proveedores()
        if proveedores:
            for p in proveedores:
                self.proveedores_tree.insert("", "end", values=(
                    p['id'],
                    p['nombre_empresa'],
                    p['contacto'],
                    p['telefono'],
                    p['correo']
                ))
        else:
            # Opción: Mostrar un mensaje en la tabla si no hay datos
            pass

    def _validate_fields(self, window, nombre, contacto, telefono, correo):
        """Valida que los campos no estén vacíos y tengan un formato básico."""
        if not all([nombre, contacto, telefono, correo]):
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.", parent=window)
            return False
        if len(telefono) < 8 or not telefono.isdigit():
             messagebox.showwarning("Advertencia", "El teléfono debe contener solo números y tener un largo razonable.", parent=window)
             return False
        if '@' not in correo or '.' not in correo:
            messagebox.showwarning("Advertencia", "Ingrese un formato de correo electrónico válido.", parent=window)
            return False
        return True
        
    # --- VENTANAS CRUD ---

    def open_add_proveedor_window(self):
        """Abre la ventana para agregar un nuevo proveedor."""
        add_window = tk.Toplevel(self.root)
        add_window.title("➕ Agregar Nuevo Proveedor")
        add_window.geometry("400x350")
        add_window.transient(self.root)  # Hacerla modal/transitoria
        add_window.grab_set()  # Bloquea la interacción con la ventana principal
        add_window.configure(bg="#f5f7fa")

        # Variables de control
        nombre_var = tk.StringVar()
        contacto_var = tk.StringVar()
        telefono_var = tk.StringVar()
        correo_var = tk.StringVar()

        frame = ttk.LabelFrame(add_window, text="Datos del Proveedor", padding="10")
        frame.pack(padx=20, pady=20, fill="x")

        # Helper para campos
        def create_field(parent, label_text, var, row):
            ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            ttk.Entry(parent, textvariable=var, width=35).grid(row=row, column=1, padx=5, pady=5)

        create_field(frame, "Empresa:", nombre_var, 0)
        create_field(frame, "Contacto:", contacto_var, 1)
        create_field(frame, "Teléfono:", telefono_var, 2)
        create_field(frame, "Correo:", correo_var, 3)

        def save_new_proveedor():
            nombre = nombre_var.get().strip()
            contacto = contacto_var.get().strip()
            telefono = telefono_var.get().strip()
            correo = correo_var.get().strip()

            if not self._validate_fields(add_window, nombre, contacto, telefono, correo):
                return
            
            exito, msg = agregar_proveedor(nombre, contacto, telefono, correo)
            
            if exito:
                messagebox.showinfo("✅ Éxito", msg, parent=add_window)
                add_window.destroy()
                self.cargar_proveedores()
            else:
                messagebox.showerror("❌ Error", msg, parent=add_window)

        btn_frame = tk.Frame(add_window, bg="#f5f7fa")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Guardar Proveedor", command=save_new_proveedor, bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancelar", command=add_window.destroy, bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), width=10).pack(side="left", padx=5)


    def open_edit_proveedor_window(self):
        """Abre la ventana para editar el proveedor seleccionado."""
        proveedor_id, nombre_empresa = self._get_selected_proveedor_data()
        if proveedor_id is None:
            return

        # Obtener los datos completos del proveedor (se requeriría una función adicional en el controlador
        # para obtener un único proveedor por ID, pero usaremos los datos de la Treeview para simplificar, 
        # asumiendo que ya están completos y son correctos)
        selected_item = self.proveedores_tree.focus()
        values = self.proveedores_tree.item(selected_item, 'values')
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"✏️ Editar Proveedor ID: {proveedor_id}")
        edit_window.geometry("400x350")
        edit_window.transient(self.root)
        edit_window.grab_set()
        edit_window.configure(bg="#f5f7fa")

        # Variables de control pre-cargadas
        nombre_var = tk.StringVar(value=values[1]) # Empresa
        contacto_var = tk.StringVar(value=values[2])
        telefono_var = tk.StringVar(value=values[3])
        correo_var = tk.StringVar(value=values[4])

        frame = ttk.LabelFrame(edit_window, text="Datos del Proveedor", padding="10")
        frame.pack(padx=20, pady=20, fill="x")
        
        # Helper para campos
        def create_field(parent, label_text, var, row):
            ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            ttk.Entry(parent, textvariable=var, width=35).grid(row=row, column=1, padx=5, pady=5)

        create_field(frame, "Empresa:", nombre_var, 0)
        create_field(frame, "Contacto:", contacto_var, 1)
        create_field(frame, "Teléfono:", telefono_var, 2)
        create_field(frame, "Correo:", correo_var, 3)

        def save_changes():
            nombre = nombre_var.get().strip()
            contacto = contacto_var.get().strip()
            telefono = telefono_var.get().strip()
            correo = correo_var.get().strip()

            if not self._validate_fields(edit_window, nombre, contacto, telefono, correo):
                return
            
            exito, msg = actualizar_proveedor(proveedor_id, nombre, contacto, telefono, correo)
            
            if exito:
                messagebox.showinfo("✅ Éxito", msg, parent=edit_window)
                edit_window.destroy()
                self.cargar_proveedores()
            else:
                messagebox.showerror("❌ Error", msg, parent=edit_window)

        btn_frame = tk.Frame(edit_window, bg="#f5f7fa")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Guardar Cambios", command=save_changes, bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancelar", command=edit_window.destroy, bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), width=10).pack(side="left", padx=5)


    def _on_double_click(self, event):
        """Maneja el doble clic para abrir la ventana de edición."""
        self.open_edit_proveedor_window()


    def eliminar_proveedor_action(self):
        """Obtiene el ID del proveedor seleccionado y llama a la función de borrado."""
        proveedor_id, nombre_empresa = self._get_selected_proveedor_data()
        if proveedor_id is None:
            return
            
        if messagebox.askyesno(
            "❓ Confirmar eliminación", 
            f"¿Está seguro de eliminar al proveedor '{nombre_empresa}' (ID: {proveedor_id})?\\n⚠️ Si existen productos asociados, la eliminación fallará.", 
            parent=self.root):
            
            self.eliminar_directo(proveedor_id)
        
    def eliminar_directo(self, proveedor_id):
        """Llama al controlador para eliminar el proveedor."""
        success, msg = eliminar_proveedor(proveedor_id)
        if success:
            messagebox.showinfo("✅ Éxito", msg, parent=self.root)
            self.cargar_proveedores()
        else:
            messagebox.showerror("❌ Error", msg, parent=self.root)

    def export_to_csv(self):
        """Exporta los datos de la tabla de proveedores a un archivo CSV."""
        proveedores = obtener_todos_proveedores()
        if not proveedores:
            messagebox.showwarning("Advertencia", "No hay datos para exportar.", parent=self.root)
            return

        # Definir encabezados de archivo CSV y las claves correspondientes
        raw_keys = ["id", "nombre_empresa", "contacto", "telefono", "correo"]
        
        ruta_sugerida = generar_ruta_csv("Reporte_Proveedores")
        
        ruta_guardado = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=ruta_sugerida,
            filetypes=[("Archivos CSV", "*.csv")],
            parent=self.root
        )

        if ruta_guardado:
            exito, mensaje = exportar_a_csv(proveedores, ruta_guardado, raw_keys)
            
            if exito:
                messagebox.showinfo("✅ Exportación Exitosa", mensaje, parent=self.root)
            else:
                messagebox.showerror("❌ Error de Exportación", mensaje, parent=self.root)


    # --- MÉTODOS DE NAVEGACIÓN CORREGIDOS (PATRÓN MVC CON Toplevel) ---

    def back_to_dashboard(self):
        """Regresa al Dashboard de forma limpia (Muestra el master y destruye el Toplevel)."""
        # self.root.master es la ventana tk.Tk() que el Dashboard ocultó (withdraw)
        # Esto solo funciona si DashboardView fue llamada con el patrón correcto.
        try:
            self.root.master.deiconify() 
        except:
            # En caso de que se haya abierto directamente sin Dashboard
            pass
        self.root.destroy() 


    def confirmar_cierre(self):
        """Cierra la sesión y regresa a la pantalla de Login."""
        if messagebox.askyesno(
            "❓ Cerrar sesión",
            f"¿Está seguro que desea cerrar sesión como {self.usuario.get('nombre', 'Usuario')}?",
            parent=self.root
        ):
            # Obtener la ventana principal (Dashboard) antes de destruirla
            main_root = self.root.master
            
            # 1. Destruir la ventana actual (Proveedores)
            self.root.destroy()
            
            # 2. Destruir la ventana principal oculta (Dashboard)
            if main_root and main_root.winfo_exists():
                main_root.destroy()
            
            # 3. Iniciar la vista de Login en una nueva instancia de Tk
            try:
                from login import LoginView
                root = tk.Tk()
                LoginView(root)
                root.mainloop()
            except Exception as e:
                messagebox.showerror("❌ Error al Abrir Login", f"No se pudo iniciar la ventana de Login: {e}")