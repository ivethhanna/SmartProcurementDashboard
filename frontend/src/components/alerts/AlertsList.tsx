import type { PurchaseAlert } from "../../types";
import { EmptyState } from "../common/EmptyState";
import { LoadingState } from "../common/LoadingState";
import { AlertCard } from "../dashboard/AlertCard";

interface AlertsListProps {
  alerts: PurchaseAlert[];
  isLoading?: boolean;
}

export function AlertsList({ alerts, isLoading = false }: AlertsListProps) {
  if (isLoading) return <LoadingState rows={3} />;

  if (!alerts.length) {
    return (
      <EmptyState
        title="No hay alertas para estos filtros"
        description="La orden actual esta dentro de los rangos esperados."
      />
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert, index) => (
        <AlertCard alert={alert} key={`${alert.sucursal}-${alert.ingrediente}-${alert.tipo}-${index}`} />
      ))}
    </div>
  );
}

