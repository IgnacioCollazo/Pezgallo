from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_usuario_actual
import models, schemas
from typing import List

router = APIRouter(prefix="/mesas", tags=["Mesas"])

TIPOS_VALIDOS = ["pequena", "mediana", "grande"]

# ─── CREATE (admin) ───────────────────────────────────────────────────────────
@router.post("/", response_model=schemas.MesaOut, status_code=201)
def crear_mesa(
    data: schemas.MesaCreate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear mesas")
    if data.tipo not in TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Tipo de mesa inválido. Opciones: {TIPOS_VALIDOS}")
    existente = db.query(models.Mesa).filter(models.Mesa.numero == data.numero).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"Ya existe la mesa número {data.numero}")
    mesa = models.Mesa(**data.model_dump())
    db.add(mesa)
    db.commit()
    db.refresh(mesa)
    return mesa

# ─── READ ALL (público) ───────────────────────────────────────────────────────
@router.get("/", response_model=List[schemas.MesaOut])
def listar_mesas(db: Session = Depends(get_db)):
    return db.query(models.Mesa).order_by(models.Mesa.numero).all()

# ─── READ ONE ────────────────────────────────────────────────────────────────
@router.get("/{mesa_id}", response_model=schemas.MesaOut)
def obtener_mesa(mesa_id: int, db: Session = Depends(get_db)):
    mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return mesa

# ─── UPDATE (admin) ───────────────────────────────────────────────────────────
@router.put("/{mesa_id}", response_model=schemas.MesaOut)
def actualizar_mesa(
    mesa_id: int,
    data: schemas.MesaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden modificar mesas")
    if data.tipo is not None and data.tipo not in TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Tipo de mesa inválido. Opciones: {TIPOS_VALIDOS}")
    mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    for campo, valor in data.model_dump(exclude_none=True).items():
        setattr(mesa, campo, valor)

    db.commit()
    db.refresh(mesa)
    return mesa

# ─── PATCH estado (admin) ─────────────────────────────────────────────────────
@router.patch("/{mesa_id}/estado", response_model=schemas.MesaOut)
def cambiar_estado_mesa(
    mesa_id: int,
    data: schemas.EstadoMesaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden cambiar el estado")
    mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    estados_validos = [e.value for e in models.EstadoMesa]
    if data.estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Opciones: {estados_validos}")
    mesa.estado = data.estado
    db.commit()
    db.refresh(mesa)
    return mesa

# ─── DELETE (admin) ───────────────────────────────────────────────────────────
@router.delete("/{mesa_id}", status_code=200)
def eliminar_mesa(
    mesa_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar mesas")
    mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    db.delete(mesa)
    db.commit()
    return {"mensaje": f"Mesa {mesa_id} eliminada correctamente"}
