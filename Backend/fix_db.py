import sqlite3
conn = sqlite3.connect('pezgallo.db')
try:
    conn.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT DEFAULT 'cliente'")
except:
    pass
conn.execute("UPDATE usuarios SET rol='admin' WHERE correo='segundas@serviciosweb.com'")
conn.commit()
conn.close()
print('Listo')