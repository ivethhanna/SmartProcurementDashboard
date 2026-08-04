from types import SimpleNamespace

from app.services.procurement.converters import (
    conversion_factor_from_ingredient,
    formato_a_unidad_base,
    parse_purchase_format,
    unidad_base_a_formato,
)


def test_parse_standard_format() -> None:
    parsed = parse_purchase_format("Saco 25 kg", "kg")

    assert parsed.factor_to_base_unit == 25
    assert parsed.unit == "kg"


def test_parse_grams_to_kg() -> None:
    parsed = parse_purchase_format("Paquete 250 gr", "kg")

    assert parsed.factor_to_base_unit == 0.25


def test_parse_box_units() -> None:
    parsed = parse_purchase_format("Caja x 12 und", "und")

    assert parsed.factor_to_base_unit == 12


def test_conversion_uses_explicit_factor_first() -> None:
    ingredient = SimpleNamespace(conversion_factor=2.55, purchase_format="Lata 2550 gr", base_unit="kg")

    assert conversion_factor_from_ingredient(ingredient) == 2.55


def test_format_to_base_and_back_rounds_up() -> None:
    assert formato_a_unidad_base(3, 25) == 75
    assert unidad_base_a_formato(76, 25) == 4
    assert unidad_base_a_formato(75, 25) == 3
