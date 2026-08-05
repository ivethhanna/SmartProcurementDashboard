import { Download, PencilLine } from "lucide-react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useMemo, useState } from "react";
import { AlertsList } from "../components/alerts/AlertsList";
import { ConsumptionTrendChart } from "../components/charts/ConsumptionTrendChart";
import { AiSummaryBanner } from "../components/chat/AiSummaryBanner";
import { EmptyState } from "../components/common/EmptyState";
import { SectionCard } from "../components/common/SectionCard";
import { HealthScoreBadge } from "../components/dashboard/HealthScoreBadge";
import { KpiCards } from "../components/dashboard/KpiCards";
import { useAlerts, useDashboardSummary } from "../hooks/useAlerts";
import { useDataset } from "../hooks/useDatasets";
import { useOrdersByProvider } from "../hooks/useRecommendations";
import { correctedOrderExportUrl } from "../services/api";
import type { AlertType, PurchaseAlert, Severity } from "../types";

interface DashboardProps {
  onNavigate?: (page: string) => void;
  onOpenManualEntry?: () => void;
}

const alertTypes: Array<{ value: AlertType | "todas"; label: string }> = [
  { value: "todas", label: "Tipo" },
  { value: "quiebre", label: "Quiebre" },
  { value: "sobre_pedido", label: "Sobre pedido" },
  { value: "olvidado", label: "Olvidado" },
];

const severities: Array<{ value: Severity | "todas"; label: string }> = [
  { value: "todas", label: "Severidad" },
  { value: "alta", label: "Alta" },
  { value: "media", label: "Media" },
  { value: "baja", label: "Baja" },
];

export default function Dashboard({ onNavigate, onOpenManualEntry }: DashboardProps) {
  const [branch, setBranch] = useState("todas");
  const [type, setType] = useState<AlertType | "todas">("todas");
  const [severity, setSeverity] = useState<Severity | "todas">("todas");
  const filters = { sucursal: branch, tipo: type, severidad: severity };

  const alertsQuery = useAlerts(filters);
  const summaryQuery = useDashboardSummary();
  const consumptionQuery = useDataset("consumption");
  const ingredientsQuery = useDataset("ingredients");
  const ordersQuery = useOrdersByProvider();

  const alerts = useMemo(() => alertsQuery.data ?? [], [alertsQuery.data]);
  const summary = summaryQuery.data;
  const branches = useMemo(
    () => Object.keys(summary?.health_scores ?? {}).sort(),
    [summary],
  );

  const totalCombinations = useMemo(() => {
    const rows = consumptionQuery.data ?? [];
    return new Set(rows.map((row) => `${row.branch}-${row.ingredient_id}`)).size || undefined;
  }, [consumptionQuery.data]);

  const trendPoints = useMemo(
    () => buildTrendPoints(alerts, ingredientsQuery.data ?? [], consumptionQuery.data ?? []),
    [alerts, ingredientsQuery.data, consumptionQuery.data],
  );

  const severityData = useMemo(
    () => [
      { name: "Alta", value: alerts.filter((alert) => alert.severidad === "alta").length, fill: "#dc2626" },
      { name: "Media", value: alerts.filter((alert) => alert.severidad === "media").length, fill: "#d97706" },
      { name: "Baja", value: alerts.filter((alert) => alert.severidad === "baja").length, fill: "#2563eb" },
    ],
    [alerts],
  );

  const firstProvider = ordersQuery.data?.[0];

  return (
    <main className="bg-white">
      <div className="mx-auto max-w-[1440px] px-4 py-6 lg:px-6">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Revision semanal</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-normal text-slate-950">Ordenes de compra</h1>
            <p className="mt-1 text-sm text-slate-600">
              Estado general, riesgos y acciones para las 4 sucursales piloto.
            </p>
          </div>
          <button
            className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={onOpenManualEntry}
            type="button"
          >
            <PencilLine className="h-4 w-4" aria-hidden="true" />
            Captura manual
          </button>
        </div>

        <KpiCards
          alerts={alerts}
          isLoading={alertsQuery.isLoading || summaryQuery.isLoading}
          summary={summary}
          totalCombinations={totalCombinations}
        />

        <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="min-w-0 space-y-6">
            <div className="grid gap-4 lg:grid-cols-2">
              <ConsumptionTrendChart points={trendPoints} />
              <SeverityChart data={severityData} />
            </div>

            <section>
              <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <h2 className="text-sm font-semibold text-slate-950">Alertas</h2>
                <Filters
                  branch={branch}
                  branches={branches}
                  severity={severity}
                  setBranch={setBranch}
                  setSeverity={setSeverity}
                  setType={setType}
                  type={type}
                />
              </div>
              {alertsQuery.isError ? (
                <EmptyState title="No se pudieron cargar las alertas" description="Verifica que el backend este activo." />
              ) : (
                <AlertsList alerts={alerts} isLoading={alertsQuery.isLoading} />
              )}
            </section>
          </section>

          <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">
            <AiSummaryBanner alerts={alerts} />

            <SectionCard title="Health score">
              <div className="space-y-2">
                {summary ? (
                  Object.entries(summary.health_scores)
                    .sort((a, b) => a[1] - b[1])
                    .map(([scoreBranch, score]) => (
                      <HealthScoreBadge branch={scoreBranch} key={scoreBranch} score={score} />
                    ))
                ) : (
                  <EmptyState title="Sin health score" />
                )}
              </div>
            </SectionCard>

            <SectionCard title="Pedido recomendado">
              {firstProvider ? (
                <div className="space-y-3">
                  <p className="text-sm text-slate-600">
                    {firstProvider.proveedor}: {firstProvider.items.length} items listos para revisar.
                  </p>
                  <button
                    className="text-sm font-medium text-blue-700 hover:underline"
                    onClick={() => onNavigate?.("recommendations")}
                    type="button"
                  >
                    Ver pedido completo
                  </button>
                </div>
              ) : (
                <EmptyState title="Sin pedido recomendado" description="No hay items corregidos disponibles." />
              )}
            </SectionCard>

            <a
              className="flex h-10 items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-medium text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              href={correctedOrderExportUrl()}
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Exportar pedido corregido
            </a>
          </aside>
        </div>
      </div>
    </main>
  );
}

function buildTrendPoints(alerts: PurchaseAlert[], ingredients: Record<string, unknown>[], rows: Record<string, unknown>[]) {
  const alert = alerts[0];
  if (!alert) return [];
  const ingredient = ingredients.find((row) => row.external_id === alert.ingrediente_id);
  if (!ingredient) return [];
  return rows
    .filter((row) => row.branch === alert.sucursal && row.ingredient_id === ingredient.id)
    .slice(0, 6)
    .map((row) => ({
      semana: String(row.week),
      consumo: Number(row.quantity_base_unit),
      proyectado: alert.explicacion.consumo_proyectado,
    }));
}

function SeverityChart({ data }: { data: Array<{ name: string; value: number; fill: string }> }) {
  if (!data.some((item) => item.value > 0)) {
    return <EmptyState title="Sin alertas por severidad" description="No hay datos para graficar." />;
  }
  return (
    <div className="h-72 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold text-slate-950">Alertas por severidad</h2>
      <ResponsiveContainer height="86%" width="100%">
        <BarChart data={data} margin={{ bottom: 0, left: -20, right: 12, top: 8 }}>
          <XAxis axisLine={false} dataKey="name" fontSize={12} tickLine={false} />
          <YAxis axisLine={false} allowDecimals={false} fontSize={12} tickLine={false} />
          <Tooltip />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((item) => <Cell fill={item.fill} key={item.name} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function Filters(props: {
  branch: string;
  branches: string[];
  severity: Severity | "todas";
  setBranch: (value: string) => void;
  setSeverity: (value: Severity | "todas") => void;
  setType: (value: AlertType | "todas") => void;
  type: AlertType | "todas";
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      <select className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm" onChange={(e) => props.setBranch(e.target.value)} value={props.branch}>
        <option value="todas">Sucursal</option>
        {props.branches.map((item) => <option key={item} value={item}>{item}</option>)}
      </select>
      <select className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm" onChange={(e) => props.setType(e.target.value as AlertType | "todas")} value={props.type}>
        {alertTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
      </select>
      <select className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm" onChange={(e) => props.setSeverity(e.target.value as Severity | "todas")} value={props.severity}>
        {severities.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
      </select>
    </div>
  );
}
