from fastapi.testclient import TestClient

from app.database.database import Base, SessionLocal, engine
from app.database.seed import reset_database_to_sample_data
from app.main import app


def setup_function() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        reset_database_to_sample_data(db)
    finally:
        db.close()


def test_chat_endpoint_returns_fallback_without_api_key() -> None:
    client = TestClient(app)

    response = client.post("/api/chat", json={"pregunta": "Que reviso primero?"})

    assert response.status_code == 200
    body = response.json()
    assert body["respuesta"]
    assert body["ai_configurada"] is False


def test_summary_ai_returns_text_without_api_key() -> None:
    client = TestClient(app)

    response = client.post("/api/summary-ai", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]
    assert body["ai_configurada"] is False
