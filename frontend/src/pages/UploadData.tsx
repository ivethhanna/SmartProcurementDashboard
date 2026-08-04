import { useState } from "react";
import { EditableTable } from "../components/tables/EditableTable";
import { CsvUploadZone } from "../components/upload/CsvUploadZone";
import { useDataset, useResetData, useUploadDataset } from "../hooks/useDatasets";

const DATASETS = [
  { key: "ingredients", label: "Ingredientes" },
  { key: "inventory", label: "Inventario" },
  { key: "consumption", label: "Consumo" },
  { key: "purchase_orders", label: "Ordenes" },
];

export default function UploadData() {
  const [dataset, setDataset] = useState(DATASETS[0].key);
  const [message, setMessage] = useState<string | null>(null);
  const datasetQuery = useDataset(dataset);
  const uploadMutation = useUploadDataset(dataset);
  const resetMutation = useResetData();

  async function upload(file: File) {
    const result = await uploadMutation.mutateAsync(file);
    setMessage(`${result.rows} filas cargadas.`);
  }

  async function restoreOriginals() {
    await resetMutation.mutateAsync();
    setMessage("Datos originales restaurados.");
  }

  return (
    <main className="bg-white">
      <div className="mx-auto max-w-[1440px] px-4 py-6 lg:px-6">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Carga de datos</p>
            <h1 className="mt-2 text-2xl font-semibold text-slate-950">Datasets semanales</h1>
          </div>
          <button
            className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
            disabled={resetMutation.isPending}
            onClick={restoreOriginals}
            type="button"
          >
            Restaurar datos originales
          </button>
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

        <div className="space-y-4">
          <CsvUploadZone onUpload={upload} />
          {(message || datasetQuery.error || uploadMutation.error || resetMutation.error) && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {message ?? "No se pudo completar la operacion."}
            </div>
          )}
          <div>
            <h2 className="mb-3 text-sm font-semibold text-slate-950">Datos cargados</h2>
            <EditableTable editable isLoading={datasetQuery.isLoading} rows={datasetQuery.data ?? []} />
          </div>
        </div>
      </div>
    </main>
  );
}
