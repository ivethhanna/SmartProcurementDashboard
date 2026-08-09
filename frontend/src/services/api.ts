import axios from "axios";
import type { BranchAnomaly, DashboardSummary, ProviderOrderGroup, PurchaseAlert } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error("Falta configurar VITE_API_BASE_URL con la URL del backend");
}

export const api = axios.create({
  baseURL: API_BASE_URL,
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

export async function fetchReferenceData() {
  const response = await api.get<{
    sucursales: string[];
    ingredientes: Array<{ id: number; ingrediente_id: string; nombre: string; proveedor: string; unidad_base: string }>;
    proveedores: Array<{ id: number; nombre: string }>;
    unidades: string[];
    semanas: string[];
    tipos_formato: string[];
    formatos_compra: string[];
  }>("/api/data/reference");
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

export type CreateDatasetRowResponse = Record<string, unknown> & {
  status?: "created" | "updated";
};

export async function createDatasetRow(dataset: string, payload: Record<string, unknown>) {
  const response = await api.post<CreateDatasetRowResponse>(`/api/data/${dataset}`, payload);
  return response.data;
}

export async function updateDatasetRow(dataset: string, rowId: number, payload: Record<string, unknown>) {
  const response = await api.put<Record<string, unknown>>(`/api/data/${dataset}/${rowId}`, payload);
  return response.data;
}

export async function deleteDatasetRow(dataset: string, rowId: number) {
  const response = await api.delete<{ status: string }>(`/api/data/${dataset}/${rowId}`);
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

export interface ChatMessagePayload {
  role: "user" | "assistant";
  text: string;
}

export async function askAiChat(payload: string | { pregunta: string; historial?: ChatMessagePayload[] }) {
  const body = typeof payload === "string" ? { pregunta: payload } : payload;
  const response = await api.post<{ respuesta: string; ai_configurada: boolean }>("/api/chat", body);
  return response.data;
}

export async function generateAiSummary(alertas: PurchaseAlert[]) {
  const response = await api.post<{ summary: string; ai_configurada: boolean }>("/api/summary-ai", { alertas });
  return response.data;
}

export async function fetchAlertThresholds() {
  const response = await api.get<{
    porcentaje_diferencia_severidad_alta: number;
    porcentaje_diferencia_severidad_media: number;
    multiplicador_perecedero: number;
  }>("/api/config/alerts-thresholds");
  return response.data;
}

export async function updateAlertThresholds(payload: {
  porcentaje_diferencia_severidad_alta: number;
  porcentaje_diferencia_severidad_media: number;
  multiplicador_perecedero: number;
}) {
  const response = await api.put("/api/config/alerts-thresholds", payload);
  return response.data;
}

export async function resetAlertThresholds() {
  const response = await api.post("/api/config/alerts-thresholds/reset");
  return response.data;
}

export async function fetchAiStatus() {
  const response = await api.get<{
    proveedor: string;
    key_configurada: boolean;
    modelo: string;
    llamadas_hoy: number;
    limite_diario_conocido: number;
    ultima_llamada_exitosa: string | null;
    ultimo_error: string | null;
  }>("/api/config/ai-status");
  return response.data;
}
