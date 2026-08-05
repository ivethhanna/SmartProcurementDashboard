import type { PurchaseAlert } from "../../types";
import { useDisplayPreferences } from "../../hooks/useDisplayPreferences";
import { EmptyState } from "../common/EmptyState";
import { LoadingState } from "../common/LoadingState";
import { AlertCard } from "../dashboard/AlertCard";

interface AlertsListProps {
  alerts: PurchaseAlert[];
  isLoading?: boolean;
}

export function AlertsList({ alerts, isLoading = false }: AlertsListProps) {
  const { prefs } = useDisplayPreferences();
  if (isLoading) return <LoadingState rows={3} />;

  if (!alerts.length) {
    return (
      <EmptyState
        title="No hay alertas para estos filtros"
        description="La orden actual esta dentro de los rangos esperados."
      />
    );
  }

  const severityRank = { alta: 3, media: 2, baja: 1 };
  const sortedAlerts = [...alerts].sort((a, b) => {
    if (prefs.defaultSort === "impacto") return b.impacto_dinero - a.impacto_dinero;
    if (prefs.defaultSort === "sucursal") return a.sucursal.localeCompare(b.sucursal);
    if (prefs.defaultSort === "ingrediente") return a.ingrediente.localeCompare(b.ingrediente);
    return severityRank[b.severidad] - severityRank[a.severidad];
  });
  const visibleAlerts = prefs.alertsPerPage === "all" ? sortedAlerts : sortedAlerts.slice(0, prefs.alertsPerPage);

  return (
    <div className="space-y-3">
      {visibleAlerts.map((alert, index) => (
        <AlertCard alert={alert} key={`${alert.sucursal}-${alert.ingrediente}-${alert.tipo}-${index}`} />
      ))}
      {visibleAlerts.length < alerts.length && (
        <p className="text-xs text-slate-500">Mostrando {visibleAlerts.length} de {alerts.length} alertas.</p>
      )}
    </div>
  );
}
