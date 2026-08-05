import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createDatasetRow, deleteDatasetRow, fetchDataset, resetData, updateDatasetRow, uploadDatasetCsv } from "../services/api";

function invalidateProcurementViews(queryClient: ReturnType<typeof useQueryClient>, dataset?: string) {
  if (dataset) queryClient.invalidateQueries({ queryKey: ["dataset", dataset] });
  queryClient.invalidateQueries({ queryKey: ["alerts"] });
  queryClient.invalidateQueries({ queryKey: ["summary"] });
  queryClient.invalidateQueries({ queryKey: ["orders-by-provider"] });
  queryClient.invalidateQueries({ queryKey: ["anomalies"] });
  queryClient.invalidateQueries({ queryKey: ["reference-data"] });
}

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
      invalidateProcurementViews(queryClient, dataset);
    },
  });
}

export function useCreateDatasetRow(dataset: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => createDatasetRow(dataset, payload),
    onSuccess: () => {
      invalidateProcurementViews(queryClient, dataset);
    },
  });
}

export function useUpdateDatasetRow(dataset: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ rowId, payload }: { rowId: number; payload: Record<string, unknown> }) =>
      updateDatasetRow(dataset, rowId, payload),
    onSuccess: () => {
      invalidateProcurementViews(queryClient, dataset);
    },
  });
}

export function useDeleteDatasetRow(dataset: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rowId: number) => deleteDatasetRow(dataset, rowId),
    onSuccess: () => {
      invalidateProcurementViews(queryClient, dataset);
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
