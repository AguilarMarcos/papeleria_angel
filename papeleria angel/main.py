#main.py
import tkinter as tk
from login import LoginView
def main(usuario_logueado=None):
    root = tk.Tk()
    if usuario_logueado:
        from dashboard_view import DashboardView
        DashboardView(root, usuario_logueado)
    else:
        LoginView(root)
    root.mainloop()
if __name__ == "__main__":
    main()