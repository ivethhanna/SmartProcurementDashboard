import { Download, PackageCheck, Radar } from "lucide-react";
import { useMemo } from "react";
import { ConsumptionTrendChart } from "../components/charts/ConsumptionTrendChart";
import { EmptyState } from "../components/common/EmptyState";
import { SectionCard } from "../components/common/SectionCard";
import { useAlerts } from "../hooks/useAlerts";
import { useDataset } from "../hooks/useDatasets";
import { useAnomalies, useConsumptionDataset, useOrdersByProvider } from "../hooks/useRecommendations";
import { correctedOrderExportUrl } from "../services/api";
import type { PurchaseAlert } from "../types";

export default function Recommendations() {
  const anomaliesQuery = useAnomalies();
  const groupsQuery = useOrdersByProvider();
  const consumptionQuery = useConsumptionDataset();
  const ingredientsQuery = useDataset("ingredients");
  const alertsQuery = useAlerts({});

  const trendPoints = useMemo(
    () => buildTrendPoints(alertsQuery.data ?? [], ingredientsQuery.data ?? [], consumptionQuery.data ?? []),
    [alertsQuery.data, ingredientsQuery.data, consumptionQuery.data],
  );

  const groups = groupsQuery.data ?? [];
  const anomalies = anomaliesQuery.data ?? [];

  return (
    <main className="bg-white">
      <div className="mx-auto max-w-[1440px] px-4 py-6 lg:px-6">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recomendaciones</p>
            <h1 className="mt-2 text-2xl font-semibold text-slate-950">Pedido corregido</h1>
            <p className="mt-1 text-sm text-slate-600">Anomalias entre sucursales y orden consolidada por proveedor.</p>
          </div>
          <a
            className="inline-flex h-9 items-center gap-2 rounded-md bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            href={correctedOrderExportUrl()}
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            Exportar Excel
          </a>
        </div>

        <div className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
          <SectionCard title="Anomalias detectadas">
            {anomaliesQuery.isLoading ? (
              <div className="h-40 animate-pulse rounded-md bg-slate-50" />
            ) : anomalies.length ? (
              <div className="space-y-3">
                {anomalies.map((anomaly) => (
                  <article className="rounded-md border border-slate-200 bg-white p-3" key={`${anomaly.sucursal}-${anomaly.ingrediente}`}>
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-slate-950">{anomaly.sucursal}</p>
                      <span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 ring-1 ring-blue-200">
                        {anomaly.ratio_vs_mediana}x
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{anomaly.mensaje}</p>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState title="Sin anomalias" description="No hay pedidos fuera de patron entre sucursales." />
            )}
          </SectionCard>

          <section className="space-y-6">
            <ConsumptionTrendChart points={trendPoints} />

            <SectionCard
              action={
                <span className="inline-flex items-center gap-2 text-xs text-slate-500">
                  <PackageCheck className="h-4 w-4" aria-hidden="true" />
                  {groups.length} proveedores
                </span>
              }
              title="Orden agrupada por proveedor"
            >
              {groupsQuery.isLoading ? (
                <div className="h-56 animate-pulse rounded-md bg-slate-50" />
              ) : groups.length ? (
                <div className="divide-y divide-slate-200">
                  {groups.map((group) => (
                    <details key={group.proveedor} open={groups.length <= 3}>
                      <summary className="flex cursor-pointer items-center justify-between py-3 text-sm font-semibold text-slate-950">
                        {group.proveedor}
                        <span className="text-xs font-medium text-slate-500">{group.items.length} items</span>
                      </summary>
                      <div className="overflow-x-auto pb-3">
                        <table className="min-w-full text-left text-sm">
                          <thead className="text-xs text-slate-500">
                            <tr>
                              <th className="py-2 pr-4 font-medium">Sucursal</th>
                              <th className="py-2 pr-4 font-medium">Ingrediente</th>
                              <th className="py-2 pr-4 font-medium">Formatos</th>
                              <th className="py-2 pr-4 font-medium">Unidad base</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {group.items.map((item) => (
                              <tr key={`${item.sucursal}-${item.ingrediente_id}`}>
                                <td className="py-2 pr-4 text-slate-700">{item.sucursal}</td>
                                <td className="py-2 pr-4 text-slate-700">{item.ingrediente}</td>
                                <td className="py-2 pr-4 font-medium text-slate-950">
                                  {item.cantidad_formatos_corregida} x {item.formato_compra}
                                </td>
                                <td className="py-2 pr-4 text-slate-700">
                                  {item.cantidad_unidad_base_corregida} {item.unidad}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </details>
                  ))}
                </div>
              ) : (
                <EmptyState title="Sin pedido corregido" description="No hay items agrupados por proveedor." />
              )}
            </SectionCard>
          </section>
        </div>
      </div>
    </main>
  );
}

function buildTrendPoints(alerts: PurchaseAlert[], ingredients: Record<string, unknown>[], rows: Record<string, unknown>[]) {
  const alert = alerts[0];
  if (!alert) return [];
  const ingredient = ingredients.find((row) => row.name === alert.ingrediente);
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

