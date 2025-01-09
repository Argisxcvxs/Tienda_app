from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Importar los modelos para que SQLAlchemy los reconozca
from models.db import Cliente, Proveedor, Producto, Venta, DetalleVenta, Factura, Usuario

# Definir una ruta de ejemplo
@app.route('/')
def index():
    return '¡Hola, mundo!'

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)