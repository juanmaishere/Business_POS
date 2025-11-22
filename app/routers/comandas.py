from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from database import get_db
import crud, schemas
from routers.websocket import manager

router = APIRouter()  # mounted in main with prefix /api/comandas

@router.post("/", response_model=schemas.ComandaOut)
async def create_comanda_endpoint(payload: schemas.ComandaCreate, db: Session = Depends(get_db)):
    mesa = crud.get_mesa(db, payload.mesa_id)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    com = crud.create_comanda(db, payload.mesa_id,
                              items=[it.dict() for it in payload.items] if payload.items else None,
                              reuse_active=True)

    crud.set_mesa_estado(db, payload.mesa_id, "ocupada")
    total = crud.calcular_total_mesa(db, payload.mesa_id)

    try:
        await manager.broadcast("cocina", json.dumps({
            "type": "new_comanda",
            "comanda": schemas.ComandaOut.from_orm(com).dict()
        }))
    except Exception:
        pass

    try:
        await manager.broadcast("mozo", json.dumps({
            "type": "mesa_update",
            "mesa_id": payload.mesa_id,
            "estado": "ocupada",
            "total": total
        }))
    except Exception:
        pass

    return com

@router.post("/{comanda_id}/items", response_model=schemas.ItemComandaOut)
async def add_item_endpoint(comanda_id: int, item: schemas.ItemComandaCreate, db: Session = Depends(get_db)):
    com = crud.get_comanda(db, comanda_id)
    if not com:
        raise HTTPException(status_code=404, detail="Comanda no encontrada")

    db_item = crud.add_item_to_comanda(db, comanda_id, item)
    if not db_item:
        raise HTTPException(status_code=400, detail="Producto no existe")

    total = crud.calcular_total_mesa(db, com.mesa_id)

    try:
        await manager.broadcast("cocina", json.dumps({
            "type": "update_comanda",
            "comanda_id": comanda_id,
            "item": {
                "id": db_item.id,
                "producto_id": db_item.producto_id,
                "producto": db_item.producto.nombre if db_item.producto else None,
                "cantidad": db_item.cantidad
            },
            "total": total
        }))
    except Exception:
        pass

    try:
        await manager.broadcast("mozo", json.dumps({
            "type": "mesa_update",
            "mesa_id": com.mesa_id,
            "estado": "ocupada",
            "total": total
        }))
    except Exception:
        pass

    return db_item

@router.get("/", response_model=List[schemas.ComandaOut])
def list_comandas(db: Session = Depends(get_db)):
    return crud.get_comandas(db)

@router.get("/kitchen", response_model=List[schemas.ComandaOut])
def kitchen_list(db: Session = Depends(get_db)):
    return crud.get_open_comandas(db)

@router.patch("/items/{item_id}/estado", response_model=schemas.ItemComandaOut)
async def patch_item_estado(item_id: int, estado: str, db: Session = Depends(get_db)):
    item = crud.set_item_estado(db, item_id, estado)
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    try:
        await manager.broadcast("mozo", json.dumps({
            "type": "item_ready",
            "item_id": item_id,
            "comanda_id": item.comanda_id
        }))
    except Exception:
        pass

    try:
        await manager.broadcast("cocina", json.dumps({
            "type": "item_ready",
            "item_id": item_id,
            "comanda_id": item.comanda_id
        }))
    except Exception:
        pass

    return item

@router.patch("/{comanda_id}/estado", response_model=schemas.ComandaOut)
async def patch_comanda_estado(comanda_id: int, estado: str, db: Session = Depends(get_db)):
    com = crud.set_comanda_estado(db, comanda_id, estado)
    if not com:
        raise HTTPException(status_code=404, detail="Comanda no encontrada")

    try:
        await manager.broadcast("mozo", json.dumps({
            "type": "comanda_listo" if estado == "lista" else "comanda_estado",
            "comanda_id": comanda_id,
            "estado": estado
        }))
    except Exception:
        pass

    try:
        await manager.broadcast("cocina", json.dumps({
            "type": "comanda_listo" if estado == "lista" else "comanda_estado",
            "comanda_id": comanda_id,
            "estado": estado
        }))
    except Exception:
        pass

    return com

@router.post("/{comanda_id}/listo")
async def marcar_comanda_lista(comanda_id: int, db: Session = Depends(get_db)):
    com = crud.set_comanda_estado(db, comanda_id, "lista")
    try:
        await manager.broadcast("mozo", json.dumps({"type": "comanda_listo", "comanda_id": comanda_id}))
    except Exception:
        pass
    try:
        await manager.broadcast("cocina", json.dumps({"type": "comanda_listo", "comanda_id": comanda_id}))
    except Exception:
        pass
    return {"ok": True}
