import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { DATASETS, formColumns } from "../../config/datasetSchemas";
import { useReferenceData } from "../../hooks/useReferenceData";
import { ManualEntryForm } from "./ManualEntryForm";

interface ManualEntryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialDataset?: string;
}

export function ManualEntryModal({ open, onOpenChange, initialDataset = "purchase_orders" }: ManualEntryModalProps) {
  const [dataset, setDataset] = useState(initialDataset);
  const reference = useReferenceData();

  useEffect(() => {
    if (open) setDataset(initialDataset);
  }, [initialDataset, open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onOpenChange, open]);

  if (!open) return null;

  const datasetLabel = DATASETS.find((item) => item.key === dataset)?.label ?? dataset;

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-950/40 px-4 py-8"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onOpenChange(false);
      }}
      role="dialog"
    >
      <div className="w-full max-w-2xl rounded-lg bg-white shadow-xl">
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Captura manual</p>
            <h2 className="mt-1 text-lg font-semibold text-slate-950">{datasetLabel}</h2>
          </div>
          <button
            aria-label="Cerrar captura manual"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => onOpenChange(false)}
            type="button"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="px-5 py-4">
          <div className="mb-4 flex flex-wrap gap-2">
            {DATASETS.map((item) => (
              <button
                className={`rounded-md px-3 py-2 text-sm font-medium ${
                  dataset === item.key ? "bg-slate-950 text-white" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
                key={item.key}
                onClick={() => setDataset(item.key)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>

          <ManualEntryForm
            columns={formColumns(dataset, {
              sucursales: reference.sucursales,
              ingredientes: reference.ingredientes,
              proveedores: reference.proveedores,
              unidades: reference.unidades,
              semanas: reference.semanas,
              tiposFormato: reference.tiposFormato,
              formatosCompra: reference.formatosCompra,
            })}
            dataset={dataset}
            onSuccess={() => onOpenChange(false)}
          />
        </div>
      </div>
    </div>
  );
}
