import { AlertTriangle, CheckCircle2, PackagePlus, ShieldCheck } from "lucide-react";
import type { DashboardSummary, PurchaseAlert } from "../../types";

interface KpiCardsProps {
  alerts: PurchaseAlert[];
  summary?: DashboardSummary;
  totalCombinations?: number;
  isLoading?: boolean;
}

function lowestHealthScore(summary?: DashboardSummary) {
  const scores = Object.values(summary?.health_scores ?? {});
  return scores.length ? Math.min(...scores) : null;
}

export function KpiCards({ alerts, summary, totalCombinations, isLoading = false }: KpiCardsProps) {
  const riskCount = alerts.filter((alert) => alert.tipo === "quiebre" && alert.severidad === "alta").length;
  const overOrderCount = alerts.filter((alert) => alert.tipo === "sobre_pedido").length;
  const alertKeys = new Set(alerts.map((alert) => `${alert.sucursal}-${alert.ingrediente}`));
  const correctCount = typeof totalCombinations === "number" ? Math.max(totalCombinations - alertKeys.size, 0) : null;
  const health = lowestHealthScore(summary);

  const cards = [
    {
      label: "Riesgos detectados",
      value: riskCount,
      hint: "Quiebres de severidad alta",
      icon: AlertTriangle,
      color: "text-red-700",
      bg: "bg-red-50",
    },
    {
      label: "Sobre pedidos",
      value: overOrderCount,
      hint: "Ordenes por encima de necesidad",
      icon: PackagePlus,
      color: "text-amber-700",
      bg: "bg-amber-50",
    },
    {
      label: "Compras correctas",
      value: correctCount ?? "Sin datos",
      hint: "Sucursal/ingrediente sin alerta",
      icon: CheckCircle2,
      color: "text-emerald-700",
      bg: "bg-emerald-50",
    },
    {
      label: "Health Score",
      value: health ?? "Sin datos",
      hint: "Puntaje mas bajo de sucursales",
      icon: ShieldCheck,
      color: "text-blue-700",
      bg: "bg-blue-50",
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" key={card.label}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-600">{card.label}</p>
                <p className="mt-2 text-2xl font-semibold tracking-normal text-slate-950">
                  {isLoading ? "..." : card.value}
                </p>
              </div>
              <span className={`rounded-md p-2 ${card.bg}`}>
                <Icon className={`h-4 w-4 ${card.color}`} aria-hidden="true" />
              </span>
            </div>
            <p className="mt-3 text-xs text-slate-500">{card.hint}</p>
          </section>
        );
      })}
    </div>
  );
}

