from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db
from app.services.ai.ai_chat import answer_question, build_ai_context, generate_weekly_summary
from app.services.dashboard_data import get_dashboard_summary, get_live_alerts

router = APIRouter(prefix="/api", tags=["ai"])


class ChatRequest(BaseModel):
    pregunta: str


class SummaryRequest(BaseModel):
    alertas: list[dict] | None = None


@router.post("/chat")
def chat_with_data(request: ChatRequest, db: Session = Depends(get_db)) -> dict[str, str | bool]:
    alerts = get_live_alerts(db)
    summary = get_dashboard_summary(db)
    context = build_ai_context(alerts, summary)
    return {
        "respuesta": answer_question(request.pregunta, context),
        "ai_configurada": bool(settings.anthropic_api_key),
    }


@router.post("/summary-ai")
def weekly_summary(request: SummaryRequest, db: Session = Depends(get_db)) -> dict[str, str | bool]:
    alerts = request.alertas if request.alertas is not None else get_live_alerts(db)
    return {
        "summary": generate_weekly_summary(alerts),
        "ai_configurada": bool(settings.anthropic_api_key),
    }
