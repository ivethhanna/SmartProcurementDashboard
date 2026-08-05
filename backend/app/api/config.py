from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db
from app.services.ai.usage import ai_usage_status
from app.services.alerts.config import DEFAULT_ALERTS_CONFIG, alerts_config_dict, update_alerts_config

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/alerts-thresholds")
def get_alerts_thresholds(db: Session = Depends(get_db)) -> dict[str, float]:
    return alerts_config_dict(db)


@router.put("/alerts-thresholds")
def put_alerts_thresholds(payload: dict, db: Session = Depends(get_db)) -> dict[str, float]:
    try:
        return update_alerts_config(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/alerts-thresholds/reset")
def reset_alerts_thresholds(db: Session = Depends(get_db)) -> dict[str, float]:
    return update_alerts_config(db, DEFAULT_ALERTS_CONFIG)


@router.get("/ai-status")
def get_ai_status() -> dict[str, object]:
    usage = ai_usage_status()
    return {
        "proveedor": "gemini",
        "key_configurada": bool(settings.gemini_api_key),
        "modelo": settings.gemini_model,
        # Gemini does not expose a simple real-time remaining quota endpoint here.
        # This is a local display limit, configured from the environment.
        "limite_diario_conocido": settings.gemini_daily_limit,
        **usage,
    }
