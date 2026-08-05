import { FormEvent, useState } from "react";
import type { ColumnConfig } from "../../config/datasetSchemas";
import { buildCreatePayload } from "../../config/datasetSchemas";
import { useCreateDatasetRow } from "../../hooks/useDatasets";

interface ManualEntryFormProps {
  dataset: string;
  columns: ColumnConfig[];
  onSuccess?: () => void;
}

function readableError(error: unknown) {
  if (typeof error === "object" && error !== null && "response" in error) {
    const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail;
    if (detail) return detail;
  }
  return "No se pudo guardar la fila.";
}

export function ManualEntryForm({ dataset, columns, onSuccess }: ManualEntryFormProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const mutation = useCreateDatasetRow(dataset);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage(null);
    try {
      await mutation.mutateAsync(buildCreatePayload(dataset, values));
      setValues({});
      setMessage("Fila guardada.");
      onSuccess?.();
    } catch (error) {
      setMessage(readableError(error));
    }
  }

  return (
    <form className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" onSubmit={submit}>
      <div className="grid gap-4 md:grid-cols-2">
        {columns.map((field) => (
          <FieldEditor
            field={field}
            key={field.key}
            onChange={(value) => setValues((current) => ({ ...current, [field.key]: value }))}
            value={values[field.key] ?? ""}
          />
        ))}
        {dataset === "ingredients" && values.proveedor === "__new__" && (
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Nuevo proveedor</span>
            <input
              className="mt-1 h-10 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              onChange={(event) => setValues((current) => ({ ...current, proveedor_nuevo: event.target.value }))}
              required
              value={values.proveedor_nuevo ?? ""}
            />
          </label>
        )}
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

function FieldEditor({ field, value, onChange }: { field: ColumnConfig; value: string; onChange: (value: string) => void }) {
  const inputClass = "mt-1 h-10 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{field.label}</span>
      {field.type === "select" || field.type === "boolean" ? (
        <select className={inputClass} onChange={(event) => onChange(event.target.value)} required={field.required} value={value}>
          <option value="">Seleccionar</option>
          {(field.type === "boolean" ? [{ value: "true", label: "Si" }, { value: "false", label: "No" }] : field.options ?? []).map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      ) : (
        <input
          className={inputClass}
          min={field.type === "number" ? 0 : undefined}
          onChange={(event) => onChange(event.target.value)}
          required={field.required}
          type={field.type === "number" ? "number" : "text"}
          value={value}
        />
      )}
    </label>
  );
}
