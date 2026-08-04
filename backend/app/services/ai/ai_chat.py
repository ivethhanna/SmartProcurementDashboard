from typing import Any

from app.core.config import settings


def build_ai_context(alerts: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    compact_alerts = [
        {
            "sucursal": alert["sucursal"],
            "ingrediente": alert["ingrediente"],
            "tipo": alert["tipo"],
            "severidad": alert["severidad"],
            "impacto_dinero": alert["impacto_dinero"],
            "mensaje": alert["mensaje"],
            "explicacion": {
                "consumo_proyectado": alert["explicacion"]["consumo_proyectado"],
                "inventario_actual": alert["explicacion"]["inventario_actual"],
                "necesidad_real": alert["explicacion"]["necesidad_real"],
                "orden_recibida_unidad_base": alert["explicacion"]["orden_recibida_unidad_base"],
                "tolerancia_redondeo_aplicada": alert["explicacion"]["tolerancia_redondeo_aplicada"],
                "tendencia": alert["explicacion"].get("tendencia"),
            },
        }
        for alert in alerts[:12]
    ]
    return {
        "kpis": {
            "total_alertas": summary.get("total_alertas"),
            "dinero_en_riesgo_total": summary.get("dinero_en_riesgo_total"),
            "sucursal_mas_critica": summary.get("sucursal_mas_critica"),
            "health_scores": summary.get("health_scores"),
        },
        "alertas_prioritarias": compact_alerts,
    }


def _fallback_weekly_summary(alerts: list[dict[str, Any]]) -> str:
    if not alerts:
        return "No hay alertas activas. La orden semanal esta dentro de los rangos esperados."
    top = alerts[0]
    total_money = sum(float(alert["impacto_dinero"]) for alert in alerts)
    critical_branches = sorted({str(alert["sucursal"]) for alert in alerts[:3]})
    return (
        f"Hay {len(alerts)} alertas activas con ${total_money:,.2f} en riesgo estimado. "
        f"La prioridad es {top['sucursal']} por {top['tipo'].replace('_', ' ')} de {top['ingrediente']}. "
        f"Revisar primero: {', '.join(critical_branches)}."
    )


def _fallback_answer(question: str, context: dict[str, Any]) -> str:
    alerts = context.get("alertas_prioritarias", [])
    if not alerts:
        return "No hay alertas activas en este momento. Puedes cargar nuevos datos o revisar el resumen general."
    top = alerts[0]
    return (
        f"Con los datos actuales, la alerta mas importante es en {top['sucursal']}: "
        f"{top['mensaje']} Impacto estimado: ${float(top['impacto_dinero']):,.2f}. "
        "La IA externa no esta configurada, asi que esta respuesta usa el resumen calculado localmente."
    )


def generate_response(prompt: str) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY no configurada")

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=500,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if getattr(block, "type", "") == "text").strip()
    except Exception as exc:
        raise RuntimeError(f"No se pudo generar respuesta con Anthropic: {exc}") from exc


def answer_question(pregunta: str, contexto_datos: dict[str, Any]) -> str:
    prompt = (
        "Eres un asistente para la gerente de compras de Barrio Pizza. "
        "Responde en espanol, directo y accionable. No inventes datos fuera del contexto.\n\n"
        f"Pregunta: {pregunta}\n\n"
        f"Contexto estructurado: {contexto_datos}"
    )
    try:
        return generate_response(prompt)
    except RuntimeError:
        return _fallback_answer(pregunta, contexto_datos)


def generate_weekly_summary(alertas: list[dict[str, Any]]) -> str:
    prompt = (
        "Resume en 3-4 lineas las alertas semanales de compras para Barrio Pizza. "
        "Prioriza sucursales criticas, perecederos y dinero en riesgo. "
        "Escribe en espanol claro para una gerente de compras.\n\n"
        f"Alertas: {alertas[:12]}"
    )
    try:
        return generate_response(prompt)
    except RuntimeError:
        return _fallback_weekly_summary(alertas)
