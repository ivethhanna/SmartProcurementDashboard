from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consumption import Consumption
from app.models.ingredient import Ingredient
from app.models.inventory import Inventory
from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier
from app.services.alerts.alerts_engine import generate_alerts
from app.services.alerts.health_score import health_scores_by_branch


def _supplier_name_map(db: Session) -> dict[int, str]:
    return {
        supplier.id: supplier.name
        for supplier in db.scalars(select(Supplier)).all()
    }


def _ingredient_rows(db: Session) -> list[dict[str, Any]]:
    ingredients = db.scalars(select(Ingredient)).all()
    suppliers = _supplier_name_map(db)
    return [
        {
            "ingrediente_id": ingredient.external_id,
            "nombre": ingredient.name,
            "proveedor": suppliers.get(ingredient.supplier_id or 0, "Sin proveedor"),
            "unidad_base": ingredient.base_unit,
            "formato_compra": ingredient.purchase_format,
            "unidad_base_por_formato": ingredient.conversion_factor,
            "es_perecedero": ingredient.is_perishable,
            "costo_unitario_estimado": ingredient.estimated_unit_cost,
        }
        for ingredient in ingredients
    ]


def _ingredient_id_map(db: Session) -> dict[int, str]:
    return {
        ingredient.id: ingredient.external_id
        for ingredient in db.scalars(select(Ingredient)).all()
    }


def _consumption_rows(db: Session, ingredient_ids: dict[int, str]) -> list[dict[str, Any]]:
    rows = db.scalars(select(Consumption)).all()
    return [
        {
            "sucursal": row.branch,
            "ingrediente_id": ingredient_ids[row.ingredient_id],
            "semana": row.week,
            "consumo_unidad_base": row.quantity_base_unit,
        }
        for row in rows
        if row.ingredient_id in ingredient_ids
    ]


def _inventory_rows(db: Session, ingredient_ids: dict[int, str]) -> list[dict[str, Any]]:
    rows = db.scalars(select(Inventory)).all()
    return [
        {
            "sucursal": row.branch,
            "ingrediente_id": ingredient_ids[row.ingredient_id],
            "stock_actual_unidad_base": row.quantity_base_unit,
        }
        for row in rows
        if row.ingredient_id in ingredient_ids
    ]


def _order_rows(db: Session, ingredient_ids: dict[int, str]) -> list[dict[str, Any]]:
    rows = db.scalars(select(PurchaseOrder)).all()
    return [
        {
            "sucursal": row.branch,
            "ingrediente_id": ingredient_ids[row.ingredient_id],
            "cantidad_formatos": row.quantity_formats,
        }
        for row in rows
        if row.ingredient_id in ingredient_ids
    ]


def get_live_alerts(db: Session) -> list[dict[str, Any]]:
    data = get_procurement_data(db)
    return generate_alerts(
        ingredient_rows=data["ingredients"],
        consumption_rows=data["consumption"],
        inventory_rows=data["inventory"],
        order_rows=data["purchase_orders"],
    )


def get_procurement_data(db: Session) -> dict[str, list[dict[str, Any]]]:
    ingredient_ids = _ingredient_id_map(db)
    return {
        "ingredients": _ingredient_rows(db),
        "consumption": _consumption_rows(db, ingredient_ids),
        "inventory": _inventory_rows(db, ingredient_ids),
        "purchase_orders": _order_rows(db, ingredient_ids),
    }


def get_branches(db: Session) -> list[str]:
    branches = set(db.scalars(select(Consumption.branch)).all())
    branches.update(db.scalars(select(Inventory.branch)).all())
    branches.update(db.scalars(select(PurchaseOrder.branch)).all())
    return sorted(branches)


def get_last_update(db: Session) -> datetime | None:
    candidates: list[datetime] = []
    for model in (Ingredient, Consumption, Inventory, PurchaseOrder):
        value = db.scalar(select(model.updated_at).order_by(model.updated_at.desc()).limit(1))
        if value is not None:
            candidates.append(value)
    return max(candidates) if candidates else None


def get_dashboard_summary(db: Session) -> dict[str, Any]:
    alerts = get_live_alerts(db)
    branches = get_branches(db)
    health_scores = health_scores_by_branch(alerts, branches=branches)
    worst_branch = min(health_scores.items(), key=lambda item: item[1])[0] if health_scores else None
    return {
        "total_alertas": len(alerts),
        "dinero_en_riesgo_total": round(sum(float(alert["impacto_dinero"]) for alert in alerts), 2),
        "sucursal_mas_critica": worst_branch,
        "health_scores": health_scores,
        "ultima_actualizacion": get_last_update(db),
    }
