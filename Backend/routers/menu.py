from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_usuario_actual
import models, schemas
from typing import List, Optional

router = APIRouter(prefix="/menu", tags=["Menú"])

# ─── CREATE (admin) ───────────────────────────────────────────────────────────
@router.post("/", response_model=schemas.ItemMenuOut, status_code=201)
def crear_item(
    data: schemas.ItemMenuCreate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden agregar platillos")
    item = models.ItemMenu(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# ─── READ ALL (público) — filtrable por categoría ─────────────────────────────
@router.get("/", response_model=List[schemas.ItemMenuOut])
def listar_menu(
    categoria: Optional[str] = None,
    solo_disponibles: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(models.ItemMenu)
    if categoria:
        query = query.filter(models.ItemMenu.categoria == categoria)
    if solo_disponibles:
        query = query.filter(models.ItemMenu.disponible == True)
    return query.order_by(models.ItemMenu.categoria, models.ItemMenu.nombre).all()

# ─── READ ONE ────────────────────────────────────────────────────────────────
@router.get("/{item_id}", response_model=schemas.ItemMenuOut)
def obtener_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ItemMenu).filter(models.ItemMenu.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return item

# ─── UPDATE (admin) ───────────────────────────────────────────────────────────
@router.put("/{item_id}", response_model=schemas.ItemMenuOut)
def actualizar_item(
    item_id: int,
    data: schemas.ItemMenuUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden modificar platillos")
    item = db.query(models.ItemMenu).filter(models.ItemMenu.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")

    for campo, valor in data.model_dump(exclude_none=True).items():
        setattr(item, campo, valor)

    db.commit()
    db.refresh(item)
    return item

# ─── PATCH disponibilidad (admin) ─────────────────────────────────────────────
@router.patch("/{item_id}/disponibilidad", response_model=schemas.ItemMenuOut)
def cambiar_disponibilidad(
    item_id: int,
    disponible: bool,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    item = db.query(models.ItemMenu).filter(models.ItemMenu.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    item.disponible = disponible
    db.commit()
    db.refresh(item)
    return item

# ─── DELETE (admin) ───────────────────────────────────────────────────────────
@router.delete("/{item_id}", status_code=200)
def eliminar_item(
    item_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar platillos")
    item = db.query(models.ItemMenu).filter(models.ItemMenu.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    db.delete(item)
    db.commit()
    return {"mensaje": f"Platillo {item_id} eliminado correctamente"}
