from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/pedidos", tags=["pedidos"])

@router.post("/", response_model=schemas.PedidoOut)
def crear_pedido(
    datos: schemas.PedidoCreate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    total = 0.0
    detalles = []

    for detalle in datos.items:
        item = db.query(models.ItemMenu).filter(models.ItemMenu.id == detalle.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {detalle.item_id} no encontrado")
        subtotal = item.precio * detalle.cantidad
        total += subtotal
        detalles.append(models.DetallePedido(
            item_id=item.id,
            cantidad=detalle.cantidad,
            precio_unitario=item.precio
        ))

    pedido = models.Pedido(
        usuario_id=usuario_actual.id,
        mesa_id=datos.mesa_id,
        total=total,
        estado="pendiente"
    )
    db.add(pedido)
    db.flush()

    for d in detalles:
        d.pedido_id = pedido.id
        db.add(d)

    # Actualizar estado de mesa
    if datos.mesa_id:
        mesa = db.query(models.Mesa).filter(models.Mesa.id == datos.mesa_id).first()
        if mesa:
            mesa.estado = models.EstadoMesa.esperando_pedido

    db.commit()
    db.refresh(pedido)
    return pedido

@router.get("/mis-pedidos")
def mis_pedidos(
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    return db.query(models.Pedido).filter(
        models.Pedido.usuario_id == usuario_actual.id
    ).order_by(models.Pedido.fecha_creacion.desc()).all()

@router.patch("/{pedido_id}/estado")
def actualizar_estado_pedido(
    pedido_id: int,
    estado: str,
    db: Session = Depends(get_db),
    usuario_actual=Depends(auth.get_usuario_actual)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    estados_validos = ["pendiente", "preparando", "listo", "entregado"]
    if estado not in estados_validos:
        raise HTTPException(status_code=400, detail="Estado inválido")

    pedido.estado = estado

    # Si el pedido fue entregado, mesa pasa a "comiendo"
    if estado == "entregado" and pedido.mesa_id:
        mesa = db.query(models.Mesa).filter(models.Mesa.id == pedido.mesa_id).first()
        if mesa:
            mesa.estado = models.EstadoMesa.ocupada

    db.commit()
    return {"mensaje": f"Pedido {pedido_id} actualizado a '{estado}'"}