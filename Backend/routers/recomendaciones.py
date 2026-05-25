from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models, auth

router = APIRouter(prefix="/recomendaciones", tags=["recomendaciones"])

@router.get("/")
def obtener_recomendaciones(
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    """
    Lógica de recomendaciones:
    1. Detecta qué items pide frecuentemente el usuario
    2. Busca usuarios con gustos similares
    3. Recomienda lo que esos usuarios piden y este no ha probado
    """

    # Items que ha pedido el usuario actual
    mis_items = db.query(
        models.DetallePedido.item_id,
        func.count(models.DetallePedido.item_id).label('veces')
    ).join(models.Pedido).filter(
        models.Pedido.usuario_id == usuario_actual.id
    ).group_by(models.DetallePedido.item_id).all()

    mis_item_ids = [i.item_id for i in mis_items]

    if not mis_item_ids:
        # Sin historial: recomendar los más populares
        populares = db.query(
            models.ItemMenu,
            func.count(models.DetallePedido.id).label('total')
        ).join(models.DetallePedido, models.DetallePedido.item_id == models.ItemMenu.id
        ).group_by(models.ItemMenu.id
        ).order_by(func.count(models.DetallePedido.id).desc()
        ).limit(3).all()

        return {
            "tipo": "populares",
            "mensaje": "Los más pedidos en PezGallo",
            "recomendaciones": [
                {"id": item.id, "nombre": item.nombre, "precio": item.precio, "categoria": item.categoria}
                for item, _ in populares
            ]
        }

    # Usuarios que han pedido los mismos items que yo
    usuarios_similares = db.query(
        models.Pedido.usuario_id
    ).join(models.DetallePedido).filter(
        models.DetallePedido.item_id.in_(mis_item_ids),
        models.Pedido.usuario_id != usuario_actual.id
    ).distinct().all()

    ids_similares = [u.usuario_id for u in usuarios_similares]

    if not ids_similares:
        # Sin usuarios similares: recomendar de la misma categoría
        mis_categorias = db.query(models.ItemMenu.categoria).filter(
            models.ItemMenu.id.in_(mis_item_ids)
        ).distinct().all()
        cats = [c.categoria for c in mis_categorias]

        sugeridos = db.query(models.ItemMenu).filter(
            models.ItemMenu.categoria.in_(cats),
            ~models.ItemMenu.id.in_(mis_item_ids),
            models.ItemMenu.disponible == True
        ).limit(3).all()

        return {
            "tipo": "misma_categoria",
            "mensaje": f"Basado en tus categorías favoritas: {', '.join(cats)}",
            "recomendaciones": [
                {"id": i.id, "nombre": i.nombre, "precio": i.precio, "categoria": i.categoria}
                for i in sugeridos
            ]
        }

    # Items que piden usuarios similares y yo NO he pedido
    items_no_probados = db.query(
        models.ItemMenu,
        func.count(models.DetallePedido.id).label('popularidad')
    ).join(models.DetallePedido, models.DetallePedido.item_id == models.ItemMenu.id
    ).join(models.Pedido, models.Pedido.id == models.DetallePedido.pedido_id
    ).filter(
        models.Pedido.usuario_id.in_(ids_similares),
        ~models.ItemMenu.id.in_(mis_item_ids),
        models.ItemMenu.disponible == True
    ).group_by(models.ItemMenu.id
    ).order_by(func.count(models.DetallePedido.id).desc()
    ).limit(3).all()

    # Item más pedido por el usuario (su favorito)
    favorito_id = max(mis_items, key=lambda x: x.veces).item_id
    favorito = db.query(models.ItemMenu).filter(models.ItemMenu.id == favorito_id).first()

    return {
        "tipo": "colaborativo",
        "mensaje": f"A quienes les gusta '{favorito.nombre}' como a ti, también disfrutan:",
        "recomendaciones": [
            {"id": item.id, "nombre": item.nombre, "precio": item.precio, "categoria": item.categoria}
            for item, _ in items_no_probados
        ]
    }