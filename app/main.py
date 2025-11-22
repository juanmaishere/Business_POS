from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import productos, mesas, comandas, websocket

# Crear tablas (solo en dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="POS Comandas - FastAPI scaffold")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # solo para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(productos.router, prefix="/api/items", tags=["items"])
app.include_router(mesas.router)   # mesas router ya tiene prefix
app.include_router(comandas.router, prefix="/api/comandas", tags=["comandas"])

# Websocket router se monta en /ws
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/")
def root():
    return {"msg": "Backend ready"}
