from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- USUARIOS ---
class UsuarioCreate(BaseModel):
    nombre: str
    correo: EmailStr
    password: str

class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

class UsuarioOut(BaseModel):
    id: int
    nombre: str
    correo: str
    fecha_registro: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- MESAS ---
class MesaOut(BaseModel):
    id: int
    numero: int
    capacidad: int
    tipo: str
    estado: str
    es_componible: bool
    tablones_disponibles: int
    pos_x: int
    pos_y: int

    class Config:
        from_attributes = True

# --- MENU ---
class ItemMenuOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    categoria: str
    disponible: bool

    class Config:
        from_attributes = True

# --- PEDIDOS ---
class DetallePedidoCreate(BaseModel):
    item_id: int
    cantidad: int

class PedidoCreate(BaseModel):
    mesa_id: Optional[int]
    items: List[DetallePedidoCreate]

class DetallePedidoOut(BaseModel):
    item_id: int
    cantidad: int
    precio_unitario: float

    class Config:
        from_attributes = True

class PedidoOut(BaseModel):
    id: int
    estado: str
    total: float
    fecha_creacion: datetime
    items: List[DetallePedidoOut]

    class Config:
        from_attributes = True

# --- RESERVACIONES ---
class ReservacionCreate(BaseModel):
    mesa_id: int
    num_personas: int
    fecha_hora: datetime

class ReservacionOut(BaseModel):
    id: int
    mesa_id: int
    num_personas: int
    fecha_hora: datetime
    activa: bool

    class Config:
        from_attributes = True