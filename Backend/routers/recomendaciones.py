from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_usuario_actual
import models
from typing import List

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])

@router.get("/")
def obtener_recomendaciones(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    """
    Recomienda platillos basados en los pedidos anteriores del usuario.
    Si no tiene historial, devuelve los platillos más populares.
    """
    # Buscar items que el usuario ha pedido antes
    pedidos_usuario = (
        db.query(models.Pedido)
        .filter(models.Pedido.usuario_id == usuario_actual.id)
        .all()
    )

    if pedidos_usuario:
        # Contar frecuencia de cada item en los pedidos del usuario
        conteo = {}
        for pedido in pedidos_usuario:
            for detalle in pedido.items:
                conteo[detalle.item_id] = conteo.get(detalle.item_id, 0) + detalle.cantidad

        # Ordenar por más pedido y tomar los top 3
        top_ids = sorted(conteo, key=conteo.get, reverse=True)[:3]
        recomendaciones = [
            db.query(models.ItemMenu).filter(
                models.ItemMenu.id == item_id,
                models.ItemMenu.disponible == True
            ).first()
            for item_id in top_ids
        ]
        recomendaciones = [r for r in recomendaciones if r is not None]
        mensaje = f"Basado en tus pedidos anteriores, {usuario_actual.nombre}"
    else:
        # Sin historial: devolver los primeros 3 platillos disponibles
        recomendaciones = (
            db.query(models.ItemMenu)
            .filter(models.ItemMenu.disponible == True)
            .limit(3)
            .all()
        )
        mensaje = "Nuestros platillos más populares"

    return {
        "mensaje": mensaje,
        "recomendaciones": [
            {
                "id": item.id,
                "nombre": item.nombre,
                "descripcion": item.descripcion,
                "precio": item.precio,
                "categoria": item.categoria,
            }
            for item in recomendaciones
        ]
    }
