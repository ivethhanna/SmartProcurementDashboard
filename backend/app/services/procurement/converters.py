import math
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from unicodedata import normalize


UNIT_ALIASES = {
    "kg": "kg",
    "kilo": "kg",
    "kilos": "kg",
    "kilogramo": "kg",
    "kilogramos": "kg",
    "g": "g",
    "gr": "g",
    "gramo": "g",
    "gramos": "g",
    "l": "L",
    "lt": "L",
    "lts": "L",
    "litro": "L",
    "litros": "L",
    "und": "und",
    "unidad": "und",
    "unidades": "und",
    "u": "und",
}


@dataclass(frozen=True)
class ParsedPurchaseFormat:
    quantity: float
    unit: str
    factor_to_base_unit: float


def _normalize_text(value: str) -> str:
    ascii_text = normalize("NFKD", value.strip().lower()).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text)


def _to_base_factor(quantity: float, parsed_unit: str, base_unit: str) -> float:
    normalized_base = UNIT_ALIASES.get(_normalize_text(base_unit), _normalize_text(base_unit))
    if parsed_unit == normalized_base:
        return quantity
    if parsed_unit == "g" and normalized_base == "kg":
        return quantity / 1000
    raise ValueError(f"No se puede convertir de {parsed_unit} a {base_unit}")


def parse_purchase_format(format_text: str, base_unit: str) -> ParsedPurchaseFormat:
    """Parse a purchase format such as 'Saco 25 kg', 'Caja x 12 und' or 'Paquete 250 gr'.

    If the format does not include an explicit number, common one-unit labels such
    as 'Kilo' and 'Unidad' are interpreted as one base unit.
    """
    text = _normalize_text(format_text)
    number_match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    quantity = float(number_match.group(1).replace(",", ".")) if number_match else 1.0

    unit = None
    for raw_token in re.findall(r"[a-zA-Z]+", text):
        candidate = UNIT_ALIASES.get(raw_token)
        if candidate:
            unit = candidate
    if unit is None:
        unit = UNIT_ALIASES.get(_normalize_text(base_unit), _normalize_text(base_unit))

    factor = _to_base_factor(quantity, unit, base_unit)
    return ParsedPurchaseFormat(quantity=quantity, unit=unit, factor_to_base_unit=factor)


def conversion_factor_from_ingredient(ingredient: object) -> float:
    """Return the base-unit quantity included in one purchase format.

    The CSV/model field `conversion_factor` is the authoritative value when
    present because it already encodes business-specific formats. The text parser
    is used as fallback for uploaded rows that only provide `purchase_format`.
    """
    explicit_factor = getattr(ingredient, "conversion_factor", None)
    if explicit_factor is not None:
        return float(explicit_factor)

    purchase_format = getattr(ingredient, "purchase_format", None)
    base_unit = getattr(ingredient, "base_unit", None)
    if not purchase_format or not base_unit:
        raise ValueError("El ingrediente necesita conversion_factor o purchase_format/base_unit")
    return parse_purchase_format(str(purchase_format), str(base_unit)).factor_to_base_unit


def formato_a_unidad_base(cantidad_formatos: float, factor: float) -> float:
    if factor <= 0:
        raise ValueError("El factor de conversion debe ser mayor que cero")
    return float(cantidad_formatos) * float(factor)


def unidad_base_a_formato(cantidad_unidad_base: float, factor: float) -> int:
    if factor <= 0:
        raise ValueError("El factor de conversion debe ser mayor que cero")
    if cantidad_unidad_base <= 0:
        return 0
    return int(math.ceil(float(cantidad_unidad_base) / float(factor)))


def round_quantity(value: float, digits: int = 2) -> float:
    quantizer = Decimal("1") if digits == 0 else Decimal("1." + ("0" * digits))
    return float(Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP))
