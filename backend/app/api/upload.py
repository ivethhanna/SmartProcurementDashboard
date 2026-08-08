from datetime import UTC, datetime
from io import StringIO
from typing import Any
from unicodedata import normalize

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.seed import validate_columns, reset_database_to_sample_data
from app.database.upsert_helper import upsert_by_unique_key
from app.models.consumption import Consumption
from app.models.ingredient import Ingredient
from app.models.inventory import Inventory
from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier

router = APIRouter(prefix="/api/data", tags=["data"])


DATASET_MODELS = {
    "ingredients": Ingredient,
    "inventory": Inventory,
    "consumption": Consumption,
    "purchase_orders": PurchaseOrder,
    "suppliers": Supplier,
}

UPLOAD_DATASETS = {"ingredients", "inventory", "consumption", "purchase_orders"}
MAX_UPLOAD_BYTES = 1_000_000
DEFAULT_BRANCHES = {"Brisas del Golf", "Costa del Este", "Marbella", "Via Argentina"}


def _model_for_dataset(dataset: str):
    model = DATASET_MODELS.get(dataset)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Dataset no soportado: {dataset}")
    return model


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {
        column.name: getattr(row, column.name)
        for column in row.__table__.columns
    }

def _parse_bool(value: Any) -> bool:
    normalized = normalize("NFKD", str(value).strip().lower()).encode("ascii", "ignore").decode("ascii")
    return normalized in {"si", "true", "1", "yes", "y"}


def _known_branches(db: Session) -> set[str]:
    branches = set(DEFAULT_BRANCHES)
    branches.update(str(value) for value in db.scalars(select(Consumption.branch)).all())
    branches.update(str(value) for value in db.scalars(select(Inventory.branch)).all())
    branches.update(str(value) for value in db.scalars(select(PurchaseOrder.branch)).all())
    return branches


def _validate_branch(db: Session, value: Any) -> str:
    branch = str(value).strip()
    if branch not in _known_branches(db):
        raise HTTPException(status_code=422, detail=f"sucursal no existe: {branch}")
    return branch


def _ingredient_by_external_id(db: Session) -> dict[str, Ingredient]:
    return {
        ingredient.external_id: ingredient
        for ingredient in db.scalars(select(Ingredient)).all()
    }


def _supplier_by_name(db: Session) -> dict[str, Supplier]:
    return {
        supplier.name: supplier
        for supplier in db.scalars(select(Supplier)).all()
    }


def _get_or_create_supplier(db: Session, name: str) -> Supplier:
    clean_name = name.strip()
    suppliers = _supplier_by_name(db)
    supplier = suppliers.get(clean_name)
    if supplier is not None:
        return supplier
    supplier = Supplier(name=clean_name, updated_at=datetime.now(UTC))
    db.add(supplier)
    db.flush()
    return supplier


def _require_columns(payload: dict[str, Any], required: set[str]) -> None:
    missing = required.difference(payload.keys())
    if missing:
        raise HTTPException(status_code=422, detail=f"Campos faltantes: {', '.join(sorted(missing))}")


def _payload_value(payload: dict[str, Any], keys: tuple[str, ...], field: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    raise HTTPException(status_code=422, detail=f"Campos faltantes: {field}")


def _coerce_non_negative_float(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{field} debe ser numerico") from exc
    if number < 0:
        raise HTTPException(status_code=422, detail=f"{field} no puede ser negativo")
    return number


def _coerce_positive_float(value: Any, field: str) -> float:
    number = _coerce_non_negative_float(value, field)
    if number <= 0:
        raise HTTPException(status_code=422, detail=f"{field} debe ser mayor que cero")
    return number


def _create_ingredient(db: Session, payload: dict[str, Any]) -> Ingredient:
    _require_columns(
        payload,
        {
            "ingrediente_id",
            "nombre",
            "proveedor",
            "unidad_base",
            "formato_compra",
            "unidad_base_por_formato",
            "es_perecedero",
        },
    )
    supplier = _get_or_create_supplier(db, str(payload["proveedor"]))
    return Ingredient(
        external_id=str(payload["ingrediente_id"]).strip(),
        name=str(payload["nombre"]).strip(),
        supplier_id=supplier.id,
        base_unit=str(payload["unidad_base"]).strip(),
        purchase_format=str(payload["formato_compra"]).strip(),
        conversion_factor=_coerce_positive_float(payload["unidad_base_por_formato"], "unidad_base_por_formato"),
        is_perishable=_parse_bool(payload["es_perecedero"]),
        estimated_unit_cost=_coerce_non_negative_float(payload.get("costo_unitario_estimado", 2.5), "costo_unitario_estimado"),
        updated_at=datetime.now(UTC),
    )


def _resolve_ingredient_id(db: Session, external_id: Any) -> int:
    value = str(external_id).strip()
    ingredient = _ingredient_by_external_id(db).get(value)
    if ingredient is not None:
        return ingredient.id
    try:
        ingredient_id = int(value)
    except (TypeError, ValueError):
        ingredient_id = 0
    if ingredient_id and db.get(Ingredient, ingredient_id) is not None:
        return ingredient_id
    raise HTTPException(status_code=422, detail=f"ingrediente_id no existe: {external_id}")


def _create_consumption(db: Session, payload: dict[str, Any]) -> Consumption:
    branch = _payload_value(payload, ("sucursal", "branch"), "sucursal")
    ingredient_id = _payload_value(payload, ("ingrediente_id", "ingredient_id"), "ingrediente_id")
    week = _payload_value(payload, ("semana", "week"), "semana")
    quantity = _payload_value(
        payload,
        ("consumo_unidad_base", "quantity_base_unit", "quantity_consumed"),
        "consumo_unidad_base",
    )
    return Consumption(
        branch=_validate_branch(db, branch),
        ingredient_id=_resolve_ingredient_id(db, ingredient_id),
        week=str(week).strip(),
        quantity_base_unit=_coerce_non_negative_float(quantity, "consumo_unidad_base"),
        updated_at=datetime.now(UTC),
    )


def _create_inventory(db: Session, payload: dict[str, Any]) -> Inventory:
    branch = _payload_value(payload, ("sucursal", "branch"), "sucursal")
    ingredient_id = _payload_value(payload, ("ingrediente_id", "ingredient_id"), "ingrediente_id")
    quantity = _payload_value(payload, ("stock_actual_unidad_base", "quantity_base_unit"), "stock_actual_unidad_base")
    return Inventory(
        branch=_validate_branch(db, branch),
        ingredient_id=_resolve_ingredient_id(db, ingredient_id),
        quantity_base_unit=_coerce_non_negative_float(quantity, "stock_actual_unidad_base"),
        updated_at=datetime.now(UTC),
    )


def _create_purchase_order(db: Session, payload: dict[str, Any]) -> PurchaseOrder:
    branch = _payload_value(payload, ("sucursal", "branch"), "sucursal")
    ingredient_id = _payload_value(payload, ("ingrediente_id", "ingredient_id"), "ingrediente_id")
    quantity = _payload_value(payload, ("cantidad_formatos", "quantity_formats"), "cantidad_formatos")
    return PurchaseOrder(
        branch=_validate_branch(db, branch),
        ingredient_id=_resolve_ingredient_id(db, ingredient_id),
        quantity_formats=_coerce_non_negative_float(quantity, "cantidad_formatos"),
        updated_at=datetime.now(UTC),
    )


ROW_CREATORS = {
    "ingredients": _create_ingredient,
    "consumption": _create_consumption,
    "inventory": _create_inventory,
    "purchase_orders": _create_purchase_order,
}

UPSERT_UNIQUE_KEYS = {
    "ingredients": ("external_id",),
    "consumption": ("branch", "ingredient_id", "week"),
    "inventory": ("branch", "ingredient_id"),
    "purchase_orders": ("branch", "ingredient_id"),
}


@router.post("/reset")
def reset_data(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        reset_database_to_sample_data(db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "reset"}


def _clear_upload_dataset(db: Session, dataset: str) -> None:
    if dataset == "ingredients":
        db.execute(delete(PurchaseOrder))
        db.execute(delete(Inventory))
        db.execute(delete(Consumption))
        db.execute(delete(Ingredient))
        db.execute(delete(Supplier))
    else:
        db.execute(delete(_model_for_dataset(dataset)))


def _replace_dataset_rows(db: Session, dataset: str, rows: list[dict[str, Any]]) -> None:
    creator = ROW_CREATORS[dataset]
    _clear_upload_dataset(db, dataset)
    db.flush()
    for row in rows:
        db.add(creator(db, row))
    db.commit()


@router.get("/reference")
def get_reference_data(db: Session = Depends(get_db)) -> dict[str, Any]:
    suppliers = {supplier.id: supplier.name for supplier in db.scalars(select(Supplier)).all()}
    ingredients = db.scalars(select(Ingredient)).all()
    purchase_formats = sorted({ingredient.purchase_format for ingredient in ingredients if ingredient.purchase_format})
    format_types = sorted({str(value).split()[0] for value in purchase_formats if str(value).strip()})
    units = sorted({ingredient.base_unit for ingredient in ingredients if ingredient.base_unit})
    weeks = sorted({row.week for row in db.scalars(select(Consumption)).all()})
    return {
        "sucursales": sorted(_known_branches(db)),
        "ingredientes": [
            {
                "id": ingredient.id,
                "ingrediente_id": ingredient.external_id,
                "nombre": ingredient.name,
                "proveedor": suppliers.get(ingredient.supplier_id or 0, "Sin proveedor"),
                "unidad_base": ingredient.base_unit,
            }
            for ingredient in sorted(ingredients, key=lambda item: item.name)
        ],
        "proveedores": [
            {"id": supplier.id, "nombre": supplier.name}
            for supplier in sorted(db.scalars(select(Supplier)).all(), key=lambda item: item.name)
        ],
        "unidades": units,
        "semanas": weeks,
        "tipos_formato": format_types,
        "formatos_compra": purchase_formats,
    }


@router.get("/{dataset}")
def get_dataset(dataset: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    model = _model_for_dataset(dataset)
    rows = db.scalars(select(model)).all()
    return [_row_to_dict(row) for row in rows]


@router.post("/{dataset}")
def create_dataset_row(
    dataset: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if dataset not in ROW_CREATORS:
        raise HTTPException(status_code=404, detail=f"Dataset no soportado: {dataset}")
    try:
        row = ROW_CREATORS[dataset](db, payload)
        if dataset in UPSERT_UNIQUE_KEYS:
            row_data = _row_to_dict(row)
            row_data.pop("id", None)
            unique_fields = UPSERT_UNIQUE_KEYS[dataset]
            unique_filters = {field: row_data.pop(field) for field in unique_fields}
            row, was_created = upsert_by_unique_key(db, type(row), unique_filters, row_data)
            db.refresh(row)
            return {**_row_to_dict(row), "status": "created" if was_created else "updated"}

        db.add(row)
        db.commit()
        db.refresh(row)
        return {**_row_to_dict(row), "status": "created"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/{dataset}/{row_id}")
def update_dataset_row(
    dataset: str,
    row_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    model = _model_for_dataset(dataset)
    row = db.get(model, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Fila no encontrada")

    try:
        for field, value in payload.items():
            if not hasattr(row, field) or field == "id":
                continue
            if field == "branch":
                value = _validate_branch(db, value)
            if field == "ingredient_id":
                try:
                    ingredient_id = int(value)
                except (TypeError, ValueError) as exc:
                    raise HTTPException(status_code=422, detail=f"ingredient_id invalido: {value}") from exc
                if db.get(Ingredient, ingredient_id) is None:
                    raise HTTPException(status_code=422, detail=f"ingredient_id no existe: {value}")
                value = ingredient_id
            if isinstance(row, Ingredient) and field == "supplier_id":
                try:
                    supplier_id = int(value)
                except (TypeError, ValueError) as exc:
                    raise HTTPException(status_code=422, detail=f"supplier_id invalido: {value}") from exc
                if db.get(Supplier, supplier_id) is None:
                    raise HTTPException(status_code=422, detail=f"supplier_id no existe: {value}")
                value = supplier_id
            if field in {"quantity_base_unit", "quantity_formats", "conversion_factor", "estimated_unit_cost"}:
                value = _coerce_non_negative_float(value, field)
            if field == "is_perishable":
                value = _parse_bool(value)
            setattr(row, field, value)
        row.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(row)
        return _row_to_dict(row)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{dataset}")
def clear_dataset(dataset: str, db: Session = Depends(get_db)) -> dict[str, str]:
    model = _model_for_dataset(dataset)
    db.execute(delete(model))
    db.commit()
    return {"status": "deleted"}


@router.delete("/{dataset}/{row_id}")
def delete_dataset_row(dataset: str, row_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    model = _model_for_dataset(dataset)
    row = db.get(model, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Fila no encontrada")
    if isinstance(row, Ingredient):
        has_related = any(
            db.scalar(select(related.id).where(related.ingredient_id == row.id).limit(1)) is not None
            for related in (Consumption, Inventory, PurchaseOrder)
        )
        if has_related:
            raise HTTPException(
                status_code=422,
                detail="No se puede eliminar un ingrediente con consumo, inventario u ordenes relacionadas.",
            )
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


@router.post("/{dataset}/upload")
async def upload_dataset_csv(
    dataset: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if dataset not in UPLOAD_DATASETS:
        raise HTTPException(status_code=404, detail=f"Dataset no soportado: {dataset}")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="El archivo debe ser CSV")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="El archivo supera el limite de 1 MB")

    try:
        text = content.decode("utf-8-sig")
        df = pd.read_csv(StringIO(text))
        validate_columns(dataset, df)
        _replace_dataset_rows(db, dataset, df.to_dict(orient="records"))
    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"CSV invalido: {exc}") from exc

    return {"status": "uploaded", "dataset": dataset, "rows": len(df)}
