import sqlite3

conn = sqlite3.connect("casa_del_rebozo.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS productos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  precio REAL NOT NULL,
  imagen TEXT,
  categoria TEXT,
  cantidad INTEGER DEFAULT 10
)

""")

cur.execute("SELECT COUNT(*) FROM productos")
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO productos (nombre, descripcion, precio, imagen, categoria, cantidad) VALUES (?,?,?,?,?,?)",
                ("Rebozo Tradicional", "Rebozo artesanal de Tenancingo", 450.00, "rebozo_1.jpg", "Rebozos", 10))
    cur.execute("INSERT INTO productos (nombre, descripcion, precio, imagen, categoria, cantidad) VALUES (?,?,?,?,?,?)",
                ("Blusa Bordada", "Blusa artesanal", 350.00, "blusa_1.jpg", "Blusas", 5))
    cur.execute("INSERT INTO productos (nombre, descripcion, precio, imagen, categoria, cantidad) VALUES (?,?,?,?,?,?)",
                ("Vestido Artesanal", "Vestido artesanal", 500.00, "vestido_2.jpg", "Vestidos", 5))
    cur.execute("INSERT INTO productos (nombre, descripcion, precio, imagen, categoria, cantidad) VALUES (?,?,?,?,?,?)",
                ("Accesorio Artesanal", "Accesorio artesanal", 120.00, "accesorios_2.jpg", "Accesorios", 10))
    cur.execute("INSERT INTO productos (nombre, descripcion, precio, imagen, categoria, cantidad) VALUES (?,?,?,?,?,?)",
                ("Articulo para Hogar", "Articulo para hogar", 250.00, "hogar_1.jpg", "Hogar", 5))
                
conn.commit()
conn.close()
print("Listo, tabla productos creada")