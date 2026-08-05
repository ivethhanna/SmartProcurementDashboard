from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.config import AlertsConfig

DEFAULT_ALERTS_CONFIG = {
    "porcentaje_diferencia_severidad_alta": 0.5,
    "porcentaje_diferencia_severidad_media": 0.15,
    "multiplicador_perecedero": 2.0,
}


def ensure_alerts_config(db: Session) -> AlertsConfig:
    config = db.scalar(select(AlertsConfig).limit(1))
    if config is None:
        config = AlertsConfig(id=1, **DEFAULT_ALERTS_CONFIG)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def alerts_config_dict(db: Session) -> dict[str, float]:
    config = ensure_alerts_config(db)
    return {
        "porcentaje_diferencia_severidad_alta": config.porcentaje_diferencia_severidad_alta,
        "porcentaje_diferencia_severidad_media": config.porcentaje_diferencia_severidad_media,
        "multiplicador_perecedero": config.multiplicador_perecedero,
    }


def update_alerts_config(db: Session, payload: dict[str, Any]) -> dict[str, float]:
    high = float(payload.get("porcentaje_diferencia_severidad_alta", 0))
    medium = float(payload.get("porcentaje_diferencia_severidad_media", 0))
    perishable = float(payload.get("multiplicador_perecedero", 0))
    if high <= 0 or medium <= 0 or perishable <= 0:
        raise ValueError("Todos los valores deben ser mayores que cero.")
    if high <= medium:
        raise ValueError("El umbral de severidad alta debe ser mayor que el de severidad media.")
    config = ensure_alerts_config(db)
    config.porcentaje_diferencia_severidad_alta = high
    config.porcentaje_diferencia_severidad_media = medium
    config.multiplicador_perecedero = perishable
    config.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(config)
    return alerts_config_dict(db)
