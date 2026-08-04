from collections import defaultdict
from typing import Any

from app.services.forecasting.projections import ProjectionResult, project_consumption
from app.services.procurement.calculations import OrderComparison, compare_order_to_need


SEVERITY_WEIGHT = {
    "alta": 3,
    "media": 2,
    "baja": 1,
}


def _group_consumption(consumption_rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in consumption_rows:
        key = (str(row["sucursal"]), str(row["ingrediente_id"]))
        grouped[key].append({"week": row["semana"], "value": float(row["consumo_unidad_base"])})
    return grouped


def _index_inventory(inventory_rows: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    return {
        (str(row["sucursal"]), str(row["ingrediente_id"])): float(row["stock_actual_unidad_base"])
        for row in inventory_rows
    }


def _index_orders(order_rows: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    return {
        (str(row["sucursal"]), str(row["ingrediente_id"])): float(row["cantidad_formatos"])
        for row in order_rows
    }


def _index_ingredients(ingredient_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["ingrediente_id"]): row for row in ingredient_rows}


def _severity(alert_type: str, comparison: OrderComparison, projection: ProjectionResult, ingredient: dict[str, Any]) -> str:
    is_perishable = bool(ingredient["es_perecedero"])
    relative = comparison.difference_base_units / max(comparison.real_need, comparison.tolerance_base_units, 1)
    high_consumption = projection.projected_consumption >= comparison.tolerance_base_units * 4

    if alert_type == "quiebre":
        if is_perishable or high_consumption or relative >= 0.5:
            return "alta"
        return "media"

    if alert_type == "olvidado":
        if is_perishable or high_consumption:
            return "alta"
        return "media"

    if is_perishable and relative >= 0.5:
        return "alta"
    if is_perishable or relative >= 0.5:
        return "media"
    return "baja"


def _message(alert_type: str, branch: str, ingredient_name: str, quantity: float, unit: str) -> str:
    rounded = round(quantity, 2)
    if alert_type == "quiebre":
        return (
            f"ALERTA: {branch} est\u00e1 pidiendo {rounded} {unit} de {ingredient_name} "
            "menos que lo proyectado \u2192 riesgo de quiebre."
        )
    if alert_type == "sobre_pedido":
        return (
            f"ALERTA: {branch} est\u00e1 pidiendo {rounded} {unit} de {ingredient_name} "
            "m\u00e1s que lo proyectado \u2192 posible sobre-pedido."
        )
    return (
        f"ALERTA: {branch} no incluy\u00f3 {ingredient_name} en la orden de esta semana "
        "\u2192 riesgo de quiebre."
    )


def _historical_explanation(projection: ProjectionResult) -> list[dict[str, object]]:
    return [
        {"semana": point.week, "consumo": point.value, "descartado_outlier": point.is_outlier}
        for point in projection.points
    ]


def _alert_score(alert: dict[str, Any]) -> float:
    severity = SEVERITY_WEIGHT[str(alert["severidad"])]
    explanation = alert["explicacion"]
    need = max(float(explanation["necesidad_real"]), float(explanation["tolerancia_redondeo_aplicada"]), 1)
    relative = float(alert["cantidad_diferencia"]) / need
    perishable = 1.35 if alert["es_perecedero"] else 1.0
    return severity * relative * perishable


def _is_consistent_historical_consumption(projection: ProjectionResult) -> bool:
    used_positive = [value for value in projection.weeks_used if value > 0]
    return len(used_positive) >= 4 and (sum(used_positive) / len(used_positive)) > 0


def _build_alert(
    branch: str,
    ingredient: dict[str, Any],
    alert_type: str,
    severity: str,
    comparison: OrderComparison,
    projection: ProjectionResult,
) -> dict[str, Any]:
    unit = str(ingredient["unidad_base"])
    ingredient_name = str(ingredient["nombre"])
    explanation = {
        "consumo_historico_usado": _historical_explanation(projection),
        "consumo_proyectado": comparison.projected_consumption,
        "inventario_actual": comparison.current_inventory,
        "necesidad_real": comparison.real_need,
        "orden_recibida_formatos": comparison.ordered_formats,
        "orden_recibida_unidad_base": comparison.ordered_base_units,
        "tolerancia_redondeo_aplicada": comparison.tolerance_base_units,
        "tendencia": projection.trend,
        "confianza": projection.confidence,
    }
    return {
        "sucursal": branch,
        "ingrediente": ingredient_name,
        "tipo": alert_type,
        "severidad": severity,
        "cantidad_diferencia": comparison.difference_base_units,
        "unidad": unit,
        "impacto_dinero": comparison.impact_money,
        "es_perecedero": bool(ingredient["es_perecedero"]),
        "mensaje": _message(alert_type, branch, ingredient_name, comparison.difference_base_units, unit),
        "explicacion": explanation,
    }


def generate_alerts(
    ingredient_rows: list[dict[str, Any]],
    consumption_rows: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
    order_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ingredients = _index_ingredients(ingredient_rows)
    consumption_by_key = _group_consumption(consumption_rows)
    inventory_by_key = _index_inventory(inventory_rows)
    orders_by_key = _index_orders(order_rows)
    alerts: list[dict[str, Any]] = []

    for key, history in consumption_by_key.items():
        branch, ingredient_id = key
        ingredient = ingredients.get(ingredient_id)
        if ingredient is None:
            raise ValueError(f"Consumo referencia ingrediente_id '{ingredient_id}' no encontrado")

        projection = project_consumption(history)
        inventory = inventory_by_key.get(key, 0.0)
        ordered_formats = orders_by_key.get(key, 0.0)
        conversion_factor = float(ingredient["unidad_base_por_formato"])
        unit_cost = float(ingredient.get("costo_unitario_estimado", 0) or 0)

        comparison = compare_order_to_need(
            projected_consumption=projection.projected_consumption,
            current_inventory=inventory,
            ordered_formats=ordered_formats,
            conversion_factor=conversion_factor,
            estimated_unit_cost=unit_cost,
        )

        alert_type = comparison.alert_type
        if key not in orders_by_key and _is_consistent_historical_consumption(projection):
            alert_type = "olvidado"

        if alert_type is None:
            continue

        severity = _severity(alert_type, comparison, projection, ingredient)
        alerts.append(_build_alert(branch, ingredient, alert_type, severity, comparison, projection))

    return sorted(alerts, key=_alert_score, reverse=True)
