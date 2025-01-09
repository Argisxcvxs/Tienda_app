from src.app import db

# Modelo para la tabla 'Clientes'
class Cliente(db.Model):
    __tablename__ = 'Clientes'
    id_cliente = db.Column(db.Integer, primary_key=True)  # Clave primaria
    nombre = db.Column(db.String(255), nullable=False)  # Nombre del cliente
    correo_electronico = db.Column(db.String(255), nullable=False, unique=True)  # Correo electrónico único
    direccion = db.Column(db.Text)  # Dirección del cliente

# Modelo para la tabla 'Proveedores'
class Proveedor(db.Model):
    __tablename__ = 'Proveedores'
    id_proveedor = db.Column(db.Integer, primary_key=True)  # Clave primaria
    nombre = db.Column(db.String(255), nullable=False)  # Nombre del proveedor
    contacto = db.Column(db.String(255))  # Información de contacto del proveedor
    direccion = db.Column(db.Text)  # Dirección del proveedor
    telefono = db.Column(db.String(20))  # Teléfono del proveedor

# Modelo para la tabla 'Productos'
class Producto(db.Model):
    __tablename__ = 'Productos'
    id_producto = db.Column(db.Integer, primary_key=True)  # Clave primaria
    nombre = db.Column(db.String(255), nullable=False)  # Nombre del producto
    descripcion = db.Column(db.Text)  # Descripción del producto
    precio = db.Column(db.Numeric(10, 2), nullable=False)  # Precio del producto
    stock = db.Column(db.Integer, nullable=False)  # Cantidad en stock
    id_proveedor = db.Column(db.Integer, db.ForeignKey('Proveedores.id_proveedor'))  # Clave foránea a 'Proveedores'
    proveedor = db.relationship('Proveedor', backref=db.backref('productos', lazy=True))  # Relación con 'Proveedores'

# Modelo para la tabla 'Ventas'
class Venta(db.Model):
    __tablename__ = 'Ventas'
    id_venta = db.Column(db.Integer, primary_key=True)  # Clave primaria
    fecha = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Fecha de la venta
    total = db.Column(db.Numeric(10, 2), nullable=False)  # Total de la venta
    id_cliente = db.Column(db.Integer, db.ForeignKey('Clientes.id_cliente'), nullable=False)  # Clave foránea a 'Clientes'
    cliente = db.relationship('Cliente', backref=db.backref('ventas', lazy=True))  # Relación con 'Clientes'

# Modelo para la tabla 'Detalles_Venta'
class DetalleVenta(db.Model):
    __tablename__ = 'Detalles_Venta'
    id_detalle = db.Column(db.Integer, primary_key=True)  # Clave primaria
    id_venta = db.Column(db.Integer, db.ForeignKey('Ventas.id_venta'), nullable=False)  # Clave foránea a 'Ventas'
    id_producto = db.Column(db.Integer, db.ForeignKey('Productos.id_producto'), nullable=False)  # Clave foránea a 'Productos'
    cantidad = db.Column(db.Integer, nullable=False)  # Cantidad de productos vendidos
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # Precio unitario del producto
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)  # Subtotal (cantidad * precio_unitario)
    venta = db.relationship('Venta', backref=db.backref('detalles', lazy=True))  # Relación con 'Ventas'
    producto = db.relationship('Producto', backref=db.backref('detalles', lazy=True))  # Relación con 'Productos'

# Modelo para la tabla 'Facturas'
class Factura(db.Model):
    __tablename__ = 'Facturas'
    id_factura = db.Column(db.Integer, primary_key=True)  # Clave primaria
    fecha = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Fecha de la factura
    total = db.Column(db.Numeric(10, 2), nullable=False)  # Total de la factura
    id_cliente = db.Column(db.Integer, db.ForeignKey('Clientes.id_cliente'))  # Clave foránea a 'Clientes'
    id_proveedor = db.Column(db.Integer, db.ForeignKey('Proveedores.id_proveedor'))  # Clave foránea a 'Proveedores'
    cliente = db.relationship('Cliente', backref=db.backref('facturas', lazy=True))  # Relación con 'Clientes'
    proveedor = db.relationship('Proveedor', backref=db.backref('facturas', lazy=True))  # Relación con 'Proveedores'

# Modelo para la tabla 'Usuarios'
class Usuario(db.Model):
    __tablename__ = 'Usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)  # Clave primaria
    nombre_usuario = db.Column(db.String(255), nullable=False, unique=True)  # Nombre de usuario único
    contraseña = db.Column(db.String(255), nullable=False)  # Contraseña del usuario