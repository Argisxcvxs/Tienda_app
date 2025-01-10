from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config.config import Config
from models.db import db
   

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Importar los modelos para que SQLAlchemy los reconozca
from models.db import Cliente, Proveedor, Producto, Venta, DetalleVenta, Factura, Usuario

"codigo"

# Definir una ruta de ejemplo
@app.route('/')
def index():
    "front end"
    return render_template('index.html')

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)