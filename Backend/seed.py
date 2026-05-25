from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --- MESAS ---
mesas = [
    # Mesas pequeñas (2 personas)
    {"numero": 1, "capacidad": 2, "tipo": "pequena", "pos_x": 1, "pos_y": 1},
    {"numero": 2, "capacidad": 2, "tipo": "pequena", "pos_x": 2, "pos_y": 1},
    {"numero": 3, "capacidad": 2, "tipo": "pequena", "pos_x": 3, "pos_y": 1},
    # Mesas medianas (4 personas)
    {"numero": 4, "capacidad": 4, "tipo": "mediana", "pos_x": 1, "pos_y": 3},
    {"numero": 5, "capacidad": 4, "tipo": "mediana", "pos_x": 2, "pos_y": 3},
    {"numero": 6, "capacidad": 4, "tipo": "mediana", "pos_x": 3, "pos_y": 3},
    # Mesas grandes (6 personas, componibles)
    {"numero": 7, "capacidad": 6, "tipo": "grande", "es_componible": True, "tablones_disponibles": 2, "pos_x": 1, "pos_y": 5},
    {"numero": 8, "capacidad": 6, "tipo": "grande", "es_componible": True, "tablones_disponibles": 2, "pos_x": 2, "pos_y": 5},
    {"numero": 9, "capacidad": 6, "tipo": "grande", "es_componible": True, "tablones_disponibles": 2, "pos_x": 3, "pos_y": 5},
]

for m in mesas:
    mesa = models.Mesa(**m)
    db.add(mesa)

# --- MENÚ ---
menu = [
    # Tostadas
    {"nombre": "Tostada de Aguachile", "descripcion": "Camaron fresco en aguachile verde, cebolla morada y pepino", "precio": 85.0, "categoria": "tostadas"},
    {"nombre": "Tostada Tahitiana", "descripcion": "Camaron marinado al estilo tahitiano con coco y limon", "precio": 90.0, "categoria": "tostadas"},
    {"nombre": "Tostada de Atun", "descripcion": "Atun fresco con aguacate y salsa de soya", "precio": 95.0, "categoria": "tostadas"},
    # Burritos
    {"nombre": "Burrito de Camaron", "descripcion": "Camaron salteado con arroz, frijoles y pico de gallo", "precio": 110.0, "categoria": "burritos"},
    {"nombre": "Burrito de Pescado", "descripcion": "Filete de pescado empanizado con ensalada y crema", "precio": 105.0, "categoria": "burritos"},
    # Hamburguesas
    {"nombre": "Hamburguesa Crunchy de Camaron", "descripcion": "Camaron crocante con lechuga, tomate y aderezo especial", "precio": 120.0, "categoria": "hamburguesas"},
    # Especialidades
    {"nombre": "Balazos", "descripcion": "Tostadas pequenas con camaron, limon y salsa valentina", "precio": 75.0, "categoria": "especialidades"},
    {"nombre": "Ceviche PezGallo", "descripcion": "Ceviche de camaron y pulpo con tostadas", "precio": 130.0, "categoria": "especialidades"},
    # Bebidas
    {"nombre": "Agua de Jamaica", "precio": 30.0, "categoria": "bebidas"},
    {"nombre": "Limonada", "precio": 35.0, "categoria": "bebidas"},
    {"nombre": "Refresco", "precio": 25.0, "categoria": "bebidas"},
]

for item in menu:
    i = models.ItemMenu(**item)
    db.add(i)

db.commit()
db.close()
print("✅ Base de datos poblada correctamente")