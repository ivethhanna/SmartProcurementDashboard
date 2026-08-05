import { Bot, Send } from "lucide-react";
import { FormEvent, useState } from "react";
import { useAiChat } from "../../hooks/useAi";

interface Message {
  role: "user" | "assistant";
  text: string;
}

interface ChatWidgetProps {
  expanded?: boolean;
}

export function ChatWidget({ expanded = false }: ChatWidgetProps) {
  const mutation = useAiChat();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Pregunta sobre alertas, sucursales, inventario, proveedores o pedidos de Barrio Pizza." },
  ]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question) return;
    setInput("");
    setMessages((current) => [...current, { role: "user", text: question }]);
    try {
      const response = await mutation.mutateAsync({ pregunta: question, historial: messages });
      setMessages((current) => [...current, { role: "assistant", text: response.respuesta }]);
    } catch {
      setMessages((current) => [...current, { role: "assistant", text: "No pude consultar el chat en este momento." }]);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
        <Bot className="h-4 w-4 text-blue-700" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-slate-950">Chat IA</h2>
      </div>
      <div className={`${expanded ? "min-h-[520px]" : "max-h-72"} space-y-3 overflow-y-auto bg-slate-50 px-4 py-4`}>
        {messages.map((message, index) => (
          <div
            className={`whitespace-pre-wrap rounded-lg px-3 py-2 text-sm leading-6 ${
              message.role === "user"
                ? "ml-auto max-w-[82%] bg-slate-950 text-white"
                : "mr-auto max-w-[88%] bg-white text-slate-700 ring-1 ring-slate-200"
            }`}
            key={`${message.role}-${index}`}
          >
            {message.text}
          </div>
        ))}
        {mutation.isPending && <p className="text-sm text-slate-500">Consultando datos...</p>}
      </div>
      <form className="flex gap-2 border-t border-slate-200 p-3" onSubmit={submit}>
        <input
          className="h-9 min-w-0 flex-1 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          onChange={(event) => setInput(event.target.value)}
          placeholder="Pregunta por una sucursal, alerta, proveedor o pedido"
          value={input}
        />
        <button
          className="inline-flex h-9 items-center gap-2 rounded-md bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
          disabled={mutation.isPending}
          type="submit"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
          Enviar
        </button>
      </form>
    </section>
  );
}
