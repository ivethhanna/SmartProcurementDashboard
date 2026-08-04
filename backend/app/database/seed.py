from pathlib import Path
from unicodedata import normalize

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.consumption import Consumption
from app.models.ingredient import Ingredient
from app.models.inventory import Inventory
from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier


SAMPLE_DATA_DIR = Path(__file__).resolve().parents[2] / "sample_data"

EXPECTED_COLUMNS = {
    "ingredients": {
        "ingrediente_id",
        "nombre",
        "proveedor",
        "unidad_base",
        "formato_compra",
        "unidad_base_por_formato",
        "es_perecedero",
    },
    "consumption": {"sucursal", "ingrediente_id", "semana", "consumo_unidad_base"},
    "inventory": {"sucursal", "ingrediente_id", "stock_actual_unidad_base"},
    "purchase_orders": {"sucursal", "ingrediente_id", "cantidad_formatos"},
}

CSV_FILES = {
    "ingredients": "ingredientes.csv",
    "consumption": "consumo_historico.csv",
    "inventory": "inventario_actual.csv",
    "purchase_orders": "orden_compra_semana.csv",
}

DEFAULT_UNIT_COSTS = {
    "harina": 1.35,
    "harina_gf": 4.25,
    "semola": 1.8,
    "levadura": 7.5,
    "queso_mozzarella": 6.8,
    "mozzarella": 6.8,
    "salsa_tomate": 2.2,
    "tomate": 2.2,
    "pepperoni": 9.5,
    "jamon": 5.4,
    "bacon": 8.2,
    "hongos": 4.1,
    "aceite_oliva": 8.0,
}


def _read_csv(dataset: str) -> pd.DataFrame:
    path = SAMPLE_DATA_DIR / CSV_FILES[dataset]
    if not path.exists():
        raise FileNotFoundError(f"No existe el CSV requerido: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    validate_columns(dataset, df)
    return df


def validate_columns(dataset: str, df: pd.DataFrame) -> None:
    expected = EXPECTED_COLUMNS[dataset]
    missing = expected.difference(df.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"Columnas faltantes para {dataset}: {missing_columns}")


def _ingredient_for_row(
    ingredient_by_external_id: dict[str, Ingredient],
    external_id: object,
    dataset: str,
) -> Ingredient:
    ingredient_key = str(external_id).strip()
    ingredient = ingredient_by_external_id.get(ingredient_key)
    if ingredient is None:
        raise ValueError(
            f"{dataset} referencia ingrediente_id '{ingredient_key}', pero no existe en ingredientes.csv"
        )
    return ingredient


def _parse_bool(value: object) -> bool:
    normalized = normalize("NFKD", str(value).strip().lower()).encode("ascii", "ignore").decode("ascii")
    return normalized in {"si", "true", "1", "yes", "y"}


def _estimated_cost(external_id: str, name: str) -> float:
    normalized_id = external_id.strip().lower()
    normalized_name = name.strip().lower()
    if normalized_id in DEFAULT_UNIT_COSTS:
        return DEFAULT_UNIT_COSTS[normalized_id]
    for token, cost in DEFAULT_UNIT_COSTS.items():
        if token.replace("_", " ") in normalized_name:
            return cost
    return 2.5


def _row_estimated_cost(row: dict[str, object], external_id: str, name: str) -> float:
    value = row.get("costo_unitario_estimado")
    if value is not None and pd.notna(value):
        return float(value)
    return _estimated_cost(external_id, name)


def reset_database_to_sample_data(db: Session) -> None:
    db.execute(delete(PurchaseOrder))
    db.execute(delete(Inventory))
    db.execute(delete(Consumption))
    db.execute(delete(Ingredient))
    db.execute(delete(Supplier))
    db.flush()

    try:
        ingredients_df = _read_csv("ingredients")
        supplier_by_name: dict[str, Supplier] = {}

        for supplier_name in sorted(ingredients_df["proveedor"].dropna().astype(str).unique()):
            supplier = Supplier(name=supplier_name)
            db.add(supplier)
            supplier_by_name[supplier_name] = supplier
        db.flush()

        ingredient_by_external_id: dict[str, Ingredient] = {}
        for row in ingredients_df.to_dict(orient="records"):
            external_id = str(row["ingrediente_id"]).strip()
            name = str(row["nombre"]).strip()
            supplier_name = str(row["proveedor"]).strip()
            ingredient = Ingredient(
                external_id=external_id,
                name=name,
                supplier_id=supplier_by_name[supplier_name].id,
                base_unit=str(row["unidad_base"]).strip(),
                purchase_format=str(row["formato_compra"]).strip(),
                conversion_factor=float(row["unidad_base_por_formato"]),
                is_perishable=_parse_bool(row["es_perecedero"]),
                estimated_unit_cost=_row_estimated_cost(row, external_id, name),
            )
            db.add(ingredient)
            ingredient_by_external_id[external_id] = ingredient
        db.flush()

        for row in _read_csv("consumption").to_dict(orient="records"):
            ingredient = _ingredient_for_row(ingredient_by_external_id, row["ingrediente_id"], "consumo_historico.csv")
            db.add(
                Consumption(
                    branch=str(row["sucursal"]).strip(),
                    ingredient_id=ingredient.id,
                    week=str(row["semana"]).strip(),
                    quantity_base_unit=float(row["consumo_unidad_base"]),
                )
            )

        for row in _read_csv("inventory").to_dict(orient="records"):
            ingredient = _ingredient_for_row(ingredient_by_external_id, row["ingrediente_id"], "inventario_actual.csv")
            db.add(
                Inventory(
                    branch=str(row["sucursal"]).strip(),
                    ingredient_id=ingredient.id,
                    quantity_base_unit=float(row["stock_actual_unidad_base"]),
                )
            )

        for row in _read_csv("purchase_orders").to_dict(orient="records"):
            ingredient = _ingredient_for_row(ingredient_by_external_id, row["ingrediente_id"], "orden_compra_semana.csv")
            db.add(
                PurchaseOrder(
                    branch=str(row["sucursal"]).strip(),
                    ingredient_id=ingredient.id,
                    quantity_formats=float(row["cantidad_formatos"]),
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise


def seed_database_if_empty(db: Session) -> bool:
    has_ingredients = db.scalar(select(Ingredient.id).limit(1)) is not None
    if has_ingredients:
        return False
    reset_database_to_sample_data(db)
    return True
