import { ArrowDownUp, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { ColumnConfig } from "../../config/datasetSchemas";
import { EmptyState } from "../common/EmptyState";

interface EditableTableProps {
  rows: Record<string, unknown>[];
  editable?: boolean;
  isLoading?: boolean;
  columns?: ColumnConfig[];
  onSave?: (rowId: number, patch: Record<string, unknown>) => Promise<void>;
  onDelete?: (rowId: number) => Promise<void>;
}

export function EditableTable({ rows, editable = false, isLoading = false, columns: configuredColumns, onSave, onDelete }: EditableTableProps) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [draftRows, setDraftRows] = useState(rows);
  const [savingCell, setSavingCell] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);

  useEffect(() => {
    setDraftRows(rows);
    setMessage(null);
  }, [rows]);
  const columns = useMemo<ColumnConfig[]>(
    () => configuredColumns ?? Object.keys(rows[0] ?? {}).slice(0, 8).map((key) => ({ key, label: key, type: "text" })),
    [configuredColumns, rows],
  );

  const visibleRows = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const filtered = normalized
      ? draftRows.filter((row) => Object.values(row).some((value) => String(value ?? "").toLowerCase().includes(normalized)))
      : draftRows;
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => String(a[sortKey] ?? "").localeCompare(String(b[sortKey] ?? "")));
  }, [draftRows, query, sortKey]);

  async function saveCell(row: Record<string, unknown>, column: string) {
    if (!editable || !onSave || column === "id") return;
    const rowId = Number(row.id);
    if (!Number.isFinite(rowId)) return;

    const original = rows.find((item) => item.id === row.id);
    const nextValue = row[column];
    if (String(original?.[column] ?? "") === String(nextValue ?? "")) return;

    const cellKey = `${rowId}-${column}`;
    setSavingCell(cellKey);
    setMessage(null);
    try {
      await onSave(rowId, { [column]: nextValue });
      setMessage("Cambio guardado.");
    } catch {
      setDraftRows(rows);
      setMessage("No se pudo guardar el cambio.");
    } finally {
      setSavingCell(null);
    }
  }

  if (isLoading) return <div className="h-72 animate-pulse rounded-lg border border-slate-200 bg-slate-50" />;
  if (!rows.length) return <EmptyState title="Sin filas" description="No hay datos disponibles para este dataset." />;

  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
        <Search className="h-4 w-4 text-slate-500" aria-hidden="true" />
        <input
          className="h-9 min-w-0 flex-1 border-none text-sm outline-none"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar en la tabla"
          value={query}
        />
      </div>
      <div className="max-h-[520px] overflow-auto">
        <table className="min-w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 bg-slate-50 text-xs text-slate-500">
            <tr>
              {columns.map((column) => (
                <th className="whitespace-nowrap border-b border-slate-200 px-3 py-2 font-medium" key={column.key}>
                  <button className="inline-flex items-center gap-1" onClick={() => setSortKey(column.key)} type="button">
                    {column.label}
                    <ArrowDownUp className="h-3 w-3" aria-hidden="true" />
                  </button>
                </th>
              ))}
              {editable && onDelete && <th className="w-12 border-b border-slate-200 px-3 py-2" />}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {visibleRows.map((row, rowIndex) => (
              <tr className="hover:bg-slate-50" key={String(row.id ?? rowIndex)}>
                {columns.map((column) => (
                  <td className="whitespace-nowrap px-3 py-2 text-slate-700" key={column.key}>
                    {editable && column.key !== "id" ? (
                      <CellEditor
                        column={column}
                        disabled={savingCell === `${Number(row.id)}-${column.key}`}
                        onBlur={() => saveCell(row, column.key)}
                        onChange={(value) =>
                          setDraftRows((current) =>
                            current.map((item) => (item.id === row.id ? { ...item, [column.key]: value } : item)),
                          )
                        }
                        value={row[column.key]}
                      />
                    ) : (
                      displayValue(row[column.key], column)
                    )}
                  </td>
                ))}
                {editable && onDelete && (
                  <td className="px-3 py-2 text-right">
                    <button
                      className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 hover:bg-red-50 hover:text-red-700"
                      onClick={() => setPendingDeleteId(Number(row.id))}
                      type="button"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editable && (
        <p className="border-t border-slate-200 px-4 py-2 text-xs text-slate-500">
          {message ?? "Los cambios se guardan al salir del campo."}
        </p>
      )}
      {pendingDeleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/30 px-4">
          <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-4 shadow-lg">
            <h3 className="text-sm font-semibold text-slate-950">Eliminar fila</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Esta accion no se puede deshacer. Confirma que quieres borrar este registro.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                onClick={() => setPendingDeleteId(null)}
                type="button"
              >
                Cancelar
              </button>
              <button
                className="h-9 rounded-md bg-red-700 px-3 text-sm font-medium text-white hover:bg-red-800"
                onClick={() => {
                  onDelete?.(pendingDeleteId).finally(() => setPendingDeleteId(null));
                }}
                type="button"
              >
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function displayValue(value: unknown, column: ColumnConfig) {
  if (column.type === "boolean") return value ? "Si" : "No";
  if (column.type === "select") return column.options?.find((option) => option.value === String(value))?.label ?? String(value ?? "");
  return String(value ?? "");
}

function CellEditor(props: {
  column: ColumnConfig;
  disabled?: boolean;
  value: unknown;
  onChange: (value: string | boolean) => void;
  onBlur: () => void;
}) {
  const common = "h-8 min-w-28 rounded-md border border-slate-200 bg-white px-2 text-sm outline-none focus:border-blue-500 disabled:opacity-60";
  if (props.column.type === "select" || props.column.type === "boolean") {
    const selectOptions = props.column.type === "boolean" ? [{ value: "true", label: "Si" }, { value: "false", label: "No" }] : props.column.options ?? [];
    return (
      <select
        className={common}
        disabled={props.disabled}
        onBlur={props.onBlur}
        onChange={(event) => props.onChange(props.column.type === "boolean" ? event.target.value === "true" : event.target.value)}
        value={props.column.type === "boolean" ? String(Boolean(props.value)) : String(props.value ?? "")}
      >
        {selectOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    );
  }
  return (
    <input
      className={common}
      disabled={props.disabled}
      min={props.column.type === "number" ? 0 : undefined}
      onBlur={props.onBlur}
      onChange={(event) => props.onChange(event.target.value)}
      onKeyDown={(event) => {
        if (event.key === "Enter") event.currentTarget.blur();
      }}
      type={props.column.type === "number" ? "number" : "text"}
      value={String(props.value ?? "")}
    />
  );
}
