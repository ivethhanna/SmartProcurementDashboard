export type Severity = "alta" | "media" | "baja";

export type AlertType = "quiebre" | "sobre_pedido" | "olvidado";

export interface HistoricalExplanationPoint {
  semana: string;
  consumo: number;
  descartado_outlier: boolean;
}

export interface AlertExplanation {
  consumo_historico_usado: HistoricalExplanationPoint[];
  consumo_proyectado: number;
  inventario_actual: number;
  necesidad_real: number;
  orden_recibida_formatos: number;
  orden_recibida_unidad_base: number;
  tolerancia_redondeo_aplicada: number;
  tendencia?: "creciente" | "estable" | "decreciente";
  confianza?: "alta" | "media" | "baja";
}

export interface PurchaseAlert {
  sucursal: string;
  ingrediente_id: string;
  ingrediente: string;
  tipo: AlertType;
  severidad: Severity;
  cantidad_diferencia: number;
  unidad: string;
  impacto_dinero: number;
  es_perecedero: boolean;
  mensaje: string;
  explicacion: AlertExplanation;
}

export interface DashboardSummary {
  total_alertas: number;
  dinero_en_riesgo_total: number;
  sucursal_mas_critica: string | null;
  health_scores: Record<string, number>;
  ultima_actualizacion: string | null;
}

export interface BranchAnomaly {
  sucursal: string;
  ingrediente_id: string;
  ingrediente: string;
  unidad: string;
  orden_unidad_base: number;
  tipo: "alta" | "baja";
  mediana_otras_sucursales: number;
  ratio_vs_mediana: number;
  mensaje: string;
}

export interface ProviderOrderItem {
  sucursal: string;
  ingrediente_id: string;
  ingrediente: string;
  unidad: string;
  formato_compra: string;
  cantidad_formatos_corregida: number;
  cantidad_unidad_base_corregida: number;
  consumo_proyectado: number;
  inventario_actual: number;
  necesidad_real: number;
}

export interface ProviderOrderGroup {
  proveedor: string;
  items: ProviderOrderItem[];
}
