from database import SessionLocal, engine, Base
import models, auth

db = SessionLocal()

# Usuarios de prueba
usuarios = [
    {"nombre": "Romel", "correo": "romel@pezgallo.com", "password": "1234"},
    {"nombre": "Karol", "correo": "karol@pezgallo.com", "password": "1234"},
    {"nombre": "Ana",   "correo": "ana@pezgallo.com",   "password": "1234"},
]

for u in usuarios:
    existe = db.query(models.Usuario).filter(models.Usuario.correo == u["correo"]).first()
    if not existe:
        nuevo = models.Usuario(
            nombre=u["nombre"],
            correo=u["correo"],
            password_hash=auth.hashear_password(u["password"])
        )
        db.add(nuevo)

db.commit()

# Historial de pedidos simulado
# Romel: Burrito de camaron (id=4) + Tostada Tahitiana (id=2) — 4 veces
# Ana: Burrito de camaron (id=4) + Hamburguesa Crunchy (id=6)

def crear_pedido(usuario_id, items):
    pedido = models.Pedido(usuario_id=usuario_id, total=0)
    db.add(pedido)
    db.flush()
    total = 0
    for item_id, cantidad in items:
        item = db.query(models.ItemMenu).filter(models.ItemMenu.id == item_id).first()
        if item:
            db.add(models.DetallePedido(
                pedido_id=pedido.id,
                item_id=item_id,
                cantidad=cantidad,
                precio_unitario=item.precio
            ))
            total += item.precio * cantidad
    pedido.total = total
    db.commit()

romel = db.query(models.Usuario).filter(models.Usuario.correo == "romel@pezgallo.com").first()
ana   = db.query(models.Usuario).filter(models.Usuario.correo == "ana@pezgallo.com").first()

# Romel pide lo mismo 4 veces
for _ in range(4):
    crear_pedido(romel.id, [(4, 1), (2, 1)])  # Burrito camaron + Tahitiana

# Ana pide burrito + hamburguesa
crear_pedido(ana.id, [(4, 1), (6, 1)])  # Burrito camaron + Hamburguesa crunchy
crear_pedido(ana.id, [(7, 1), (2, 1)])  # Balazos + Tahitiana

db.close()
print("✅ Usuarios y historial creados")