#client_orders_view.py
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

        self.client_id_map = {}
        self.add_pedido_window = None
        self.abono_window = None
        self.abono_history_window = None

        # --- Estilos ---
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#d3e0e7", foreground="#2c3e50")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.map("TButton", background=[("active", "#3498db")])
        style.configure("T.Blue.TButton", background="#3498db", foreground="white", font=("Arial", 10, "bold"))
        style.configure("T.Red.TButton", background="#e74c3c", foreground="white", font=("Arial", 10, "bold"))

        # --- Barra superior ---
        top_bar = tk.Frame(root, bg="#2c3e50", height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="📝 Pedidos de Clientes (Abonos y Encargos)", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20, pady=10)
        tk.Button(root, text="← Volver al Dashboard", command=self.back_to_dashboard, bg="#6c757d", fg="white", font=("Arial", 10)).pack(anchor="nw", padx=20, pady=10)

        # --- Frame principal ---
        main_frame = tk.Frame(root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Tabla de pedidos ---
        list_frame = ttk.LabelFrame(main_frame, text="Listado de Pedidos a Clientes", padding="10")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("ID", "Cliente", "Descripción", "Fecha Pedido", "Total", "Abonado", "Pendiente", "Estado")
        self.pedidos_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        for col in columns:
            self.pedidos_tree.heading(col, text=col)
            self.pedidos_tree.column(col, width=120, anchor=tk.CENTER)

        self.pedidos_tree.column("Cliente", width=200, anchor=tk.W)
        self.pedidos_tree.column("Descripción", width=250, anchor=tk.W)
        self.pedidos_tree.column("Total", width=100, anchor=tk.E)
        self.pedidos_tree.column("Abonado", width=100, anchor=tk.E)
        self.pedidos_tree.column("Pendiente", width=100, anchor=tk.E)

        # Tags para estados
        self.pedidos_tree.tag_configure('pendiente', background='#fcf8e3')  # Amarillo
        self.pedidos_tree.tag_configure('abonado', background='#d9edf7')    # Azul
        self.pedidos_tree.tag_configure('completado', background='#d4edda') # Verde
        self.pedidos_tree.tag_configure('cancelado', background='#f8d7da')  # Rojo

        self.pedidos_tree.pack(fill="both", expand=True)

        # --- Botones ---
        btn_frame = tk.Frame(main_frame, bg="#f5f7fa")
        btn_frame.pack(fill="x", pady=10, padx=10)
        ttk.Button(btn_frame, text="➕ Nuevo Pedido Cliente", command=self.open_add_pedido_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💵 Registrar Abono", command=self.open_abono_window, style="T.Blue.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔍 Ver Abonos", command=self.show_abonos).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Eliminar Pedido", command=self.delete_pedido_action, style="T.Red.TButton").pack(side="left", padx=5)

        self.load_pedidos()

    def load_pedidos(self):
        for item in self.pedidos_tree.get_children():
            self.pedidos_tree.delete(item)

        try:
            pedidos = client_orders_controller.obtener_pedidos_cliente()
            if pedidos is None:
                pedidos = []
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los pedidos:\n{e}", parent=self.root)
            return

        for p in pedidos:
            # ✅ Redondeo explícito para evitar errores de punto flotante
            total = float(p['total'])
            abonado = float(p['total_abonado'])
            pendiente = round(total - abonado, 2)
            estado = p.get('estado', 'pendiente').lower()

            self.pedidos_tree.insert("", tk.END, values=(
                p['id'],
                p['cliente_nombre'],
                p['descripcion'] or 'N/A',
                p['fecha_pedido'],
                f"{total:.2f}",
                f"{abonado:.2f}",
                f"{pendiente:.2f}",
                p.get('estado', 'Pendiente')
            ), tags=(estado,))

    def _load_client_data(self):
        try:
            clientes = clientes_controller.obtener_todos_clientes()
            if clientes is None:
                clientes = []
            self.client_id_map = {f"{c['nombre']} {c['apellido']} (ID: {c['id']})": c['id'] for c in clientes}
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los clientes:\n{e}", parent=self.root)
            self.client_id_map = {}

    # ✅ Nueva función: verificar si una ventana está abierta y enfocarla
    def is_window_open(self, window_ref):
        return window_ref and window_ref.winfo_exists()

    def open_add_pedido_window(self):
        # 🔒 Evitar múltiples ventanas
        if self.is_window_open(self.add_pedido_window):
            self.add_pedido_window.focus()
            return

        self._load_client_data()
        if not self.client_id_map:
            messagebox.showerror("❌ Error", "No hay clientes registrados. Registre al menos uno primero.")
            return

        add_window = tk.Toplevel(self.root)
        self.add_pedido_window = add_window
        add_window.title("📝 Nuevo Encargo de Cliente (Abonos)")
        add_window.geometry("500x450")
        add_window.transient(self.root)
        add_window.grab_set()

        # ✅ Limpieza al cerrar con X
        def on_close():
            self.add_pedido_window = None
            add_window.destroy()
        add_window.protocol("WM_DELETE_WINDOW", on_close)

        # --- Frame de datos ---
        input_frame = ttk.LabelFrame(add_window, text="Datos del Pedido", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cliente_var = tk.StringVar()
        cliente_combo = ttk.Combobox(input_frame, textvariable=self.cliente_var, values=list(self.client_id_map.keys()), state="readonly", width=30)
        cliente_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        cliente_combo.current(0)

        ttk.Label(input_frame, text="Descripción (Maqueta/Encargo):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.descripcion_entry = ttk.Entry(input_frame, width=30)
        self.descripcion_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Fecha Entrega Estimada (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.fecha_estimada_entry = ttk.Entry(input_frame, width=30)
        self.fecha_estimada_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.fecha_estimada_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        # --- Frame financiero ---
        financial_frame = ttk.LabelFrame(add_window, text="Total y Abono Inicial", padding="10")
        financial_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(financial_frame, text="Precio Total del Encargo ($):").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.total_encargo_entry = ttk.Entry(financial_frame, width=15)
        self.total_encargo_entry.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        self.total_encargo_entry.insert(0, "0.00")

        ttk.Label(financial_frame, text="Monto de Abono Inicial ($):").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.abono_inicial_entry = ttk.Entry(financial_frame, width=15)
        self.abono_inicial_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        self.abono_inicial_entry.insert(0, "0.00")

        # --- Botón ---
        ttk.Button(add_window, 
                   text="💾 FINALIZAR Y REGISTRAR ENCARGO CON ABONO", 
                   command=self.final_register_pedido, 
                   style="T.Blue.TButton").pack(pady=20)

    def final_register_pedido(self):
        try:
            cliente_display = self.cliente_var.get().strip()
            if not cliente_display:
                messagebox.showerror("❌ Error", "Debe seleccionar un cliente.", parent=self.add_pedido_window)
                return

            # Sanitizar y convertir montos
            total_str = self.total_encargo_entry.get().replace(',', '.').strip()
            abono_str = self.abono_inicial_entry.get().replace(',', '.').strip()

            if not total_str or not abono_str:
                messagebox.showerror("❌ Error", "Complete los campos de Total y Abono.", parent=self.add_pedido_window)
                return

            total = float(total_str)
            abono_inicial = float(abono_str)

            if total <= 0:
                messagebox.showerror("❌ Error", "El precio total debe ser mayor a cero.", parent=self.add_pedido_window)
                return
            if abono_inicial < 0:
                messagebox.showerror("❌ Error", "El abono inicial no puede ser negativo.", parent=self.add_pedido_window)
                return
            if abono_inicial > total:
                messagebox.showerror("❌ Error", f"El abono (${abono_inicial:.2f}) no puede superar el total (${total:.2f}).", parent=self.add_pedido_window)
                return

            cliente_id = self.client_id_map.get(cliente_display)
            if not cliente_id:
                messagebox.showerror("❌ Error", "Cliente seleccionado inválido.", parent=self.add_pedido_window)
                return

            fecha_entrega = self.fecha_estimada_entry.get().strip()
            if not validar_fecha(fecha_entrega):
                messagebox.showerror("❌ Error", "La fecha de entrega debe tener formato YYYY-MM-DD válido.", parent=self.add_pedido_window)
                return

            descripcion = self.descripcion_entry.get().strip() or "Sin descripción"

            # 📞 LLAMADA AL CONTROLADOR
            exito, mensaje = client_orders_controller.registrar_pedido_simple(
                cliente_id=cliente_id,
                usuario_id=self.usuario['id'],
                total=total,
                abono_inicial=abono_inicial,
                descripcion=descripcion,
                fecha_entrega=fecha_entrega
            )

            if exito:
                messagebox.showinfo("✅ Éxito", mensaje, parent=self.add_pedido_window)
                self.load_pedidos()
                self.add_pedido_window.destroy()
                self.add_pedido_window = None
            else:
                messagebox.showerror("❌ Error", mensaje, parent=self.add_pedido_window)

        except ValueError as ve:
            messagebox.showerror("❌ Error", "Asegúrese de ingresar números válidos en Total y Abono.", parent=self.add_pedido_window)
        except Exception as e:
            messagebox.showerror("❌ Error Fatal", f"Error inesperado:\n{e}", parent=self.add_pedido_window)

    def open_abono_window(self):
        selected_item = self.pedidos_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido para registrar un abono.")
            return

        values = self.pedidos_tree.item(selected_item, 'values')
        pedido_id = values[0]
        cliente_nombre = values[1]
        estado = values[7].lower()

        # 🔒 Bloquear abonos en pedidos cancelados/completados
        if estado in ('cancelado', 'completado'):
            messagebox.showinfo("ℹ️ Información", f"No se pueden registrar abonos a pedidos '{estado}'.", parent=self.root)
            return

        try:
            pendiente_pago = float(values[6])  # Columna "Pendiente"
        except (ValueError, IndexError):
            messagebox.showerror("❌ Error", "No se pudo leer el monto pendiente.")
            return

        if pendiente_pago <= 0:
            messagebox.showinfo("ℹ️ Información", f"El pedido ya está cubierto (Pendiente: ${pendiente_pago:.2f}).", parent=self.root)
            return

        # 🔒 Evitar múltiples ventanas
        if self.is_window_open(self.abono_window):
            self.abono_window.focus()
            return

        abono_window = tk.Toplevel(self.root)
        self.abono_window = abono_window
        abono_window.title(f"💵 Registrar Abono Pedido #{pedido_id}")
        abono_window.geometry("400x200")
        abono_window.transient(self.root)
        abono_window.grab_set()

        def on_close():
            self.abono_window = None
            abono_window.destroy()
        abono_window.protocol("WM_DELETE_WINDOW", on_close)

        frame = ttk.LabelFrame(abono_window, text=f"Abono para {cliente_nombre}", padding="10")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        ttk.Label(frame, text=f"Total Pendiente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text=f"${pendiente_pago:.2f}", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame, text="Monto del Abono ($):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.abono_monto_entry = ttk.Entry(frame, width=15)
        self.abono_monto_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.abono_monto_entry.insert(0, f"{min(pendiente_pago, 100.0):.2f}")  # Sugiere un valor razonable

        def registrar():
            try:
                monto_str = self.abono_monto_entry.get().replace(',', '.').strip()
                if not monto_str:
                    messagebox.showerror("❌ Error", "Ingrese un monto.", parent=abono_window)
                    return
                monto = float(monto_str)
                if monto <= 0:
                    messagebox.showerror("❌ Error", "El monto debe ser positivo.", parent=abono_window)
                    return
                if monto > pendiente_pago:
                    if not messagebox.askyesno("❓ Monto alto", 
                        f"El abono (${monto:.2f}) supera el pendiente (${pendiente_pago:.2f}).\n¿Desea continuar? (Se ajustará a ${pendiente_pago:.2f})",
                        parent=abono_window):
                        return
                    monto = pendiente_pago

                exito, mensaje = client_orders_controller.registrar_abono(pedido_id, monto)
                if exito:
                    messagebox.showinfo("✅ Éxito", mensaje, parent=abono_window)
                    self.load_pedidos()
                    abono_window.destroy()
                    self.abono_window = None
                else:
                    messagebox.showerror("❌ Error", mensaje, parent=abono_window)

            except ValueError:
                messagebox.showerror("❌ Error", "Monto inválido. Use números (ej. 25.50).", parent=abono_window)
            except Exception as e:
                messagebox.showerror("❌ Error", f"Error al registrar: {e}", parent=abono_window)

        ttk.Button(frame, text="💾 Registrar Abono", command=registrar, style="T.Blue.TButton").grid(row=2, column=0, columnspan=2, pady=15)

    def show_abonos(self):
        selected_item = self.pedidos_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido para ver el historial de abonos.")
            return

        pedido_id = self.pedidos_tree.item(selected_item, 'values')[0]
        cliente_nombre = self.pedidos_tree.item(selected_item, 'values')[1]

        # 🔒 Evitar múltiples ventanas
        if self.is_window_open(self.abono_history_window):
            self.abono_history_window.focus()
            return

        try:
            abonos = client_orders_controller.obtener_abonos_pedido(pedido_id)
            if abonos is None:
                abonos = []
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los abonos:\n{e}", parent=self.root)
            return

        if not abonos:
            messagebox.showinfo("ℹ️ Información", f"No hay abonos registrados para el Pedido {pedido_id}.", parent=self.root)
            return

        hist_window = tk.Toplevel(self.root)
        self.abono_history_window = hist_window
        hist_window.title(f"Historial de Abonos Pedido #{pedido_id} - {cliente_nombre}")
        hist_window.geometry("400x300")
        hist_window.transient(self.root)
        hist_window.grab_set()

        def on_close():
            self.abono_history_window = None
            hist_window.destroy()
        hist_window.protocol("WM_DELETE_WINDOW", on_close)

        tree_frame = ttk.LabelFrame(hist_window, text="Detalle de Abonos", padding="10")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Fecha", "Monto")
        abono_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns:
            abono_tree.heading(col, text=col)
            abono_tree.column(col, width=150, anchor=tk.CENTER)

        for a in abonos:
            abono_tree.insert("", tk.END, values=(a['fecha_abono'], f"${float(a['monto']):.2f}"))

        abono_tree.pack(fill="both", expand=True)

    def delete_pedido_action(self):
        selected_item = self.pedidos_tree.focus()
        if not selected_item:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un pedido para eliminar.")
            return

        values = self.pedidos_tree.item(selected_item, 'values')
        pedido_id = values[0]
        cliente_nombre = values[1]
        estado = values[7].lower()

        if estado == "completado":
            msg = f"¿Eliminar pedido COMPLETADO #{pedido_id}?\n⚠️ Esta acción es irreversible y afecta registros contables."
        else:
            msg = f"¿Eliminar pedido #{pedido_id} de {cliente_nombre}?\nSe eliminarán también todos los abonos."

        if not messagebox.askyesno("❓ Confirmar Eliminación", msg, parent=self.root):
            return

        try:
            exito, mensaje = client_orders_controller.eliminar_pedido_cliente(pedido_id)
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje, parent=self.root)
                self.load_pedidos()
            else:
                messagebox.showerror("❌ Error", mensaje, parent=self.root)
        except Exception as e:
            messagebox.showerror("❌ Error Fatal", f"Error al eliminar:\n{e}", parent=self.root)

    def back_to_dashboard(self):
        self.root.destroy()
        # ✅ Recomendación: en lugar de crear Tk() aquí, debería ser gestionado por un AppManager
        # Pero para no romper tu flujo:
        try:
            from dashboard_view import DashboardView
            root = tk.Tk()
            DashboardView(root, self.usuario)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo abrir el dashboard:\n{e}")