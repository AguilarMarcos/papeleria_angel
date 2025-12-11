import tkinter as tk
from tkinter import ttk, messagebox
from auth_controller import login, registrar_usuario


class LoginView:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 Iniciar Sesión - Papelería Ángel")
        self.root.geometry("400x450")
        self.root.configure(bg="#f5f7fa")
        self.root.resizable(False, False)

        # ---------- CONTENEDOR PRINCIPAL ----------
        main_frame = tk.Frame(root, bg="white", padx=40, pady=40)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            main_frame, text="📦 Papelería Ángel",
            font=("Arial", 20, "bold"), fg="#2c3e50", bg="white"
        ).pack(pady=(0, 20))

        # ---------- EMAIL ----------
        tk.Label(main_frame, text="Correo electrónico", font=("Arial", 12),
                 bg="white", fg="#2c3e50").pack(anchor="w")
        self.email_entry = tk.Entry(main_frame, font=("Arial", 12), width=25)
        self.email_entry.pack(pady=5, fill="x")

        # ---------- PASSWORD ----------
        tk.Label(main_frame, text="Contraseña", font=("Arial", 12),
                 bg="white", fg="#2c3e50").pack(anchor="w")
        self.password_entry = tk.Entry(main_frame, font=("Arial", 12),
                                       show="*", width=25)
        self.password_entry.pack(pady=5, fill="x")

        # ---------- BOTONES ----------
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame, text="Iniciar Sesión", command=self.login_user,
            bg="#3498db", fg="white", font=("Arial", 12, "bold"),
            width=15, relief="flat"
        ).pack(pady=5)

        tk.Button(
            btn_frame, text="Registrar Usuario", command=self.show_register,
            bg="#95a5a6", fg="white", font=("Arial", 11),
            width=15, relief="flat"
        ).pack(pady=5)

        tk.Button(
            btn_frame, text="🚪 Salir del Sistema",
            command=self.salir_sistema,
            bg="#e74c3c", fg="white", font=("Arial", 11, "bold"),
            width=15, relief="flat"
        ).pack(pady=10)

    # ======================================================================
    # LOGICA DE AUTENTICACIÓN
    # ======================================================================
    def salir_sistema(self):
        if messagebox.askyesno("Salir", "¿Desea salir del sistema?"):
            self.root.destroy()

    def login_user(self):
        correo = self.email_entry.get().strip()
        contraseña = self.password_entry.get().strip()

        if not correo or not contraseña:
            messagebox.showwarning("Campos vacíos", "Complete ambos campos.")
            return

        success, usuario_logueado = login(correo, contraseña)

        if not success:
            messagebox.showerror("Error", usuario_logueado)
            return

        # Login correcto
        self.root.destroy()
        from dashboard_view import DashboardView
        new_root = tk.Tk()
        DashboardView(new_root, usuario_logueado)
        new_root.mainloop()

    # ======================================================================
    # REGISTRO DE USUARIO
    # ======================================================================
    def show_register(self):
        self.root.withdraw()

        reg = tk.Toplevel(self.root)
        reg.title("Registrar Usuario")
        reg.geometry("450x600")
        reg.resizable(False, False)
        reg.protocol("WM_DELETE_WINDOW", lambda: [reg.destroy(), self.root.deiconify()])

        frame = tk.Frame(reg, bg="white", padx=30, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="📝 Crear Cuenta",
                 font=("Arial", 18, "bold"), bg="white").pack(pady=(5, 20))

        # ----- FORMULARIO -----
        def create(label, password=False, combo=False, options=None):
            tk.Label(frame, text=label, font=("Arial", 11),
                     bg="white").pack(anchor="w")
            if combo:
                var = tk.StringVar()
                box = ttk.Combobox(frame, textvariable=var, values=options, state="readonly")
                box.set(options[0])
                box.pack(pady=5, fill="x")
                return var
            else:
                entry = tk.Entry(frame, show="*" if password else "")
                entry.pack(pady=5, fill="x")
                return entry

        nombre = create("Nombre")
        correo = create("Correo Electrónico")
        contraseña = create("Contraseña", password=True)
        rol = create("Rol", combo=True, options=["administrador", "cajero"])

        # ----- BOTONES -----
        def registrar():
            n = nombre.get().strip() if isinstance(nombre, tk.Entry) else nombre.get()
            c = correo.get().strip()
            p = contraseña.get()
            r = rol.get()

            if not all([n, c, p, r]):
                messagebox.showwarning("Campos incompletos", "Complete todos los campos.", parent=reg)
                return

            if "@" not in c or "." not in c:
                messagebox.showwarning("Email inválido", "Ingrese un correo válido.", parent=reg)
                return

            if len(p) < 6:
                messagebox.showwarning("Contraseña débil", "Debe tener al menos 6 caracteres.", parent=reg)
                return

            ok, msg = registrar_usuario(n, c, p, r)

            if ok:
                messagebox.showinfo("Registro exitoso", msg, parent=reg)
                reg.destroy()
                self.root.deiconify()
            else:
                messagebox.showerror("Error", msg, parent=reg)

        tk.Button(frame, text="Registrar", command=registrar,
                  bg="#2ecc71", fg="white", font=("Arial", 12, "bold"),
                  width=12).pack(pady=15)

        tk.Button(frame, text="Cancelar",
                  command=lambda: [reg.destroy(), self.root.deiconify()],
                  bg="#e74c3c", fg="white", font=("Arial", 12, "bold"),
                  width=12).pack()
