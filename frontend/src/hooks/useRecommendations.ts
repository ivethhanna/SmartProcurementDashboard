import { useQuery } from "@tanstack/react-query";
import { fetchAnomalies, fetchDataset, fetchOrdersByProvider } from "../services/api";

export function useAnomalies() {
  return useQuery({
    queryKey: ["anomalies"],
    queryFn: fetchAnomalies,
  });
}

export function useOrdersByProvider() {
  return useQuery({
    queryKey: ["orders-by-provider"],
    queryFn: fetchOrdersByProvider,
  });
}

export function useConsumptionDataset() {
  return useQuery({
    queryKey: ["dataset", "consumption"],
    queryFn: () => fetchDataset("consumption"),
  });
}

