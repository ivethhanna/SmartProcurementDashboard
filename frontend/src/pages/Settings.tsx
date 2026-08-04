import { EditableTable } from "../components/tables/EditableTable";
import { useDataset } from "../hooks/useDatasets";

export default function Settings() {
  const ingredientsQuery = useDataset("ingredients");
  const rows = (ingredientsQuery.data ?? []).map((row) => ({
    id: row.id,
    ingrediente: row.name,
    unidad_base: row.base_unit,
    costo_unitario_estimado: row.estimated_unit_cost,
    perecedero: row.is_perishable,
  }));

  return (
    <main className="bg-white">
      <div className="mx-auto max-w-[1440px] px-4 py-6 lg:px-6">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ajustes</p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-950">Configuracion</h1>
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section>
            <h2 className="mb-3 text-sm font-semibold text-slate-950">Costos unitarios</h2>
            <EditableTable editable isLoading={ingredientsQuery.isLoading} rows={rows} />
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-950">Conexion IA</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              La API key se valida desde el backend cuando se usa el resumen ejecutivo o el chat.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
