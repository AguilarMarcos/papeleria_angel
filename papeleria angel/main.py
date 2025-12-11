# main.py
import tkinter as tk
from login import LoginView

def main(usuario_logueado=None):
    root = tk.Tk()
    root.title("Papelería Ángel")
    root.geometry("1250x700")

    if usuario_logueado:
        from dashboard_view import DashboardView
        DashboardView(root, usuario_logueado)
    else:
        LoginView(root)

    root.mainloop()

if __name__ == "__main__":
    main()
