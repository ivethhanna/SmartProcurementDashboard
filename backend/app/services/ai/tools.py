from typing import Any
from unicodedata import normalize

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consumption import Consumption
from app.models.ingredient import Ingredient
from app.models.inventory import Inventory
from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier
from app.services.alerts.health_score import health_scores_by_branch
from app.services.dashboard_data import get_branches, get_live_alerts, get_procurement_data
from app.services.forecasting.anomaly_detection import detect_cross_branch_anomalies
from app.services.forecasting.projections import project_consumption
from app.services.procurement.converters import formato_a_unidad_base
from app.services.procurement.supplier_grouping import build_corrected_orders_by_provider


TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "get_alerts",
        "description": "Obtiene alertas activas de compras, filtrables por sucursal, tipo o severidad.",
        "parameters": {
            "type": "object",
            "properties": {
                "sucursal": {"type": "string", "description": "Nombre de la sucursal, opcional."},
                "tipo": {"type": "string", "description": "quiebre, sobre_pedido u olvidado."},
                "severidad": {"type": "string", "description": "alta, media o baja."},
            },
        },
    },
    {
        "name": "get_consumption_history",
        "description": "Obtiene el consumo historico semanal de un ingrediente en una sucursal.",
        "parameters": {
            "type": "object",
            "properties": {
                "sucursal": {"type": "string"},
                "ingrediente": {"type": "string"},
            },
            "required": ["sucursal", "ingrediente"],
        },
    },
    {
        "name": "get_inventory",
        "description": "Obtiene inventario actual por sucursal, opcionalmente filtrado por ingrediente.",
        "parameters": {
            "type": "object",
            "properties": {
                "sucursal": {"type": "string"},
                "ingrediente": {"type": "string"},
            },
            "required": ["sucursal"],
        },
    },
    {
        "name": "get_current_order",
        "description": "Obtiene la orden de compra actual de una sucursal, en formatos y unidad base.",
        "parameters": {
            "type": "object",
            "properties": {"sucursal": {"type": "string"}},
            "required": ["sucursal"],
        },
    },
    {
        "name": "get_projection",
        "description": "Calcula la proyeccion de consumo de proxima semana para una sucursal e ingrediente.",
        "parameters": {
            "type": "object",
            "properties": {
                "sucursal": {"type": "string"},
                "ingrediente": {"type": "string"},
            },
            "required": ["sucursal", "ingrediente"],
        },
    },
    {
        "name": "get_health_scores",
        "description": "Obtiene el health score actual de todas las sucursales.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_anomalies",
        "description": "Obtiene ordenes raras comparando sucursales entre si; puede filtrarse por ingrediente.",
        "parameters": {
            "type": "object",
            "properties": {"ingrediente": {"type": "string"}},
        },
    },
    {
        "name": "get_orders_by_provider",
        "description": "Obtiene el pedido corregido agrupado por proveedor; puede filtrarse por proveedor.",
        "parameters": {
            "type": "object",
            "properties": {"proveedor": {"type": "string"}},
        },
    },
    {
        "name": "list_ingredients",
        "description": "Lista ingredientes del catalogo, filtrables por proveedor o perecedero.",
        "parameters": {
            "type": "object",
            "properties": {
                "proveedor": {"type": "string"},
                "es_perecedero": {"type": "boolean"},
            },
        },
    },
    {
        "name": "list_sucursales",
        "description": "Lista las sucursales disponibles e incluye resumen de consumo historico y valor estimado de la orden actual por sucursal. Usala para preguntas como cual sucursal gasta, consume o pide mas.",
        "parameters": {"type": "object", "properties": {}},
    },
]


def _normalize(value: object) -> str:
    text = normalize("NFKD", str(value).strip().lower()).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def _supplier_map(db: Session) -> dict[int, str]:
    return {supplier.id: supplier.name for supplier in db.scalars(select(Supplier)).all()}


def _ingredient_payload(ingredient: Ingredient, suppliers: dict[int, str]) -> dict[str, Any]:
    return {
        "ingrediente_id": ingredient.external_id,
        "nombre": ingredient.name,
        "proveedor": suppliers.get(ingredient.supplier_id or 0, "Sin proveedor"),
        "unidad_base": ingredient.base_unit,
        "formato_compra": ingredient.purchase_format,
        "unidad_base_por_formato": ingredient.conversion_factor,
        "es_perecedero": ingredient.is_perishable,
        "costo_unitario_estimado": ingredient.estimated_unit_cost,
    }


def _find_branch(db: Session, sucursal: str) -> str | None:
    target = _normalize(sucursal)
    branches = get_branches(db)
    exact = [branch for branch in branches if _normalize(branch) == target]
    if exact:
        return exact[0]
    contains = [branch for branch in branches if target in _normalize(branch) or _normalize(branch) in target]
    return contains[0] if len(contains) == 1 else None


def _find_ingredient(db: Session, ingrediente: str) -> Ingredient | None:
    target = _normalize(ingrediente)
    ingredients = db.scalars(select(Ingredient)).all()
    exact = [
        ingredient
        for ingredient in ingredients
        if _normalize(ingredient.external_id) == target or _normalize(ingredient.name) == target
    ]
    if exact:
        return exact[0]
    contains = [
        ingredient
        for ingredient in ingredients
        if target in _normalize(ingredient.name) or target in _normalize(ingredient.external_id)
    ]
    return contains[0] if len(contains) == 1 else None


def _ingredient_not_found(value: str) -> dict[str, str]:
    return {"error": f"No encontre el ingrediente '{value}' en el catalogo de Barrio Pizza."}


def _branch_not_found(value: str) -> dict[str, str]:
    return {"error": f"No encontre la sucursal '{value}' en los datos de Barrio Pizza."}


def get_alerts(db: Session, sucursal: str | None = None, tipo: str | None = None, severidad: str | None = None) -> dict[str, Any]:
    alerts = get_live_alerts(db)
    if sucursal:
        branch = _find_branch(db, sucursal)
        if branch is None:
            return _branch_not_found(sucursal)
        alerts = [alert for alert in alerts if alert["sucursal"] == branch]
    if tipo:
        alerts = [alert for alert in alerts if alert["tipo"] == tipo]
    if severidad:
        alerts = [alert for alert in alerts if alert["severidad"] == severidad]
    return {"total": len(alerts), "alertas": alerts[:30]}


def get_consumption_history(db: Session, sucursal: str, ingrediente: str) -> dict[str, Any]:
    branch = _find_branch(db, sucursal)
    if branch is None:
        return _branch_not_found(sucursal)
    ingredient = _find_ingredient(db, ingrediente)
    if ingredient is None:
        return _ingredient_not_found(ingrediente)
    rows = db.scalars(
        select(Consumption).where(Consumption.branch == branch, Consumption.ingredient_id == ingredient.id)
    ).all()
    if not rows:
        return {"error": f"No hay datos de consumo para '{ingredient.name}' en {branch}."}
    history = sorted(
        [{"semana": row.week, "consumo": row.quantity_base_unit, "unidad": ingredient.base_unit} for row in rows],
        key=lambda row: row["semana"],
    )
    return {
        "sucursal": branch,
        "ingrediente": ingredient.name,
        "unidad": ingredient.base_unit,
        "total": round(sum(float(row["consumo"]) for row in history), 2),
        "historial": history,
    }


def get_inventory(db: Session, sucursal: str, ingrediente: str | None = None) -> dict[str, Any]:
    branch = _find_branch(db, sucursal)
    if branch is None:
        return _branch_not_found(sucursal)
    suppliers = _supplier_map(db)
    query = select(Inventory).where(Inventory.branch == branch)
    ingredient = None
    if ingrediente:
        ingredient = _find_ingredient(db, ingrediente)
        if ingredient is None:
            return _ingredient_not_found(ingrediente)
        query = query.where(Inventory.ingredient_id == ingredient.id)
    rows = db.scalars(query).all()
    if not rows:
        label = f" de '{ingredient.name}'" if ingredient else ""
        return {"error": f"No hay inventario{label} para {branch}."}
    ingredients = {item.id: item for item in db.scalars(select(Ingredient)).all()}
    items = [
        {
            **_ingredient_payload(ingredients[row.ingredient_id], suppliers),
            "sucursal": branch,
            "stock_actual_unidad_base": row.quantity_base_unit,
        }
        for row in rows[:80]
        if row.ingredient_id in ingredients
    ]
    return {"sucursal": branch, "total_items": len(rows), "inventario": items}


def get_current_order(db: Session, sucursal: str) -> dict[str, Any]:
    branch = _find_branch(db, sucursal)
    if branch is None:
        return _branch_not_found(sucursal)
    suppliers = _supplier_map(db)
    rows = db.scalars(select(PurchaseOrder).where(PurchaseOrder.branch == branch)).all()
    if not rows:
        return {"error": f"No hay orden de compra actual para {branch}."}
    ingredients = {item.id: item for item in db.scalars(select(Ingredient)).all()}
    items = []
    valor_estimado_total = 0.0
    for row in rows[:100]:
        ingredient = ingredients.get(row.ingredient_id)
        if ingredient is None:
            continue
        payload = _ingredient_payload(ingredient, suppliers)
        cantidad_unidad_base = round(formato_a_unidad_base(row.quantity_formats, ingredient.conversion_factor), 2)
        valor_estimado = round(cantidad_unidad_base * float(ingredient.estimated_unit_cost or 0), 2)
        valor_estimado_total += valor_estimado
        items.append(
            {
                **payload,
                "sucursal": branch,
                "cantidad_formatos": row.quantity_formats,
                "cantidad_unidad_base": cantidad_unidad_base,
                "valor_estimado": valor_estimado,
            }
        )
    return {"sucursal": branch, "total_items": len(rows), "valor_estimado_total": round(valor_estimado_total, 2), "orden": items}


def get_projection(db: Session, sucursal: str, ingrediente: str) -> dict[str, Any]:
    history = get_consumption_history(db, sucursal, ingrediente)
    if "error" in history:
        return history
    projection = project_consumption([{"week": row["semana"], "value": row["consumo"]} for row in history["historial"]])
    return {
        "sucursal": history["sucursal"],
        "ingrediente": history["ingrediente"],
        "unidad": history["unidad"],
        "consumo_proyectado": projection.projected_consumption,
        "tendencia": projection.trend,
        "confianza": projection.confidence,
        "semanas_usadas": projection.weeks_used,
        "historial": history["historial"],
    }


def get_health_scores(db: Session) -> dict[str, Any]:
    alerts = get_live_alerts(db)
    scores = health_scores_by_branch(alerts, branches=get_branches(db))
    worst = min(scores.items(), key=lambda item: item[1]) if scores else None
    return {"health_scores": scores, "sucursal_peor_score": worst[0] if worst else None, "peor_score": worst[1] if worst else None}


def get_anomalies(db: Session, ingrediente: str | None = None) -> dict[str, Any]:
    data = get_procurement_data(db)
    anomalies = detect_cross_branch_anomalies(data["ingredients"], data["purchase_orders"])
    if ingrediente:
        ingredient = _find_ingredient(db, ingrediente)
        if ingredient is None:
            return _ingredient_not_found(ingrediente)
        anomalies = [item for item in anomalies if item["ingrediente_id"] == ingredient.external_id]
    return {"total": len(anomalies), "anomalias": anomalies[:30]}


def get_orders_by_provider(db: Session, proveedor: str | None = None) -> dict[str, Any]:
    data = get_procurement_data(db)
    groups = build_corrected_orders_by_provider(data["ingredients"], data["consumption"], data["inventory"])
    if proveedor:
        target = _normalize(proveedor)
        groups = [group for group in groups if target in _normalize(group["proveedor"])]
        if not groups:
            return {"error": f"No encontre pedido corregido para el proveedor '{proveedor}'."}
    return {"total_proveedores": len(groups), "proveedores": groups[:20]}


def list_ingredients(db: Session, proveedor: str | None = None, es_perecedero: bool | None = None) -> dict[str, Any]:
    suppliers = _supplier_map(db)
    ingredients = db.scalars(select(Ingredient)).all()
    rows = [_ingredient_payload(ingredient, suppliers) for ingredient in ingredients]
    if proveedor:
        target = _normalize(proveedor)
        rows = [row for row in rows if target in _normalize(row["proveedor"])]
    if es_perecedero is not None:
        rows = [row for row in rows if bool(row["es_perecedero"]) is bool(es_perecedero)]
    return {"total": len(rows), "ingredientes": rows[:80], "limitado": len(rows) > 80}


def list_sucursales(db: Session) -> dict[str, Any]:
    branches = get_branches(db)
    ingredients = {item.id: item for item in db.scalars(select(Ingredient)).all()}
    consumption_totals = {branch: 0.0 for branch in branches}
    order_values = {branch: 0.0 for branch in branches}

    for row in db.scalars(select(Consumption)).all():
        if row.branch in consumption_totals:
            consumption_totals[row.branch] += float(row.quantity_base_unit)

    for row in db.scalars(select(PurchaseOrder)).all():
        ingredient = ingredients.get(row.ingredient_id)
        if ingredient is None or row.branch not in order_values:
            continue
        quantity_base = formato_a_unidad_base(row.quantity_formats, ingredient.conversion_factor)
        order_values[row.branch] += quantity_base * float(ingredient.estimated_unit_cost or 0)

    resumen = [
        {
            "sucursal": branch,
            "consumo_total_6_semanas_unidad_base_mixta": round(consumption_totals[branch], 2),
            "valor_estimado_orden_actual": round(order_values[branch], 2),
        }
        for branch in branches
    ]
    return {"total": len(branches), "sucursales": branches, "resumen_por_sucursal": resumen}


TOOL_EXECUTORS = {
    "get_alerts": get_alerts,
    "get_consumption_history": get_consumption_history,
    "get_inventory": get_inventory,
    "get_current_order": get_current_order,
    "get_projection": get_projection,
    "get_health_scores": get_health_scores,
    "get_anomalies": get_anomalies,
    "get_orders_by_provider": get_orders_by_provider,
    "list_ingredients": list_ingredients,
    "list_sucursales": list_sucursales,
}


def execute_tool(db: Session, name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    executor = TOOL_EXECUTORS.get(name)
    if executor is None:
        return {"error": f"Herramienta no soportada: {name}"}
    try:
        return executor(db, **(arguments or {}))
    except TypeError as exc:
        return {"error": f"Parametros invalidos para {name}: {exc}"}
