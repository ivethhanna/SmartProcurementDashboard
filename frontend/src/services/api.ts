import axios from "axios";
import type { BranchAnomaly, DashboardSummary, ProviderOrderGroup, PurchaseAlert } from "../types";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
});

export interface AlertFilters {
  sucursal?: string;
  tipo?: string;
  severidad?: string;
}

export async function fetchAlerts(filters: AlertFilters = {}) {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value && value !== "todas"),
  );
  const response = await api.get<PurchaseAlert[]>("/api/alerts", { params });
  return response.data;
}

export async function fetchDashboardSummary() {
  const response = await api.get<DashboardSummary>("/api/summary");
  return response.data;
}

export async function fetchDataset(dataset: string) {
  const response = await api.get<Record<string, unknown>[]>(`/api/data/${dataset}`);
  return response.data;
}

export async function uploadDatasetCsv(dataset: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<{ status: string; rows: number }>(`/api/data/${dataset}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function resetData() {
  const response = await api.post<{ status: string }>("/api/data/reset");
  return response.data;
}

export async function createDatasetRow(dataset: string, payload: Record<string, unknown>) {
  const response = await api.post<Record<string, unknown>>(`/api/data/${dataset}`, payload);
  return response.data;
}

export async function fetchAnomalies() {
  const response = await api.get<BranchAnomaly[]>("/api/anomalies");
  return response.data;
}

export async function fetchOrdersByProvider() {
  const response = await api.get<ProviderOrderGroup[]>("/api/orders-by-provider");
  return response.data;
}

export function correctedOrderExportUrl() {
  return `${api.defaults.baseURL}/api/export/pedido-corregido`;
}

export async function askAiChat(pregunta: string) {
  const response = await api.post<{ respuesta: string; ai_configurada: boolean }>("/api/chat", { pregunta });
  return response.data;
}

export async function generateAiSummary(alertas: PurchaseAlert[]) {
  const response = await api.post<{ summary: string; ai_configurada: boolean }>("/api/summary-ai", { alertas });
  return response.data;
}
