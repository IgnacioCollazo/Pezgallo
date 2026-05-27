from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_usuario_actual
import models, schemas
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])

def verificar_admin(usuario_actual: models.Usuario):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")

# ─── PEDIDOS ──────────────────────────────────────────────────────────────────

@router.get("/pedidos", response_model=List[schemas.AdminPedidoOut])
def listar_pedidos_admin(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    verificar_admin(usuario_actual)
    pedidos = db.query(models.Pedido).order_by(models.Pedido.fecha_creacion.desc()).all()
    resultado = []
    for p in pedidos:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == p.usuario_id).first()
        items_out = []
        for det in p.items:
            item = db.query(models.ItemMenu).filter(models.ItemMenu.id == det.item_id).first()
            items_out.append(schemas.AdminPedidoItemOut(
                nombre=item.nombre if item else f"Item {det.item_id}",
                cantidad=det.cantidad,
                precio_unitario=det.precio_unitario
            ))
        resultado.append(schemas.AdminPedidoOut(
            id=p.id,
            usuario=usuario.nombre if usuario else "Desconocido",
            mesa=p.mesa_id,
            estado=p.estado,
            total=p.total,
            fecha=p.fecha_creacion,
            items=items_out
        ))
    return resultado

@router.patch("/pedidos/{pedido_id}/estado", response_model=schemas.PedidoOut)
def cambiar_estado_pedido(
    pedido_id: int,
    data: schemas.EstadoPedidoUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    verificar_admin(usuario_actual)
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

# ─── MESAS ────────────────────────────────────────────────────────────────────

@router.get("/mesas", response_model=List[schemas.MesaOut])
def listar_mesas_admin(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    verificar_admin(usuario_actual)
    return db.query(models.Mesa).order_by(models.Mesa.numero).all()

@router.patch("/mesas/{mesa_id}/estado", response_model=schemas.MesaOut)
def cambiar_estado_mesa(
    mesa_id: int,
    data: schemas.EstadoMesaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    verificar_admin(usuario_actual)
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

# ─── USUARIOS ─────────────────────────────────────────────────────────────────

@router.get("/usuarios", response_model=List[schemas.UsuarioOut])
def listar_usuarios_admin(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    verificar_admin(usuario_actual)
    return db.query(models.Usuario).all()

@router.patch("/usuarios/{usuario_id}/rol", response_model=schemas.UsuarioOut)
def cambiar_rol_usuario(
    usuario_id: int,
    rol: str,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    verificar_admin(usuario_actual)
    if rol not in ["admin", "cliente"]:
        raise HTTPException(status_code=400, detail="Rol inválido. Opciones: admin, cliente")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.rol = rol
    db.commit()
    db.refresh(usuario)
    return usuario

# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    verificar_admin(usuario_actual)
    total_pedidos = db.query(models.Pedido).count()
    pedidos_pendientes = db.query(models.Pedido).filter(models.Pedido.estado == "pendiente").count()
    pedidos_preparando = db.query(models.Pedido).filter(models.Pedido.estado == "preparando").count()
    mesas_libres = db.query(models.Mesa).filter(models.Mesa.estado == "libre").count()
    mesas_ocupadas = db.query(models.Mesa).filter(models.Mesa.estado == "ocupada").count()
    total_usuarios = db.query(models.Usuario).count()
    total_platillos = db.query(models.ItemMenu).count()

    return {
        "pedidos": {
            "total": total_pedidos,
            "pendientes": pedidos_pendientes,
            "preparando": pedidos_preparando,
        },
        "mesas": {
            "libres": mesas_libres,
            "ocupadas": mesas_ocupadas,
        },
        "usuarios": total_usuarios,
        "platillos_en_menu": total_platillos,
    }
