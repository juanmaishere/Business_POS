from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Mesa, Comanda, ItemComanda, Producto

router = APIRouter(prefix="/api/mesas", tags=["mesas"])


# ---------------------------------------------------------
# Crear mesa
# ---------------------------------------------------------
@router.post("/", response_model=dict)
def create_mesa(data: dict, db: Session = Depends(get_db)):
    numero = data.get("numero")
    if not numero:
        raise HTTPException(status_code=400, detail="Número inválido")

    mesa = Mesa(numero=numero, estado="libre")
    db.add(mesa)
    db.commit()
    db.refresh(mesa)
    return {"id": mesa.id, "numero": mesa.numero, "estado": mesa.estado}


# ---------------------------------------------------------
# Listado de mesas
# ---------------------------------------------------------
@router.get("/", response_model=list[dict])
def list_mesas(db: Session = Depends(get_db)):
    mesas = db.query(Mesa).all()
    return [{"id": m.id, "numero": m.numero, "estado": m.estado} for m in mesas]


# ---------------------------------------------------------
# NUEVO: Resumen de mesa (items + total)
# ---------------------------------------------------------
@router.get("/{mesa_id}/resumen")
def obtener_cuenta(mesa_id: int, db: Session = Depends(get_db)):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    # SOLO COMANDAS NO PAGADAS
    comandas_pendientes = (
        db.query(Comanda)
        .filter(Comanda.mesa_id == mesa_id, Comanda.estado_pago == "pendiente")
        .all()
    )

    items = []
    total = 0

    for c in comandas_pendientes:
        for it in c.items:
            precio = it.producto.precio
            subtotal = precio * it.cantidad
            total += subtotal
            items.append({
                "nombre": it.producto.nombre,
                "cantidad": it.cantidad,
                "precio": precio,
                "subtotal": subtotal,
            })

    return {
        "mesa_id": mesa_id,
        "total": total,
        "items": items
    }

# ---------------------------------------------------------
# Cerrar mesa
# ---------------------------------------------------------
@router.post("/{mesa_id}/cerrar")
def cerrar_mesa(mesa_id: int, metodo_pago: str, db: Session = Depends(get_db)):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    # OBTENER COMANDAS NO PAGADAS
    comandas_pendientes = (
        db.query(Comanda)
        .filter(Comanda.mesa_id == mesa_id, Comanda.estado_pago == "pendiente")
        .all()
    )

    total = 0
    detalles = []

    for c in comandas_pendientes:
        for it in c.items:
            subtotal = it.producto.precio * it.cantidad
            total += subtotal
            detalles.append({
                "producto": it.producto.nombre,
                "cantidad": it.cantidad,
                "subtotal": subtotal
            })

        # MARCAR COMANDA COMO PAGADA
        c.estado_pago = "pagado"

    mesa.estado = "libre"
    db.commit()

    return {
        "total": total,
        "detalles": detalles,
        "metodo_pago": metodo_pago
    }