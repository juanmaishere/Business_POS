import React, { useEffect, useState } from "react";
import useWebSocket from "../hooks/useWebSocket";

export default function KitchenPage() {
  const { connected, messages } = useWebSocket("cocina");
  const [comandas, setComandas] = useState([]); // cada comanda incluye items []

  const base = window.__API_BASE__ || "http://localhost:8000";

  useEffect(() => {
    // fetch inicial de comandas abiertas
    fetch(`${base}/api/comandas/kitchen`)
      .then(r => r.json())
      .then(data => setComandas(Array.isArray(data) ? data : []))
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!messages || !messages.length) return;

    messages.forEach(msg => {
      if (!msg || !msg.type) return;

      if (msg.type === "new_comanda" && msg.comanda) {
        // Prepend nueva comanda
        setComandas(prev => [msg.comanda, ...prev]);
      } else if (msg.type === "update_comanda" && msg.comanda_id) {
        setComandas(prev => prev.map(c => c.id === msg.comanda_id ? { ...c, items: [...(c.items || []), msg.item] } : c));
      } else if (msg.type === "comanda_listo" && msg.comanda_id) {
        // remover comanda lista
        setComandas(prev => prev.filter(c => c.id !== msg.comanda_id));
      } else if (msg.type === "item_ready" && msg.comanda_id && msg.item_id) {
        // quitar item concreto de la comanda
        setComandas(prev => prev.map(c => c.id === msg.comanda_id ? { ...c, items: (c.items || []).filter(i => i.id !== msg.item_id) } : c));
      }
    });
  }, [messages]);

  const marcarListo = async (comandaId) => {
    // confirm
    if (!confirm("Marcar comanda como LISTA?")) return;

    try {
      const res = await fetch(`${base}/api/comandas/${comandaId}/estado?estado=lista`, { method: "PATCH" });
      if (!res.ok) throw new Error("Error marcando comanda");
      // local: removerla
      setComandas(prev => prev.filter(c => c.id !== comandaId));
    } catch (e) {
      console.error(e);
      alert("No se pudo marcar como lista");
    }
  };

  // opcional: marcar item listo (por item)
  const marcarItemListo = async (comandaId, itemId) => {
    if (!confirm("Marcar item como LISTO?")) return;
    try {
      const res = await fetch(`${base}/api/comandas/items/${itemId}/estado?estado=listo`, { method: "PATCH" });
      if (!res.ok) throw new Error("Error marcando item");
      setComandas(prev => prev.map(c => c.id === comandaId ? { ...c, items: (c.items || []).filter(i => i.id !== itemId) } : c));
    } catch (e) {
      console.error(e);
      alert("No se pudo marcar item");
    }
  };

  const renderItemName = (it) => {
    // soporta varias formas: producto.nombre, producto (string), producto_id
    if (!it) return "";
    if (it.producto && typeof it.producto === "object") return it.producto.nombre || it.producto_id || it.producto;
    if (it.producto && typeof it.producto === "string") return it.producto;
    return it.producto_id ? `#${it.producto_id}` : "Item";
  };

  return (
    <div className="p-4">
      <h2 className="text-lg font-bold mb-4">Cocina</h2>
      <div className="space-y-4">
        {comandas.length === 0 && <div>No hay comandas</div>}
        {comandas.map(c => (
          <div key={c.id} className="bg-white p-3 rounded shadow">
            <div className="flex justify-between">
              <div>Mesa {c.mesa_id}</div>
              <div># {c.id}</div>
            </div>
            <div className="mt-2">
              {(c.items || []).map(it => (
                <div key={it.id} className="flex justify-between items-center py-1">
                  <div>{renderItemName(it)} x{it.cantidad}</div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => marcarItemListo(c.id, it.id)}
                      className="bg-yellow-500 text-white px-2 py-1 rounded text-sm"
                    >
                      Listo (item)
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-2 flex gap-2">
              <button onClick={() => marcarListo(c.id)} className="bg-green-500 text-white px-3 py-1 rounded">Listo (comanda)</button>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 text-sm text-gray-500">WS: {connected ? 'connected' : 'disconnected'}</div>
    </div>
  );
}
