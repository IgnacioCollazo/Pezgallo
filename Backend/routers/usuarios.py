from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
from datetime import timedelta

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.post("/registro", response_model=schemas.UsuarioOut)
def registrar(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    existe = db.query(models.Usuario).filter(models.Usuario.correo == usuario.correo).first()
    if existe:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    nuevo = models.Usuario(
        nombre=usuario.nombre,
        correo=usuario.correo,
        password_hash=auth.hashear_password(usuario.password)
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.post("/login", response_model=schemas.Token)
def login(datos: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.correo == datos.correo).first()
    if not usuario or not auth.verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = auth.crear_token(
        data={"sub": usuario.correo},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

@router.get("/yo", response_model=schemas.UsuarioOut)
def mi_perfil(usuario_actual=Depends(auth.get_usuario_actual)):
    return usuario_actual