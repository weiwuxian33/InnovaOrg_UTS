import os

# Carpeta base del proyecto (para ubicar el archivo .db de forma absoluta)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Cambia esto en producción (usa una variable de entorno real)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cambia-esta-clave-en-produccion')

    # Base de datos local SQLite (un solo archivo, sin servidor externo)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'innova_corp.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Credenciales del administrador por defecto (solo se crea si no existe)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@innovacorp.com')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123!')

    # Datos fiscales del emisor (tu empresa) para las facturas — ajústalos a los reales
    EMPRESA_RAZON_SOCIAL = os.environ.get('EMPRESA_RAZON_SOCIAL', 'Innova Corp, C.A.')
    EMPRESA_RIF = os.environ.get('EMPRESA_RIF', 'J-40123456-7')
    EMPRESA_DIRECCION_FISCAL = os.environ.get(
        'EMPRESA_DIRECCION_FISCAL',
        'Av. Principal, Edificio Innova, Piso 1, Caracas, Venezuela'
    )
    PORCENTAJE_IVA = 16.00
