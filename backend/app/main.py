from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai_chat, config as config_api, dashboard, inventory, purchase_orders, recommendations, upload
from app.core.config import settings
from app.database.database import Base, SessionLocal, engine
from app.database.seed import seed_database_if_empty
from app.models import config, consumption, ingredient, inventory as inventory_model, purchase_order, supplier
from app.services.alerts.config import ensure_alerts_config


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database_if_empty(db)
        ensure_alerts_config(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Barrio Pizza AI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(inventory.router)
app.include_router(purchase_orders.router)
app.include_router(dashboard.router)
app.include_router(recommendations.router)
app.include_router(ai_chat.router)
app.include_router(config_api.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
