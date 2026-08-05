import { useState } from "react";
import { ManualEntryForm } from "../components/manual_forms/ManualEntryForm";
import { DATASETS, formColumns } from "../config/datasetSchemas";
import { useReferenceData } from "../hooks/useReferenceData";

export default function ManualEntry() {
  const [dataset, setDataset] = useState(DATASETS[3].key);
  const reference = useReferenceData();

  return (
    <main className="bg-white">
      <div className="mx-auto max-w-3xl px-4 py-6 lg:px-6">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Captura manual</p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-950">Agregar una fila</h1>
          <p className="mt-1 text-sm text-slate-600">Correcciones puntuales sin subir un CSV completo.</p>
        </div>

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
        />
      </div>
    </main>
  );
}
