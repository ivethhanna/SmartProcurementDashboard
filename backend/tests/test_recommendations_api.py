from fastapi.testclient import TestClient

from app.database.database import Base, SessionLocal, engine
from app.database.seed import reset_database_to_sample_data
from app.main import app
from app.services.exports.exports import EXPORT_DIR
from app.services.forecasting.anomaly_detection import detect_cross_branch_anomalies
from app.services.procurement.supplier_grouping import build_corrected_orders_by_provider


def setup_function() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        reset_database_to_sample_data(db)
    finally:
        db.close()


def test_detect_cross_branch_anomaly() -> None:
    anomalies = detect_cross_branch_anomalies(
        [{"ingrediente_id": "harina", "nombre": "Harina", "unidad_base": "kg", "unidad_base_por_formato": 25}],
        [
            {"sucursal": "A", "ingrediente_id": "harina", "cantidad_formatos": 10},
            {"sucursal": "B", "ingrediente_id": "harina", "cantidad_formatos": 10},
            {"sucursal": "C", "ingrediente_id": "harina", "cantidad_formatos": 10},
            {"sucursal": "D", "ingrediente_id": "harina", "cantidad_formatos": 30},
        ],
    )

    assert anomalies[0]["sucursal"] == "D"
    assert anomalies[0]["tipo"] == "alta"


def test_supplier_grouping_builds_corrected_orders() -> None:
    groups = build_corrected_orders_by_provider(
        [
            {
                "ingrediente_id": "harina",
                "nombre": "Harina",
                "proveedor": "Molinos",
                "unidad_base": "kg",
                "formato_compra": "Saco 25 kg",
                "unidad_base_por_formato": 25,
            }
        ],
        [
            {"sucursal": "A", "ingrediente_id": "harina", "semana": "S1", "consumo_unidad_base": 100},
            {"sucursal": "A", "ingrediente_id": "harina", "semana": "S2", "consumo_unidad_base": 100},
            {"sucursal": "A", "ingrediente_id": "harina", "semana": "S3", "consumo_unidad_base": 100},
            {"sucursal": "A", "ingrediente_id": "harina", "semana": "S4", "consumo_unidad_base": 100},
            {"sucursal": "A", "ingrediente_id": "harina", "semana": "S5", "consumo_unidad_base": 100},
            {"sucursal": "A", "ingrediente_id": "harina", "semana": "S6", "consumo_unidad_base": 100},
        ],
        [{"sucursal": "A", "ingrediente_id": "harina", "stock_actual_unidad_base": 10}],
    )

    assert groups[0]["proveedor"] == "Molinos"
    assert groups[0]["items"][0]["cantidad_formatos_corregida"] == 4


def test_recommendation_endpoints_and_export() -> None:
    client = TestClient(app)

    anomalies = client.get("/api/anomalies")
    health = client.get("/api/health-scores")
    providers = client.get("/api/orders-by-provider")
    export = client.get("/api/export/pedido-corregido")

    assert anomalies.status_code == 200
    assert health.status_code == 200
    assert providers.status_code == 200
    assert len(providers.json()) >= 1
    assert export.status_code == 200
    assert export.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert EXPORT_DIR.exists()


def test_orders_by_provider_reflects_new_supplier_from_manual_entries() -> None:
    client = TestClient(app)

    ingredient = client.post(
        "/api/data/ingredients",
        json={
            "ingrediente_id": "qa_proveedor_nuevo",
            "nombre": "QA Proveedor Nuevo",
            "proveedor": "Proveedor QA Nuevo",
            "unidad_base": "kg",
            "formato_compra": "Caja 1 kg",
            "unidad_base_por_formato": 1,
            "es_perecedero": "No",
            "costo_unitario_estimado": 1,
        },
    )
    assert ingredient.status_code == 200

    for week in range(1, 7):
        response = client.post(
            "/api/data/consumption",
            json={
                "branch": "Via Argentina",
                "ingredient_id": "qa_proveedor_nuevo",
                "week": f"S{week}",
                "quantity_base_unit": 10,
            },
        )
        assert response.status_code == 200

    inventory = client.post(
        "/api/data/inventory",
        json={
            "branch": "Via Argentina",
            "ingredient_id": "qa_proveedor_nuevo",
            "quantity_base_unit": 0,
        },
    )
    assert inventory.status_code == 200

    providers = client.get("/api/orders-by-provider")

    assert providers.status_code == 200
    groups = {group["proveedor"]: group for group in providers.json()}
    assert "Proveedor QA Nuevo" in groups
    assert groups["Proveedor QA Nuevo"]["items"][0]["ingrediente"] == "QA Proveedor Nuevo"


def test_orders_by_provider_moves_existing_ingredient_to_new_supplier() -> None:
    client = TestClient(app)

    before = client.get("/api/orders-by-provider").json()
    assert any(
        group["proveedor"] == "Molinos Central"
        and any(item["ingrediente_id"] == "harina" for item in group["items"])
        for group in before
    )

    ingredient = client.post(
        "/api/data/ingredients",
        json={
            "ingrediente_id": "harina",
            "nombre": "Harina 00",
            "proveedor": "Proveedor Harina Nuevo",
            "unidad_base": "kg",
            "formato_compra": "Saco 25 kg",
            "unidad_base_por_formato": 25,
            "es_perecedero": "No",
            "costo_unitario_estimado": 1,
        },
    )

    assert ingredient.status_code == 200
    assert ingredient.json()["status"] == "updated"

    after = client.get("/api/orders-by-provider").json()
    assert any(
        group["proveedor"] == "Proveedor Harina Nuevo"
        and any(item["ingrediente_id"] == "harina" for item in group["items"])
        for group in after
    )
