import tkinter as tk
from tkinter import ttk

# Paleta y tipografía profesional
PALETTE = {
    'bg': '#f4f6f8',
    'surface': '#ffffff',
    'primary': '#2b6ea3',
    'accent': '#27ae60',
    'muted': '#7f8c8d',
    'danger': '#e74c3c',
    'header': '#1f3548'
}


def apply_style(root):
    """Aplicar estilo global y configurar `ttk.Style` para una apariencia más profesional.

    No modifica lógica de las vistas, solo colores, fuentes y estilos de widgets.
    """
    try:
        style = ttk.Style(root)
        # Intentar usar tema nativo si está disponible
        for theme in ('clam', 'alt', 'default'):
            try:
                style.theme_use(theme)
                break
            except Exception:
                continue

        # Tipografías
        default_font = ('Segoe UI', 10)
        heading_font = ('Segoe UI', 12, 'bold')
        root.option_add('*Font', default_font)
        root.option_add('*Button.Font', ('Segoe UI', 10, 'bold'))
        root.option_add('*Label.Font', default_font)

        # Colores básicos
        root.configure(bg=PALETTE['bg'])

        # Estilos de botones
        style.configure('Primary.TButton', background=PALETTE['primary'], foreground='white', borderwidth=0, focusthickness=3)
        style.map('Primary.TButton', background=[('active', PALETTE['primary'])])

        style.configure('Accent.TButton', background=PALETTE['accent'], foreground='white', borderwidth=0)
        style.map('Accent.TButton', background=[('active', PALETTE['accent'])])

        style.configure('Danger.TButton', background=PALETTE['danger'], foreground='white', borderwidth=0)
        style.map('Danger.TButton', background=[('active', PALETTE['danger'])])

        # Treeview improvements
        style.configure('Treeview', background=PALETTE['surface'], fieldbackground=PALETTE['surface'], foreground='black')
        style.configure('Treeview.Heading', font=heading_font, background=PALETTE['header'], foreground='white')

    except Exception:
        # No fallar si algo del estilo no es compatible en el sistema
        pass


def style_button(btn, kind='primary'):
    """Aplicar estilo ttk a un botón existente. No cambia su comando ni texto.

    kind: 'primary'|'accent'|'danger'|'muted'
    """
    mapping = {
        'primary': 'Primary.TButton',
        'accent': 'Accent.TButton',
        'danger': 'Danger.TButton'
    }
    style_name = mapping.get(kind, 'Primary.TButton')
    try:
        btn.config(style=style_name)
    except Exception:
        # Si es un tk.Button, conservar background pero ajustar fuente
        try:
            if kind == 'danger':
                btn.config(bg=PALETTE['danger'], fg='white')
            elif kind == 'accent':
                btn.config(bg=PALETTE['accent'], fg='white')
            else:
                btn.config(bg=PALETTE['primary'], fg='white')
        except Exception:
            pass
