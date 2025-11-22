from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProductoBase(BaseModel):
    nombre: str
    precio: float
    categoria: Optional[str] = None

class ProductoCreate(ProductoBase):
    pass

class ProductoOut(ProductoBase):
    id: int
    class Config:
        orm_mode = True

class ItemComandaCreate(BaseModel):
    producto_id: int
    cantidad: int = 1

class ItemComandaOut(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    estado: str
    producto: Optional[ProductoOut] = None
    class Config:
        orm_mode = True

class ComandaCreate(BaseModel):
    mesa_id: int
    items: Optional[List[ItemComandaCreate]] = []

class ComandaOut(BaseModel):
    id: int
    mesa_id: int
    estado: str
    created_at: datetime
    items: List[ItemComandaOut] = []
    class Config:
        orm_mode = True

class MesaCreate(BaseModel):
    numero: int

class MesaOut(BaseModel):
    id: int
    numero: int
    estado: str
    comandas: List[ComandaOut] = []
    class Config:
        orm_mode = True
