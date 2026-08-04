import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EmptyState } from "../common/EmptyState";

interface ConsumptionTrendChartProps {
  points: Array<{ semana: string; consumo: number; proyectado: number }>;
  title?: string;
}

export function ConsumptionTrendChart({ points, title = "Consumo proyectado vs. real" }: ConsumptionTrendChartProps) {
  if (!points.length) {
    return <EmptyState title="Sin tendencia disponible" description="No hay consumo historico suficiente para graficar." />;
  }

  return (
    <div className="h-72 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
        <span className="text-xs text-slate-500">Real / proyectado</span>
      </div>
      <ResponsiveContainer height="86%" width="100%">
        <LineChart data={points} margin={{ bottom: 0, left: -20, right: 12, top: 8 }}>
          <XAxis axisLine={false} dataKey="semana" fontSize={12} tickLine={false} />
          <YAxis axisLine={false} fontSize={12} tickLine={false} />
          <Tooltip />
          <Line dataKey="consumo" dot={false} stroke="#0f172a" strokeWidth={2} />
          <Line dataKey="proyectado" dot={false} stroke="#2563eb" strokeDasharray="4 4" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

