from typing import Any

from app.services.forecasting.projections import project_consumption
from app.services.procurement.calculations import calculate_real_need
from app.services.procurement.converters import formato_a_unidad_base, unidad_base_a_formato


def build_corrected_orders_by_provider(
    ingredient_rows: list[dict[str, Any]],
    consumption_rows: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ingredients = {str(row["ingrediente_id"]): row for row in ingredient_rows}
    inventory = {
        (str(row["sucursal"]), str(row["ingrediente_id"])): float(row["stock_actual_unidad_base"])
        for row in inventory_rows
    }
    grouped_consumption: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in consumption_rows:
        key = (str(row["sucursal"]), str(row["ingrediente_id"]))
        grouped_consumption.setdefault(key, []).append({"week": row["semana"], "value": row["consumo_unidad_base"]})

    provider_groups: dict[str, list[dict[str, Any]]] = {}
    for (branch, ingredient_id), history in grouped_consumption.items():
        ingredient = ingredients.get(ingredient_id)
        if ingredient is None:
            continue

        projection = project_consumption(history)
        factor = float(ingredient["unidad_base_por_formato"])
        real_need = calculate_real_need(
            projection.projected_consumption,
            inventory.get((branch, ingredient_id), 0.0),
        )
        corrected_formats = unidad_base_a_formato(real_need, factor)
        if corrected_formats <= 0:
            continue

        corrected_base = formato_a_unidad_base(corrected_formats, factor)
        provider = str(ingredient.get("proveedor") or "Sin proveedor")
        provider_groups.setdefault(provider, []).append(
            {
                "sucursal": branch,
                "ingrediente_id": ingredient_id,
                "ingrediente": ingredient["nombre"],
                "unidad": ingredient["unidad_base"],
                "formato_compra": ingredient["formato_compra"],
                "cantidad_formatos_corregida": corrected_formats,
                "cantidad_unidad_base_corregida": round(corrected_base, 2),
                "consumo_proyectado": projection.projected_consumption,
                "inventario_actual": round(inventory.get((branch, ingredient_id), 0.0), 2),
                "necesidad_real": round(real_need, 2),
            }
        )

    return [
        {
            "proveedor": provider,
            "items": sorted(items, key=lambda item: (item["sucursal"], item["ingrediente"])),
        }
        for provider, items in sorted(provider_groups.items())
    ]
