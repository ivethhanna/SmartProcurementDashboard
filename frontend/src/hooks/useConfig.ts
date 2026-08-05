import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAiStatus, fetchAlertThresholds, resetAlertThresholds, updateAlertThresholds } from "../services/api";

export function useAlertThresholds() {
  return useQuery({ queryKey: ["alert-thresholds"], queryFn: fetchAlertThresholds });
}

export function useUpdateAlertThresholds() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateAlertThresholds,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alert-thresholds"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
  });
}

export function useResetAlertThresholds() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: resetAlertThresholds,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alert-thresholds"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
  });
}

export function useAiStatus() {
  return useQuery({ queryKey: ["ai-status"], queryFn: fetchAiStatus });
}
