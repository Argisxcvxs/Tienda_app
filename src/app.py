import sys
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
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

        # Crear el cliente asociado
        nuevo_cliente = Cliente(
            id_cliente=nuevo_usuario.id_usuario,  # Usa el mismo ID del usuario
            nombre=nombre,
            correo=correo_electronico
        )
        db.session.add(nuevo_cliente)
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
            # Guardar datos en la sesión
            session['usuario_id'] = usuario.id_usuario
            session['is_admin'] = usuario.is_admin
            
            print(f"Sesión iniciada: {session}")  # Debug para ver qué guarda la sesión
            
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

@app.route('/producto/<int:producto_id>')
def producto_detalle(producto_id):
    producto = Producto.query.filter_by(id_producto=producto_id).first_or_404()
    return render_template('producto_detalle.html', producto=producto)

# Ruta para el carrito de compras
@app.route('/carrito')
def carrito():
    if 'usuario_id' not in session or session.get('is_admin'):
        return redirect(url_for('catalogo'))
    
    # Obtener el ID del usuario desde la sesión
    usuario_id = session['usuario_id']
    
    # Buscar la venta asociada al usuario en estado 'carrito'
    venta = Venta.query.filter_by(id_cliente=usuario_id, estado='carrito').first()

    # Si no hay una venta en estado 'carrito', mostrar carrito vacío
    if not venta:
        detalles = []
    else:
        # Obtener los detalles de la venta excluyendo productos eliminados
        detalles = (
            DetalleVenta.query
            .outerjoin(Producto, DetalleVenta.id_producto == Producto.id_producto)
            .filter(
                DetalleVenta.id_venta == venta.id_venta,
                Producto.id_producto != None  # Asegura que el producto no ha sido eliminado
            )
            .all()
        )
    
    return render_template('carrito.html', detalles=detalles)

# Ruta para añadir un producto al carrito
@app.route('/add_to_cart/<int:producto_id>', methods=['POST'])
def add_to_cart(producto_id):
    if 'usuario_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    # Verificar si el cliente existe en la base de datos
    cliente = Cliente.query.get(session['usuario_id'])
    if not cliente:
        return 'Cliente no encontrado. Por favor, inicie sesión nuevamente.', 400

    # Verificar si el producto existe y hay stock
    producto = Producto.query.get(producto_id)
    if not producto or producto.stock <= 0:
        return 'Producto no encontrado o sin stock', 400

    # Buscar o crear una venta en estado 'carrito' para el cliente
    venta_actual = Venta.query.filter_by(id_cliente=cliente.id_cliente, estado='carrito').first()
    if not venta_actual:
        venta_actual = Venta(
            fecha_venta=datetime.now(),
            id_cliente=cliente.id_cliente,
            estado='carrito',
            total=0.0  # Inicializa el total como 0.0
        )
        db.session.add(venta_actual)
        db.session.commit()

    # Verificar si el producto ya está en el carrito
    detalle_existente = DetalleVenta.query.filter_by(id_venta=venta_actual.id_venta, id_producto=producto.id_producto).first()
    if detalle_existente:
        # Incrementar la cantidad y el subtotal del producto
        detalle_existente.cantidad += 1
        detalle_existente.subtotal += producto.precio
    else:
        # Crear un nuevo detalle de venta si no existe en el carrito
        detalle_venta = DetalleVenta(
            id_venta=venta_actual.id_venta,
            id_producto=producto.id_producto,
            cantidad=1,
            precio_unitario=producto.precio,
            subtotal=producto.precio,
            nombre_producto=producto.nombre  # Aquí se agrega el nombre del producto
        )
        db.session.add(detalle_venta)

    # Reducir el stock del producto
    producto.stock -= 1

    # Actualizar el total de la venta
    venta_actual.total += producto.precio

    # Guardar todos los cambios
    db.session.commit()

    return redirect(url_for('carrito'))

#ruta para procesar la compra
@app.route('/procesar_compra', methods=['POST'])
def procesar_compra():
    id_venta = request.form.get('id_venta')
    id_producto = request.form.get('id_producto')
    cantidad = int(request.form.get('cantidad', 1))  # Por defecto, una unidad

    # Validaciones básicas
    if not id_venta or not id_producto:
        flash("Error: Faltan datos para procesar la compra.")
        return redirect(url_for('carrito'))

    try:
        # Obtener los datos del producto
        producto = Producto.query.get(id_producto)
        if not producto:
            flash("Producto no encontrado.")
            return redirect(url_for('carrito'))

        # Crear un registro en detalles de venta
        detalle = DetalleVenta(
            id_venta=id_venta,
            id_producto=id_producto,
            cantidad=cantidad,
            precio_unitario=producto.precio,  # Guarda el precio actual del producto
            subtotal=producto.precio * cantidad,  # Calcula el subtotal
            nombre_producto=producto.nombre  # Guarda el nombre del producto
        )
        db.session.add(detalle)
        db.session.commit()

        flash("Compra procesada exitosamente.")
        return redirect(url_for('carrito'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar la compra: {str(e)}")
        return redirect(url_for('carrito'))

# Ruta para la vista de proveedores (administrador)
@app.route('/admin/proveedores', methods=['GET'])
def admin_proveedores():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    proveedores = Proveedor.query.all()
    return render_template('admin_proveedores.html', proveedores=proveedores)

#ruta para la ventas de los productos
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
                if producto:  # Si el producto existe
                    productos_comprados.append({
                        'producto': producto.nombre,
                        'fecha_compra': venta.fecha_venta.strftime('%Y-%m-%d')
                    })
                else:  # Si el producto fue eliminado
                    productos_comprados.append({
                        'producto': 'Producto eliminado',
                        'fecha_compra': venta.fecha_venta.strftime('%Y-%m-%d')
                    })

        # Solo agregar información si el cliente tiene productos comprados
        if cliente and productos_comprados:
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
    
    # Ajusta la ruta de las imágenes si corresponde
    for producto in productos:
        if producto.foto:
            if producto.foto.startswith("static/uploads/"):
                producto.foto = producto.foto.replace("static/uploads/", "uploads/")
            elif not producto.foto.startswith("uploads/"):
                producto.foto = f"uploads/{producto.foto}"
        else:
            # Asigna una imagen predeterminada si no tiene foto
            producto.foto = "default_image.jpg"
    
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
    # Verificar si el usuario está autenticado y es administrador
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Buscar el producto en la base de datos
    producto = Producto.query.get(producto_id)
    if not producto:
        return 'Producto no encontrado', 404
    
    # Eliminar la imagen del sistema de archivos si existe
    if producto.foto and isinstance(producto.foto, str):
        foto_path = os.path.join('src', producto.foto)
        if os.path.exists(foto_path):
            os.remove(foto_path)
    
    # Eliminar el producto de la base de datos
    db.session.delete(producto)
    db.session.commit()
    
    # Redirigir al catálogo de productos disponibles
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

@app.route('/facturas')
def lista_facturas():
    """Muestra la lista de facturas."""
    facturas = Factura.query.all()
    return render_template('lista_facturas.html', facturas=facturas)

@app.route('/facturas/crear/<int:id_venta>', methods=['GET', 'POST'])
def crear_factura(id_venta):
    """Crea una nueva factura para una venta existente."""
    venta = Venta.query.get(id_venta)

    if not venta:
        return f"La venta con ID {id_venta} no existe.", 404

    if request.method == 'POST':
        fecha_emision = datetime.now()
        total = venta.total  # Asume que el modelo Venta tiene un campo `total`

        nueva_factura = Factura(id_venta=id_venta, fecha_emision=fecha_emision, total=total)
        db.session.add(nueva_factura)
        db.session.commit()

        return redirect(url_for('lista_facturas'))

    return render_template('crear_factura.html', venta=venta)

if __name__ == '__main__':
    app.run(debug=True)

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)