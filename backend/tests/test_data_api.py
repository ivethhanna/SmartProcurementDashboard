from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database.database import Base, SessionLocal, engine
from app.database.seed import reset_database_to_sample_data
from app.main import app


ROOT = Path(__file__).resolve().parents[1]


def setup_function() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        reset_database_to_sample_data(db)
    finally:
        db.close()


def test_upload_inventory_csv_replaces_dataset() -> None:
    client = TestClient(app)
    csv_bytes = (ROOT / "sample_data" / "inventario_actual.csv").read_bytes()

    response = client.post(
        "/api/data/inventory/upload",
        files={"file": ("inventario_actual.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["rows"] == 88
    inventory = client.get("/api/data/inventory").json()
    assert len(inventory) == 88


def test_upload_rejects_missing_columns() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/data/inventory/upload",
        files={"file": ("bad.csv", b"sucursal,ingrediente_id\nCosta,harina\n", "text/csv")},
    )

    assert response.status_code == 422
    assert "Columnas faltantes" in response.json()["detail"]


def test_create_manual_purchase_order_row() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/data/purchase_orders",
        json={"sucursal": "Brisas del Golf", "ingrediente_id": "mozzarella", "cantidad_formatos": 2},
    )

    assert response.status_code == 200
    assert response.json()["branch"] == "Brisas del Golf"
    assert response.json()["quantity_formats"] == 2


@pytest.mark.parametrize(
    ("dataset", "payload_1", "payload_2", "quantity_field"),
    [
        (
            "inventory",
            {"branch": "Via Argentina", "ingredient_id": 11, "quantity_base_unit": 500.0},
            {"branch": "Via Argentina", "ingredient_id": 11, "quantity_base_unit": 300.0},
            "quantity_base_unit",
        ),
        (
            "purchase_orders",
            {"branch": "Costa del Este", "ingredient_id": 20, "quantity_formats": 33.0},
            {"branch": "Costa del Este", "ingredient_id": 20, "quantity_formats": 10.0},
            "quantity_formats",
        ),
        (
            "consumption",
            {"branch": "Via Argentina", "ingredient_id": 11, "week": "S1", "quantity_base_unit": 80.0},
            {"branch": "Via Argentina", "ingredient_id": 11, "week": "S1", "quantity_base_unit": 95.0},
            "quantity_base_unit",
        ),
    ],
)
def test_create_duplicate_composite_key_updates_without_500(
    dataset: str,
    payload_1: dict[str, object],
    payload_2: dict[str, object],
    quantity_field: str,
) -> None:
    client = TestClient(app)

    response_1 = client.post(f"/api/data/{dataset}", json=payload_1)
    response_2 = client.post(f"/api/data/{dataset}", json=payload_2)

    assert response_1.status_code == 200
    assert response_1.json()["status"] == "updated"
    assert response_2.status_code != 500, (
        f"Duplicate entry in {dataset} still crashes with an unhandled 500 error"
    )
    assert response_2.status_code == 200
    assert response_2.json()["status"] == "updated"
    assert response_2.json()[quantity_field] == payload_2[quantity_field]


def test_reference_data_returns_selector_values() -> None:
    client = TestClient(app)

    response = client.get("/api/data/reference")

    assert response.status_code == 200
    body = response.json()
    assert "Via Argentina" in body["sucursales"]
    assert any(item["ingrediente_id"] == "pepperoni" for item in body["ingredientes"])
    assert any(item["nombre"] == "Distrib. Bella Italia" for item in body["proveedores"])
    assert "kg" in body["unidades"]


def test_create_rejects_unknown_branch() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/data/purchase_orders",
        json={"sucursal": "Sucursal inventada", "ingrediente_id": "harina", "cantidad_formatos": 2},
    )

    assert response.status_code == 422
    assert "sucursal no existe" in response.json()["detail"]


def test_create_rejects_unknown_ingredient() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/data/inventory",
        json={"sucursal": "Brisas del Golf", "ingrediente_id": "ingrediente_inventado", "stock_actual_unidad_base": 2},
    )

    assert response.status_code == 422
    assert "ingrediente_id no existe" in response.json()["detail"]


def test_create_ingredient_rejects_zero_conversion_factor() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/data/ingredients",
        json={
            "ingrediente_id": "qa_factor_cero",
            "nombre": "QA Factor Cero",
            "proveedor": "QA",
            "unidad_base": "kg",
            "formato_compra": "Saco 0 kg",
            "unidad_base_por_formato": 0,
            "es_perecedero": "No",
            "costo_unitario_estimado": 1,
        },
    )

    assert response.status_code == 422
    assert "unidad_base_por_formato debe ser mayor que cero" in response.json()["detail"]


def test_create_ingredient_accepts_si_with_accent_as_perishable() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/data/ingredients",
        json={
            "ingrediente_id": "qa_perecedero",
            "nombre": "QA Perecedero",
            "proveedor": "QA",
            "unidad_base": "kg",
            "formato_compra": "Caja 1 kg",
            "unidad_base_por_formato": 1,
            "es_perecedero": "sí",
            "costo_unitario_estimado": 1,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_perishable"] is True


def test_update_purchase_order_row_persists() -> None:
    client = TestClient(app)
    row = client.post(
        "/api/data/purchase_orders",
        json={"sucursal": "Brisas del Golf", "ingrediente_id": "mozzarella", "cantidad_formatos": 2},
    ).json()

    response = client.put(
        f"/api/data/purchase_orders/{row['id']}",
        json={"quantity_formats": 4},
    )

    assert response.status_code == 200
    assert response.json()["quantity_formats"] == 4


def test_delete_row_requires_existing_row_and_blocks_related_ingredient() -> None:
    client = TestClient(app)

    blocked = client.delete("/api/data/ingredients/1")
    missing = client.delete("/api/data/purchase_orders/999999")

    assert blocked.status_code == 422
    assert "No se puede eliminar un ingrediente" in blocked.json()["detail"]
    assert missing.status_code == 404


def test_reset_data_does_not_require_body() -> None:
    client = TestClient(app)

    response = client.post("/api/data/reset")

    assert response.status_code == 200
    assert response.json() == {"status": "reset"}
