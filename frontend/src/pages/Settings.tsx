import { useEffect, useState } from "react";
import { SectionCard } from "../components/common/SectionCard";
import { useAiStatus, useAlertThresholds, useResetAlertThresholds, useUpdateAlertThresholds } from "../hooks/useConfig";
import { useDisplayPreferences } from "../hooks/useDisplayPreferences";

interface SettingsProps {
  onNavigate?: (page: string) => void;
}

export default function Settings({ onNavigate }: SettingsProps) {
  const thresholdsQuery = useAlertThresholds();
  const updateThresholds = useUpdateAlertThresholds();
  const resetThresholds = useResetAlertThresholds();
  const aiStatus = useAiStatus();
  const { prefs, updatePrefs } = useDisplayPreferences();
  const [thresholds, setThresholds] = useState({
    porcentaje_diferencia_severidad_alta: 0.5,
    porcentaje_diferencia_severidad_media: 0.15,
    multiplicador_perecedero: 2,
  });

  useEffect(() => {
    if (thresholdsQuery.data) setThresholds(thresholdsQuery.data);
  }, [thresholdsQuery.data]);

  const exampleRatio = 12 / 40;
  const exampleSeverity =
    exampleRatio >= thresholds.porcentaje_diferencia_severidad_alta
      ? "alta"
      : exampleRatio >= thresholds.porcentaje_diferencia_severidad_media
        ? "media"
        : "baja";
  const usage = aiStatus.data;

  return (
    <main className="bg-white">
      <div className="mx-auto max-w-[1100px] px-4 py-6 lg:px-6">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ajustes</p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-950">Configuracion</h1>
        </div>

        <div className="space-y-6">
          <SectionCard title="Umbrales de severidad">
            <div className="grid gap-4 md:grid-cols-3">
              <NumberField label="Alta desde" value={thresholds.porcentaje_diferencia_severidad_alta} onChange={(value) => setThresholds((current) => ({ ...current, porcentaje_diferencia_severidad_alta: value }))} />
              <NumberField label="Media desde" value={thresholds.porcentaje_diferencia_severidad_media} onChange={(value) => setThresholds((current) => ({ ...current, porcentaje_diferencia_severidad_media: value }))} />
              <NumberField label="Multiplicador perecedero" value={thresholds.multiplicador_perecedero} onChange={(value) => setThresholds((current) => ({ ...current, multiplicador_perecedero: value }))} />
            </div>
            <p className="mt-3 text-sm text-slate-600">
              Ejemplo: una diferencia de 12 kg en una necesidad de 40 kg equivale a 30% y seria severidad <span className="font-semibold">{exampleSeverity}</span>.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="h-9 rounded-md bg-slate-950 px-3 text-sm font-medium text-white" onClick={() => updateThresholds.mutate(thresholds)} type="button">Guardar cambios</button>
              <button className="h-9 rounded-md border border-slate-200 px-3 text-sm font-medium text-slate-700" onClick={() => resetThresholds.mutate()} type="button">Restaurar valores por defecto</button>
            </div>
          </SectionCard>

          <SectionCard title="Conexion IA">
            <div className="space-y-3">
              <p className="text-sm text-slate-700">{usage?.key_configurada ? "Key configurada" : "Key no configurada"} · Modelo: {usage?.modelo ?? "N/D"}</p>
              <progress
                className="h-2 w-full overflow-hidden rounded-full accent-blue-700"
                max={usage?.limite_diario_conocido || 1}
                value={usage?.llamadas_hoy ?? 0}
              />
              <p className="text-xs text-slate-500">
                {usage?.llamadas_hoy ?? 0} / {usage?.limite_diario_conocido ?? 0} llamadas hoy. Conteo local aproximado, no cuota oficial de Google.
              </p>
              {usage?.ultimo_error && <p className="text-sm text-red-700">Ultimo error: {usage.ultimo_error}</p>}
            </div>
          </SectionCard>

          <SectionCard title="Preferencias de visualizacion">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Alertas por pagina</span>
                <select className="mt-1 h-10 w-full rounded-md border border-slate-200 px-3 text-sm" value={prefs.alertsPerPage} onChange={(event) => updatePrefs({ alertsPerPage: event.target.value === "all" ? "all" : Number(event.target.value) as 10 | 25 | 50 })}>
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value="all">Todas</option>
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Orden por defecto</span>
                <select className="mt-1 h-10 w-full rounded-md border border-slate-200 px-3 text-sm" value={prefs.defaultSort} onChange={(event) => updatePrefs({ defaultSort: event.target.value as typeof prefs.defaultSort })}>
                  <option value="severidad">Severidad</option>
                  <option value="impacto">$ impacto</option>
                  <option value="sucursal">Sucursal</option>
                  <option value="ingrediente">Ingrediente</option>
                </select>
              </label>
            </div>
          </SectionCard>

          <SectionCard title="Costos unitarios">
            <p className="text-sm text-slate-600">Los costos unitarios se editan desde Datos &gt; Ingredientes para evitar duplicar campos.</p>
            <button className="mt-3 h-9 rounded-md border border-slate-200 px-3 text-sm font-medium text-slate-700" onClick={() => onNavigate?.("upload")} type="button">Ir a Datos</button>
          </SectionCard>
        </div>
      </div>
    </main>
  );
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <input className="mt-1 h-10 w-full rounded-md border border-slate-200 px-3 text-sm" min={0.01} step={0.01} type="number" value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}
