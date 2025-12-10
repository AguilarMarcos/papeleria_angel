# login.py
import tkinter as tk
from tkinter import ttk, messagebox
from hashlib import sha256
from database import conectar

def hash_password(password):
    """Devuelve el hash SHA-256 de una contraseña."""
    return sha256(password.encode('utf-8')).hexdigest()

def authenticate_user(correo, contraseña):
    """Verifica credenciales del usuario."""
    conn = conectar()
    if not conn:
        return False, "Error de conexión a la base de datos."

    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM usuarios WHERE correo = %s"
    cursor.execute(query, (correo,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and user['contraseña'] == hash_password(contraseña):
        return True, user
    else:
        return False, "Correo o contraseña incorrectos."

class LoginView:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 Iniciar Sesión - Papelería Ángel")
        self.root.geometry("400x450")
        self.root.configure(bg="#f5f7fa")
        self.root.resizable(False, False)

        main_frame = tk.Frame(root, bg="white", padx=40, pady=40, relief="flat", bd=0)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(main_frame, text="📦 Papelería Ángel", font=("Arial", 20, "bold"), fg="#2c3e50", bg="white").pack(pady=(0, 20))

        tk.Label(main_frame, text="Correo electrónico", font=("Arial", 12), bg="white", fg="#2c3e50").pack(anchor="w", pady=(10, 0))
        self.email_entry = tk.Entry(main_frame, font=("Arial", 12), width=25, relief="solid", bd=1)
        self.email_entry.pack(pady=5, fill="x")

        tk.Label(main_frame, text="Contraseña", font=("Arial", 12), bg="white", fg="#2c3e50").pack(anchor="w", pady=(10, 0))
        self.password_entry = tk.Entry(main_frame, show="*", font=("Arial", 12), width=25, relief="solid", bd=1)
        self.password_entry.pack(pady=5, fill="x")

        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(pady=20)

        login_btn = tk.Button(
            btn_frame,
            text="Iniciar Sesión",
            command=self.login_user,
            bg="#3498db",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=1,
            relief="flat",
            activebackground="#2980b9"
        )
        login_btn.pack(pady=5)

        register_btn = tk.Button(
            btn_frame,
            text="Registrar Usuario",
            command=self.show_register,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11),
            width=15,
            height=1,
            relief="flat",
            activebackground="#7f8c8d"
        )
        register_btn.pack(pady=5)

        # Botón "Salir del Sistema"
        exit_btn = tk.Button(
            btn_frame,
            text="🚪 Salir del Sistema",
            command=self.salir_sistema,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            width=15,
            height=1,
            relief="flat",
            activebackground="#c0392b"
        )
        exit_btn.pack(pady=10)

        self.is_register_mode = False

    def salir_sistema(self):
        self.root.destroy()

    def login_user(self):
        correo = self.email_entry.get().strip()
        contraseña = self.password_entry.get()

        if not correo or not contraseña:
            messagebox.showwarning("⚠️ Campos vacíos", "Por favor, complete ambos campos.")
            return

        success, result = authenticate_user(correo, contraseña)
        if success:
            self.root.destroy()
            from dashboard_view import DashboardView
            new_root = tk.Tk()
            DashboardView(new_root, result)
            new_root.mainloop()
        else:
            messagebox.showerror("❌ Error", result)

    def show_register(self):
        if not self.is_register_mode:
            self.is_register_mode = True

            tk.Label(self.root, text="Nombre", font=("Arial", 12), bg="white", fg="#2c3e50").place(x=120, y=220)
            self.name_entry = tk.Entry(self.root, font=("Arial", 12), width=25, relief="solid", bd=1)
            self.name_entry.place(x=120, y=245)

            register_btn = tk.Button(
                self.root,
                text="Registrar",
                command=self.register_user,
                bg="#2ecc71",
                fg="white",
                font=("Arial", 12, "bold"),
                width=15,
                height=1,
                relief="flat",
                activebackground="#27ae60"
            )
            register_btn.place(x=140, y=320)

            self.register_btn = register_btn

    def register_user(self):
        nombre = self.name_entry.get().strip()
        correo = self.email_entry.get().strip()
        contraseña = self.password_entry.get()

        if not nombre or not correo or not contraseña:
            messagebox.showwarning("⚠️ Campos vacíos", "Por favor, complete todos los campos.")
            return

        if "@" not in correo or "." not in correo:
            messagebox.showwarning("⚠️ Correo inválido", "El correo debe tener un formato válido.")
            return

        if len(contraseña) < 6:
            messagebox.showwarning("⚠️ Contraseña débil", "La contraseña debe tener al menos 6 caracteres.")
            return

        from user_controller import add_user
        success, msg = add_user(nombre, correo, contraseña)
        if success:
            messagebox.showinfo("✅ Éxito", msg)
            self.name_entry.delete(0, tk.END)
            # Volver al modo de inicio de sesión
            self.is_register_mode = False
            self.register_btn.destroy()
        else:
            messagebox.showerror("❌ Error", msg)