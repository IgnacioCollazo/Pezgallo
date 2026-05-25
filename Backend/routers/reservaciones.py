from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
import models, schemas, auth

router = APIRouter(prefix="/reservaciones", tags=["reservaciones"])

@router.post("/", response_model=schemas.ReservacionOut)
def crear_reservacion(
    datos: schemas.ReservacionCreate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    mesa = db.query(models.Mesa).filter(models.Mesa.id == datos.mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    if mesa.estado != models.EstadoMesa.libre:
        raise HTTPException(status_code=400, detail="Mesa no disponible")
    if mesa.capacidad < datos.num_personas:
        raise HTTPException(status_code=400, detail=f"La mesa solo tiene capacidad para {mesa.capacidad} personas")

    # Reservar la mesa
    mesa.estado = models.EstadoMesa.reservada
    reservacion = models.Reservacion(
        usuario_id=usuario_actual.id,
        mesa_id=datos.mesa_id,
        num_personas=datos.num_personas,
        fecha_hora=datos.fecha_hora
    )
    db.add(reservacion)
    db.commit()
    db.refresh(reservacion)
    return reservacion

@router.get("/mis-reservaciones")
def mis_reservaciones(
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    return db.query(models.Reservacion).filter(
        models.Reservacion.usuario_id == usuario_actual.id,
        models.Reservacion.activa == True
    ).all()

@router.delete("/{reservacion_id}")
def cancelar_reservacion(
    reservacion_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    reservacion = db.query(models.Reservacion).filter(
        models.Reservacion.id == reservacion_id,
        models.Reservacion.usuario_id == usuario_actual.id
    ).first()
    if not reservacion:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")

    reservacion.activa = False
    mesa = db.query(models.Mesa).filter(models.Mesa.id == reservacion.mesa_id).first()
    if mesa:
        mesa.estado = models.EstadoMesa.libre
    db.commit()
    return {"mensaje": "Reservación cancelada"}