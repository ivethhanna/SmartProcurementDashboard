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
