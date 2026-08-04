from statistics import median
from typing import Any


def detect_cross_branch_anomalies(
    ingredient_rows: list[dict[str, Any]],
    order_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect branch orders that are far from the other pilot branches.

    A branch is flagged when its converted base-unit order is more than double
    or less than half the median of the other branches for the same ingredient.
    This is a simple typo/out-of-pattern guard, not the main projection check.
    """
    ingredients = {str(row["ingrediente_id"]): row for row in ingredient_rows}
    by_ingredient: dict[str, list[dict[str, Any]]] = {}

    for order in order_rows:
        ingredient_id = str(order["ingrediente_id"])
        ingredient = ingredients.get(ingredient_id)
        if ingredient is None:
            continue
        converted = float(order["cantidad_formatos"]) * float(ingredient["unidad_base_por_formato"])
        by_ingredient.setdefault(ingredient_id, []).append(
            {
                "sucursal": str(order["sucursal"]),
                "ingrediente_id": ingredient_id,
                "ingrediente": ingredient["nombre"],
                "unidad": ingredient["unidad_base"],
                "orden_unidad_base": round(converted, 2),
            }
        )

    anomalies: list[dict[str, Any]] = []
    for ingredient_id, rows in by_ingredient.items():
        if len(rows) < 3:
            continue
        for row in rows:
            others = [candidate["orden_unidad_base"] for candidate in rows if candidate["sucursal"] != row["sucursal"]]
            if not others:
                continue
            other_median = median(others)
            if other_median <= 0:
                continue
            ratio = row["orden_unidad_base"] / other_median
            if ratio > 2:
                direction = "alta"
            elif ratio < 0.5:
                direction = "baja"
            else:
                continue
            anomalies.append(
                {
                    **row,
                    "tipo": direction,
                    "mediana_otras_sucursales": round(other_median, 2),
                    "ratio_vs_mediana": round(ratio, 2),
                    "mensaje": (
                        f"{row['sucursal']} pide {row['orden_unidad_base']} {row['unidad']} de "
                        f"{row['ingrediente']}, {round(ratio, 2)}x vs. la mediana de las otras sucursales."
                    ),
                }
            )

    return sorted(anomalies, key=lambda item: abs(float(item["ratio_vs_mediana"]) - 1), reverse=True)
