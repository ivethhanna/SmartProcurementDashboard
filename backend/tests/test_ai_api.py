from fastapi.testclient import TestClient

from app.core.config import settings
from app.database.database import Base, SessionLocal, engine
from app.database.seed import reset_database_to_sample_data
from app.main import app
from app.services.ai.ai_chat import answer_question, build_ai_context, enrich_ai_context, generate_weekly_summary
from app.services.ai.tools import execute_tool


def setup_function() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        reset_database_to_sample_data(db)
    finally:
        db.close()


def test_chat_endpoint_returns_fallback_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "")
    client = TestClient(app)

    response = client.post("/api/chat", json={"pregunta": "Que reviso primero?"})

    assert response.status_code == 200
    body = response.json()
    assert body["respuesta"]
    assert body["ai_configurada"] is False


def test_summary_ai_returns_text_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "")
    client = TestClient(app)

    response = client.post("/api/summary-ai", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]
    assert body["ai_configurada"] is False


def test_ai_context_includes_branch_status() -> None:
    context = build_ai_context(
        [
            {
                "sucursal": "Via Argentina",
                "ingrediente_id": "albahaca",
                "ingrediente": "Albahaca fresca",
                "tipo": "sobre_pedido",
                "severidad": "alta",
                "cantidad_diferencia": 4.57,
                "unidad": "kg",
                "impacto_dinero": 11.43,
                "mensaje": "ALERTA: Via Argentina está pidiendo 4.57 kg de Albahaca fresca más que lo proyectado → posible sobre-pedido.",
                "explicacion": {
                    "consumo_proyectado": 1.43,
                    "inventario_actual": 1.0,
                    "necesidad_real": 0.43,
                    "orden_recibida_unidad_base": 5.0,
                    "tolerancia_redondeo_aplicada": 0.25,
                },
            }
        ],
        {
            "total_alertas": 1,
            "dinero_en_riesgo_total": 11.43,
            "sucursal_mas_critica": "Via Argentina",
            "health_scores": {"Via Argentina": 70},
        },
    )

    branch = context["estado_por_sucursal"][0]
    assert branch["sucursal"] == "Via Argentina"
    assert branch["health_score"] == 70
    assert branch["total_alertas"] == 1
    assert branch["alertas"][0]["ingrediente"] == "Albahaca fresca"


def test_enriched_ai_context_includes_app_data() -> None:
    context = enrich_ai_context(
        build_ai_context([], {"health_scores": {"Via Argentina": 100}}),
        {
            "ingredients": [
                {
                    "ingrediente_id": "harina",
                    "nombre": "Harina 00",
                    "proveedor": "Molinos",
                    "unidad_base": "kg",
                    "formato_compra": "Saco 25 kg",
                    "unidad_base_por_formato": 25,
                    "es_perecedero": False,
                }
            ],
            "consumption": [{"sucursal": "Via Argentina", "ingrediente_id": "harina", "consumo_unidad_base": 300}],
            "inventory": [{"sucursal": "Via Argentina", "ingrediente_id": "harina"}],
            "purchase_orders": [{"sucursal": "Via Argentina", "ingrediente_id": "harina"}],
        },
        [{"sucursal": "Via Argentina", "ingrediente": "Harina 00"}],
        [{"proveedor": "Molinos", "items": [{"ingrediente": "Harina 00"}]}],
    )

    assert context["datasets"]["sucursales"] == ["Via Argentina"]
    assert context["datasets"]["proveedores"] == ["Molinos"]
    assert context["anomalias_entre_sucursales"][0]["ingrediente"] == "Harina 00"
    assert context["pedido_corregido_por_proveedor"][0]["proveedor"] == "Molinos"
    assert context["analitica_consumo"]["top_consumo_total_6_semanas"][0]["ingrediente"] == "Harina 00"
    assert context["analitica_consumo"]["top_consumo_total_6_semanas"][0]["consumo_total_6_semanas"] > 0


def test_out_of_scope_question_does_not_call_ai(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "configured")
    db = SessionLocal()
    try:
        response = answer_question("Escribeme un poema sobre la luna", None, db)
    finally:
        db.close()

    assert response == "Solo puedo ayudar con preguntas sobre compras, inventario, sucursales, proveedores, alertas y pedidos de Barrio Pizza."


def test_ai_tools_return_real_consumption_data() -> None:
    db = SessionLocal()
    try:
        result = execute_tool(db, "get_consumption_history", {"sucursal": "Via Argentina", "ingrediente": "harina"})
    finally:
        db.close()

    assert result["sucursal"] == "Via Argentina"
    assert result["ingrediente"] == "Harina 00"
    assert result["unidad"] == "kg"
    assert len(result["historial"]) == 6
    assert result["total"] > 0


def test_ai_tool_reports_missing_ingredient() -> None:
    db = SessionLocal()
    try:
        result = execute_tool(db, "get_consumption_history", {"sucursal": "Via Argentina", "ingrediente": "queso azul"})
    finally:
        db.close()

    assert "error" in result
    assert "queso azul" in result["error"]


def test_list_sucursales_includes_spend_summary() -> None:
    db = SessionLocal()
    try:
        result = execute_tool(db, "list_sucursales", {})
    finally:
        db.close()

    assert result["total"] == 4
    assert result["resumen_por_sucursal"]
    assert "valor_estimado_orden_actual" in result["resumen_por_sucursal"][0]


def test_weekly_summary_returns_complete_sentence_without_ai(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "")
    summary = generate_weekly_summary(
        [
            {
                "sucursal": "Brisas del Golf",
                "tipo": "quiebre",
                "ingrediente": "Mozzarella",
                "severidad": "alta",
                "impacto_dinero": 120.0,
            }
        ]
    )

    assert len(summary) > 80
    assert summary.endswith(".")
