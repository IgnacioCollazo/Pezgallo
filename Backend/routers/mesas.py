from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from typing import List
import models, schemas, auth

router = APIRouter(prefix="/mesas", tags=["mesas"])

@router.get("/", response_model=List[schemas.MesaOut])
def listar_mesas(db: Session = Depends(get_db)):
    return db.query(models.Mesa).all()

@router.get("/{mesa_id}", response_model=schemas.MesaOut)
def detalle_mesa(mesa_id: int, db: Session = Depends(get_db)):
    mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return mesa

@router.post("/sugerir")
def sugerir_mesa(num_personas: int, db: Session = Depends(get_db)):
    """
    Lógica inteligente de asignación:
    1. Mesa libre con capacidad exacta
    2. Mesa libre con capacidad inmediata superior
    3. Descomponer mesa grande si hay tablones disponibles
    4. Combinar tablón libre de mesa ocupada parcialmente
    """

    # 1 y 2: Mesa libre con capacidad suficiente
    mesa = db.query(models.Mesa).filter(
        models.Mesa.estado == models.EstadoMesa.libre,
        models.Mesa.capacidad >= num_personas
    ).order_by(models.Mesa.capacidad).first()

    if mesa:
        return {
            "mesa_id": mesa.id,
            "numero": mesa.numero,
            "capacidad": mesa.capacidad,
            "accion": "asignar_directo",
            "mensaje": f"Mesa {mesa.numero} disponible para {num_personas} personas"
        }

    # 3: Descomponer mesa grande (6 personas = 2 tablones)
    # Si necesitan 4 o menos, usar 1 tablón de mesa grande libre
    if num_personas <= 4:
        mesa_grande = db.query(models.Mesa).filter(
            models.Mesa.es_componible == True,
            models.Mesa.tablones_disponibles == 2,
            models.Mesa.estado == models.EstadoMesa.libre
        ).first()

        if mesa_grande:
            return {
                "mesa_id": mesa_grande.id,
                "numero": mesa_grande.numero,
                "capacidad": 4,
                "accion": "descomponer_usar_un_tablon",
                "tablones_a_usar": 1,
                "mensaje": f"Se usará 1 tablón de la mesa {mesa_grande.numero} (capacidad para {num_personas} personas)"
            }

    # 4: Escenario especial — grupo de 5 con mesa de 4 disponible + tablón suelto
    # Mesa grande parcialmente ocupada (3 personas, quedan 3 sillas = 1 tablón libre)
    if num_personas == 5:
        mesa_4 = db.query(models.Mesa).filter(
            models.Mesa.estado == models.EstadoMesa.libre,
            models.Mesa.capacidad == 4
        ).first()

        mesa_tablon = db.query(models.Mesa).filter(
            models.Mesa.es_componible == True,
            models.Mesa.tablones_disponibles >= 1,
            models.Mesa.estado != models.EstadoMesa.libre
        ).first()

        if mesa_4 and mesa_tablon:
            return {
                "mesa_id": mesa_4.id,
                "numero": mesa_4.numero,
                "capacidad": 5,
                "accion": "combinar_mesa_tablon",
                "mesa_extra_id": mesa_tablon.id,
                "mensaje": f"Combinar mesa {mesa_4.numero} + 1 tablón de mesa {mesa_tablon.numero} para acomodar {num_personas} personas"
            }

    return {
        "mensaje": "No hay mesas disponibles en este momento",
        "accion": "ninguna"
    }

@router.patch("/{mesa_id}/estado")
def cambiar_estado(
    mesa_id: int,
    estado: models.EstadoMesa,
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    mesa.estado = estado
    db.commit()
    db.refresh(mesa)
    return {"mensaje": f"Mesa {mesa.numero} actualizada a '{estado}'"}

@router.patch("/{mesa_id}/descomponer")
def descomponer_mesa(
    mesa_id: int,
    tablones_a_liberar: int = 1,
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    """Libera tablones de una mesa grande para redistribuir"""
    mesa = db.query(models.Mesa).filter(
        models.Mesa.id == mesa_id,
        models.Mesa.es_componible == True
    ).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada o no es componible")

    mesa.tablones_disponibles = min(2, mesa.tablones_disponibles + tablones_a_liberar)
    if mesa.tablones_disponibles == 2:
        mesa.estado = models.EstadoMesa.libre

    db.commit()
    return {"mensaje": f"Mesa {mesa.numero} ahora tiene {mesa.tablones_disponibles} tablón(es) disponible(s)"}