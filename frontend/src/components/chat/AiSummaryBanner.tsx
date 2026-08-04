import { Sparkles } from "lucide-react";
import { useState } from "react";
import { useAiSummary } from "../../hooks/useAi";
import type { PurchaseAlert } from "../../types";

interface AiSummaryBannerProps {
  alerts: PurchaseAlert[];
}

export function AiSummaryBanner({ alerts }: AiSummaryBannerProps) {
  const [summary, setSummary] = useState<string | null>(null);
  const mutation = useAiSummary();

  async function generateSummary() {
    const response = await mutation.mutateAsync(alerts);
    setSummary(response.summary);
  }

  return (
    <section className="rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="rounded-md bg-white p-2 text-blue-700 ring-1 ring-blue-200">
          <Sparkles className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-950">Resumen ejecutivo</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {summary ?? "Genera una lectura breve de prioridades antes de aprobar compras."}
          </p>
          {mutation.isError && <p className="mt-2 text-sm text-red-700">No se pudo generar el resumen.</p>}
          <button
            className="mt-3 h-9 rounded-md bg-blue-700 px-3 text-sm font-medium text-white hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
            disabled={mutation.isPending}
            onClick={generateSummary}
            type="button"
          >
            {mutation.isPending ? "Generando..." : "Generar resumen"}
          </button>
        </div>
      </div>
    </section>
  );
}

