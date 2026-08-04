from pathlib import Path

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
        json={"sucursal": "Nueva", "ingrediente_id": "harina", "cantidad_formatos": 2},
    )

    assert response.status_code == 200
    assert response.json()["branch"] == "Nueva"
    assert response.json()["quantity_formats"] == 2

