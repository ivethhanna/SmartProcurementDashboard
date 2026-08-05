import { ChatWidget } from "../components/chat/ChatWidget";

export default function Chat() {
  return (
    <main className="bg-white">
      <div className="mx-auto max-w-[1100px] px-4 py-6 lg:px-6">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Chat IA</p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-950">Asistente de compras</h1>
          <p className="mt-1 text-sm text-slate-600">
            Consulta el estado vivo de alertas, inventario, proveedores y pedidos de Barrio Pizza.
          </p>
        </div>

        <ChatWidget expanded />
      </div>
    </main>
  );
}
