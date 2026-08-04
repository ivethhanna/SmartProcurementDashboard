from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.dashboard_data import get_dashboard_summary, get_live_alerts

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/alerts")
def list_alerts(
    sucursal: str | None = Query(default=None),
    tipo: str | None = Query(default=None, pattern="^(quiebre|sobre_pedido|olvidado)$"),
    severidad: str | None = Query(default=None, pattern="^(alta|media|baja)$"),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    alerts = get_live_alerts(db)
    if sucursal:
        alerts = [alert for alert in alerts if alert["sucursal"] == sucursal]
    if tipo:
        alerts = [alert for alert in alerts if alert["tipo"] == tipo]
    if severidad:
        alerts = [alert for alert in alerts if alert["severidad"] == severidad]
    return alerts


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return get_dashboard_summary(db)
