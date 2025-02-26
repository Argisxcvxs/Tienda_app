from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Modelo de usuarios
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    correo_electronico = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Modelo de clientes
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    direccion = db.Column(db.String(200), nullable=True)

# Modelo de proveedores
class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100), nullable=False)

# Modelo de productos
class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    foto = db.Column(db.String(200), nullable=True)  # Ruta de la foto

# Modelo de productos agotados
class ProductoAgotado(db.Model):
    __tablename__ = 'productos_agotados'
    id_agotado = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    nombre_producto = db.Column(db.String(100), nullable=False)
    fecha_agotado = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    producto = db.relationship('Producto', backref=db.backref('productos_agotados', lazy=True))

# Modelo de ventas
class Venta(db.Model):
    __tablename__ = 'ventas'
    id_venta = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    fecha_venta = db.Column(db.DateTime, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='carrito')
    cliente = db.relationship('Cliente', backref=db.backref('ventas', lazy=True))
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)

# Modelo de detalles de ventas
class DetalleVenta(db.Model):
    __tablename__ = 'detalles_venta'
    id_detalle_venta = db.Column(db.Integer, primary_key=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=True)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    nombre_producto = db.Column(db.String(255), nullable=False)
    producto = db.relationship('Producto', backref=db.backref('detalles_venta', lazy=True))

# Modelo de facturas
class Factura(db.Model):
    __tablename__ = 'facturas'
    id_factura = db.Column(db.Integer, primary_key=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'), nullable=False)
    fecha_emision = db.Column(db.DateTime, nullable=False)
    total = db.Column(db.Float, nullable=False)
    venta = db.relationship('Venta', backref=db.backref('factura', uselist=False))

# Simulación de trigger para productos agotados
@db.event.listens_for(Producto, 'after_update')
def registrar_producto_agotado(mapper, connection, target):
    if target.stock == 0:
        producto_agotado = ProductoAgotado(
            id_producto=target.id_producto,
            nombre_producto=target.nombre
        )
        db.session.add(producto_agotado)
        db.session.commit()

# Inicialización de la base de datos
def init_db():
    db.create_all()
