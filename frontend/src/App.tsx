import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AppHeader } from "./components/common/AppHeader";
import { useDashboardSummary } from "./hooks/useAlerts";
import Dashboard from "./pages/Dashboard";
import ManualEntry from "./pages/ManualEntry";
import Recommendations from "./pages/Recommendations";
import Settings from "./pages/Settings";
import UploadData from "./pages/UploadData";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

const pages = {
  dashboard: Dashboard,
  upload: UploadData,
  manual: ManualEntry,
  recommendations: Recommendations,
  settings: Settings,
};

function AppContent() {
  const [activePage, setActivePage] = useState<keyof typeof pages>("dashboard");
  const { data: summary } = useDashboardSummary();
  const CurrentPage = pages[activePage];
  const navigate = (page: string) => {
    if (page in pages) setActivePage(page as keyof typeof pages);
  };

  return (
    <div className="min-h-screen bg-white text-slate-950">
      <AppHeader activePage={activePage} lastUpdated={summary?.ultima_actualizacion} onNavigate={navigate} />
      <CurrentPage onNavigate={navigate} />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
