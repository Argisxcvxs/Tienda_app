from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tu_usuario:tu_contraseña@localhost/tienda'
db = SQLAlchemy(app)
