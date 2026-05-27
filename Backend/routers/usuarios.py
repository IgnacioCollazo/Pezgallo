from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth import hashear_password, verificar_password, crear_token, get_usuario_actual
import models, schemas
from typing import List

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# ─── CREATE ───────────────────────────────────────────────────────────────────
@router.post("/registro", response_model=schemas.UsuarioOut, status_code=201)
def registrar_usuario(data: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Usuario).filter(models.Usuario.correo == data.correo).first()
    if existente:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    usuario = models.Usuario(
        nombre=data.nombre,
        correo=data.correo,
        password_hash=hashear_password(data.password),
        rol="cliente"
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario

# ─── LOGIN ────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=schemas.Token)
def login(data: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.correo == data.correo).first()
    if not usuario or not verificar_password(data.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = crear_token({"sub": usuario.correo})
    return {"access_token": token, "token_type": "bearer"}

# ─── READ (yo) ────────────────────────────────────────────────────────────────
@router.get("/yo", response_model=schemas.UsuarioOut)
def perfil_actual(usuario: models.Usuario = Depends(get_usuario_actual)):
    return usuario

# ─── READ ALL (solo admin) ────────────────────────────────────────────────────
@router.get("/", response_model=List[schemas.UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return db.query(models.Usuario).all()

# ─── READ ONE ────────────────────────────────────────────────────────────────
@router.get("/{usuario_id}", response_model=schemas.UsuarioOut)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    # Admin puede ver cualquiera; cliente solo a sí mismo
    if usuario_actual.rol != "admin" and usuario_actual.id != usuario_id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# ─── UPDATE ───────────────────────────────────────────────────────────────────
@router.put("/{usuario_id}", response_model=schemas.UsuarioOut)
def actualizar_usuario(
    usuario_id: int,
    data: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin" and usuario_actual.id != usuario_id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.nombre is not None:
        usuario.nombre = data.nombre
    if data.correo is not None:
        # verificar que no esté en uso
        dup = db.query(models.Usuario).filter(
            models.Usuario.correo == data.correo,
            models.Usuario.id != usuario_id
        ).first()
        if dup:
            raise HTTPException(status_code=400, detail="Correo ya en uso")
        usuario.correo = data.correo
    if data.password is not None:
        usuario.password_hash = hashear_password(data.password)
    if data.rol is not None and usuario_actual.rol == "admin":
        usuario.rol = data.rol

    db.commit()
    db.refresh(usuario)
    return usuario

# ─── DELETE ───────────────────────────────────────────────────────────────────
@router.delete("/{usuario_id}", status_code=200)
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "admin" and usuario_actual.id != usuario_id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(usuario)
    db.commit()
    return {"mensaje": f"Usuario {usuario_id} eliminado correctamente"}
