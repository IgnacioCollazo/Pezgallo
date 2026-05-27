from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_usuario_actual
import models, schemas
from typing import List

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

# ─── CREATE ───────────────────────────────────────────────────────────────────
@router.post("/", response_model=schemas.PedidoOut, status_code=201)
def crear_pedido(
    data: schemas.PedidoCreate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if not data.items:
        raise HTTPException(status_code=400, detail="El pedido debe tener al menos un item")

    # Validar mesa si se envía
    if data.mesa_id:
        mesa = db.query(models.Mesa).filter(models.Mesa.id == data.mesa_id).first()
        if not mesa:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")

    pedido = models.Pedido(
        usuario_id=usuario_actual.id,
        mesa_id=data.mesa_id,
        estado="pendiente",
        total=0.0
    )
    db.add(pedido)
    db.flush()  # obtiene el id sin hacer commit

    total = 0.0
    for detalle in data.items:
        item = db.query(models.ItemMenu).filter(models.ItemMenu.id == detalle.item_id).first()
        if not item:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Platillo {detalle.item_id} no encontrado")
        if not item.disponible:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"'{item.nombre}' no está disponible")

        subtotal = item.precio * detalle.cantidad
        total += subtotal

        det = models.DetallePedido(
            pedido_id=pedido.id,
            item_id=item.id,
            cantidad=detalle.cantidad,
            precio_unitario=item.precio
        )
        db.add(det)

    pedido.total = round(total, 2)

    # Actualizar estado de la mesa si aplica
    if data.mesa_id:
        mesa = db.query(models.Mesa).filter(models.Mesa.id == data.mesa_id).first()
        if mesa:
            mesa.estado = models.EstadoMesa.esperando_pedido

    db.commit()
    db.refresh(pedido)
    return pedido

# ─── READ ALL (admin ve todos; cliente ve los suyos) ──────────────────────────
@router.get("/", response_model=List[schemas.PedidoOut])
def listar_pedidos(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol == "admin":
        return db.query(models.Pedido).order_by(models.Pedido.fecha_creacion.desc()).all()
    return (
        db.query(models.Pedido)
        .filter(models.Pedido.usuario_id == usuario_actual.id)
        .order_by(models.Pedido.fecha_creacion.desc())
        .all()
    )

# ─── MIS PEDIDOS (alias amigable para el frontend) ────────────────────────────
@router.get("/mis-pedidos", response_model=List[schemas.PedidoOut])
def mis_pedidos(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    return (
        db.query(models.Pedido)
        .filter(models.Pedido.usuario_id == usuario_actual.id)
        .order_by(models.Pedido.fecha_creacion.desc())
        .all()
    )

# ─── READ ONE ────────────────────────────────────────────────────────────────
@router.get("/{pedido_id}", response_model=schemas.PedidoOut)
def obtener_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if usuario_actual.rol != "admin" and pedido.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="Sin permiso para ver este pedido")
    return pedido

# ─── UPDATE estado ────────────────────────────────────────────────────────────
@router.put("/{pedido_id}", response_model=schemas.PedidoOut)
def actualizar_pedido(
    pedido_id: int,
    data: schemas.PedidoUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Solo admin puede cambiar el estado; el dueño puede cambiar la mesa
    if data.estado is not None:
        if usuario_actual.rol != "admin":
            raise HTTPException(status_code=403, detail="Solo admin puede cambiar el estado del pedido")
        estados_validos = ["pendiente", "preparando", "listo", "entregado"]
        if data.estado not in estados_validos:
            raise HTTPException(status_code=400, detail=f"Estado inválido. Opciones: {estados_validos}")
        pedido.estado = data.estado

    if data.mesa_id is not None:
        if usuario_actual.rol != "admin" and pedido.usuario_id != usuario_actual.id:
            raise HTTPException(status_code=403, detail="Sin permiso")
        pedido.mesa_id = data.mesa_id

    db.commit()
    db.refresh(pedido)
    return pedido

# ─── PATCH estado (alias para admin) ─────────────────────────────────────────
@router.patch("/{pedido_id}/estado", response_model=schemas.PedidoOut)
def cambiar_estado_pedido(
    pedido_id: int,
    data: schemas.EstadoPedidoUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    estados_validos = ["pendiente", "preparando", "listo", "entregado"]
    if data.estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Opciones: {estados_validos}")
    pedido.estado = data.estado
    db.commit()
    db.refresh(pedido)
    return pedido

# ─── DELETE (admin o dueño si está pendiente) ─────────────────────────────────
@router.delete("/{pedido_id}", status_code=200)
def eliminar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if usuario_actual.rol != "admin" and pedido.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    if usuario_actual.rol != "admin" and pedido.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solo puedes cancelar pedidos en estado 'pendiente'")

    # Eliminar detalles primero
    db.query(models.DetallePedido).filter(models.DetallePedido.pedido_id == pedido_id).delete()
    db.delete(pedido)
    db.commit()
    return {"mensaje": f"Pedido {pedido_id} eliminado correctamente"}
