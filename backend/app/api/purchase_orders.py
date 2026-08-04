from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.dashboard_data import get_procurement_data
from app.services.exports.exports import export_corrected_orders_to_excel
from app.services.procurement.supplier_grouping import build_corrected_orders_by_provider

router = APIRouter(prefix="/api", tags=["purchase-orders"])


@router.get("/orders-by-provider")
def get_orders_by_provider(db: Session = Depends(get_db)):
    data = get_procurement_data(db)
    return build_corrected_orders_by_provider(
        data["ingredients"],
        data["consumption"],
        data["inventory"],
    )


@router.get("/export/pedido-corregido")
def export_corrected_order(db: Session = Depends(get_db)):
    data = get_procurement_data(db)
    groups = build_corrected_orders_by_provider(
        data["ingredients"],
        data["consumption"],
        data["inventory"],
    )
    path = export_corrected_orders_to_excel(groups)
    return FileResponse(
        path,
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
