# crud.py (síncrono)
from sqlalchemy.orm import Session
import models, schemas
from models import Mesa, Comanda, ItemComanda, Producto


def get_mesa(db: Session, mesa_id: int):
    return db.query(Mesa).filter(Mesa.id == mesa_id).first()


def get_mesas(db: Session):
    return db.query(Mesa).all()


def create_mesa(db: Session, data):
    mesa = Mesa(numero=data.numero)
    db.add(mesa)
    db.commit()
    db.refresh(mesa)
    return mesa


def get_items_por_mesa(db: Session, mesa_id: int):
    return (
        db.query(ItemComanda)
        .join(Comanda)
        .filter(Comanda.mesa_id == mesa_id, Comanda.estado == "abierta")
        .all()
    )

# --- productos ---
def create_producto(db: Session, producto: schemas.ProductoCreate):
    db_prod = models.Producto(nombre=producto.nombre, precio=producto.precio, categoria=producto.categoria)
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    return db_prod

def get_productos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Producto).offset(skip).limit(limit).all()

def get_producto(db: Session, producto_id: int):
    return db.query(models.Producto).filter(models.Producto.id == producto_id).first()

# --- mesas ---
def create_mesa(db: Session, mesa: schemas.MesaCreate):
    db_m = models.Mesa(numero=mesa.numero, estado="libre")
    db.add(db_m)
    db.commit()
    db.refresh(db_m)
    return db_m

def get_mesas(db: Session):
    return db.query(models.Mesa).all()

def get_mesa(db: Session, mesa_id: int):
    return db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()

def set_mesa_estado(db: Session, mesa_id: int, estado: str):
    mesa = get_mesa(db, mesa_id)
    if not mesa:
        return None
    mesa.estado = estado
    db.commit()
    db.refresh(mesa)
    return mesa

# --- comandas y items ---
def get_comanda(db: Session, comanda_id: int):
    return db.query(models.Comanda).filter(models.Comanda.id == comanda_id).first()

def get_comandas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Comanda).offset(skip).limit(limit).all()

def get_open_comandas(db: Session):
    return db.query(models.Comanda).filter(models.Comanda.estado == "abierta").all()

# helper: comanda activa por mesa
def get_comanda_activa(db: Session, mesa_id: int):
    return db.query(models.Comanda).filter(models.Comanda.mesa_id == mesa_id, models.Comanda.estado == "abierta").order_by(models.Comanda.created_at.desc()).first()

# crear comanda (opcional reuse_active)
def create_comanda(db: Session, mesa_id: int, items: list = None, reuse_active: bool = False):
    if reuse_active:
        active = get_comanda_activa(db, mesa_id)
        if active:
            if items:
                for it in items:
                    add_item_to_comanda_dict(db, active.id, it)
            db.refresh(active)
            return active

    db_com = models.Comanda(mesa_id=mesa_id, estado="abierta")
    db.add(db_com)
    db.commit()
    db.refresh(db_com)

    if items:
        for it in items:
            prod = get_producto(db, it['producto_id'])
            if not prod:
                continue
            db_item = models.ItemComanda(
                comanda_id=db_com.id,
                producto_id=it['producto_id'],
                cantidad=it.get('cantidad', 1),
                estado="pendiente"
            )
            db.add(db_item)
            db.commit()
            db.refresh(db_item)

    db.refresh(db_com)
    return db_com

# agregar item (schema)
def add_item_to_comanda(db: Session, comanda_id: int, item: schemas.ItemComandaCreate):
    return add_item_to_comanda_dict(db, comanda_id, {'producto_id': item.producto_id, 'cantidad': item.cantidad})

# agregar item (dict)
def add_item_to_comanda_dict(db: Session, comanda_id: int, item_dict: dict):
    prod = get_producto(db, item_dict['producto_id'])
    if not prod:
        return None
    db_item = models.ItemComanda(comanda_id=comanda_id, producto_id=item_dict['producto_id'], cantidad=item_dict.get('cantidad',1), estado="pendiente")
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def set_item_estado(db: Session, item_id: int, estado: str):
    db_item = db.query(models.ItemComanda).filter(models.ItemComanda.id == item_id).first()
    if not db_item:
        return None
    db_item.estado = estado
    db.commit()
    db.refresh(db_item)
    return db_item

def set_comanda_estado(db: Session, comanda_id: int, estado: str):
    com = get_comanda(db, comanda_id)
    if not com:
        return None
    com.estado = estado
    db.commit()
    db.refresh(com)
    return com

def get_items_por_mesa(db: Session, mesa_id: int):
    comandas = db.query(models.Comanda).filter(models.Comanda.mesa_id == mesa_id).all()
    items = []
    for c in comandas:
        items.extend(c.items)
    return items

def calcular_total_mesa(db: Session, mesa_id: int):
    total = 0.0
    comandas = db.query(models.Comanda).filter(models.Comanda.mesa_id == mesa_id, models.Comanda.estado == "abierta").all()
    for com in comandas:
        for it in com.items:
            if it.producto and it.producto.precio:
                total += it.producto.precio * it.cantidad
    return total

def cerrar_mesa(db: Session, mesa_id: int, metodo_pago: str = "efectivo"):
    comandas = db.query(models.Comanda).filter(models.Comanda.mesa_id == mesa_id, models.Comanda.estado == "abierta").all()
    total = 0.0
    detalles = []
    for com in comandas:
        for it in com.items:
            producto = it.producto
            precio = producto.precio if producto and producto.precio else 0
            total += precio * it.cantidad
            detalles.append({
                "comanda_id": com.id,
                "item_id": it.id,
                "producto_id": it.producto_id,
                "nombre": producto.nombre if producto else None,
                "cantidad": it.cantidad,
                "precio_unit": precio,
                "subtotal": precio * it.cantidad
            })
        com.estado = "cerrada"
        db.commit()
        db.refresh(com)

    mesa = get_mesa(db, mesa_id)
    if mesa:
        mesa.estado = "libre"
        db.commit()
        db.refresh(mesa)

    return {"total": total, "detalles": detalles, "metodo": metodo_pago}
