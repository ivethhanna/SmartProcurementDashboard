from fastapi.testclient import TestClient

from app.database.database import Base, SessionLocal, engine
from app.database.seed import reset_database_to_sample_data
from app.main import app


def setup_module() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        reset_database_to_sample_data(db)
    finally:
        db.close()


def test_alert_thresholds_can_be_updated_and_reset() -> None:
    client = TestClient(app)

    updated = client.put(
        "/api/config/alerts-thresholds",
        json={
            "porcentaje_diferencia_severidad_alta": 0.4,
            "porcentaje_diferencia_severidad_media": 0.1,
            "multiplicador_perecedero": 1.5,
        },
    )

    assert updated.status_code == 200
    assert updated.json()["porcentaje_diferencia_severidad_alta"] == 0.4

    current = client.get("/api/config/alerts-thresholds")
    assert current.status_code == 200
    assert current.json()["multiplicador_perecedero"] == 1.5

    reset = client.post("/api/config/alerts-thresholds/reset")
    assert reset.status_code == 200
    assert reset.json()["porcentaje_diferencia_severidad_alta"] == 0.5


def test_alert_thresholds_reject_invalid_order() -> None:
    client = TestClient(app)

    response = client.put(
        "/api/config/alerts-thresholds",
        json={
            "porcentaje_diferencia_severidad_alta": 0.1,
            "porcentaje_diferencia_severidad_media": 0.2,
            "multiplicador_perecedero": 1.0,
        },
    )

    assert response.status_code == 422
    assert "alta debe ser mayor" in response.json()["detail"]


def test_ai_status_endpoint_reports_local_usage_shape() -> None:
    client = TestClient(app)

    response = client.get("/api/config/ai-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["proveedor"] == "gemini"
    assert "key_configurada" in payload
    assert "llamadas_hoy" in payload
    assert "limite_diario_conocido" in payload
