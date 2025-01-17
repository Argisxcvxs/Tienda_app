from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'Usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), nullable=False, unique=True)
    correo_electronico = db.Column(db.String(120), nullable=False, unique=True)
    contrasena = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Relación con los clientes
    clientes = db.relationship('Cliente', backref='usuario', lazy=True)

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'

class Cliente(db.Model):
    __tablename__ = 'Clientes'
    
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(100), nullable=False)
    correo_electronico = db.Column(db.String(120), nullable=True)
    direccion_cliente = db.Column(db.String(255))
    telefono_cliente = db.Column(db.String(20))
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)

    # Relación con ventas
    ventas = db.relationship('Venta', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nombre_cliente}>'

class Proveedor(db.Model):
    __tablename__ = 'Proveedores'

    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre_proveedor = db.Column(db.String(100), nullable=False)
    telefono_proveedor = db.Column(db.String(20))
    direccion_proveedor = db.Column(db.String(255))
    correo_proveedor = db.Column(db.String(120))

    # Relación con productos
    productos = db.relationship('Producto', backref='proveedor', lazy=True)

    def __repr__(self):
        return f'<Proveedor {self.nombre_proveedor}>'

class Producto(db.Model):
    __tablename__ = 'Productos'

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre_producto = db.Column(db.String(100), nullable=False)
    descripcion_producto = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad_stock = db.Column(db.Integer, nullable=False)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('Proveedores.id_proveedor'))

    # Relación con detalle de ventas
    detalles_venta = db.relationship('DetalleVenta', backref='producto', lazy=True)

    def __repr__(self):
        return f'<Producto {self.nombre_producto}>'

class Venta(db.Model):
    __tablename__ = 'Ventas'

    id_venta = db.Column(db.Integer, primary_key=True)
    fecha_venta = db.Column(db.DateTime, default=db.func.current_timestamp())
    id_cliente = db.Column(db.Integer, db.ForeignKey('Clientes.id_cliente'))
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario'))
    total = db.Column(db.Numeric(10, 2), nullable=False)
    direccion_envio = db.Column(db.String(255))
    estado_envio = db.Column(db.String(50))

    # Relación con los detalles de ventas
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)

    # Relación con factura
    factura = db.relationship('Factura', backref='venta', uselist=False)

    def __repr__(self):
        return f'<Venta {self.id_venta}>'

class DetalleVenta(db.Model):
    __tablename__ = 'DetalleVentas'

    id_detalle = db.Column(db.Integer, primary_key=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('Ventas.id_venta'))
    id_producto = db.Column(db.Integer, db.ForeignKey('Productos.id_producto'))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<DetalleVenta {self.id_detalle}>'

class Factura(db.Model):
    __tablename__ = 'Facturas'

    id_factura = db.Column(db.Integer, primary_key=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('Ventas.id_venta'))
    fecha_factura = db.Column(db.DateTime, default=db.func.current_timestamp())
    total = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<Factura {self.id_factura}>'
