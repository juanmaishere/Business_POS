from database import SessionLocal
import crud, schemas

db = SessionLocal()

# crear algunas mesas
for i in range(1, 13):
    crud.create_mesa(db, schemas.MesaCreate(numero=i))

# crear algunos productos
productos = [
    schemas.ProductoCreate(nombre="Café Americano", precio=120, categoria="Bebidas"),
    schemas.ProductoCreate(nombre="Capuccino", precio=150, categoria="Bebidas"),
    schemas.ProductoCreate(nombre="Medialuna", precio=80, categoria="Comida"),
]
for p in productos:
    crud.create_producto(db, p)

db.close()
print("DB poblada con mesas y productos")