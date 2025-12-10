import pytest

from products_view import validate_date, ProductsView


class TestProductsViewLogic:
    def make_view(self):
        # Create instance without calling __init__ to avoid Tkinter UI setup
        view = ProductsView.__new__(ProductsView)
        return view

    # --- validate_date ---
    def test_validate_date_accepts_valid_format(self):
        assert validate_date("2025-01-31") is True

    def test_validate_date_rejects_invalid_format(self):
        # Wrong separators and invalid month/day
        assert validate_date("31/01/2025") is False
        assert validate_date("2025-13-01") is False
        assert validate_date("2025-00-10") is False
        assert validate_date("2025-02-30") is False
        assert validate_date("") is False

    # --- extract_proveedor_id ---
    def test_extract_proveedor_id_parses_leading_id(self):
        view = self.make_view()
        assert view.extract_proveedor_id("12 - Proveedor ABC") == 12

    def test_extract_proveedor_id_returns_none_on_empty_or_malformed(self):
        view = self.make_view()
        assert view.extract_proveedor_id("") is None
        assert view.extract_proveedor_id("   ") is None
        assert view.extract_proveedor_id("Proveedor sin ID") is None
        assert view.extract_proveedor_id("abc - Proveedor XYZ") is None
        assert view.extract_proveedor_id("99-") == 99  # still splits, trims not required by code

    # --- validate_inputs ---
    def test_validate_inputs_fails_when_required_missing(self):
        view = self.make_view()
        valid, msg = view.validate_inputs(
            nombre="",
            precio_compra="10.0",
            precio_venta="15.0",
            stock="5",
            proveedor_str="1 - Prov",
            categoria="Utiles",
            fecha="2025-01-01",
            is_edit=False,
        )
        assert valid is False
        assert "obligatorios" in msg

    def test_validate_inputs_fails_on_invalid_numeric_types(self):
        view = self.make_view()
        valid, msg = view.validate_inputs(
            nombre="Lapiz",
            precio_compra="diez",
            precio_venta="quince",
            stock="cinco",
            proveedor_str="1 - Prov",
            categoria="Utiles",
            fecha="2025-01-01",
            is_edit=False,
        )
        assert valid is False
        assert "deben ser números válidos" in msg

    def test_validate_inputs_fails_on_invalid_provider(self):
        view = self.make_view()
        valid, msg = view.validate_inputs(
            nombre="Lapiz",
            precio_compra="10.0",
            precio_venta="15.0",
            stock="5",
            proveedor_str="Proveedor sin ID",
            categoria="Utiles",
            fecha="2025-01-01",
            is_edit=False,
        )
        assert valid is False
        assert "Proveedor inválido" in msg

    def test_validate_inputs_fails_on_invalid_date_when_creating(self):
        view = self.make_view()
        valid, msg = view.validate_inputs(
            nombre="Lapiz",
            precio_compra="10.0",
            precio_venta="15.0",
            stock="5",
            proveedor_str="2 - Prov",
            categoria="Utiles",
            fecha="2025/01/01",  # invalid format
            is_edit=False,
        )
        assert valid is False
        assert "formato" in msg

    def test_validate_inputs_succeeds_on_create_with_valid_data(self):
        view = self.make_view()
        valid, result = view.validate_inputs(
            nombre="Lapiz",
            precio_compra="10.5",
            precio_venta="15.75",
            stock="7",
            proveedor_str="3 - Prov",
            categoria="Utiles",
            fecha="2025-01-05",
            is_edit=False,
        )
        assert valid is True
        # result is (nombre, pc float, pv float, stock int, categoria, proveedor_id int, fecha)
        assert result[0] == "Lapiz"
        assert isinstance(result[1], float) and result[1] == 10.5
        assert isinstance(result[2], float) and result[2] == 15.75
        assert isinstance(result[3], int) and result[3] == 7
        assert result[4] == "Utiles"
        assert isinstance(result[5], int) and result[5] == 3
        assert result[6] == "2025-01-05"

    def test_validate_inputs_succeeds_on_edit_ignores_date_and_returns_none_for_fecha(self):
        view = self.make_view()
        # Provide invalid date to ensure it's ignored on edit
        valid, result = view.validate_inputs(
            nombre="Borrador",
            precio_compra="1.0",
            precio_venta="2.0",
            stock="10",
            proveedor_str="5 - Prov",
            categoria="Utiles",
            fecha="invalid-date",
            is_edit=True,
        )
        assert valid is True
        assert result[-1] is None  # fecha is None on edit per implementation
