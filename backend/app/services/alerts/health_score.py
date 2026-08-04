SEVERITY_PENALTIES = {
    "alta": 25,
    "media": 12,
    "baja": 5,
}


def health_score_for_alerts(alerts: list[dict[str, object]]) -> int:
    penalty = sum(SEVERITY_PENALTIES.get(str(alert.get("severidad")), 0) for alert in alerts)
    return max(100 - penalty, 0)


def health_scores_by_branch(alerts: list[dict[str, object]], branches: list[str] | None = None) -> dict[str, int]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for alert in alerts:
        grouped.setdefault(str(alert["sucursal"]), []).append(alert)

    if branches:
        for branch in branches:
            grouped.setdefault(branch, [])

    return {branch: health_score_for_alerts(branch_alerts) for branch, branch_alerts in grouped.items()}
