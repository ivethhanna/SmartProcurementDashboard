import { useState } from "react";

export type AlertsPerPage = 10 | 25 | 50 | "all";
export type AlertSort = "severidad" | "impacto" | "sucursal" | "ingrediente";

const DEFAULT_PREFS: { alertsPerPage: AlertsPerPage; defaultSort: AlertSort } = {
  alertsPerPage: 25,
  defaultSort: "severidad",
};

export function useDisplayPreferences() {
  const [prefs, setPrefs] = useState(() => {
    try {
      const saved = localStorage.getItem("barrio-pizza-display-prefs");
      return saved ? { ...DEFAULT_PREFS, ...JSON.parse(saved) } : DEFAULT_PREFS;
    } catch {
      return DEFAULT_PREFS;
    }
  });

  const updatePrefs = (updates: Partial<typeof DEFAULT_PREFS>) => {
    const next = { ...prefs, ...updates };
    setPrefs(next);
    localStorage.setItem("barrio-pizza-display-prefs", JSON.stringify(next));
  };

  return { prefs, updatePrefs };
}
