from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_usuario_actual
import models, schemas
from typing import List

router = APIRouter(prefix="/reservaciones", tags=["Reservaciones"])

# ─── CREATE ───────────────────────────────────────────────────────────────────
@router.post("/", response_model=schemas.ReservacionOut, status_code=201)
def crear_reservacion(
    data: schemas.ReservacionCreate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    mesa = db.query(models.Mesa).filter(models.Mesa.id == data.mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    if mesa.estado == models.EstadoMesa.ocupada:
        raise HTTPException(status_code=400, detail="La mesa está ocupada")
    if data.num_personas > mesa.capacidad:
        raise HTTPException(
            status_code=400,
            detail=f"La mesa {mesa.numero} tiene capacidad para {mesa.capacidad} personas"
        )

    reservacion = models.Reservacion(
        usuario_id=usuario_actual.id,
        mesa_id=data.mesa_id,
        num_personas=data.num_personas,
        fecha_hora=data.fecha_hora,
        activa=True
    )
    db.add(reservacion)

    # Marcar la mesa como reservada
    mesa.estado = models.EstadoMesa.reservada

    db.commit()
    db.refresh(reservacion)
    return reservacion

# ─── READ ALL (admin ve todas; cliente ve las suyas) ──────────────────────────
@router.get("/", response_model=List[schemas.ReservacionOut])
def listar_reservaciones(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol == "admin":
        return db.query(models.Reservacion).order_by(models.Reservacion.fecha_hora).all()
    return (
        db.query(models.Reservacion)
        .filter(models.Reservacion.usuario_id == usuario_actual.id)
        .order_by(models.Reservacion.fecha_hora)
        .all()
    )

# ─── MIS RESERVACIONES ────────────────────────────────────────────────────────
@router.get("/mis-reservaciones", response_model=List[schemas.ReservacionOut])
def mis_reservaciones(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    return (
        db.query(models.Reservacion)
        .filter(models.Reservacion.usuario_id == usuario_actual.id)
        .order_by(models.Reservacion.fecha_hora)
        .all()
    )

# ─── READ ONE ────────────────────────────────────────────────────────────────
@router.get("/{reservacion_id}", response_model=schemas.ReservacionOut)
def obtener_reservacion(
    reservacion_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    reservacion = db.query(models.Reservacion).filter(models.Reservacion.id == reservacion_id).first()
    if not reservacion:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    if usuario_actual.rol != "admin" and reservacion.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    return reservacion

# ─── UPDATE ───────────────────────────────────────────────────────────────────
@router.put("/{reservacion_id}", response_model=schemas.ReservacionOut)
def actualizar_reservacion(
    reservacion_id: int,
    data: schemas.ReservacionUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    reservacion = db.query(models.Reservacion).filter(models.Reservacion.id == reservacion_id).first()
    if not reservacion:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    if usuario_actual.rol != "admin" and reservacion.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="Sin permiso")

    if data.mesa_id is not None:
        nueva_mesa = db.query(models.Mesa).filter(models.Mesa.id == data.mesa_id).first()
        if not nueva_mesa:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        # Liberar la mesa anterior
        if reservacion.mesa_id != data.mesa_id:
            mesa_anterior = db.query(models.Mesa).filter(models.Mesa.id == reservacion.mesa_id).first()
            if mesa_anterior and mesa_anterior.estado == models.EstadoMesa.reservada:
                mesa_anterior.estado = models.EstadoMesa.libre
            nueva_mesa.estado = models.EstadoMesa.reservada
        reservacion.mesa_id = data.mesa_id

    if data.num_personas is not None:
        reservacion.num_personas = data.num_personas
    if data.fecha_hora is not None:
        reservacion.fecha_hora = data.fecha_hora
    if data.activa is not None:
        reservacion.activa = data.activa
        # Si se cancela la reservacion, liberar la mesa
        if not data.activa:
            mesa = db.query(models.Mesa).filter(models.Mesa.id == reservacion.mesa_id).first()
            if mesa and mesa.estado == models.EstadoMesa.reservada:
                mesa.estado = models.EstadoMesa.libre

    db.commit()
    db.refresh(reservacion)
    return reservacion

# ─── DELETE (cancela la reservación y libera la mesa) ─────────────────────────
@router.delete("/{reservacion_id}", status_code=200)
def cancelar_reservacion(
    reservacion_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    reservacion = db.query(models.Reservacion).filter(models.Reservacion.id == reservacion_id).first()
    if not reservacion:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    if usuario_actual.rol != "admin" and reservacion.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="Sin permiso")

    # Liberar la mesa si estaba reservada por esta reservación
    mesa = db.query(models.Mesa).filter(models.Mesa.id == reservacion.mesa_id).first()
    if mesa and mesa.estado == models.EstadoMesa.reservada:
        mesa.estado = models.EstadoMesa.libre

    db.delete(reservacion)
    db.commit()
    return {"mensaje": f"Reservación {reservacion_id} cancelada y mesa liberada"}
