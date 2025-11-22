from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Float, nullable=False)
    categoria = Column(String, nullable=True)

class Mesa(Base):
    __tablename__ = "mesas"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, nullable=False, unique=True)
    estado = Column(String, default="libre")  # libre | ocupada

    comandas = relationship("Comanda", back_populates="mesa")

class Comanda(Base):
    __tablename__ = "comandas"
    id = Column(Integer, primary_key=True, index=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id"))

    # ESTADO OPERATIVO (cocina)
    estado = Column(String, default="abierta")  # abierta | preparando | listo

    # ESTADO DE PAGO (mesas)
    estado_pago = Column(String, default="pendiente")  # pendiente | pagado

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    mesa = relationship("Mesa", back_populates="comandas")
    items = relationship("ItemComanda", back_populates="comanda", cascade="all, delete-orphan")

class ItemComanda(Base):
    __tablename__ = "items_comanda"
    id = Column(Integer, primary_key=True, index=True)
    comanda_id = Column(Integer, ForeignKey("comandas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, default=1)
    estado = Column(String, default="pendiente")  # pendiente | preparando | listo

    comanda = relationship("Comanda", back_populates="items")
    producto = relationship("Producto")
