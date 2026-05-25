from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import usuarios, mesas, reservaciones, pedidos, menu, recomendaciones

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PezGallo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios.router)
app.include_router(mesas.router)
app.include_router(reservaciones.router)
app.include_router(pedidos.router)
app.include_router(menu.router)
app.include_router(recomendaciones.router)

@app.get("/")
def root():
    return {"mensaje": "🦈 Bienvenido a PezGallo API"}