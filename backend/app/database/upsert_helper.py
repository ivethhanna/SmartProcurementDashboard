from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session


def upsert_by_unique_key(
    session: Session,
    model: type,
    unique_filters: dict[str, Any],
    data: dict[str, Any],
) -> tuple[object, bool]:
    """
    Create or update a row identified by a dataset-specific unique key.

    Returns (row, True) when a row was created and (row, False) when an
    existing row was updated.
    """
    existing = session.scalar(select(model).filter_by(**unique_filters).limit(1))
    if existing is not None:
        for key, value in data.items():
            setattr(existing, key, value)
        session.commit()
        return existing, False

    row = model(**unique_filters, **data)
    session.add(row)
    session.commit()
    return row, True
