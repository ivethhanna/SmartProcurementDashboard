from app.services.forecasting.projections import mark_iqr_outliers, project_consumption


def test_iqr_outlier_detection_marks_extreme_week() -> None:
    assert mark_iqr_outliers([10, 11, 10, 12, 11, 80]) == [False, False, False, False, False, True]


def test_projection_discards_outlier_and_weights_recent_weeks() -> None:
    result = project_consumption(
        [
            {"week": "S1", "value": 10},
            {"week": "S2", "value": 11},
            {"week": "S3", "value": 10},
            {"week": "S4", "value": 12},
            {"week": "S5", "value": 11},
            {"week": "S6", "value": 80},
        ]
    )

    assert result.points[-1].is_outlier is True
    assert result.projected_consumption == 11.0
    assert result.confidence == "media"


def test_projection_detects_growth_trend() -> None:
    result = project_consumption(
        [
            {"week": "S1", "value": 10},
            {"week": "S2", "value": 11},
            {"week": "S3", "value": 12},
            {"week": "S4", "value": 15},
            {"week": "S5", "value": 16},
            {"week": "S6", "value": 18},
        ]
    )

    assert result.trend == "creciente"
    assert result.projected_consumption > 14
