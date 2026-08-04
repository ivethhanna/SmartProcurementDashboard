import { Upload } from "lucide-react";
import { useRef, useState } from "react";

interface CsvUploadZoneProps {
  onUpload: (file: File) => Promise<void>;
}

export function CsvUploadZone({ onUpload }: CsvUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setMessage("El archivo debe ser CSV.");
      return;
    }
    setIsUploading(true);
    setMessage(null);
    try {
      await onUpload(file);
      setMessage("CSV cargado correctamente.");
    } catch (error) {
      const detail =
        typeof error === "object" && error !== null && "response" in error
          ? String((error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "")
          : "";
      setMessage(detail || "No se pudo cargar el CSV.");
    } finally {
      setIsUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div
      className="rounded-lg border border-dashed border-stone-300 bg-white px-4 py-5"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        handleFile(event.dataTransfer.files[0]);
      }}
    >
      <input
        accept=".csv"
        className="hidden"
        onChange={(event) => handleFile(event.target.files?.[0])}
        ref={inputRef}
        type="file"
      />
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-stone-100">
            <Upload className="h-5 w-5 text-stone-700" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold text-stone-950">Subir CSV</p>
            <p className="text-sm text-stone-500">Arrastra el archivo o seleccionalo desde tu equipo.</p>
          </div>
        </div>
        <button
          className="h-10 rounded-md bg-stone-950 px-4 text-sm font-semibold text-white disabled:opacity-60"
          disabled={isUploading}
          onClick={() => inputRef.current?.click()}
          type="button"
        >
          {isUploading ? "Subiendo..." : "Seleccionar"}
        </button>
      </div>
      {message && <p className="mt-3 text-sm text-stone-600">{message}</p>}
    </div>
  );
}
