from datetime import UTC, datetime
from io import StringIO
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.seed import validate_columns, reset_database_to_sample_data
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
    return str(value).strip().lower() in {"si", "sí", "true", "1", "yes", "y"}


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


def _coerce_non_negative_float(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{field} debe ser numerico") from exc
    if number < 0:
        raise HTTPException(status_code=422, detail=f"{field} no puede ser negativo")
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
        conversion_factor=_coerce_non_negative_float(payload["unidad_base_por_formato"], "unidad_base_por_formato"),
        is_perishable=_parse_bool(payload["es_perecedero"]),
        estimated_unit_cost=_coerce_non_negative_float(payload.get("costo_unitario_estimado", 2.5), "costo_unitario_estimado"),
        updated_at=datetime.now(UTC),
    )


def _resolve_ingredient_id(db: Session, external_id: Any) -> int:
    ingredient = _ingredient_by_external_id(db).get(str(external_id).strip())
    if ingredient is None:
        raise HTTPException(status_code=422, detail=f"ingrediente_id no existe: {external_id}")
    return ingredient.id


def _create_consumption(db: Session, payload: dict[str, Any]) -> Consumption:
    _require_columns(payload, {"sucursal", "ingrediente_id", "semana", "consumo_unidad_base"})
    return Consumption(
        branch=str(payload["sucursal"]).strip(),
        ingredient_id=_resolve_ingredient_id(db, payload["ingrediente_id"]),
        week=str(payload["semana"]).strip(),
        quantity_base_unit=_coerce_non_negative_float(payload["consumo_unidad_base"], "consumo_unidad_base"),
        updated_at=datetime.now(UTC),
    )


def _create_inventory(db: Session, payload: dict[str, Any]) -> Inventory:
    _require_columns(payload, {"sucursal", "ingrediente_id", "stock_actual_unidad_base"})
    return Inventory(
        branch=str(payload["sucursal"]).strip(),
        ingredient_id=_resolve_ingredient_id(db, payload["ingrediente_id"]),
        quantity_base_unit=_coerce_non_negative_float(payload["stock_actual_unidad_base"], "stock_actual_unidad_base"),
        updated_at=datetime.now(UTC),
    )


def _create_purchase_order(db: Session, payload: dict[str, Any]) -> PurchaseOrder:
    _require_columns(payload, {"sucursal", "ingrediente_id", "cantidad_formatos"})
    return PurchaseOrder(
        branch=str(payload["sucursal"]).strip(),
        ingredient_id=_resolve_ingredient_id(db, payload["ingrediente_id"]),
        quantity_formats=_coerce_non_negative_float(payload["cantidad_formatos"], "cantidad_formatos"),
        updated_at=datetime.now(UTC),
    )


ROW_CREATORS = {
    "ingredients": _create_ingredient,
    "consumption": _create_consumption,
    "inventory": _create_inventory,
    "purchase_orders": _create_purchase_order,
}


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
        db.add(row)
        db.commit()
        db.refresh(row)
        return _row_to_dict(row)
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


@router.post("/reset")
def reset_data(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        reset_database_to_sample_data(db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "reset"}
