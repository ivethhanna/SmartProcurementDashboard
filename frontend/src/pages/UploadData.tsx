import { useState } from "react";
import { PencilLine } from "lucide-react";
import { EditableTable } from "../components/tables/EditableTable";
import { CsvUploadZone } from "../components/upload/CsvUploadZone";
import { DATASETS, tableColumns } from "../config/datasetSchemas";
import { useDataset, useDeleteDatasetRow, useResetData, useUpdateDatasetRow, useUploadDataset } from "../hooks/useDatasets";
import { useReferenceData } from "../hooks/useReferenceData";

interface UploadDataProps {
  onNavigate?: (page: string) => void;
  onOpenManualEntry?: () => void;
}

export default function UploadData({ onOpenManualEntry }: UploadDataProps) {
  const [dataset, setDataset] = useState(DATASETS[0].key);
  const [message, setMessage] = useState<string | null>(null);
  const datasetQuery = useDataset(dataset);
  const uploadMutation = useUploadDataset(dataset);
  const updateMutation = useUpdateDatasetRow(dataset);
  const deleteMutation = useDeleteDatasetRow(dataset);
  const resetMutation = useResetData();
  const reference = useReferenceData();

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
          <div className="flex flex-wrap gap-2">
            <button
              className="inline-flex h-9 items-center gap-2 rounded-md bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={onOpenManualEntry}
              type="button"
            >
              <PencilLine className="h-4 w-4" aria-hidden="true" />
              Captura manual
            </button>
            <button
              className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
              disabled={resetMutation.isPending}
              onClick={restoreOriginals}
              type="button"
            >
              Restaurar datos originales
            </button>
          </div>
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
            <EditableTable
              columns={tableColumns(dataset, {
                sucursales: reference.sucursales,
                ingredientes: reference.ingredientes,
                proveedores: reference.proveedores,
                unidades: reference.unidades,
                semanas: reference.semanas,
                tiposFormato: reference.tiposFormato,
                formatosCompra: reference.formatosCompra,
              })}
              editable
              isLoading={datasetQuery.isLoading}
              onDelete={(rowId) => deleteMutation.mutateAsync(rowId).then(() => undefined)}
              onSave={(rowId, payload) => updateMutation.mutateAsync({ rowId, payload }).then(() => undefined)}
              rows={datasetQuery.data ?? []}
            />
          </div>
        </div>
      </div>
    </main>
  );
}
