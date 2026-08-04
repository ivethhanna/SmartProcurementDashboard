from app.services.alerts.alerts_engine import generate_alerts
from app.services.alerts.health_score import health_scores_by_branch
from app.services.procurement.calculations import compare_order_to_need


INGREDIENTS = [
    {
        "ingrediente_id": "harina",
        "nombre": "Harina 00",
        "unidad_base": "kg",
        "unidad_base_por_formato": 25,
        "es_perecedero": False,
        "costo_unitario_estimado": 1.35,
    },
    {
        "ingrediente_id": "mozzarella",
        "nombre": "Mozzarella",
        "unidad_base": "kg",
        "unidad_base_por_formato": 10,
        "es_perecedero": True,
        "costo_unitario_estimado": 6.8,
    },
]


def _history(branch: str, ingredient_id: str, values: list[float]) -> list[dict[str, object]]:
    return [
        {
            "sucursal": branch,
            "ingrediente_id": ingredient_id,
            "semana": f"S{index}",
            "consumo_unidad_base": value,
        }
        for index, value in enumerate(values, start=1)
    ]


def test_rounding_tolerance_prevents_small_over_order_alert() -> None:
    comparison = compare_order_to_need(
        projected_consumption=101,
        current_inventory=0,
        ordered_formats=5,
        conversion_factor=25,
        estimated_unit_cost=1,
    )

    assert comparison.alert_type is None
    assert comparison.ordered_base_units == 125


def test_generates_shortage_alert_with_required_message_shape() -> None:
    alerts = generate_alerts(
        INGREDIENTS,
        _history("Brisas", "harina", [100, 100, 100, 100, 100, 100]),
        [{"sucursal": "Brisas", "ingrediente_id": "harina", "stock_actual_unidad_base": 0}],
        [{"sucursal": "Brisas", "ingrediente_id": "harina", "cantidad_formatos": 2}],
    )

    assert len(alerts) == 1
    assert alerts[0]["tipo"] == "quiebre"
    assert alerts[0]["severidad"] in {"media", "alta"}
    assert alerts[0]["mensaje"] == "ALERTA: Brisas está pidiendo 50.0 kg de Harina 00 menos que lo proyectado → riesgo de quiebre."
    assert alerts[0]["explicacion"]["orden_recibida_unidad_base"] == 50


def test_generates_perishable_over_order_with_higher_severity() -> None:
    alerts = generate_alerts(
        INGREDIENTS,
        _history("Costa", "mozzarella", [20, 20, 20, 20, 20, 20]),
        [{"sucursal": "Costa", "ingrediente_id": "mozzarella", "stock_actual_unidad_base": 0}],
        [{"sucursal": "Costa", "ingrediente_id": "mozzarella", "cantidad_formatos": 5}],
    )

    assert alerts[0]["tipo"] == "sobre_pedido"
    assert alerts[0]["severidad"] == "alta"
    assert alerts[0]["impacto_dinero"] == 204


def test_generates_forgotten_alert_when_no_order_exists() -> None:
    alerts = generate_alerts(
        INGREDIENTS,
        _history("Marbella", "harina", [25, 26, 25, 26, 25, 26]),
        [{"sucursal": "Marbella", "ingrediente_id": "harina", "stock_actual_unidad_base": 0}],
        [],
    )

    assert alerts[0]["tipo"] == "olvidado"
    assert "no incluyó Harina 00" in alerts[0]["mensaje"]


def test_health_scores_penalize_by_severity() -> None:
    scores = health_scores_by_branch(
        [
            {"sucursal": "Brisas", "severidad": "alta"},
            {"sucursal": "Brisas", "severidad": "media"},
            {"sucursal": "Costa", "severidad": "baja"},
        ],
        branches=["Brisas", "Costa", "Marbella"],
    )

    assert scores["Brisas"] == 63
    assert scores["Costa"] == 95
    assert scores["Marbella"] == 100
