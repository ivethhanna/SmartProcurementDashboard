from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class AlertsConfig(Base):
    __tablename__ = "alerts_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    porcentaje_diferencia_severidad_alta: Mapped[float] = mapped_column(Float, default=0.5)
    porcentaje_diferencia_severidad_media: Mapped[float] = mapped_column(Float, default=0.15)
    multiplicador_perecedero: Mapped[float] = mapped_column(Float, default=2.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
