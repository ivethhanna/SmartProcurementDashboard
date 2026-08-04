from dataclasses import dataclass

from app.services.procurement.converters import formato_a_unidad_base, unidad_base_a_formato


@dataclass(frozen=True)
class OrderComparison:
    projected_consumption: float
    current_inventory: float
    real_need: float
    ordered_formats: float
    ordered_base_units: float
    difference_base_units: float
    difference_formats: float
    tolerance_base_units: float
    impact_money: float
    alert_type: str | None
    corrected_order_formats: int
    corrected_order_base_units: float


def calculate_real_need(projected_consumption: float, current_inventory: float) -> float:
    return max(float(projected_consumption) - float(current_inventory), 0.0)


def compare_order_to_need(
    projected_consumption: float,
    current_inventory: float,
    ordered_formats: float,
    conversion_factor: float,
    estimated_unit_cost: float,
) -> OrderComparison:
    """Compare an order against real need using one full purchase format as tolerance."""
    real_need = calculate_real_need(projected_consumption, current_inventory)
    ordered_base_units = formato_a_unidad_base(ordered_formats, conversion_factor)
    difference = ordered_base_units - real_need
    tolerance = float(conversion_factor)

    alert_type: str | None = None
    if abs(difference) >= tolerance:
        alert_type = "sobre_pedido" if difference > 0 else "quiebre"

    corrected_formats = unidad_base_a_formato(real_need, conversion_factor)
    corrected_base_units = formato_a_unidad_base(corrected_formats, conversion_factor)

    return OrderComparison(
        projected_consumption=round(float(projected_consumption), 2),
        current_inventory=round(float(current_inventory), 2),
        real_need=round(real_need, 2),
        ordered_formats=float(ordered_formats),
        ordered_base_units=round(ordered_base_units, 2),
        difference_base_units=round(abs(difference), 2),
        difference_formats=round(abs(difference) / tolerance, 2) if tolerance else 0,
        tolerance_base_units=round(tolerance, 2),
        impact_money=round(abs(difference) * float(estimated_unit_cost), 2),
        alert_type=alert_type,
        corrected_order_formats=corrected_formats,
        corrected_order_base_units=round(corrected_base_units, 2),
    )
