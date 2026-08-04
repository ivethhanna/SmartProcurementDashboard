from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.alerts.health_score import health_scores_by_branch
from app.services.dashboard_data import get_branches, get_live_alerts, get_procurement_data
from app.services.forecasting.anomaly_detection import detect_cross_branch_anomalies

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    data = get_procurement_data(db)
    return detect_cross_branch_anomalies(data["ingredients"], data["purchase_orders"])


@router.get("/health-scores")
def get_health_scores(db: Session = Depends(get_db)):
    alerts = get_live_alerts(db)
    return health_scores_by_branch(alerts, branches=get_branches(db))
