import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AppHeader } from "./components/common/AppHeader";
import { ManualEntryModal } from "./components/manual_forms/ManualEntryModal";
import Chat from "./pages/Chat";
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
  chat: Chat,
  upload: UploadData,
  manual: ManualEntry,
  recommendations: Recommendations,
  settings: Settings,
};

function AppContent() {
  const [activePage, setActivePage] = useState<keyof typeof pages>("dashboard");
  const [manualEntryOpen, setManualEntryOpen] = useState(false);
  const CurrentPage = pages[activePage];
  const navigate = (page: string) => {
    if (page in pages) setActivePage(page as keyof typeof pages);
  };

  return (
    <div className="min-h-screen bg-white text-slate-950">
      <AppHeader activePage={activePage} onNavigate={navigate} />
      <CurrentPage onNavigate={navigate} onOpenManualEntry={() => setManualEntryOpen(true)} />
      <ManualEntryModal open={manualEntryOpen} onOpenChange={setManualEntryOpen} />
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
