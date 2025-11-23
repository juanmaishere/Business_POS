import React from "react";
import "../index.css";

export default function CloseMesaModal({ cuenta, onClose, onPagar }) {
    if (!cuenta) return null;

    return (
        <div className="modal-overlay">
            <div className="modal">
                <h2>Cuenta - Mesa {cuenta.mesa_id}</h2>

                <div className="detalles-list">
                    {cuenta.items.map((it) => (
                        <div key={it.item_id} className="detalle-item">
                            <div>
                                <strong>{it.nombre}</strong>
                                <div className="detalle-cantidad">
                                    x{it.cantidad} • ${it.precio}
                                </div>
                            </div>
                            <div className="detalle-subtotal">${it.subtotal}</div>
                        </div>
                    ))}
                </div>

                <div className="total">
                    <strong>Total: </strong> ${cuenta.total}
                </div>

                <div className="acciones">
                    <button className="btn-efectivo"
                        onClick={() => onPagar("efectivo")}
                    >
                        Pagar Efectivo
                    </button>

                    <button className="btn-tarjeta"
                        onClick={() => onPagar("tarjeta")}
                    >
                        Pagar Tarjeta
                    </button>

                    <button className="btn-cancelar" onClick={onClose}>
                        Cancelar
                    </button>
                </div>
            </div>
        </div>
    );
}
