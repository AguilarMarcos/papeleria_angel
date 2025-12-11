# client_orders_view.py - VERSIÓN PERFECTA
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import clientes_controller 
import client_orders_controller 


def validar_fecha(fecha_str):
    """Valida que la cadena tenga formato YYYY-MM-DD y sea una fecha válida."""
    try:
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


class ClientOrdersView:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("📝 Gestión de Pedidos a Clientes (Ventas a Crédito)")
        self.root.geometry("1400x750")
        self.root.configure(bg="#f5f7fa")
        self.root.protocol("WM_DELETE_WINDOW", self.back_to_dashboard)

        self.client_id_map = {}
        self.add_pedido_window = None
        self.abono_window = None
        self.abono_history_window = None

        # --- Estilos ---
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#d3e0e7", foreground="#2c3e50")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        # Estilos para los estados del pedido (Mejora: Asegurar todos los estados)
        style.configure('Completado', background='#d3f3d3') # Verde claro
        style.configure('Abonado', background='#fff3cd')    # Amarillo claro
        style.configure('Pendiente', background='#f7d3d3')  # Rojo claro
        style.map("TButton", background=[("active", "#3498db")])

        # Cargar clientes (para el combobox de nuevo pedido)
        self.cargar_clientes()

        # --- Barra superior ---
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="📝 Pedidos a Clientes (Ventas a Crédito)", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)
        
        tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10)).pack(anchor="nw", padx=20, pady=10)

        # --- Frame principal de Controles ---
        controls_frame = tk.Frame(root, bg="#f5f7fa")
        controls_frame.pack(fill="x", padx=20, pady=(0, 10))

        ttk.Button(controls_frame, text="➕ Nuevo Pedido", command=self.open_add_pedido_window, style="T.Blue.TButton").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="💵 Registrar Abono", command=self.open_abono_window, style="T.Green.TButton").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="🗑️ Eliminar Pedido", command=self.delete_pedido_action, style="T.Red.TButton").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="🔄 Recargar", command=self.load_pedidos, style="TButton").pack(side="right", padx=5)


        # --- Treeview para Pedidos ---
        tree_frame = tk.Frame(root, padx=20, pady=5)
        tree_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")

        self.pedidos_tree = ttk.Treeview(
            tree_frame, 
            columns=("ID", "Cliente", "Fecha Pedido", "Fecha Entrega", "Total", "Abonado", "Pendiente", "Estado"), 
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.pedidos_tree.yview)

        # Definir Columnas
        cols = {
            "ID": 50, "Cliente": 200, "Fecha Pedido": 120, "Fecha Entrega": 120, 
            "Total": 100, "Abonado": 100, "Pendiente": 100, "Estado": 100
        }
        for col, width in cols.items():
            self.pedidos_tree.heading(col, text=col)
            self.pedidos_tree.column(col, width=width, anchor="center")
        
        # Agregar columna oculta para el ID
        self.pedidos_tree.column("#0", width=0, stretch=tk.NO)

        self.pedidos_tree.pack(fill="both", expand=True)
        self.pedidos_tree.bind("<Double-1>", self.open_abono_history_window)

        # Cargar datos al iniciar
        self.load_pedidos()


    def cargar_clientes(self):
        """Carga los clientes para usar en el combobox de registro."""
        self.client_id_map = {}
        clientes = clientes_controller.obtener_todos_clientes()
        for c in clientes:
            nombre_completo = f"{c['nombre']} {c['apellido']} (ID: {c['id']})"
            self.client_id_map[nombre_completo] = c['id']

    def load_pedidos(self):
        """Carga y muestra todos los pedidos en el Treeview."""
        for item in self.pedidos_tree.get_children():
            self.pedidos_tree.delete(item)
            
        pedidos_data = client_orders_controller.obtener_pedidos_cliente()
        
        if not pedidos_data and pedidos_data is not None: # Si la lista está vacía
             self.pedidos_tree.insert("", "end", values=("", "No hay pedidos registrados", "", "", "", "", "", ""), tags=('Pendiente',))
             return

        for pedido in pedidos_data:
            total = client_orders_controller._safe_float(pedido.get('total_pedido'))
            abonado = client_orders_controller._safe_float(pedido.get('abonado'))
            pendiente = total - abonado
            estado = pedido.get('estado_actual', 'Pendiente')
            
            # Asignar tags visuales
            tags = ()
            if estado.lower() == "completado":
                tags = ('Completado',)
            elif estado.lower() == "abonado":
                tags = ('Abonado',)
            else:
                tags = ('Pendiente',)
            
            self.pedidos_tree.insert("", "end", values=(
                pedido['id'],
                pedido['cliente_nombre_completo'],
                pedido['fecha_pedido'],
                pedido['fecha_entrega_estimada'] if pedido['fecha_entrega_estimada'] else 'N/A',
                f"${total:.2f}",
                f"${abonado:.2f}",
                f"${pendiente:.2f}",
                estado
            ), tags=tags)


    # ============================================================================
    # ACCIONES DE PEDIDO
    # ============================================================================

    def open_add_pedido_window(self):
        """Abre la ventana para registrar un nuevo pedido a crédito."""
        if self.add_pedido_window and self.add_pedido_window.winfo_exists():
            self.add_pedido_window.lift()
            return
        
        self.add_pedido_window = tk.Toplevel(self.root)
        self.add_pedido_window.title("📝 Registrar Nuevo Pedido a Crédito")
        self.add_pedido_window.geometry("450x400")
        self.add_pedido_window.configure(bg="#f5f7fa")
        self.add_pedido_window.resizable(False, False)

        frame = ttk.LabelFrame(self.add_pedido_window, text="Datos del Pedido", padding="15 15 15 15")
        frame.pack(padx=20, pady=20, fill="x")

        # Variables de control
        cliente_var = tk.StringVar(self.add_pedido_window)
        total_var = tk.StringVar(self.add_pedido_window)
        anticipo_var = tk.StringVar(self.add_pedido_window, value='0.00')
        fecha_entrega_var = tk.StringVar(self.add_pedido_window, value=datetime.now().strftime('%Y-%m-%d'))
        
        # Opciones del ComboBox
        cliente_nombres = list(self.client_id_map.keys())
        if not cliente_nombres:
            messagebox.showerror("❌ Error", "No hay clientes registrados. Registre un cliente primero.", parent=self.root)
            self.add_pedido_window.destroy()
            return

        # Widgets
        row = 0
        ttk.Label(frame, text="Cliente:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        cliente_cb = ttk.Combobox(frame, textvariable=cliente_var, values=cliente_nombres, state="readonly", width=35)
        cliente_cb.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        cliente_cb.set(cliente_nombres[0])
        row += 1

        ttk.Label(frame, text="Total del Pedido ($):").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=total_var, width=35).grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        row += 1

        ttk.Label(frame, text="Anticipo ($) (Opcional):").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=anticipo_var, width=35).grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        row += 1

        ttk.Label(frame, text="Fecha Entrega (YYYY-MM-DD):").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=fecha_entrega_var, width=35).grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        row += 1


        def registrar():
            cliente_nombre = cliente_var.get()
            total_str = total_var.get().strip()
            anticipo_str = anticipo_var.get().strip() or '0.00'
            fecha_entrega = fecha_entrega_var.get().strip()

            # Validaciones de la vista
            try:
                total = float(total_str)
                anticipo = float(anticipo_str)
            except ValueError:
                messagebox.showerror("❌ Error", "Total y Anticipo deben ser números válidos.", parent=self.add_pedido_window)
                return

            if cliente_nombre not in self.client_id_map:
                messagebox.showerror("❌ Error", "Debe seleccionar un cliente válido.", parent=self.add_pedido_window)
                return

            if total <= 0:
                messagebox.showerror("❌ Error", "El Total del Pedido debe ser mayor a $0.00.", parent=self.add_pedido_window)
                return

            if anticipo < 0:
                messagebox.showerror("❌ Error", "El Anticipo no puede ser negativo.", parent=self.add_pedido_window)
                return
                
            if anticipo > total:
                messagebox.showerror("❌ Error", "El Anticipo no puede ser mayor al Total.", parent=self.add_pedido_window)
                return

            if fecha_entrega and not validar_fecha(fecha_entrega):
                 messagebox.showerror("❌ Error", "Formato de fecha de entrega inválido. Use YYYY-MM-DD.", parent=self.add_pedido_window)
                 return

            cliente_id = self.client_id_map[cliente_nombre]
            
            # Llamada al controlador
            exito, mensaje = client_orders_controller.registrar_pedido_cliente(
                cliente_id, 
                fecha_entrega, 
                total, 
                anticipo
            )

            if exito:
                messagebox.showinfo("✅ Éxito", mensaje, parent=self.add_pedido_window)
                self.add_pedido_window.destroy()
                self.load_pedidos()
            else:
                messagebox.showerror("❌ Error", mensaje, parent=self.add_pedido_window)

        # Botones
        button_frame = tk.Frame(self.add_pedido_window, bg="#f5f7fa")
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="💾 Registrar Pedido", command=registrar, style="T.Blue.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.add_pedido_window.destroy).pack(side="left", padx=5)


    def open_abono_window(self):
        """Abre la ventana para registrar un abono al pedido seleccionado."""
        if self.abono_window and self.abono_window.winfo_exists():
            self.abono_window.lift()
            return

        selected_item = self.pedidos_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido para registrar un abono.")
            return

        values = self.pedidos_tree.item(selected_item, 'values')
        pedido_id = int(values[0])
        cliente_nombre = values[1]
        
        # Usar los valores formateados de la vista para la información (son strings como "$100.00")
        total_str = values[4].replace('$', '')
        abonado_str = values[5].replace('$', '')
        
        try:
            total = float(total_str)
            abonado = float(abonado_str)
        except ValueError:
            messagebox.showerror("❌ Error de datos", "No se pudo leer el total/abonado del pedido seleccionado.")
            return

        pendiente_pago = total - abonado
        
        if pendiente_pago <= 0.01: # Con tolerancia float
            messagebox.showinfo("ℹ️ Información", f"El pedido #{pedido_id} de {cliente_nombre} ya está Completado. No requiere más abonos.")
            return

        # Crear la ventana de abono
        self.abono_window = tk.Toplevel(self.root)
        self.abono_window.title(f"💵 Registrar Abono - Pedido #{pedido_id}")
        self.abono_window.geometry("400x300")
        self.abono_window.configure(bg="#f5f7fa")
        self.abono_window.resizable(False, False)

        frame = ttk.LabelFrame(self.abono_window, text="Detalles del Abono", padding="15 15 15 15")
        frame.pack(padx=20, pady=20, fill="x")

        # Mostrar info
        ttk.Label(frame, text=f"Cliente: {cliente_nombre}").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text=f"Total: ${total:.2f}").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame, text=f"Abonado: ${abonado:.2f}").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame, text=f"Pendiente: ${pendiente_pago:.2f}", font=("Arial", 11, "bold")).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Variables de control
        monto_var = tk.StringVar(self.abono_window)
        metodo_var = tk.StringVar(self.abono_window, value="Efectivo")
        metodos = ["Efectivo", "Tarjeta", "Transferencia", "Otro"]

        # Widgets de entrada
        ttk.Label(frame, text="Monto del Abono ($):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=monto_var, width=15).grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame, text="Método de Pago:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        ttk.Combobox(frame, textvariable=metodo_var, values=metodos, state="readonly", width=15).grid(row=5, column=1, padx=5, pady=5, sticky="ew")


        def registrar_abono_action():
            monto_str = monto_var.get().strip()
            metodo = metodo_var.get()

            try:
                monto_abono = float(monto_str)
            except ValueError:
                messagebox.showerror("❌ Error", "Monto debe ser un número válido.", parent=self.abono_window)
                return

            if monto_abono <= 0:
                messagebox.showerror("❌ Error", "El monto del abono debe ser mayor a $0.00.", parent=self.abono_window)
                return
            
            # La validación de que el monto no exceda el pendiente se realiza también en el controlador.
            
            usuario_id = self.usuario.get('id', 1) # Usar ID del usuario logueado o un valor por defecto
            
            exito, mensaje = client_orders_controller.registrar_abono(
                pedido_id, 
                monto_abono, 
                metodo, 
                usuario_id
            )

            if exito:
                messagebox.showinfo("✅ Éxito", mensaje, parent=self.abono_window)
                self.abono_window.destroy()
                self.load_pedidos()
            else:
                messagebox.showerror("❌ Error", mensaje, parent=self.abono_window)

        # Botones
        button_frame = tk.Frame(self.abono_window, bg="#f5f7fa")
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="💸 Registrar Abono", command=registrar_abono_action, style="T.Green.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.abono_window.destroy).pack(side="left", padx=5)


    def open_abono_history_window(self, event=None):
        """Abre la ventana para ver el historial de abonos del pedido seleccionado."""
        if self.abono_history_window and self.abono_history_window.winfo_exists():
            self.abono_history_window.lift()
            return
            
        selected_item = self.pedidos_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido para ver el historial de abonos.")
            return

        values = self.pedidos_tree.item(selected_item, 'values')
        pedido_id = values[0]
        cliente_nombre = values[1]

        abonos = client_orders_controller.obtener_abonos_pedido(pedido_id)

        self.abono_history_window = tk.Toplevel(self.root)
        self.abono_history_window.title(f"📜 Historial de Abonos - Pedido #{pedido_id} ({cliente_nombre})")
        self.abono_history_window.geometry("600x400")
        self.abono_history_window.configure(bg="#f5f7fa")
        
        # Frame
        frame = tk.Frame(self.abono_history_window, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        # Treeview para el historial
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        tree = ttk.Treeview(
            frame, 
            columns=("ID", "Fecha", "Monto", "Método", "Cajero"), 
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)

        cols = {"ID": 50, "Fecha": 150, "Monto": 100, "Método": 100, "Cajero": 150}
        for col, width in cols.items():
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")

        tree.pack(fill="both", expand=True)

        if not abonos:
            tree.insert("", "end", values=("", "No hay abonos registrados para este pedido.", "", "", ""))
        else:
            for abono in abonos:
                tree.insert("", "end", values=(
                    abono['id'],
                    abono['fecha_abono'],
                    f"${client_orders_controller._safe_float(abono['monto']):.2f}",
                    abono['metodo_pago'],
                    abono['usuario_cajero']
                ))

        # Botón de cerrar
        ttk.Button(self.abono_history_window, text="Cerrar", command=self.abono_history_window.destroy).pack(pady=10)


    def delete_pedido_action(self):
        """Elimina el pedido seleccionado."""
        selected_item = self.pedidos_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido para eliminar.")
            return

        values = self.pedidos_tree.item(selected_item, 'values')
        pedido_id = values[0]
        cliente_nombre = values[1]
        estado = values[7].lower()

        if estado == "completado":
            msg = f"¿Eliminar pedido COMPLETADO #{pedido_id} de {cliente_nombre}? \n\n⚠️ Esta acción es irreversible y elimina registros contables (abonos)."
        else:
            msg = f"¿Eliminar pedido #{pedido_id} de {cliente_nombre}? \n\nSe eliminarán también todos los abonos relacionados."

        if not messagebox.askyesno("❓ Confirmar Eliminación", msg, parent=self.root):
            return

        try:
            # Eliminar asegurando que el ID es un entero
            exito, mensaje = client_orders_controller.eliminar_pedido_cliente(int(pedido_id))
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje, parent=self.root)
                self.load_pedidos()
            else:
                messagebox.showerror("❌ Error", mensaje, parent=self.root)
        except Exception as e:
            messagebox.showerror("❌ Error Fatal", f"Error al eliminar:\n{e}", parent=self.root)

    
    def back_to_dashboard(self):
        """Cierra la vista actual y regresa al Dashboard."""
        self.root.destroy()
        try:
            # Importar de forma local para evitar problemas de dependencia circular
            from dashboard_view import DashboardView
            root = tk.Tk()
            DashboardView(root, self.usuario)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("❌ Error de Navegación", f"No se pudo abrir el dashboard:\n{e}")