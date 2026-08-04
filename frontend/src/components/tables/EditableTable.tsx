import { ArrowDownUp, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "../common/EmptyState";

interface EditableTableProps {
  rows: Record<string, unknown>[];
  editable?: boolean;
  isLoading?: boolean;
}

export function EditableTable({ rows, editable = false, isLoading = false }: EditableTableProps) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [draftRows, setDraftRows] = useState(rows);

  useEffect(() => setDraftRows(rows), [rows]);
  const columns = useMemo(() => Object.keys(rows[0] ?? {}).slice(0, 8), [rows]);

  const visibleRows = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const filtered = normalized
      ? draftRows.filter((row) => Object.values(row).some((value) => String(value ?? "").toLowerCase().includes(normalized)))
      : draftRows;
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => String(a[sortKey] ?? "").localeCompare(String(b[sortKey] ?? "")));
  }, [draftRows, query, sortKey]);

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
                <th className="whitespace-nowrap border-b border-slate-200 px-3 py-2 font-medium" key={column}>
                  <button className="inline-flex items-center gap-1" onClick={() => setSortKey(column)} type="button">
                    {column}
                    <ArrowDownUp className="h-3 w-3" aria-hidden="true" />
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {visibleRows.map((row, rowIndex) => (
              <tr className="hover:bg-slate-50" key={String(row.id ?? rowIndex)}>
                {columns.map((column) => (
                  <td className="whitespace-nowrap px-3 py-2 text-slate-700" key={column}>
                    {editable && column !== "id" ? (
                      <input
                        className="h-8 min-w-28 rounded-md border border-transparent bg-transparent px-2 text-sm outline-none focus:border-blue-500 focus:bg-white"
                        onChange={(event) =>
                          setDraftRows((current) =>
                            current.map((item) => (item.id === row.id ? { ...item, [column]: event.target.value } : item)),
                          )
                        }
                        value={String(row[column] ?? "")}
                      />
                    ) : (
                      String(row[column] ?? "")
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editable && (
        <p className="border-t border-slate-200 px-4 py-2 text-xs text-slate-500">
          Los cambios editados quedan pendientes en esta vista.
        </p>
      )}
    </div>
  );
}
