import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config.config import Config
from models.db import db, Cliente, Proveedor, Producto, Venta, DetalleVenta, Factura, Usuario
from datetime import datetime
from waitress import serve
import socket

# Configuración de la app y base de datos
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
app.secret_key = Config.SECRET_KEY

@app.route('/test_socket')
def test_socket():  # Renombré la función para evitar conflicto
    # Función para realizar una conexión utilizando socket
    def conectar_servidor():
        # Crear un socket TCP/IP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Conectar al servidor (por ejemplo, www.example.com en el puerto 80)
        s.connect(('www.example.com', 80))

        # Enviar una solicitud HTTP (GET request)
        request = "GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n"
        s.send(request.encode())

        # Recibir la respuesta del servidor
        response = s.recv(4096)
        s.close()  # Cerramos el socket

        return response.decode()

    # Llamamos a la función para conectar al servidor y obtener la respuesta
    server_response = conectar_servidor()

    # Retornamos la respuesta en la página web
    return f"<p>Response from server: {server_response}</p>"

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
    if not session.get('usuario_id'):
        return redirect(url_for('login'))
    if session.get('is_admin'):
        return redirect(url_for('admin_index'))
    else:
        return redirect(url_for('catalogo'))

# Ruta para el panel de administración
@app.route('/admin')
def admin_index():
    if not session.get('usuario_id') or not session.get('is_admin'):
        return redirect(url_for('login'))
    clientes = Cliente.query.all()
    proveedores = Proveedor.query.all()
    productos = Producto.query.all()
    return render_template('admin_index.html', clientes=clientes, proveedores=proveedores, productos=productos)

# Ruta para el catálogo de productos
@app.route('/catalogo')
def catalogo():
    if not session.get('usuario_id') or session.get('is_admin'):
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
    if not session.get('usuario_id') or session.get('is_admin'):
        return redirect(url_for('catalogo'))
    
    # Obtener el ID del usuario desde la sesión
    usuario_id = session.get('usuario_id')
    
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
    if not session.get('usuario_id') or session.get('is_admin'):
        return redirect(url_for('login'))

    cliente = db.session.get(Cliente, session.get('usuario_id'))  # Actualización del uso de Session.get
    if not cliente:
        flash("Error: Cliente no encontrado.")
        return redirect(url_for('catalogo'))

    try:
        producto = db.session.get(Producto, producto_id)  # Uso de Session.get en lugar de Query.get
        if not producto or producto.stock <= 0:
            flash("Producto no disponible o sin stock.")
            return redirect(url_for('catalogo'))

        # Obtener la cantidad seleccionada desde el formulario
        cantidad = request.form.get('cantidad', type=int, default=1)
        if cantidad <= 0:
            flash("Error: Cantidad inválida. Debe ser mayor a 0.")
            return redirect(url_for('catalogo'))

        if producto.stock < cantidad:
            flash("No hay suficiente stock disponible para la cantidad solicitada.")
            return redirect(url_for('catalogo'))

        # Buscar o crear una venta en estado 'carrito'
        venta = Venta.query.filter_by(id_cliente=cliente.id_cliente, estado='carrito').first()
        if not venta:
            venta = Venta(
                fecha_venta=datetime.now(),
                id_cliente=cliente.id_cliente,
                estado='carrito',
                total=0.0
            )
            db.session.add(venta)
            db.session.commit()

        # Buscar o crear el detalle de venta
        detalle = DetalleVenta.query.filter_by(id_venta=venta.id_venta, id_producto=producto.id_producto).first()
        if detalle:
            detalle.cantidad += cantidad
            detalle.subtotal += producto.precio * cantidad
        else:
            detalle = DetalleVenta(
                id_venta=venta.id_venta,
                id_producto=producto.id_producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=producto.precio * cantidad,
                nombre_producto=producto.nombre
            )
            db.session.add(detalle)

        # Actualizar el stock del producto y el total de la venta
        producto.stock -= cantidad
        venta.total += producto.precio * cantidad
        db.session.commit()

        flash("Producto añadido al carrito.")
        return redirect(url_for('carrito'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error al añadir el producto al carrito: {str(e)}")
        return redirect(url_for('catalogo'))

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

# Ruta para procesar la compra
@app.route('/procesar_compra', methods=['POST'])
def procesar_compra():
    id_cliente = session.get('usuario_id')
    if not id_cliente:
        flash("Usuario no autenticado. Por favor, inicia sesión.")
        return redirect(url_for('carrito'))

    # Obtener la venta en estado "carrito"
    venta = Venta.query.filter_by(id_cliente=id_cliente, estado='carrito').first()
    if not venta:
        flash("No tienes productos en el carrito.")
        return redirect(url_for('carrito'))

    try:
        # Actualizar el estado de la venta a "completado"
        venta.estado = 'completado'
        venta.fecha_venta = datetime.now()
        db.session.commit()

        # Crear la factura asociada
        factura = Factura(
            id_venta=venta.id_venta,
            fecha_emision=venta.fecha_venta,
            total=venta.total
        )
        db.session.add(factura)
        db.session.commit()

        # Retornar a carrito con los datos de la factura
        return render_template(
            'carrito.html',
            detalles=[],
            mostrar_factura=True,
            total=factura.total,
            fecha=factura.fecha_emision.strftime('%d/%m/%Y'),
            comprador=venta.cliente.nombre,
            id_factura=factura.id_factura
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar la compra: {str(e)}")
        return redirect(url_for('carrito'))

# Ruta para la vista de productos (administrador)
@app.route('/admin/productos', methods=['GET'])
def admin_productos():
    if not session.get('usuario_id') or not session.get('is_admin'):
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
    productos = Producto.query.filter(Producto.stock ==1 ).all()
    
    # Ajusta la ruta de las imágenes
    for producto in productos:
        if producto.foto.startswith("static/uploads/"):
            producto.foto = producto.foto.replace("static/uploads/", "uploads/")
        elif not producto.foto.startswith("uploads/"):
            producto.foto = f"uploads/{producto.foto}"
    
    return render_template('productos_agotados.html', productos=productos)

# Ruta para el informe de ventas
@app.route('/admin/informe_ventas', methods=['GET', 'POST'])
def informe_ventas():
    if not session.get('usuario_id') or not session.get('is_admin'):
        return redirect(url_for('login'))

    ventas = []
    mostrar_informe = False
    año = request.form.get('año', type=int) if request.method == 'POST' else 2025
    mes = request.form.get('mes', type=int) if request.method == 'POST' else 1

    if request.method == 'POST':
        ventas = Venta.query.filter(
            db.extract('year', Venta.fecha_venta) == año,
            db.extract('month', Venta.fecha_venta) == mes
        ).all()
        mostrar_informe = True

    return render_template('informe.html', ventas=ventas, mostrar_informe=mostrar_informe, año=año, mes=mes)

# Ruta para la vista de proveedores (administrador)
@app.route('/admin/proveedores', methods=['GET'])
def admin_proveedores():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    proveedores = Proveedor.query.all()
    return render_template('admin_proveedores.html', proveedores=proveedores)

# Ruta para eliminar un producto
@app.route('/admin/productos/eliminar/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    if not session.get('usuario_id') or not session.get('is_admin'):
        return redirect(url_for('login'))

    producto = Producto.query.get(producto_id)
    if not producto:
        return 'Producto no encontrado', 404

    if producto.foto:
        foto_path = os.path.join('src', producto.foto)
        if os.path.exists(foto_path):
            os.remove(foto_path)

    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for('productos_disponibles'))

# Ruta para eliminar un proveedor
@app.route('/admin/proveedores/eliminar/<int:proveedor_id>', methods=['POST'])
def eliminar_proveedor(proveedor_id):
    if not session.get('usuario_id') or not session.get('is_admin'):
        return redirect(url_for('login'))

    proveedor = Proveedor.query.get(proveedor_id)
    if not proveedor:
        return 'Proveedor no encontrado', 404

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

# Ruta para agregar un producto
@app.route('/admin/add_product', methods=['POST'])
def add_product():
    nombre = request.form['nombre']
    foto = request.files['foto']
    stock = int(request.form['stock'])
    descripcion = request.form['descripcion']
    precio = float(request.form['precio'])

    foto_path = f'static/uploads/{foto.filename}'
    foto.save(os.path.join('src/static/uploads', foto.filename))

    nuevo_producto = Producto(nombre=nombre, foto=foto_path, stock=stock, descripcion=descripcion, precio=precio)
    db.session.add(nuevo_producto)
    db.session.commit()
    return redirect('/admin')

# Ruta para agregar un proveedor
@app.route('/admin/add_supplier', methods=['POST'])
def add_supplier():
    nombre = request.form['nombre']
    contacto = request.form['contacto']

    nuevo_proveedor = Proveedor(nombre=nombre, contacto=contacto)
    db.session.add(nuevo_proveedor)
    db.session.commit()
    return redirect('/admin')

# Ruta para listar facturas
@app.route('/facturas')
def lista_facturas():
    facturas = Factura.query.all()
    cliente_info = []

    for factura in facturas:
        if factura.venta and factura.venta.cliente:
            info = {
                'id_factura': factura.id_factura,
                'id_venta': factura.venta.id_venta,
                'fecha_emision': factura.fecha_emision.strftime('%d/%m/%Y'),
                'hora_emision': factura.fecha_emision.strftime('%H:%M:%S'),
                'total': factura.total,
                'cliente': {
                    'nombre': factura.venta.cliente.nombre,
                },
                'productos_comprados': [
                    {
                        'producto': detalle.nombre_producto,
                        'precio': detalle.precio_unitario,
                        'cantidad': detalle.cantidad,
                    }
                    for detalle in factura.venta.detalles
                ]
            }
            cliente_info.append(info)

    return render_template('lista_facturas.html', cliente_info=cliente_info)


# Ruta para crear una factura
@app.route('/facturas/crear/<int:id_venta>', methods=['GET', 'POST'])
def crear_factura(id_venta):
    venta = Venta.query.get(id_venta)

    if not venta:
        flash("La venta no existe.")
        return redirect(url_for('carrito'))  # Redirigir al carrito si la venta no existe

    if not venta.detalles or not venta.cliente:
        flash("La venta está incompleta. Verifica cliente y productos.")
        return redirect(url_for('carrito'))  # Redirigir al carrito si la venta es incompleta

    try:
        nueva_factura = Factura(
            id_venta=venta.id_venta,
            fecha_emision=datetime.now(),
            total=venta.total
        )
        db.session.add(nueva_factura)
        db.session.commit()

        flash("Factura creada exitosamente.")
        return redirect(url_for('factura_compra', id_factura=nueva_factura.id_factura))  # Redirigir al cliente a su factura

    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear la factura: {str(e)}")
        return redirect(url_for('carrito'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear la factura: {str(e)}")
        return redirect(url_for('carrito'))

# Ruta para vaciar el carrito
@app.route('/vaciar_carrito', methods=['POST'])
def vaciar_carrito():
    # Obtener el cliente desde la sesión
    id_cliente = session.get('usuario_id')
    if not id_cliente:
        flash("Error: Usuario no identificado. Por favor, inicia sesión.")
        return redirect(url_for('carrito'))

    try:
        # Buscar la venta en estado "carrito" del cliente
        venta = Venta.query.filter_by(id_cliente=id_cliente, estado='carrito').first()
        if not venta:
            flash("No tienes productos en el carrito.")
            return redirect(url_for('carrito'))

        # Restaurar el stock de los productos en el carrito
        detalles = DetalleVenta.query.filter_by(id_venta=venta.id_venta).all()
        for detalle in detalles:
            producto = Producto.query.get(detalle.id_producto)
            if producto:
                producto.stock += detalle.cantidad  # Restaurar el stock
            db.session.delete(detalle)  # Eliminar el detalle de la venta

        # Eliminar la venta en estado "carrito"
        db.session.delete(venta)
        db.session.commit()

        flash("El carrito ha sido vaciado exitosamente.")
        return redirect(url_for('carrito'))

    except Exception as e:
        db.session.rollback()  # Revertir los cambios en caso de error
        flash(f"Error al vaciar el carrito: {str(e)}")
        return redirect(url_for('carrito'))


# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)

