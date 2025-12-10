import pytest

import pedidos_view as pv


# -----------------------------
# Helper fakes to avoid real Tkinter UI
# -----------------------------
class FakeVar:
    def __init__(self, value=""):
        self._value = value
    def get(self):
        return self._value
    def set(self, v):
        self._value = v


class FakeEntry:
    def __init__(self, text=""):
        self.text = text
    def get(self):
        return self.text
    def delete(self, start, end=None):
        # ignore indices; clear all
        self.text = ""
    def insert(self, index, s):
        # ignore index; append
        self.text += str(s)
    def focus(self):
        pass


class FakeTree:
    def __init__(self):
        self._rows = []  # list of (values)
        self._focus = None
    def get_children(self):
        # return identifiers; use indices as ids
        return list(range(len(self._rows)))
    def delete(self, item):
        # remove by index
        if 0 <= item < len(self._rows):
            self._rows.pop(item)
            # reset focus if needed
            self._focus = None if self._focus == item else self._focus
    def insert(self, parent, index, values=None, **kwargs):
        self._rows.append(tuple(values) if values is not None else tuple())
        return len(self._rows) - 1
    def focus(self):
        return self._focus
    def set_focus(self, idx):
        self._focus = idx
    def index(self, item):
        return item


class FakeToplevel:
    def __init__(self, exists=True):
        self._exists = exists
    def winfo_exists(self):
        return bool(self._exists)


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


class TestPedidosViewLogic:
    def make_view_with_fakes(self, monkeypatch):
        # Create instance without __init__ to avoid real Tk widgets
        view = pv.PedidosView.__new__(pv.PedidosView)
        # minimal attributes used by methods under test
        view.product_map = {}
        view.new_pedido_items = []
        view.items_tree = FakeTree()
        view.producto_var = FakeVar()
        view.cantidad_entry = FakeEntry()
        view.precio_unitario_entry = FakeEntry()

        # Patch messagebox to capture calls
        msg = MsgCapture()
        monkeypatch.setattr(pv, "messagebox", msg, raising=False)
        return view, msg

    # --- validar_fecha ---
    def test_validar_fecha_accepts_and_normalizes(self):
        assert pv.validar_fecha("2025-12-09") == "2025-12-09"
    def test_validar_fecha_returns_none_on_invalid_or_empty(self):
        assert pv.validar_fecha("") is None
        assert pv.validar_fecha("2025/12/09") is None
        assert pv.validar_fecha("2025-13-01") is None

    # --- is_window_open ---
    def test_is_window_open_true_when_exists(self):
        view = pv.PedidosView.__new__(pv.PedidosView)
        assert view.is_window_open(FakeToplevel(True)) is True
    def test_is_window_open_false_when_none_or_destroyed(self):
        view = pv.PedidosView.__new__(pv.PedidosView)
        assert view.is_window_open(None) is False
        assert view.is_window_open(FakeToplevel(False)) is False

    # --- add_item_to_pedido validations ---
    def test_add_item_to_pedido_errors_when_no_product_selected(self, monkeypatch):
        view, msg = self.make_view_with_fakes(monkeypatch)
        view.product_map = {"Prod A (ID: 1)": {"id": 1, "precio_compra": 10.0, "stock_actual": 5}}
        # Leave producto_var empty
        view.cantidad_entry.text = "2"
        view.precio_unitario_entry.text = "10.0"

        view.add_item_to_pedido()

        assert len(msg.errors) >= 1
        assert any("Seleccione un producto" in m[1] for m in msg.errors)
        assert view.new_pedido_items == []

    def test_add_item_to_pedido_errors_on_non_numeric_inputs(self, monkeypatch):
        view, msg = self.make_view_with_fakes(monkeypatch)
        view.product_map = {"Prod A (ID: 1)": {"id": 1, "precio_compra": 10.0, "stock_actual": 5}}
        view.producto_var.set("Prod A (ID: 1)")
        view.cantidad_entry.text = "dos"
        view.precio_unitario_entry.text = "10,00"  # comma will be handled but cantidad invalid triggers ValueError

        view.add_item_to_pedido()

        assert len(msg.errors) >= 1
        assert any("números válidos" in m[1] for m in msg.errors)
        assert view.new_pedido_items == []

    def test_add_item_to_pedido_success_appends_and_updates_tree(self, monkeypatch):
        view, msg = self.make_view_with_fakes(monkeypatch)
        view.product_map = {"Prod A (ID: 1)": {"id": 1, "precio_compra": 10.5, "stock_actual": 5}}
        view.producto_var.set("Prod A (ID: 1)")
        view.cantidad_entry.text = "3"
        view.precio_unitario_entry.text = "12.00"

        view.add_item_to_pedido()

        assert msg.errors == []
        assert len(view.new_pedido_items) == 1
        # update_items_tree should have inserted one row
        assert len(view.items_tree._rows) == 1
        # Ensure subtotal calculation correctness
        item = view.new_pedido_items[0]
        assert item["cantidad"] == 3
        assert item["precio_unitario"] == 12.0
        assert item["subtotal"] == 36.0

    # --- remove_item_from_pedido ---
    def test_remove_item_from_pedido_warns_when_nothing_selected(self, monkeypatch):
        view, msg = self.make_view_with_fakes(monkeypatch)
        # Seed one item and row but don't set focus
        view.new_pedido_items = [{"producto_id": 1, "producto_nombre": "Prod A", "cantidad": 1, "precio_unitario": 10.0, "subtotal": 10.0}]
        view.update_items_tree()

        view.remove_item_from_pedido()

        assert len(msg.warnings) >= 1
        assert any("Seleccione un ítem" in m[1] for m in msg.warnings)
        # nothing removed
        assert len(view.new_pedido_items) == 1

    def test_remove_item_from_pedido_removes_selected(self, monkeypatch):
        view, msg = self.make_view_with_fakes(monkeypatch)
        # seed two items
        view.new_pedidos = None  # unrelated attribute should not affect
        view.new_pedido_items = [
            {"producto_id": 1, "producto_nombre": "Prod A", "cantidad": 1, "precio_unitario": 10.0, "subtotal": 10.0},
            {"producto_id": 2, "producto_nombre": "Prod B", "cantidad": 2, "precio_unitario": 5.0, "subtotal": 10.0},
        ]
        view.update_items_tree()
        # select second row (index 1)
        view.items_tree.set_focus(1)

        view.remove_item_from_pedido()

        assert msg.warnings == []
        assert len(view.new_pedido_items) == 1
        assert view.new_pedido_items[0]["producto_id"] == 1
        # tree should reflect the removal
        assert len(view.items_tree._rows) == 1
