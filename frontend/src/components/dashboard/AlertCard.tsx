import { ChevronDown, Info, PackageMinus, PackagePlus } from "lucide-react";
import { useState } from "react";
import type { AlertType, PurchaseAlert, Severity } from "../../types";
import { preciseCurrencyFormatter } from "../../utils/formatters";

interface AlertCardProps {
  alert: PurchaseAlert;
}

const severityClasses: Record<Severity, string> = {
  alta: "border-l-red-600 bg-red-50/30",
  media: "border-l-amber-500 bg-amber-50/30",
  baja: "border-l-blue-500 bg-blue-50/30",
};

const typeMeta: Record<AlertType, { label: string; icon: typeof Info; badge: string }> = {
  quiebre: { label: "Quiebre", icon: PackageMinus, badge: "bg-red-50 text-red-700 ring-red-200" },
  sobre_pedido: { label: "Sobre pedido", icon: PackagePlus, badge: "bg-amber-50 text-amber-700 ring-amber-200" },
  olvidado: { label: "Olvidado", icon: Info, badge: "bg-blue-50 text-blue-700 ring-blue-200" },
};

export function AlertCard({ alert }: AlertCardProps) {
  const [open, setOpen] = useState(false);
  const meta = typeMeta[alert.tipo];
  const Icon = meta.icon;

  return (
    <article className={`rounded-lg border border-l-4 border-slate-200 bg-white shadow-sm ${severityClasses[alert.severidad]}`}>
      <div className="p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium ring-1 ${meta.badge}`}>
                <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                {meta.label}
              </span>
              <span className="rounded-md bg-white px-2 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200">
                Severidad {alert.severidad}
              </span>
              {alert.es_perecedero && (
                <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
                  Perecedero
                </span>
              )}
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-900">{alert.mensaje}</p>
          </div>
          <div className="grid grid-cols-2 gap-4 text-left lg:min-w-52 lg:text-right">
            <div>
              <p className="text-xs text-slate-500">Impacto</p>
              <p className="text-sm font-semibold text-slate-950">{preciseCurrencyFormatter.format(alert.impacto_dinero)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Diferencia</p>
              <p className="text-sm font-semibold text-slate-950">
                {alert.cantidad_diferencia} {alert.unidad}
              </p>
            </div>
          </div>
        </div>

        <button
          className="mt-4 inline-flex h-9 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          onClick={() => setOpen((value) => !value)}
          type="button"
        >
          Ver calculo
          <ChevronDown className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} aria-hidden="true" />
        </button>
      </div>

      {open && (
        <div className="border-t border-slate-200 bg-slate-50 p-4">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="Proyectado" value={`${alert.explicacion.consumo_proyectado} ${alert.unidad}`} />
            <Metric label="Inventario" value={`${alert.explicacion.inventario_actual} ${alert.unidad}`} />
            <Metric label="Necesidad real" value={`${alert.explicacion.necesidad_real} ${alert.unidad}`} />
            <Metric label="Orden recibida" value={`${alert.explicacion.orden_recibida_formatos} formatos`} />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {alert.explicacion.consumo_historico_usado.map((point) => (
              <span
                className={`rounded-md px-2 py-1 text-xs ring-1 ${
                  point.descartado_outlier ? "bg-red-50 text-red-700 ring-red-200" : "bg-white text-slate-600 ring-slate-200"
                }`}
                key={point.semana}
              >
                {point.semana}: {point.consumo}
              </span>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}

