from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ─────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────
class UsuarioCreate(BaseModel):
    nombre: str
    correo: EmailStr
    password: str

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[EmailStr] = None
    password: Optional[str] = None
    rol: Optional[str] = None

class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

class UsuarioOut(BaseModel):
    id: int
    nombre: str
    correo: str
    rol: str
    fecha_registro: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ─────────────────────────────────────────
# MESAS
# ─────────────────────────────────────────
class MesaCreate(BaseModel):
    numero: int
    capacidad: int
    tipo: str                          # pequena | mediana | grande
    estado: Optional[str] = "libre"
    es_componible: Optional[bool] = False
    tablones_disponibles: Optional[int] = 0
    pos_x: Optional[int] = 0
    pos_y: Optional[int] = 0

class MesaUpdate(BaseModel):
    numero: Optional[int] = None
    capacidad: Optional[int] = None
    tipo: Optional[str] = None
    estado: Optional[str] = None
    es_componible: Optional[bool] = None
    tablones_disponibles: Optional[int] = None
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None

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

# ─────────────────────────────────────────
# MENÚ
# ─────────────────────────────────────────
class ItemMenuCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    categoria: str
    disponible: Optional[bool] = True

class ItemMenuUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    categoria: Optional[str] = None
    disponible: Optional[bool] = None

class ItemMenuOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    categoria: str
    disponible: bool

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# RESERVACIONES
# ─────────────────────────────────────────
class ReservacionCreate(BaseModel):
    mesa_id: int
    num_personas: int
    fecha_hora: datetime

class ReservacionUpdate(BaseModel):
    mesa_id: Optional[int] = None
    num_personas: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    activa: Optional[bool] = None

class ReservacionOut(BaseModel):
    id: int
    usuario_id: int
    mesa_id: int
    num_personas: int
    fecha_hora: datetime
    activa: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# PEDIDOS
# ─────────────────────────────────────────
class DetallePedidoCreate(BaseModel):
    item_id: int
    cantidad: int

class PedidoCreate(BaseModel):
    mesa_id: Optional[int] = None
    items: List[DetallePedidoCreate]

class PedidoUpdate(BaseModel):
    estado: Optional[str] = None      # pendiente | preparando | listo | entregado
    mesa_id: Optional[int] = None

class DetallePedidoOut(BaseModel):
    id: int
    item_id: int
    cantidad: int
    precio_unitario: float

    class Config:
        from_attributes = True

class PedidoOut(BaseModel):
    id: int
    usuario_id: int
    mesa_id: Optional[int]
    estado: str
    total: float
    fecha_creacion: datetime
    items: List[DetallePedidoOut]

    class Config:
        from_attributes = True

# ─────────────────────────────────────────
# ADMIN (respuestas enriquecidas)
# ─────────────────────────────────────────
class AdminPedidoItemOut(BaseModel):
    nombre: str
    cantidad: int
    precio_unitario: float

class AdminPedidoOut(BaseModel):
    id: int
    usuario: str
    mesa: Optional[int]
    estado: str
    total: float
    fecha: datetime
    items: List[AdminPedidoItemOut]

class EstadoPedidoUpdate(BaseModel):
    estado: str

class EstadoMesaUpdate(BaseModel):
    estado: str
