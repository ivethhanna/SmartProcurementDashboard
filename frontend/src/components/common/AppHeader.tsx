import { FilePlus2, PencilLine } from "lucide-react";
import { formatDateTime } from "../../utils/formatters";

interface AppHeaderProps {
  activePage: string;
  lastUpdated?: string | null;
  onNavigate: (page: string) => void;
}

const navItems = [
  { key: "dashboard", label: "Dashboard" },
  { key: "recommendations", label: "Recomendaciones" },
  { key: "upload", label: "Datos" },
  { key: "settings", label: "Ajustes" },
];

export function AppHeader({ activePage, lastUpdated, onNavigate }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-3 px-4 py-3 lg:flex-row lg:items-center lg:justify-between lg:px-6">
        <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center">
          <button className="flex items-center gap-2 text-left" onClick={() => onNavigate("dashboard")} type="button">
            <span className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 bg-white text-sm font-semibold text-red-700">
              BP
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-semibold text-slate-950">Barrio Pizza</span>
              <span className="block text-xs text-slate-500">Dashboard de Compras</span>
            </span>
          </button>
          <nav className="flex gap-1 overflow-x-auto sm:border-l sm:border-slate-200 sm:pl-3">
            {navItems.map((item) => (
              <button
                className={`rounded-md px-3 py-2 text-sm font-medium transition ${
                  activePage === item.key ? "bg-slate-100 text-slate-950" : "text-slate-600 hover:bg-slate-50"
                }`}
                key={item.key}
                onClick={() => onNavigate(item.key)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-2 text-xs text-slate-500">
            Ultima actualizacion: <span className="font-medium text-slate-700">{formatDateTime(lastUpdated)}</span>
          </span>
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => onNavigate("upload")}
            type="button"
          >
            <FilePlus2 className="h-4 w-4" aria-hidden="true" />
            Importar CSV
          </button>
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => onNavigate("manual")}
            type="button"
          >
            <PencilLine className="h-4 w-4" aria-hidden="true" />
            Captura manual
          </button>
        </div>
      </div>
    </header>
  );
}

