import pytest

import sales_view as sv

# --- Fakes to avoid real Tkinter UI and blocking loops ---
class FakeLabel:
    def __init__(self):
        self.text = ""
    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]

class FakeEntry:
    def __init__(self, text=""):
        self._text = str(text)
    def get(self):
        return self._text
    def delete(self, start, end=None):
        self._text = ""
    def insert(self, index, s):
        self._text += str(s)

class FakeButton:
    def __init__(self):
        self.state = "normal"
        self.text = ""
    def config(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]
        if "text" in kwargs:
            self.text = kwargs["text"]

class FakeCombo:
    def __init__(self):
        self._value = ""
    def current(self, idx):
        pass
    def bind(self, *args, **kwargs):
        pass

class FakeRoot:
    def __init__(self):
        self.title_text = ""
        self.size = ""
        self.bg = ""
        self.protocols = {}
        self.destroyed = False
        self.after_calls = []
    def title(self, t):
        self.title_text = t
    def geometry(self, g):
        self.size = g
    def configure(self, **kwargs):
        self.bg = kwargs.get("bg", self.bg)
    def resizable(self, *args, **kwargs):
        pass
    def protocol(self, name, func):
        self.protocols[name] = func
    def after(self, ms, func):
        # record call; do not execute automatically
        self.after_calls.append((ms, func))
    def update_idletasks(self):
        pass
    def destroy(self):
        self.destroyed = True

class MsgCapture:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.infos = []
        self.confirms = []
    def showerror(self, title, msg, **kwargs):
        self.errors.append((title, msg))
        return None
    def showwarning(self, title, msg, **kwargs):
        self.warnings.append((title, msg))
        return None
    def showinfo(self, title, msg, **kwargs):
        self.infos.append((title, msg))
        return None
    def askyesno(self, title, msg, **kwargs):
        self.confirms.append((title, msg))
        return True


class TestVentasViewLogic:
    def make_view(self, monkeypatch, products):
        # Create instance without __init__ to control attributes and avoid real Tk widgets
        view = sv.VentasView.__new__(sv.VentasView)
        view.root = FakeRoot()
        view.usuario = {"id": 42, "nombre": "Tester"}
        view.producto_id_map = {}
        view.registrando = False

        # Widgets used by methods
        view.producto_var = type("SVar", (), {"get": lambda self: self._v, "set": lambda self, v: setattr(self, "_v", v)})()
        view.producto_var._v = ""
        view.producto_combo = FakeCombo()
        view.precio_label = FakeLabel()
        view.stock_label = FakeLabel()
        view.cantidad_entry = FakeEntry("1")
        view.total_label = FakeLabel()
        view.registrar_btn = FakeButton()

        # Patch messagebox
        msg = MsgCapture()
        monkeypatch.setattr(sv, "messagebox", msg, raising=False)
        # Patch data source
        monkeypatch.setattr(view, "obtener_productos_actualizados", lambda: products)
        # Initialize product map via cargar_productos (logic under test)
        view.cargar_productos()
        # If there are products, select first display
        if view.producto_id_map:
            first_display = next(iter(view.producto_id_map.keys()))
            view.producto_var.set(first_display)
        return view, msg

    # --- Behaviors to cover ---
    def test_cargar_productos_populates_map_and_coerces_types(self, monkeypatch):
        products = [
            {"id": 1, "nombre": "A", "precio_venta": "10.50", "stock": "3"},
            {"id": 2, "nombre": "B", "precio_venta": 5, "stock": 7},
        ]
        view, _ = self.make_view(monkeypatch, products)
        assert len(view.producto_id_map) == 2
        # ensure values coerced
        any_item = next(iter(view.producto_id_map.values()))
        assert isinstance(any_item["precio"], float)
        assert isinstance(any_item["stock"], int)

    def test_actualizar_datos_producto_updates_labels_and_total(self, monkeypatch):
        products = [{"id": 1, "nombre": "A", "precio_venta": 10.0, "stock": 5}]
        view, _ = self.make_view(monkeypatch, products)
        view.cantidad_entry = FakeEntry("2")  # set qty
        view.actualizar_datos_producto(None)
        assert view.precio_label.text == "$10.00"
        assert "Stock actual: 5" in view.stock_label.text
        assert view.total_label.text == "$20.00"

    def test_actualizar_total_caps_by_stock_and_informs_user(self, monkeypatch):
        products = [{"id": 1, "nombre": "A", "precio_venta": 10.0, "stock": 3}]
        view, msg = self.make_view(monkeypatch, products)
        # request more than stock
        view.cantidad_entry = FakeEntry("10")
        view.actualizar_total(None)
        # quantity adjusted and info shown
        assert any("Stock máximo" in m[0] or "Stock máximo" in m[1] for m in msg.infos)
        assert view.cantidad_entry.get() == "3"
        assert view.total_label.text == "$30.00"

    def test_registrar_venta_rejects_invalid_selection(self, monkeypatch):
        products = [{"id": 1, "nombre": "A", "precio_venta": 10.0, "stock": 5}]
        view, msg = self.make_view(monkeypatch, products)
        # Clear selection to simulate invalid
        view.producto_var.set("")
        view.registrar_venta()
        assert any("Selección inválida" in m[0] or "Selección inválida" in m[1] for m in msg.warnings)

    def test_registrar_venta_validates_quantity_bounds(self, monkeypatch):
        products = [{"id": 1, "nombre": "A", "precio_venta": 10.0, "stock": 2}]
        view, msg = self.make_view(monkeypatch, products)
        # set invalid > stock
        view.cantidad_entry = FakeEntry("5")
        view.registrar_venta()
        assert any("Cantidad inválida" in m[0] or "Cantidad inválida" in m[1] for m in msg.errors)

    def test_registrar_venta_success_shows_info_and_schedules_dashboard(self, monkeypatch):
        products = [{"id": 1, "nombre": "A", "precio_venta": 10.0, "stock": 5}]
        view, msg = self.make_view(monkeypatch, products)
        # Patch controller call
        def fake_registrar_venta_completa(producto_id, usuario_id, cantidad, precio_unitario):
            assert producto_id == 1
            assert usuario_id == 42
            assert cantidad == 2
            assert precio_unitario == 10.0
            return True, "ok"
        monkeypatch.setattr(sv, "registrar_venta_completa", fake_registrar_venta_completa)

        view.cantidad_entry = FakeEntry("2")
        view.registrar_venta()

        # button should be disabled during processing
        assert view.registrar_btn.state == "disabled"
        assert any("¡Venta Exitosa" in m[0] or "¡Venta Exitosa" in m[1] for m in msg.infos)
        # scheduled dashboard redirect
        assert len(view.root.after_calls) >= 1
        ms, func = view.root.after_calls[0]
        assert ms == 300 and callable(func)

    def test_registrar_venta_failure_shows_error_and_reenables(self, monkeypatch):
        products = [{"id": 1, "nombre": "A", "precio_venta": 10.0, "stock": 5}]
        view, msg = self.make_view(monkeypatch, products)
        # Patch controller to fail
        monkeypatch.setattr(sv, "registrar_venta_completa", lambda **kwargs: (False, "DB error"))
        view.cantidad_entry = FakeEntry("1")
        view.registrar_venta()
        # error message shown and button re-enabled
        assert any("Error" in m[0] and "DB error" in m[1] for m in msg.errors)
        assert view.registrar_btn.state == "normal"

    def test_registrar_venta_handles_unexpected_exception_and_reenables(self, monkeypatch):
        products = [{"id": 1, "nombre": "A", "precio_venta": 10.0, "stock": 5}]
        view, msg = self.make_view(monkeypatch, products)
        # Make cantidad_entry.get raise ValueError via bad string that int() fails in registrar_venta
        view.cantidad_entry = FakeEntry("not-int")
        view.registrar_venta()
        assert any("Error inesperado" in m[0] for m in msg.errors)
        assert view.registrar_btn.state == "normal"
