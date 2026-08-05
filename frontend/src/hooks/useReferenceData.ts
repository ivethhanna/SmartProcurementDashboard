import { useQuery } from "@tanstack/react-query";
import { fetchReferenceData } from "../services/api";

export function useReferenceData() {
  const reference = useQuery({
    queryKey: ["reference-data"],
    queryFn: fetchReferenceData,
  });

  return {
    reference,
    sucursales: reference.data?.sucursales ?? [],
    ingredientes: reference.data?.ingredientes ?? [],
    proveedores: reference.data?.proveedores ?? [],
    unidades: reference.data?.unidades ?? [],
    semanas: reference.data?.semanas ?? [],
    tiposFormato: reference.data?.tipos_formato ?? [],
    formatosCompra: reference.data?.formatos_compra ?? [],
    isLoading: reference.isLoading,
  };
}
