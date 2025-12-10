import logging
import pytest

import products_controller as pc


# --- Fakes for DB connection/cursor ---
class FakeCursor:
    def __init__(self, fetchall_result=None, rowcount=0, raise_on_execute=False):
        self._fetchall_result = fetchall_result or []
        self._rowcount = rowcount
        self._raise_on_execute = raise_on_execute
        self.closed = False
        self.last_query = None
        self.last_params = None

    def execute(self, query, params=None):
        if self._raise_on_execute:
            raise Exception("execute failed")
        self.last_query = query
        self.last_params = params

    def fetchall(self):
        return self._fetchall_result

    @property
    def rowcount(self):
        return self._rowcount

    def close(self):
        self.closed = True


class FakeConn:
    def __init__(self, cursor: FakeCursor):
        self._cursor = cursor
        self.closed = False
        self.committed = False
        self.rolled_back = False

    def cursor(self, dictionary=False):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


# ----------------------
# Behaviors covered:
# 1) get_all_products returns [] and logs error when DB connection fails
# 2) add_product rejects non-integer stock with "Stock inválido."
# 3) add_product returns connection error message on DB failure
# 4) update_product returns not found when rowcount == 0
# 5) delete_product succeeds (rowcount == 1) and commits
# ----------------------


def test_get_all_products_returns_empty_and_logs_when_no_connection(monkeypatch, caplog):
    monkeypatch.setattr(pc, "conectar", lambda: None)
    with caplog.at_level(logging.ERROR):
        result = pc.get_all_products()
    assert result == []
    # Either a connection error log or exception log; implementation logs a specific error
    assert any("No se pudo conectar a la base de datos en get_all_products" in rec.message
               for rec in caplog.records)


def test_add_product_rejects_non_integer_stock():
    ok, msg = pc.add_product(
        nombre="Prod",
        descripcion="Desc",
        precio_compra=1.0,
        precio_venta=2.0,
        stock="5.5",  # not an int-coercible string
        categoria="Cat",
        proveedor_id=1,
        fecha_ingreso="2025-01-01",
    )
    assert ok is False
    assert "Stock inválido" in msg


def test_add_product_returns_error_when_no_db_connection(monkeypatch):
    monkeypatch.setattr(pc, "conectar", lambda: None)
    ok, msg = pc.add_product(
        nombre="Prod",
        descripcion="Desc",
        precio_compra=1.0,
        precio_venta=2.0,
        stock=1,
        categoria="Cat",
        proveedor_id=1,
        fecha_ingreso="2025-01-01",
    )
    assert ok is False
    assert "No se pudo conectar a la base de datos" in msg


def test_update_product_returns_not_found_when_rowcount_zero(monkeypatch):
    fake_cursor = FakeCursor(rowcount=0)
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(pc, "conectar", lambda: fake_conn)

    ok, msg = pc.update_product(
        producto_id=999,
        nombre="N",
        descripcion="D",
        precio_compra=1.0,
        precio_venta=2.0,
        stock=3,
        categoria="C",
        proveedor_id=1,
    )
    assert ok is False
    assert "no encontrado" in msg.lower()
    assert fake_conn.committed is False


def test_delete_product_success_commits(monkeypatch):
    fake_cursor = FakeCursor(rowcount=1)
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(pc, "conectar", lambda: fake_conn)

    ok, msg = pc.delete_product(producto_id=1)
    assert ok is True
    assert "eliminado" in msg.lower()
    assert fake_conn.committed is True
