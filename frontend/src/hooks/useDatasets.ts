import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createDatasetRow, fetchDataset, resetData, uploadDatasetCsv } from "../services/api";

export function useDataset(dataset: string) {
  return useQuery({
    queryKey: ["dataset", dataset],
    queryFn: () => fetchDataset(dataset),
  });
}

export function useUploadDataset(dataset: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadDatasetCsv(dataset, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dataset", dataset] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
  });
}

export function useCreateDatasetRow(dataset: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => createDatasetRow(dataset, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dataset", dataset] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
  });
}

export function useResetData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: resetData,
    onSuccess: () => queryClient.invalidateQueries(),
  });
}

export function useDatasets() {
  return { datasets: {}, isLoading: false };
}

