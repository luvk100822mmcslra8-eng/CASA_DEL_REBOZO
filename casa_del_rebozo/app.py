"""Casa del Rebozo — aplicación completa (Sprints 1 a 4).
Ejecutar:  pip install flask   y luego   python app.py
Abrir:     http://127.0.0.1:5000
Admin:     usuario  admin   |  contraseña  rebozo123  (cámbiala abajo)
"""
import os
import re
import sqlite3
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "casa_del_rebozo.db")
UPLOADS = os.path.join(BASE, "static", "uploads")
EXTENSIONES = {"png", "jpg", "jpeg", "webp", "gif"}

ADMIN_USUARIO = "admin"
ADMIN_HASH = generate_password_hash("rebozo123")

CATEGORIAS = ["Rebozos", "Blusas", "Vestidos", "Accesorios", "Hogar"]

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-en-produccion"
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB por imagen


# ---------- Base de datos ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(_):
    conexion = g.pop("db", None)
    if conexion:
        conexion.close()


def iniciar_db():
    os.makedirs(UPLOADS, exist_ok=True)
    with sqlite3.connect(DB) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS productos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT DEFAULT '',
            precio REAL NOT NULL,
            cantidad INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            imagen TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS clientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            telefono TEXT NOT NULL,
            contrasena TEXT NOT NULL
        );
        """)


def admin_requerido(vista):
    @wraps(vista)
    def envoltura(*a, **k):
        if not session.get("admin"):
            flash("Inicia sesión para entrar al panel.", "error")
            return redirect(url_for("login"))
        return vista(*a, **k)
    return envoltura


# ---------- Sprint 1: inicio de sesión del administrador ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("contrasena", "")
        if usuario == ADMIN_USUARIO and check_password_hash(ADMIN_HASH, clave):
            session["admin"] = True
            return redirect(url_for("panel"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("catalogo"))


@app.route("/panel")
@admin_requerido
def panel():
    c = db()
    datos = {
        "productos": c.execute("SELECT COUNT(*) FROM productos").fetchone()[0],
        "clientes": c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0],
        "existencias": c.execute(
            "SELECT COALESCE(SUM(cantidad),0) FROM productos").fetchone()[0],
    }
    return render_template("panel.html", datos=datos)


# ---------- Sprint 2: registro de productos ----------
def imagen_valida(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in EXTENSIONES


@app.route("/productos", methods=["GET", "POST"])
@admin_requerido
def productos():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        categoria = request.form.get("categoria", "")
        errores = []
        try:
            precio = float(request.form.get("precio", ""))
            if precio <= 0:
                errores.append("El precio debe ser mayor que cero.")
        except ValueError:
            precio = 0
            errores.append("El precio debe ser un número.")
        try:
            cantidad = int(request.form.get("cantidad", ""))
            if cantidad < 0:
                errores.append("La cantidad no puede ser negativa.")
        except ValueError:
            cantidad = 0
            errores.append("La cantidad debe ser un número entero.")
        if not nombre:
            errores.append("Escribe el nombre del producto.")
        if categoria not in CATEGORIAS:
            errores.append("Elige una categoría de la lista.")

        archivo = request.files.get("imagen")
        nombre_imagen = ""
        if archivo and archivo.filename:
            if imagen_valida(archivo.filename):
                nombre_imagen = secure_filename(archivo.filename)
                base, ext = os.path.splitext(nombre_imagen)
                n = 1
                while os.path.exists(os.path.join(UPLOADS, nombre_imagen)):
                    nombre_imagen = f"{base}-{n}{ext}"
                    n += 1
            else:
                errores.append("La imagen debe ser PNG, JPG, WEBP o GIF.")

        if errores:
            for e in errores:
                flash(e, "error")
        else:
            if nombre_imagen:
                archivo.save(os.path.join(UPLOADS, nombre_imagen))
            db().execute(
                "INSERT INTO productos(nombre,descripcion,precio,cantidad,"
                "categoria,imagen) VALUES(?,?,?,?,?,?)",
                (nombre, descripcion, precio, cantidad, categoria,
                 nombre_imagen))
            db().commit()
            flash("Producto guardado.", "ok")
            return redirect(url_for("productos"))

    lista = db().execute("SELECT * FROM productos ORDER BY id DESC").fetchall()
    return render_template("productos.html", lista=lista,
                           categorias=CATEGORIAS)


@app.route("/productos/<int:pid>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_producto(pid):
    db().execute("DELETE FROM productos WHERE id=?", (pid,))
    db().commit()
    flash("Producto eliminado.", "ok")
    return redirect(url_for("productos"))


# ---------- Sprint 3: catálogo para el cliente ----------
@app.route("/")
@app.route("/catalogo")
def catalogo():
    categoria = request.args.get("categoria", "")
    if categoria in CATEGORIAS:
        filas = db().execute(
            "SELECT * FROM productos WHERE categoria=? AND cantidad>0 "
            "ORDER BY id DESC", (categoria,)).fetchall()
    else:
        categoria = ""
        filas = db().execute(
            "SELECT * FROM productos WHERE cantidad>0 ORDER BY id DESC"
        ).fetchall()
    return render_template("catalogo.html", lista=filas,
                           categorias=CATEGORIAS, activa=categoria)


# ---------- Sprint 4: registro de clientes con validación ----------
CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
TELEFONO = re.compile(r"^\d{10}$")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    valores = {"nombre": "", "correo": "", "telefono": ""}
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        telefono = re.sub(r"[\s-]", "", request.form.get("telefono", ""))
        clave = request.form.get("contrasena", "")
        repetir = request.form.get("repetir", "")
        valores = {"nombre": nombre, "correo": correo, "telefono": telefono}

        errores = []
        if len(nombre) < 3:
            errores.append("El nombre debe tener al menos 3 letras.")
        if not CORREO.match(correo):
            errores.append("Escribe un correo válido, como ana@correo.com.")
        if not TELEFONO.match(telefono):
            errores.append("El teléfono debe tener 10 dígitos.")
        if len(clave) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if clave != repetir:
            errores.append("Las contraseñas no coinciden.")
        if not errores and db().execute(
                "SELECT 1 FROM clientes WHERE correo=?", (correo,)).fetchone():
            errores.append("Ese correo ya está registrado.")

        if errores:
            for e in errores:
                flash(e, "error")
        else:
            db().execute(
                "INSERT INTO clientes(nombre,correo,telefono,contrasena) "
                "VALUES(?,?,?,?)",
                (nombre, correo, telefono, generate_password_hash(clave)))
            db().commit()
            flash("Registro completo. ¡Bienvenida a Casa del Rebozo!", "ok")
            return redirect(url_for("catalogo"))
    return render_template("registro.html", v=valores)


@app.route("/clientes")
@admin_requerido
def clientes():
    lista = db().execute(
        "SELECT id,nombre,correo,telefono FROM clientes ORDER BY id DESC"
    ).fetchall()
    return render_template("clientes.html", lista=lista)


@app.template_filter("pesos")
def pesos(valor):
    return f"${valor:,.2f}"


if __name__ == "__main__":
    iniciar_db()
app.run(debug=True)