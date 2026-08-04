import { FormEvent, useMemo, useState } from "react";
import { useCreateDatasetRow } from "../../hooks/useDatasets";

const DATASET_FIELDS: Record<string, string[]> = {
  ingredients: ["ingrediente_id", "nombre", "proveedor", "unidad_base", "formato_compra", "unidad_base_por_formato", "es_perecedero", "costo_unitario_estimado"],
  inventory: ["sucursal", "ingrediente_id", "stock_actual_unidad_base"],
  consumption: ["sucursal", "ingrediente_id", "semana", "consumo_unidad_base"],
  purchase_orders: ["sucursal", "ingrediente_id", "cantidad_formatos"],
};

interface ManualEntryFormProps {
  dataset: string;
}

function readableError(error: unknown) {
  if (typeof error === "object" && error !== null && "response" in error) {
    const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail;
    if (detail) return detail;
  }
  return "No se pudo guardar la fila.";
}

export function ManualEntryForm({ dataset }: ManualEntryFormProps) {
  const fields = useMemo(() => DATASET_FIELDS[dataset] ?? [], [dataset]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const mutation = useCreateDatasetRow(dataset);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage(null);
    try {
      await mutation.mutateAsync(values);
      setValues({});
      setMessage("Fila guardada.");
    } catch (error) {
      setMessage(readableError(error));
    }
  }

  return (
    <form className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" onSubmit={submit}>
      <div className="grid gap-4 md:grid-cols-2">
        {fields.map((field) => (
          <label className="block" key={field}>
            <span className="text-sm font-medium text-slate-700">{field}</span>
            <input
              className="mt-1 h-10 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))}
              value={values[field] ?? ""}
            />
          </label>
        ))}
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          className="h-10 rounded-md bg-slate-950 px-4 text-sm font-medium text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
          disabled={mutation.isPending}
          type="submit"
        >
          {mutation.isPending ? "Guardando..." : "Guardar fila"}
        </button>
        {message && <p className="text-sm text-slate-600">{message}</p>}
      </div>
    </form>
  );
}

