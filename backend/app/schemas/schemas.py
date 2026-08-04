from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class DashboardSummary(BaseModel):
    total_alertas: int
    dinero_en_riesgo_total: float
    sucursal_mas_critica: str | None
    health_scores: dict[str, int]
    ultima_actualizacion: str | None
