from dataclasses import dataclass
import re


@dataclass(frozen=True)
class HistoricalPoint:
    week: str
    value: float
    is_outlier: bool = False


@dataclass(frozen=True)
class ProjectionResult:
    projected_consumption: float
    trend: str
    confidence: str
    points: list[HistoricalPoint]
    weeks_used: list[float]


def _week_sort_key(week: str) -> int:
    match = re.search(r"\d+", str(week))
    return int(match.group(0)) if match else 0


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def mark_iqr_outliers(values: list[float]) -> list[bool]:
    if len(values) < 4:
        return [False for _ in values]

    sorted_values = sorted(values)
    q1 = _percentile(sorted_values, 0.25)
    q3 = _percentile(sorted_values, 0.75)
    iqr = q3 - q1
    if iqr == 0:
        return [False for _ in values]

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return [value < lower_bound or value > upper_bound for value in values]


def weighted_recent_average(values: list[float]) -> float:
    if not values:
        return 0.0
    weights = list(range(1, len(values) + 1))
    weighted_sum = sum(value * weight for value, weight in zip(values, weights))
    return weighted_sum / sum(weights)


def classify_trend(values: list[float]) -> str:
    if len(values) < 2:
        return "estable"
    first_half = values[: max(1, len(values) // 2)]
    second_half = values[len(values) // 2 :]
    baseline = sum(first_half) / len(first_half)
    recent = sum(second_half) / len(second_half)
    if baseline == 0 and recent == 0:
        return "estable"
    relative_change = (recent - baseline) / max(abs(baseline), 1)
    if relative_change > 0.08:
        return "creciente"
    if relative_change < -0.08:
        return "decreciente"
    return "estable"


def confidence_for_projection(total_points: int, used_points: int, trend: str) -> str:
    if used_points < 3:
        return "baja"
    if used_points < total_points or trend != "estable":
        return "media"
    return "alta"


def project_consumption(history: list[dict[str, object]]) -> ProjectionResult:
    """Project next-week consumption from six historical weeks.

    Formula:
    1. Sort rows by numeric week order, for example S1..S6.
    2. Detect outliers using IQR fences: Q1 - 1.5 * IQR and Q3 + 1.5 * IQR.
    3. Discard outlier weeks.
    4. Compute a recency-weighted average over remaining weeks using weights
       1..n, where the oldest used week has weight 1 and the newest has weight n.
       projection = sum(consumption_i * weight_i) / sum(weight_i).
    5. Classify trend by comparing the average of the first half vs. second half
       of the non-outlier series. More than +/-8% is creciente/decreciente;
       otherwise it is estable.
    """
    sorted_history = sorted(history, key=lambda row: _week_sort_key(str(row["week"])))
    values = [float(row["value"]) for row in sorted_history]
    outliers = mark_iqr_outliers(values)
    points = [
        HistoricalPoint(week=str(row["week"]), value=float(row["value"]), is_outlier=is_outlier)
        for row, is_outlier in zip(sorted_history, outliers)
    ]
    used_values = [point.value for point in points if not point.is_outlier]
    projected = weighted_recent_average(used_values)
    trend = classify_trend(used_values)
    confidence = confidence_for_projection(total_points=len(points), used_points=len(used_values), trend=trend)
    return ProjectionResult(
        projected_consumption=round(projected, 2),
        trend=trend,
        confidence=confidence,
        points=points,
        weeks_used=used_values,
    )


def project_grouped_consumption(rows: list[dict[str, object]]) -> dict[tuple[str, str], ProjectionResult]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        key = (str(row["branch"]), str(row["ingredient_id"]))
        grouped.setdefault(key, []).append({"week": row["week"], "value": row["value"]})
    return {key: project_consumption(history) for key, history in grouped.items()}
