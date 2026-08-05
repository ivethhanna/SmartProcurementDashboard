from datetime import UTC, date, datetime

_usage_day: date = datetime.now(UTC).date()
_calls_today = 0
_last_success: datetime | None = None
_last_error: str | None = None


def _rollover_if_needed() -> None:
    global _usage_day, _calls_today
    today = datetime.now(UTC).date()
    if today != _usage_day:
        _usage_day = today
        _calls_today = 0


def record_ai_success() -> None:
    global _calls_today, _last_success, _last_error
    _rollover_if_needed()
    _calls_today += 1
    _last_success = datetime.now(UTC)
    _last_error = None


def record_ai_error(message: str) -> None:
    global _last_error
    _rollover_if_needed()
    _last_error = message[:500]


def ai_usage_status() -> dict[str, object]:
    _rollover_if_needed()
    return {
        "llamadas_hoy": _calls_today,
        "ultima_llamada_exitosa": _last_success.isoformat() if _last_success else None,
        "ultimo_error": _last_error,
    }
