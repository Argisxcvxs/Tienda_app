import sys
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config.config import Config
from models.db import db, Cliente, Proveedor, Producto, Venta, DetalleVenta, Factura, Usuario
from datetime import datetime

# Configuración de la app y base de datos
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
app.secret_key = Config.SECRET_KEY

# Crear el superusuario si no existe
with app.app_context():
    if not Usuario.query.filter_by(nombre_usuario='GUS').first():
        superusuario = Usuario(
            nombre_usuario='GUS',
            correo_electronico='gus@example.com',
            contrasena=generate_password_hash('1234567901'),
            is_admin=True
        )
        db.session.add(superusuario)
        db.session.commit()

# Ruta para el registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        correo_electronico = request.form['correo_electronico']
        contrasena = request.form['contrasena']
        
        # Verificar si el nombre de usuario o correo electrónico ya existen
        usuario_existente = Usuario.query.filter_by(nombre_usuario=nombre).first() or \
                             Usuario.query.filter_by(correo_electronico=correo_electronico).first()
        
        if usuario_existente:
            return 'El nombre de usuario o correo electrónico ya están registrados.'

        # Crear el nuevo usuario
        nuevo_usuario = Usuario(
            nombre_usuario=nombre,
            correo_electronico=correo_electronico,
            contrasena=generate_password_hash(contrasena)
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        return redirect(url_for('login'))  # Redirigir al login

    return render_template('register.html')

# Ruta para el inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo_electronico = request.form['correo_electronico']
        contrasena = request.form['contrasena']
        usuario = Usuario.query.filter_by(correo_electronico=correo_electronico).first()
        if usuario and check_password_hash(usuario.contrasena, contrasena):
            session['usuario_id'] = usuario.id_usuario
            session['is_admin'] = usuario.is_admin
            return redirect(url_for('index'))
        else:
            return 'Credenciales incorrectas'
    return render_template('login.html')

# Ruta para la página principal
@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    if session.get('is_admin'):
        return redirect(url_for('admin_index'))
    else:
        return redirect(url_for('catalogo'))

# Ruta para el panel de administración
@app.route('/admin')
def admin_index():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    clientes = Cliente.query.all()
    proveedores = Proveedor.query.all()
    productos = Producto.query.all()
    return render_template('admin_index.html', clientes=clientes, proveedores=proveedores, productos=productos)

# Ruta para el catálogo de productos
@app.route('/catalogo')
def catalogo():
    if 'usuario_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    productos = Producto.query.all()
    return render_template('catalogo.html', productos=productos)

# Ruta para mostrar la lista de clientes
@app.route('/clientes')
def mostrar_clientes():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

# Ruta para mostrar la lista de proveedores
@app.route('/proveedores')
def mostrar_proveedores():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    proveedores = Proveedor.query.all()
    return render_template('proveedores.html', proveedores=proveedores)

# Ruta para mostrar la lista de productos
@app.route('/productos')
def mostrar_productos():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)

# Ruta para el carrito de compras
@app.route('/carrito')
def carrito():
    if 'usuario_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    usuario_id = session['usuario_id']
    ventas = Venta.query.filter_by(id_cliente=usuario_id).all()
    return render_template('carrito.html', ventas=ventas)

# Ruta para agregar un producto al carrito
@app.route('/agregar_al_carrito/<int:id_producto>', methods=['POST'])
def agregar_al_carrito(id_producto):
    if 'usuario_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    usuario_id = session['usuario_id']
    producto = Producto.query.get(id_producto)
    if producto:
        nueva_venta = Venta(id_cliente=usuario_id, fecha_venta=datetime.utcnow(), total=producto.precio)
        db.session.add(nueva_venta)
        db.session.commit()
        detalle_venta = DetalleVenta(
            id_venta=nueva_venta.id_venta,
            id_producto=producto.id_producto,
            cantidad=1,
            precio_unitario=producto.precio,
            subtotal=producto.precio
        )
        db.session.add(detalle_venta)
        db.session.commit()
        return redirect(url_for('carrito'))
    return 'Producto no encontrado'

if __name__ == '__main__':
    app.run(debug=True)
