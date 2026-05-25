from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum

class EstadoMesa(str, enum.Enum):
    libre = "libre"
    ocupada = "ocupada"
    esperando_pedido = "esperando_pedido"
    preparando = "preparando"
    reservada = "reservada"

class TipoMesa(str, enum.Enum):
    pequena = "pequena"   # 2 personas
    mediana = "mediana"   # 4 personas
    grande = "grande"     # 6 personas (2 tablones)

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)
    reservaciones = relationship("Reservacion", back_populates="usuario")
    pedidos = relationship("Pedido", back_populates="usuario")

class Mesa(Base):
    __tablename__ = "mesas"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, nullable=False)
    capacidad = Column(Integer, nullable=False)
    tipo = Column(Enum(TipoMesa), nullable=False)
    estado = Column(Enum(EstadoMesa), default=EstadoMesa.libre)
    # Para mesas grandes compuestas de 2 tablones
    es_componible = Column(Boolean, default=False)
    tablones_disponibles = Column(Integer, default=0)  # 0, 1 o 2
    pos_x = Column(Integer, default=0)  # posición en el mapa
    pos_y = Column(Integer, default=0)
    reservaciones = relationship("Reservacion", back_populates="mesa")

class ItemMenu(Base):
    __tablename__ = "items_menu"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    precio = Column(Float, nullable=False)
    categoria = Column(String, nullable=False)  # tostadas, burritos, etc
    disponible = Column(Boolean, default=True)

class Reservacion(Base):
    __tablename__ = "reservaciones"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    mesa_id = Column(Integer, ForeignKey("mesas.id"))
    num_personas = Column(Integer, nullable=False)
    fecha_hora = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    activa = Column(Boolean, default=True)
    usuario = relationship("Usuario", back_populates="reservaciones")
    mesa = relationship("Mesa", back_populates="reservaciones")

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    mesa_id = Column(Integer, ForeignKey("mesas.id"), nullable=True)
    estado = Column(String, default="pendiente")  # pendiente/preparando/listo/entregado
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    total = Column(Float, default=0.0)
    usuario = relationship("Usuario", back_populates="pedidos")
    items = relationship("DetallePedido", back_populates="pedido")

class DetallePedido(Base):
    __tablename__ = "detalle_pedidos"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    item_id = Column(Integer, ForeignKey("items_menu.id"))
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False)
    pedido = relationship("Pedido", back_populates="items")
    item = relationship("ItemMenu")