DATABASE_CONFIG = {
    'user': 'root',
    'password': '1121710953',
    'host': 'localhost',
    'database': 'tienda_final',
}

class Config:
    # Construcción de la URI de la base de datos para SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DATABASE_CONFIG['root']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['localhost']}/{DATABASE_CONFIG['tienda_final']}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Desactiva el seguimiento de modificaciones de objetos para ahorrar memoria
    SECRET_KEY = 'supersecretkey'  # Clave secreta para la gestión de sesiones y seguridad