from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


EXPORT_DIR = Path(__file__).resolve().parents[3] / "exports"


def export_corrected_orders_to_excel(groups: list[dict[str, Any]]) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"pedido_corregido_{timestamp}.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for group in groups:
            provider = str(group["proveedor"])
            sheet_name = provider[:31] or "Proveedor"
            df = pd.DataFrame(group["items"])
            if df.empty:
                df = pd.DataFrame(columns=["sucursal", "ingrediente", "cantidad_formatos_corregida"])
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    return path
