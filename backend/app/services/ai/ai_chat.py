from typing import Any
import json
import time
from unicodedata import normalize
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.ai.tools import TOOL_DECLARATIONS, execute_tool
from app.services.ai.usage import record_ai_error, record_ai_success


SYSTEM_PROMPT = """Sos el asistente de datos de Barrio Pizza, una cadena de pizzerias con sucursales en Panama.
Tu trabajo es responder preguntas de la gerente de compras sobre consumo, inventario, ordenes de compra, proveedores y alertas usando UNICAMENTE las herramientas disponibles para consultar datos reales. Nunca inventes cifras ni asumas datos que no consultaste.

Reglas:
- Si una pregunta requiere un dato, llama a la herramienta correspondiente antes de responder. No respondas de memoria ni con estimaciones propias.
- Si el dato no existe o la herramienta devuelve un error, decilo explicitamente ("No tengo datos de X para Y"), no lo completes con una suposicion.
- Responde siempre en espanol, en lenguaje simple y directo. Evita jerga de bases de datos o nombres de tablas.
- Cuando des una cifra, incluye la unidad y, si aplica, la sucursal y el ingrediente especifico a los que corresponde.
- Si la pregunta no tiene que ver con Barrio Pizza (compras, inventario, consumo, proveedores, alertas, pedidos o sucursales), indica amablemente que solo podes ayudar con esos temas.
- Si una pregunta es ambigua, por ejemplo "como estamos con el queso" sin especificar sucursal ni tipo de queso, pide la aclaracion necesaria en vez de asumir.
- Si preguntan que sucursal "gasta mas" sin mas detalle, interpreta "gasta" como valor estimado de la orden actual y usa list_sucursales; aclara que si queria consumo historico puede pedirlo aparte.
- No muestres razonamiento interno, borradores, frases como "Wait" ni analisis entre parentesis; entrega solo la respuesta final.
"""


def build_ai_context(alerts: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    compact_alerts = [
        {
            "sucursal": alert["sucursal"],
            "ingrediente_id": alert.get("ingrediente_id"),
            "ingrediente": alert["ingrediente"],
            "tipo": alert["tipo"],
            "severidad": alert["severidad"],
            "cantidad_diferencia": alert["cantidad_diferencia"],
            "unidad": alert["unidad"],
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
    branch_status: dict[str, dict[str, Any]] = {
        str(branch): {
            "sucursal": str(branch),
            "health_score": score,
            "total_alertas": 0,
            "impacto_dinero_total": 0,
            "alertas": [],
        }
        for branch, score in (summary.get("health_scores") or {}).items()
    }
    for alert in alerts:
        branch = str(alert["sucursal"])
        status = branch_status.setdefault(
            branch,
            {
                "sucursal": branch,
                "health_score": None,
                "total_alertas": 0,
                "impacto_dinero_total": 0,
                "alertas": [],
            },
        )
        status["total_alertas"] += 1
        status["impacto_dinero_total"] = round(float(status["impacto_dinero_total"]) + float(alert["impacto_dinero"]), 2)
        status["alertas"].append(
            {
                "ingrediente": alert["ingrediente"],
                "tipo": alert["tipo"],
                "severidad": alert["severidad"],
                "diferencia": f"{alert['cantidad_diferencia']} {alert['unidad']}",
                "impacto_dinero": alert["impacto_dinero"],
                "mensaje": alert["mensaje"],
                "necesidad_real": alert["explicacion"]["necesidad_real"],
                "orden_recibida_unidad_base": alert["explicacion"]["orden_recibida_unidad_base"],
            }
        )

    return {
        "kpis": {
            "total_alertas": summary.get("total_alertas"),
            "dinero_en_riesgo_total": summary.get("dinero_en_riesgo_total"),
            "sucursal_mas_critica": summary.get("sucursal_mas_critica"),
            "health_scores": summary.get("health_scores"),
        },
        "estado_por_sucursal": sorted(branch_status.values(), key=lambda item: str(item["sucursal"])),
        "alertas_prioritarias": compact_alerts,
    }


def enrich_ai_context(
    context: dict[str, Any],
    procurement_data: dict[str, list[dict[str, Any]]],
    anomalies: list[dict[str, Any]],
    provider_orders: list[dict[str, Any]],
) -> dict[str, Any]:
    ingredients = procurement_data["ingredients"]
    consumption = procurement_data["consumption"]
    inventory = procurement_data["inventory"]
    purchase_orders = procurement_data["purchase_orders"]
    branches = sorted({str(row["sucursal"]) for row in consumption + inventory + purchase_orders})
    providers = sorted({str(row.get("proveedor") or "Sin proveedor") for row in ingredients})

    provider_summary = [
        {
            "proveedor": group["proveedor"],
            "total_items": len(group["items"]),
            "items_principales": group["items"][:8],
        }
        for group in provider_orders[:8]
    ]

    ingredient_summary = [
        {
            "ingrediente_id": row["ingrediente_id"],
            "nombre": row["nombre"],
            "proveedor": row["proveedor"],
            "unidad_base": row["unidad_base"],
            "formato_compra": row["formato_compra"],
            "unidad_base_por_formato": row["unidad_base_por_formato"],
            "es_perecedero": row["es_perecedero"],
        }
        for row in ingredients[:80]
    ]
    ingredient_by_id = {str(row["ingrediente_id"]): row for row in ingredients}
    consumption_by_ingredient: dict[str, dict[str, Any]] = {}
    consumption_by_branch: dict[str, dict[str, dict[str, Any]]] = {}
    for row in consumption:
        ingredient_id = str(row["ingrediente_id"])
        ingredient = ingredient_by_id.get(ingredient_id, {})
        branch = str(row["sucursal"])
        value = float(row["consumo_unidad_base"])
        current = consumption_by_ingredient.setdefault(
            ingredient_id,
            {
                "ingrediente_id": ingredient_id,
                "ingrediente": ingredient.get("nombre", ingredient_id),
                "unidad": ingredient.get("unidad_base"),
                "proveedor": ingredient.get("proveedor"),
                "consumo_total_6_semanas": 0.0,
                "registros": 0,
                "sucursales": set(),
            },
        )
        current["consumo_total_6_semanas"] += value
        current["registros"] += 1
        current["sucursales"].add(branch)

        branch_items = consumption_by_branch.setdefault(branch, {})
        branch_current = branch_items.setdefault(
            ingredient_id,
            {
                "ingrediente_id": ingredient_id,
                "ingrediente": ingredient.get("nombre", ingredient_id),
                "unidad": ingredient.get("unidad_base"),
                "consumo_total_6_semanas": 0.0,
                "registros": 0,
            },
        )
        branch_current["consumo_total_6_semanas"] += value
        branch_current["registros"] += 1

    top_consumption = []
    for item in consumption_by_ingredient.values():
        registros = max(int(item["registros"]), 1)
        branch_count = max(len(item["sucursales"]), 1)
        top_consumption.append(
            {
                "ingrediente_id": item["ingrediente_id"],
                "ingrediente": item["ingrediente"],
                "unidad": item["unidad"],
                "proveedor": item["proveedor"],
                "consumo_total_6_semanas": round(float(item["consumo_total_6_semanas"]), 2),
                "promedio_por_registro": round(float(item["consumo_total_6_semanas"]) / registros, 2),
                "promedio_semanal_total_sucursales": round(float(item["consumo_total_6_semanas"]) / 6, 2),
                "promedio_semanal_por_sucursal": round(float(item["consumo_total_6_semanas"]) / (6 * branch_count), 2),
                "sucursales_con_consumo": sorted(item["sucursales"]),
            }
        )
    top_consumption = sorted(top_consumption, key=lambda item: item["consumo_total_6_semanas"], reverse=True)

    top_consumption_by_branch = {
        branch: sorted(
            [
                {
                    **item,
                    "consumo_total_6_semanas": round(float(item["consumo_total_6_semanas"]), 2),
                    "promedio_semanal": round(float(item["consumo_total_6_semanas"]) / 6, 2),
                }
                for item in items.values()
            ],
            key=lambda item: item["consumo_total_6_semanas"],
            reverse=True,
        )[:8]
        for branch, items in consumption_by_branch.items()
    }

    return {
        **context,
        "alcance": {
            "negocio": "Barrio Pizza",
            "temas_permitidos": [
                "alertas de compra",
                "sucursales",
                "inventario",
                "consumo historico",
                "ordenes de compra",
                "pedido corregido",
                "proveedores",
                "anomalias entre sucursales",
                "health score",
            ],
            "instruccion_fuera_de_alcance": "Si la pregunta no trata sobre estos datos, responde brevemente que solo puedes ayudar con datos de compras de Barrio Pizza.",
        },
        "app_capabilities": [
            "Dashboard con KPIs, health score y alertas accionables.",
            "Recomendaciones con anomalias entre sucursales y pedido corregido por proveedor.",
            "Carga CSV y captura/edicion manual de datasets.",
            "Chat IA conectado al estado vivo de compras e inventario.",
        ],
        "datasets": {
            "sucursales": branches,
            "proveedores": providers,
            "conteos": {
                "ingredientes": len(ingredients),
                "consumo_historico": len(consumption),
                "inventario": len(inventory),
                "ordenes_compra": len(purchase_orders),
            },
            "ingredientes": ingredient_summary,
        },
        "anomalias_entre_sucursales": anomalies[:12],
        "pedido_corregido_por_proveedor": provider_summary,
        "analitica_consumo": {
            "nota": "Ranking calculado desde consumo_historico en unidad base. Usa top_consumo_total_6_semanas para responder cual ingrediente/producto se consume mas.",
            "top_consumo_total_6_semanas": top_consumption[:15],
            "top_consumo_por_sucursal": top_consumption_by_branch,
        },
    }


def _normalize_text(value: str) -> str:
    return normalize("NFKD", value.lower()).encode("ascii", "ignore").decode("ascii")


def _is_domain_question(question: str, context: dict[str, Any]) -> bool:
    normalized_question = _normalize_text(question)
    domain_keywords = {
        "barrio",
        "pizza",
        "compra",
        "compras",
        "orden",
        "pedido",
        "proveedor",
        "proveedores",
        "sucursal",
        "sucursales",
        "inventario",
        "stock",
        "gasta",
        "gastan",
        "gasto",
        "valor",
        "consumo",
        "alerta",
        "alertas",
        "quiebre",
        "sobrepedido",
        "sobre-pedido",
        "perecedero",
        "ingrediente",
        "ingredientes",
        "health",
        "score",
        "anomalia",
        "anomalias",
        "riesgo",
        "recomendacion",
        "recomendaciones",
        "excel",
        "csv",
        "dashboard",
        "semana",
        "semanas",
        "pasada",
        "pasado",
        "anterior",
        "otra",
    }
    if any(keyword in normalized_question for keyword in domain_keywords):
        return True

    datasets = context.get("datasets", {})
    terms: list[str] = []
    terms.extend(str(branch) for branch in datasets.get("sucursales", []))
    terms.extend(str(provider) for provider in datasets.get("proveedores", []))
    terms.extend(str(item.get("nombre", "")) for item in datasets.get("ingredientes", []))
    return any(_normalize_text(term) and _normalize_text(term) in normalized_question for term in terms)


def _fallback_weekly_summary(alerts: list[dict[str, Any]]) -> str:
    if not alerts:
        return "No hay alertas activas. La orden semanal esta dentro de los rangos esperados."
    top = alerts[0]
    total_money = sum(float(alert["impacto_dinero"]) for alert in alerts)
    critical_branches = sorted({str(alert["sucursal"]) for alert in alerts[:3]})
    by_branch: dict[str, list[dict[str, Any]]] = {}
    for alert in alerts:
        by_branch.setdefault(str(alert["sucursal"]), []).append(alert)
    worst_branch, branch_alerts = max(
        by_branch.items(),
        key=lambda item: (
            sum(1 for alert in item[1] if alert["severidad"] == "alta"),
            len(item[1]),
            sum(float(alert["impacto_dinero"]) for alert in item[1]),
        ),
    )
    main_issue = branch_alerts[0]
    return (
        f"{worst_branch} es la sucursal mas critica: tiene {len(branch_alerts)} alerta(s), "
        f"incluyendo {main_issue['tipo'].replace('_', ' ')} de {main_issue['ingrediente']}. "
        f"En total hay {len(alerts)} alertas activas y ${total_money:,.2f} en impacto estimado. "
        f"Revisa primero {', '.join(critical_branches)} antes de aprobar las compras."
    )


def _fallback_answer(question: str, context: dict[str, Any]) -> str:
    alerts = context.get("alertas_prioritarias", [])
    if not alerts:
        return "No hay alertas activas en este momento. Puedes cargar nuevos datos o revisar el resumen general."
    top = alerts[0]
    return (
        f"Con los datos actuales, la alerta mas importante es en {top['sucursal']}: "
        f"{top['mensaje']} Impacto estimado: ${float(top['impacto_dinero']):,.2f}. "
        "Gemini no esta disponible, asi que esta respuesta usa el resumen calculado localmente."
    )


def _gemini_generate_content(contents: list[dict[str, Any]], *, tools: bool = False, timeout: int = 30) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY no configurada")

    model = settings.gemini_model.strip()
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 500,
        },
    }
    if tools:
        payload["tools"] = [{"functionDeclarations": TOOL_DECLARATIONS}]
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
            record_ai_success()
            return body
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        record_ai_error(detail)
        raise RuntimeError(f"No se pudo generar respuesta con Gemini: HTTP {exc.code} {detail}") from exc
    except (URLError, TimeoutError) as exc:
        record_ai_error(str(exc))
        raise RuntimeError(f"No se pudo conectar con Gemini: {exc}") from exc
    except Exception as exc:
        record_ai_error(str(exc))
        raise RuntimeError(f"No se pudo generar respuesta con Gemini: {exc}") from exc

def _extract_text(body: dict[str, Any]) -> str:
    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(str(part.get("text", "")) for part in parts).strip()
    if not text:
        raise RuntimeError(f"Gemini no devolvio texto: {body}")
    return text


def generate_response(prompt: str) -> str:
    body = _gemini_generate_content([{"role": "user", "parts": [{"text": prompt}]}], tools=False)
    return _extract_text(body)


def _history_to_contents(pregunta: str, historial: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for message in (historial or [])[-8:]:
        role = "model" if message.get("role") == "assistant" else "user"
        text = str(message.get("text") or message.get("content") or "").strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": pregunta}]})
    return contents


def _function_calls(body: dict[str, Any]) -> list[dict[str, Any]]:
    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return [part["functionCall"] for part in parts if "functionCall" in part]


def _domain_context_from_history(historial: list[dict[str, Any]] | None) -> dict[str, Any]:
    terms = []
    for message in (historial or [])[-4:]:
        text = str(message.get("text") or message.get("content") or "")
        terms.append(text)
    return {"datasets": {"sucursales": [], "proveedores": [], "ingredientes": [{"nombre": term} for term in terms]}}


def answer_question(pregunta: str, historial: list[dict[str, Any]] | None, db: Session) -> str:
    if not _is_domain_question(pregunta, _domain_context_from_history(historial)):
        return "Solo puedo ayudar con preguntas sobre compras, inventario, sucursales, proveedores, alertas y pedidos de Barrio Pizza."

    contents = _history_to_contents(pregunta, historial)
    deadline = time.monotonic() + 30
    tool_calls_count = 0
    try:
        while tool_calls_count < 8 and time.monotonic() < deadline:
            body = _gemini_generate_content(contents, tools=True, timeout=max(1, int(deadline - time.monotonic())))
            calls = _function_calls(body)
            if not calls:
                return _extract_text(body)

            model_content = body.get("candidates", [{}])[0].get("content")
            if model_content:
                contents.append(model_content)

            response_parts = []
            for call in calls:
                if tool_calls_count >= 8:
                    break
                name = call.get("name", "")
                args = call.get("args") or {}
                result = execute_tool(db, name, args)
                tool_calls_count += 1
                print(f"[ai-chat] pregunta={pregunta!r} tool={name} args={args}")
                function_response = {
                    "name": name,
                    "response": {"result": result},
                }
                if call.get("id"):
                    function_response["id"] = call["id"]
                response_parts.append({"functionResponse": function_response})

            contents.append({"role": "user", "parts": response_parts})

        body = _gemini_generate_content(contents, tools=False, timeout=max(1, int(deadline - time.monotonic())))
        return _extract_text(body)
    except RuntimeError:
        return "No pude consultar Gemini en este momento. Revisa la API key, cuota o conexion y vuelve a intentarlo."


def generate_weekly_summary(alertas: list[dict[str, Any]]) -> str:
    local_summary = _fallback_weekly_summary(alertas)
    prompt = (
        "Resume en 2 oraciones completas las alertas semanales de compras para Barrio Pizza. "
        "Prioriza sucursales criticas, perecederos y dinero en riesgo. "
        "Escribe en espanol claro para una gerente de compras. "
        "No uses markdown. No dejes frases incompletas. Termina con punto final.\n\n"
        f"Alertas: {alertas[:12]}"
    )
    try:
        response = generate_response(prompt).strip()
        if len(response) < 80 or not response.endswith((".", "!", "?")):
            return local_summary
        return response
    except RuntimeError:
        return local_summary
