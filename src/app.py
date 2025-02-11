import sys
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config.config import Config
from models.db import db, Cliente, Proveedor, Producto, Venta, DetalleVenta, Factura, Usuario
from datetime import datetime
from sqlalchemy import func


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

# Ruta para el carrito de compras
@app.route('/carrito')
def carrito():
    if 'usuario_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    usuario_id = session['usuario_id']
    ventas = Venta.query.filter_by(id_cliente=usuario_id).all()
    return render_template('carrito.html', ventas=ventas)

# Ruta para añadir un producto al carrito
@app.route('/add_to_cart/<int:producto_id>', methods=['POST'])
def add_to_cart(producto_id):
    if 'usuario_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    producto = Producto.query.get(producto_id)
    if producto:
        nueva_venta = Venta(
            fecha=datetime.now(),
            id_cliente=session['usuario_id']
        )
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

# Ruta para la vista de proveedores (administrador)
@app.route('/admin/proveedores', methods=['GET'])
def admin_proveedores():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    proveedores = Proveedor.query.all()
    return render_template('admin_proveedores.html', proveedores=proveedores)

@app.route('/admin/ventas', methods=['GET'])
def admin_ventas():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))  # Redirige al login si no es admin o no ha iniciado sesión

    # Obtener todos los clientes
    clientes = Cliente.query.all()

    # Construir la información necesaria para el template
    cliente_info = []
    for cliente in clientes:
        # Obtener las ventas del cliente
        ventas_cliente = Venta.query.filter_by(id_cliente=cliente.id_cliente).all()
        productos_comprados = []
        
        # Obtener los productos comprados en cada venta
        for venta in ventas_cliente:
            for detalle in venta.detalles:
                producto = Producto.query.get(detalle.id_producto)
                productos_comprados.append({
                    'producto': producto.nombre,
                    'fecha_compra': venta.fecha_venta.strftime('%Y-%m-%d')
                })
        
        cliente_info.append({
            'cliente': cliente,
            'productos_comprados': productos_comprados
        })

    # Enviar los datos al template
    return render_template('admin_ventas.html', cliente_info=cliente_info)

# Ruta para la vista de productos (administrador) con las opciones
@app.route('/admin/productos', methods=['GET'])
def admin_productos():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('admin_productos.html')

# Subruta para productos disponibles
@app.route('/admin/productos/disponibles', methods=['GET'])
def productos_disponibles():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Consulta los productos con stock disponible
    productos = Producto.query.filter(Producto.stock > 0).all()
    
    # Ajusta la ruta de las imágenes
    for producto in productos:
        if producto.foto.startswith("static/uploads/"):
            producto.foto = producto.foto.replace("static/uploads/", "uploads/")
        elif not producto.foto.startswith("uploads/"):
            producto.foto = f"uploads/{producto.foto}"
    
    return render_template('admin_productos_disponibles.html', productos=productos)

# Subruta para productos agotados
@app.route('/admin/productos/agotados', methods=['GET'])
def productos_agotados():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Consulta los productos sin stock
    productos = Producto.query.filter(Producto.stock == 0).all()
    
    # Ajusta la ruta de las imágenes
    for producto in productos:
        if producto.foto.startswith("static/uploads/"):
            producto.foto = producto.foto.replace("static/uploads/", "uploads/")
        elif not producto.foto.startswith("uploads/"):
            producto.foto = f"uploads/{producto.foto}"
    
    return render_template('productos_agotados.html', productos=productos)

# Ruta para el informe de ventas con selección de mes y año
@app.route('/admin/informe_ventas', methods=['GET', 'POST'])
def informe_ventas():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Inicializar las variables de ventas, la bandera de mostrar y los valores de año y mes
    ventas = []
    mostrar_informe = False
    
    # Establecer valores predeterminados si no se ha enviado el formulario
    año = request.form.get('año', type=int) if request.method == 'POST' else 2025
    mes = request.form.get('mes', type=int) if request.method == 'POST' else 1

    # Verificar si se ha enviado el formulario (POST)
    if request.method == 'POST':
        # Filtrar las ventas por año y mes, y acceder al cliente relacionado
        ventas = Venta.query.filter(
            db.extract('year', Venta.fecha_venta) == año,
            db.extract('month', Venta.fecha_venta) == mes
        ).all()
        
        # Establecer la bandera para mostrar el informe
        mostrar_informe = True

    # Retornar el template con las ventas, año, mes, y la bandera de mostrar informe
    return render_template('informe.html', ventas=ventas, mostrar_informe=mostrar_informe, año=año, mes=mes)

# Ruta para eliminar un producto por su ID
@app.route('/admin/productos/eliminar/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Buscar el producto en la base de datos
    producto = Producto.query.get(producto_id)
    if not producto:
        return 'Producto no encontrado', 404
    
    # Eliminar la imagen del sistema de archivos si existe
    if producto.foto and os.path.exists(os.path.join('src', producto.foto)):
        os.remove(os.path.join('src', producto.foto))
    
    # Eliminar el producto de la base de datos
    db.session.delete(producto)
    db.session.commit()
    
    return redirect(url_for('productos_disponibles'))

# Ruta para eliminar un proveedor por su ID
@app.route('/admin/proveedores/eliminar/<int:proveedor_id>', methods=['POST'])
def eliminar_proveedor(proveedor_id):
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Buscar el proveedor en la base de datos
    proveedor = Proveedor.query.get(proveedor_id)
    if not proveedor:
        return 'Proveedor no encontrado', 404
    
    # Eliminar el proveedor de la base de datos
    db.session.delete(proveedor)
    db.session.commit()
    
    return redirect(url_for('admin_proveedores'))
# Subruta para agregar un producto
@app.route('/admin/add_product_form')
def add_product_form():
    return render_template('add_product.html')
# subruta para agregar un proveedor
@app.route('/admin/add_supplier_form')
def add_supplier_form():
    return render_template('add_supplier.html')

    # Insertar el producto en la base de datos
@app.route('/admin/add_product', methods=['POST'])
def add_product():
    nombre = request.form['nombre']
    foto = request.files['foto']
    stock = int(request.form['stock'])
    descripcion = request.form['descripcion']
    precio = float(request.form['precio'])

    # Guardar la foto en una carpeta estática
    foto_path = f'static/uploads/{foto.filename}'
    foto.save(os.path.join('src/static/uploads', foto.filename))

    # Crear un nuevo producto y guardarlo en la base de datos
    nuevo_producto = Producto(nombre=nombre, foto=foto_path, stock=stock, descripcion=descripcion, precio=precio)
    db.session.add(nuevo_producto)
    db.session.commit()

    return redirect('/admin')
    
    # Insertar el proveedor en la base de datos
@app.route('/admin/add_supplier', methods=['POST'])
def add_supplier():
    nombre = request.form['nombre']
    contacto = request.form['contacto']

    # Crear un nuevo proveedor con los datos ingresados
    nuevo_proveedor = Proveedor(nombre=nombre, contacto=contacto)
    db.session.add(nuevo_proveedor)
    db.session.commit()

    return redirect('/admin')

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)