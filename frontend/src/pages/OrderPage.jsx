import React, { useEffect, useMemo, useState } from "react";
import useItems from "../hooks/useItems";
import useWebSocket from "../hooks/useWebSocket";
import CloseMesaModal from "../components/CloseMesaModal";


// Component: MesaGrid
function MesaGrid({ mesas, selectedId, onSelect, onCerrar }) {
  return (
    <div style={{ overflowX: "auto", padding: "8px 4px" }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        {mesas.map((m) => {
          const ocupado = m.estado && m.estado !== "libre";
          const isSelected = selectedId === m.id;
          return (
            <div
              key={m.id}
              style={{
                minWidth: 110,
                padding: 10,
                borderRadius: 6,
                background: isSelected ? "#FEE2E2" : ocupado ? "#FEE2E2" : "#ECFDF5",
                border: isSelected ? "2px solid #F43F5E" : "1px solid rgba(0,0,0,0.06)",
                boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 8,
                cursor: "pointer",
              }}
              onClick={() => onSelect(m.id)}
            >
              <div style={{ fontWeight: "700" }}>{`Mesa ${m.numero}`}</div>
              <div style={{ fontSize: 12, color: "#333" }}>{m.estado || "libre"}</div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCerrar(m.id);
                }}
                style={{
                  marginTop: 6,
                  padding: "6px 10px",
                  borderRadius: 6,
                  background: "#ffffff",
                  border: "1px solid rgba(0,0,0,0.08)",
                  fontSize: 12,
                }}
              >
                Cerrar
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Product grid (simplified)
function ProductGrid({ products, onAdd }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {products.map((p) => (
        <div key={p.id} className="bg-white rounded shadow p-3">
          <div className="font-bold">{p.nombre}</div>
          <div className="text-sm text-gray-600">{p.precio}$</div>
          <button
            onClick={() => onAdd(p)}
            className="bg-blue-500 text-white px-3 py-1 rounded mt-2"
          >
            +
          </button>
        </div>
      ))}
    </div>
  );
}

export default function OrderPage() {
  const { items, loading } = useItems();
  const { connected, messages } = useWebSocket("mozo"); // escucha updates de mozo
  const [mesas, setMesas] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [cart, setCart] = useState([]);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [mesaParaCerrar, setMesaParaCerrar] = useState(null);
  const [cuentaMesa, setCuentaMesa] = useState(null);


  const base = window.__API_BASE__ || "http://localhost:8000";

  // --- load mesas inicial ---
  useEffect(() => {
    fetch(`${base}/api/mesas`)
      .then((r) => r.json())
      .then((data) => {
        // normalizar: asegurarse que vienen {id, numero, estado}
        setMesas(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error("error fetching mesas", err);
      });
  }, [base]);

  // --- procesar mensajes WS (solo actualizaciones puntuales) ---
  useEffect(() => {
    if (!messages || !messages.length) return;
    // cada mensaje debe ser objeto con shape: { type, mesa_id, estado, total }
    messages.forEach((msg) => {
      if (!msg || !msg.type) return;
      if (msg.type === "mesa_update" && msg.mesa_id) {
        setMesas((prev) =>
          prev.map((m) => (m.id === msg.mesa_id ? { ...m, estado: msg.estado, total: msg.total } : m))
        );
      }
      if (msg.type === "comanda_listo" && msg.mesa_id) {
        // optionally mark something — but cocina handles removal
      }
    });
  }, [messages]);

  // --- categories + filtered products ---
  const categories = useMemo(() => {
    const cats = Array.from(new Set(items.map((i) => i.categoria || "Otros")));
    return cats.length ? cats : ["Bebidas", "Comida"];
  }, [items]);

  const [selectedCategory, setSelectedCategory] = useState(null);
  useEffect(() => {
    setSelectedCategory((s) => (s ?? categories[0]));
  }, [categories]);

  const filtered = items.filter((i) => (selectedCategory ? i.categoria === selectedCategory : true));

  // --- cart helpers (frontend-only until send) ---
  const addItemToCart = (p) => {
    setCart((prev) => {
      const found = prev.find((x) => x.producto_id === p.id);
      if (found) {
        return prev.map((x) => (x.producto_id === p.id ? { ...x, cantidad: x.cantidad + 1 } : x));
      }
      return [...prev, { producto_id: p.id, cantidad: 1, nombre: p.nombre, precio: p.precio }];
    });
  };

  const openCloseModal = async (mesaId) => {
    try {
      const res = await fetch(`${base}/api/mesas/${mesaId}/resumen`);
      if (!res.ok) throw new Error("Error obteniendo resumen");

      const cuenta = await res.json();
      // cuenta = { mesa_id, items[], total }

      setCuentaMesa(cuenta);
      setMesaParaCerrar(mesaId);
      setShowCloseModal(true);

    } catch (e) {
      console.error(e);
      alert("No se pudo obtener la cuenta de la mesa");
    }
  };
  const removeFromCart = (producto_id) => {
    setCart((prev) => prev.filter((x) => x.producto_id !== producto_id));
  };

  // --- select table handler (just selects, doesn't mutate state of all mesas) ---
  const handleSelectTable = (id) => {
    setSelectedTable(id);
    // optional: keep focus visible; do NOT mutate other mesas' estado client-side
  };

  // --- send comanda: POST /api/comandas ---
  const sendComanda = async () => {
    if (!selectedTable) return alert("Seleccioná mesa");
    if (!cart.length) return alert("Agregá items al carrito");

    const payload = {
      mesa_id: Number(selectedTable),
      items: cart.map((it) => ({ producto_id: it.producto_id, cantidad: it.cantidad })),
    };

    try {
      const res = await fetch(`${base}/api/comandas/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("error creating comanda");
      const comanda = await res.json();
      setCart([]);
      alert("Comanda creada: " + comanda.id);

      // update mesa locally to 'ocupada' (but real update will come via WS mesa_update)
      setMesas((prev) => prev.map((m) => (m.id === comanda.mesa_id ? { ...m, estado: "ocupada" } : m)));
    } catch (e) {
      console.error(e);
      alert("Error creando comanda");
    }
  };

  // --- cerrar mesa (POST /api/mesas/{id}/cerrar?metodo_pago=...) ---
  const confirmarCerrar = async (metodo) => {
    if (!mesaParaCerrar) return;

    try {
      const res = await fetch(
        `${base}/api/mesas/${mesaParaCerrar}/cerrar?metodo_pago=${metodo}`,
        { method: "POST" }
      );

      if (!res.ok) throw new Error("error cerrar");

      const data = await res.json(); // { total, detalles }

      // actualizar UI
      setMesas((prev) =>
        prev.map((m) =>
          m.id === mesaParaCerrar ? { ...m, estado: "libre" } : m
        )
      );

      setShowCloseModal(false);
      setMesaParaCerrar(null);
      setCuentaMesa(null);

    } catch (e) {
      console.error(e);
      alert("Error cerrando mesa");
    }
  };
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Sansueña POS</h1>

      <div style={{ marginBottom: 18 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Mesas</div>
        <MesaGrid
          mesas={mesas}
          selectedId={selectedTable}
          onSelect={handleSelectTable}
          onCerrar={openCloseModal}
        />
      </div>

      <div className="flex gap-6">
        <div style={{ width: 240 }}>
          <div className="mb-2">Categorías</div>
          <div className="flex flex-col gap-2">
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setSelectedCategory(c)}
                className={`p-2 ${selectedCategory === c ? "bg-red-500 text-white" : "bg-gray-200"}`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1">
          {loading ? <div>Cargando...</div> : <ProductGrid products={filtered} onAdd={addItemToCart} />}
        </div>

        <aside style={{ width: 320 }} className="bg-white p-4 rounded shadow">
          <div>
            <div style={{ fontWeight: "700" }}>Mesa</div>
            <div style={{ marginBottom: 8 }}>{selectedTable ? `Mesa ${selectedTable}` : "-"}</div>
          </div>

          <div className="mt-3">
            <h4>Carrito</h4>
            {cart.length === 0 && <div>Vacio</div>}
            {cart.map((it) => (
              <div key={it.producto_id} className="flex justify-between items-center">
                <div>
                  <div>{it.nombre} x{it.cantidad}</div>
                  <div style={{ fontSize: 12, color: "#666" }}>{it.precio * it.cantidad}$</div>
                </div>
                <div>
                  <button onClick={() => removeFromCart(it.producto_id)} style={{ marginLeft: 8 }}>Eliminar</button>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-3">
            <button onClick={sendComanda} className="w-full bg-red-500 text-white p-2 rounded">Enviar comanda</button>
          </div>

          <div className="mt-2 text-sm text-gray-500">WS: {connected ? "connected" : "disconnected"}</div>
        </aside>
      </div>
      <CloseMesaModal
        cuenta={cuentaMesa}
        onClose={() => setShowCloseModal(false)}
        onPagar={confirmarCerrar}
      />
    </div>
  );
}
