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


def test_alerts_endpoint_returns_live_alerts() -> None:
    client = TestClient(app)

    response = client.get("/api/alerts")

    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 1
    assert alerts[0]["mensaje"].startswith("ALERTA:")
    assert "explicacion" in alerts[0]


def test_alerts_endpoint_filters_by_severity() -> None:
    client = TestClient(app)

    response = client.get("/api/alerts", params={"severidad": "alta"})

    assert response.status_code == 200
    assert all(alert["severidad"] == "alta" for alert in response.json())


def test_summary_endpoint_returns_kpis() -> None:
    client = TestClient(app)

    response = client.get("/api/summary")

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_alertas"] >= 1
    assert summary["dinero_en_riesgo_total"] > 0
    assert summary["sucursal_mas_critica"] is not None
    assert summary["health_scores"]
