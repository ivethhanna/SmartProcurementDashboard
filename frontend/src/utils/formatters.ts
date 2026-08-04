export const currencyFormatter = new Intl.NumberFormat("es-PA", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export const preciseCurrencyFormatter = new Intl.NumberFormat("es-PA", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "Sin datos";
  return new Intl.DateTimeFormat("es-PA", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function humanizeAlertType(value: string) {
  return value.replace("_", " ");
}

