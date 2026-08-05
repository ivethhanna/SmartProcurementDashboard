from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db
from app.services.ai.ai_chat import answer_question, generate_weekly_summary
from app.services.dashboard_data import get_live_alerts

router = APIRouter(prefix="/api", tags=["ai"])


class ChatRequest(BaseModel):
    pregunta: str
    historial: list[dict] | None = None


class SummaryRequest(BaseModel):
    alertas: list[dict] | None = None


@router.post("/chat")
def chat_with_data(request: ChatRequest, db: Session = Depends(get_db)) -> dict[str, str | bool]:
    return {
        "respuesta": answer_question(request.pregunta, request.historial, db),
        "ai_configurada": bool(settings.gemini_api_key),
    }


@router.post("/summary-ai")
def weekly_summary(request: SummaryRequest, db: Session = Depends(get_db)) -> dict[str, str | bool]:
    alerts = request.alertas if request.alertas is not None else get_live_alerts(db)
    return {
        "summary": generate_weekly_summary(alerts),
        "ai_configurada": bool(settings.gemini_api_key),
    }
