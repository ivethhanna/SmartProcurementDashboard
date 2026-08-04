import { useQuery } from "@tanstack/react-query";
import { fetchAlerts, fetchDashboardSummary, type AlertFilters } from "../services/api";

export function useAlerts(filters: AlertFilters) {
  return useQuery({
    queryKey: ["alerts", filters],
    queryFn: () => fetchAlerts(filters),
  });
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["summary"],
    queryFn: fetchDashboardSummary,
  });
}

