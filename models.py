from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), nullable=False, unique=True)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='cliente')  # admin | tecnico | cliente
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login necesita un id como string
    def get_id(self):
        return str(self.id_usuario)


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id_cliente = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    nombre_razon_social = db.Column(db.String(150), nullable=False)
    tipo_documento = db.Column(db.String(1), nullable=False)  # V, E, J, G, P
    numero_documento = db.Column(db.String(15), nullable=False)
    rif = db.Column(db.String(20))
    direccion_fiscal = db.Column(db.Text, nullable=False)
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def calcular_rif(self):
        self.rif = f"{self.tipo_documento}-{self.numero_documento}"


class Tecnico(db.Model):
    __tablename__ = 'tecnicos'

    id_tecnico = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    nombre_completo = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(15), nullable=False, unique=True)
    especialidad = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)


class Servicio(db.Model):
    __tablename__ = 'servicios'

    id_servicio = db.Column(db.Integer, primary_key=True)
    codigo_interno = db.Column(db.String(20), nullable=False, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(20), nullable=False, default='servicio')  # producto | servicio
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    exento_iva = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id_servicio,
            'codigo': self.codigo_interno,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'precio': float(self.precio_unitario),
            'stock': self.stock,
        }


class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id_pedido = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    id_tecnico = db.Column(db.Integer, db.ForeignKey('tecnicos.id_tecnico'))
    id_usuario_crea = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    monto_iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    observaciones = db.Column(db.Text)

    cliente = db.relationship('Cliente', backref='pedidos')
    tecnico = db.relationship('Tecnico', backref='pedidos')


class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'

    id_detalle = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id_pedido'), nullable=False)
    id_servicio = db.Column(db.Integer, db.ForeignKey('servicios.id_servicio'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)

    pedido = db.relationship('Pedido', backref='detalles')
    servicio = db.relationship('Servicio')

    @property
    def subtotal_linea(self):
        return self.cantidad * self.precio_unitario


class Factura(db.Model):
    __tablename__ = 'facturas'

    id_factura = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id_pedido'), nullable=False, unique=True)
    numero_control = db.Column(db.String(20), nullable=False, unique=True)
    numero_factura = db.Column(db.String(20), nullable=False, unique=True)
    rif_emisor = db.Column(db.String(20), nullable=False)
    razon_social_emisor = db.Column(db.String(150), nullable=False)
    direccion_fiscal_emisor = db.Column(db.Text, nullable=False)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    rif_cliente_snapshot = db.Column(db.String(20), nullable=False)
    fecha_emision = db.Column(db.Date, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    base_imponible = db.Column(db.Numeric(12, 2), nullable=False)
    monto_exento = db.Column(db.Numeric(12, 2), default=0)
    porcentaje_iva = db.Column(db.Numeric(5, 2), default=16.00)
    monto_iva = db.Column(db.Numeric(12, 2), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    forma_pago = db.Column(db.String(30), default='contado')
    estado = db.Column(db.String(20), nullable=False, default='emitida')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
