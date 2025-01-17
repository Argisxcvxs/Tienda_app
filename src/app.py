from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config.config import Config
from models.db import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Importar los modelos para que SQLAlchemy los reconozca
from models.db import Cliente, Proveedor, Producto, Venta, DetalleVenta, Factura, Usuario

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para mostrar la lista de clientes
@app.route('/clientes')
def mostrar_clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

# Ruta para mostrar la lista de proveedores
@app.route('/proveedores')
def mostrar_proveedores():
    proveedores = Proveedor.query.all()
    return render_template('proveedores.html', proveedores=proveedores)

# Ruta para mostrar la lista de productos
@app.route('/productos')
def mostrar_productos():
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)