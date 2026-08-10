from functools import wraps
from datetime import datetime, timedelta
import io

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, flash,
    send_file, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)

from config import Config
from models import db, Usuario, Servicio, Cliente, Tecnico, Pedido, DetallePedido, Factura
import reportes

load_dotenv()  # carga variables de entorno desde .env si existe

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(id_usuario):
    return Usuario.query.get(int(id_usuario))


# ---------------------------------------------------------
# Decorador para proteger rutas solo-admin
# ---------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('No tienes permisos para acceder a esa sección.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------
# Frontend público (mantiene el diseño original)
# ---------------------------------------------------------
@app.route('/')
def index():
    return render_template(
        'index.html',
        empresa_nombre=Config.EMPRESA_RAZON_SOCIAL,
        empresa_rif=Config.EMPRESA_RIF,
        empresa_direccion=Config.EMPRESA_DIRECCION_FISCAL,
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and usuario.check_password(password) and usuario.activo:
            login_user(usuario)
            if usuario.rol == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))

        flash('Correo o contraseña incorrectos.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ---------------------------------------------------------
# API pública (usada por static/app.js)
# ---------------------------------------------------------
@app.route('/api/servicios', methods=['GET'])
def api_listar_servicios():
    servicios = Servicio.query.filter_by(activo=True).all()
    return jsonify([s.to_dict() for s in servicios])


@app.route('/api/registrar', methods=['POST'])
def api_registrar():
    data = request.get_json()
    correo = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not correo or not password:
        return jsonify({'error': 'Correo y contraseña son requeridos.'}), 400

    if Usuario.query.filter_by(correo=correo).first():
        return jsonify({'error': 'Ese correo ya está registrado.'}), 409

    if len(password) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres.'}), 400

    nuevo_usuario = Usuario(
        nombre_usuario=correo.split('@')[0],
        correo=correo,
        rol='cliente'
    )
    nuevo_usuario.set_password(password)

    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({'mensaje': '¡Registro exitoso! Ya puedes iniciar sesión.'}), 201


# ===========================================================
# PANEL ADMINISTRATIVO
# ===========================================================

# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_servicios = Servicio.query.count()
    total_clientes = Cliente.query.count()
    total_pedidos = Pedido.query.count()
    total_tecnicos = Tecnico.query.filter_by(activo=True).count()
    valor_inventario = sum(
        float(s.precio_unitario) * s.stock for s in Servicio.query.all()
    )
    return render_template(
        'admin/dashboard.html',
        activo='dashboard',
        total_servicios=total_servicios,
        total_clientes=total_clientes,
        total_pedidos=total_pedidos,
        total_tecnicos=total_tecnicos,
        valor_inventario=valor_inventario
    )


@app.route('/api/dashboard/data')
@admin_required
def api_dashboard_data():
    # Pedidos por estado
    estados = ['pendiente', 'en_proceso', 'completado', 'cancelado']
    conteo_estados = {e: Pedido.query.filter_by(estado=e).count() for e in estados}

    # Servicios vs productos
    total_servicios_tipo = Servicio.query.filter_by(tipo='servicio').count()
    total_productos_tipo = Servicio.query.filter_by(tipo='producto').count()

    # Pedidos de los últimos 7 días (agrupado por día, compatible con SQLite)
    hoy = datetime.utcnow().date()
    dias = [(hoy - timedelta(days=i)) for i in range(6, -1, -1)]
    pedidos_recientes = Pedido.query.filter(
        Pedido.fecha_pedido >= datetime.utcnow() - timedelta(days=7)
    ).all()
    conteo_por_dia = {d.strftime('%d/%m'): 0 for d in dias}
    for p in pedidos_recientes:
        if p.fecha_pedido:
            clave = p.fecha_pedido.date().strftime('%d/%m')
            if clave in conteo_por_dia:
                conteo_por_dia[clave] += 1

    return jsonify({
        'pedidos_por_estado': {
            'labels': ['Pendiente', 'En proceso', 'Completado', 'Cancelado'],
            'data': [conteo_estados[e] for e in estados]
        },
        'catalogo': {
            'labels': ['Servicios', 'Productos'],
            'data': [total_servicios_tipo, total_productos_tipo]
        },
        'pedidos_semana': {
            'labels': list(conteo_por_dia.keys()),
            'data': list(conteo_por_dia.values())
        }
    })


# ---------------------------------------------------------
# MÓDULO: Gestión de Usuarios
# ---------------------------------------------------------
@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    usuarios = Usuario.query.order_by(Usuario.fecha_creacion.desc()).all()
    return render_template('admin/usuarios.html', activo='usuarios', usuarios=usuarios)


@app.route('/api/usuarios/<int:id_usuario>/hacer_admin', methods=['POST'])
@admin_required
def api_hacer_admin(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    if usuario.rol in ('cliente', 'tecnico'):
        usuario.rol = 'admin'
        db.session.commit()
        flash(f'{usuario.correo} ahora es administrador.', 'success')
    return redirect(url_for('admin_usuarios'))


# ---------------------------------------------------------
# Clientes
# ---------------------------------------------------------
@app.route('/admin/clientes', methods=['GET', 'POST'])
@admin_required
def admin_clientes():
    if request.method == 'POST':
        cliente = Cliente(
            nombre_razon_social=request.form['nombre_razon_social'],
            tipo_documento=request.form['tipo_documento'],
            numero_documento=request.form['numero_documento'],
            direccion_fiscal=request.form['direccion_fiscal'],
            telefono=request.form.get('telefono'),
            correo=request.form.get('correo'),
        )
        cliente.calcular_rif()
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente registrado correctamente.', 'success')
        return redirect(url_for('admin_clientes'))

    clientes = Cliente.query.order_by(Cliente.fecha_registro.desc()).all()
    return render_template('admin/clientes.html', activo='clientes', clientes=clientes)


# ---------------------------------------------------------
# Productos / Servicios
# ---------------------------------------------------------
@app.route('/admin/productos', methods=['GET', 'POST'])
@admin_required
def admin_productos():
    if request.method == 'POST':
        servicio = Servicio(
            codigo_interno=request.form['codigo_interno'],
            nombre=request.form['nombre'],
            descripcion=request.form.get('descripcion'),
            tipo=request.form.get('tipo', 'servicio'),
            precio_unitario=float(request.form['precio_unitario']),
            stock=int(request.form.get('stock') or 0),
        )
        db.session.add(servicio)
        db.session.commit()
        flash('Producto/servicio guardado correctamente.', 'success')
        return redirect(url_for('admin_productos'))

    servicios = Servicio.query.order_by(Servicio.fecha_creacion.desc()).all()
    return render_template('admin/productos.html', activo='productos', servicios=servicios)


# ---------------------------------------------------------
# Técnicos
# ---------------------------------------------------------
@app.route('/admin/tecnicos', methods=['GET', 'POST'])
@admin_required
def admin_tecnicos():
    if request.method == 'POST':
        tecnico = Tecnico(
            nombre_completo=request.form['nombre_completo'],
            cedula=request.form['cedula'],
            especialidad=request.form.get('especialidad'),
            telefono=request.form.get('telefono'),
        )
        db.session.add(tecnico)
        db.session.commit()
        flash('Técnico registrado correctamente.', 'success')
        return redirect(url_for('admin_tecnicos'))

    tecnicos = Tecnico.query.all()
    return render_template('admin/tecnicos.html', activo='tecnicos', tecnicos=tecnicos)


# ---------------------------------------------------------
# Pedidos (+ generación de factura)
# ---------------------------------------------------------
@app.route('/admin/pedidos', methods=['GET', 'POST'])
@admin_required
def admin_pedidos():
    if request.method == 'POST':
        servicio = Servicio.query.get_or_404(int(request.form['id_servicio']))
        cantidad = int(request.form['cantidad'])
        id_tecnico = request.form.get('id_tecnico') or None

        subtotal = float(servicio.precio_unitario) * cantidad
        iva = 0 if servicio.exento_iva else round(subtotal * (Config.PORCENTAJE_IVA / 100), 2)

        pedido = Pedido(
            id_cliente=int(request.form['id_cliente']),
            id_tecnico=int(id_tecnico) if id_tecnico else None,
            id_usuario_crea=current_user.id_usuario,
            estado='pendiente',
            subtotal=subtotal,
            monto_iva=iva,
            total=subtotal + iva,
        )
        db.session.add(pedido)
        db.session.flush()  # para obtener pedido.id_pedido antes del commit

        detalle = DetallePedido(
            id_pedido=pedido.id_pedido,
            id_servicio=servicio.id_servicio,
            cantidad=cantidad,
            precio_unitario=servicio.precio_unitario,
        )
        db.session.add(detalle)
        db.session.commit()
        flash(f'Pedido #{pedido.id_pedido} creado correctamente.', 'success')
        return redirect(url_for('admin_pedidos'))

    pedidos = Pedido.query.order_by(Pedido.fecha_pedido.desc()).all()
    clientes = Cliente.query.all()
    tecnicos = Tecnico.query.filter_by(activo=True).all()
    servicios = Servicio.query.filter_by(activo=True).all()
    return render_template(
        'admin/pedidos.html', activo='pedidos',
        pedidos=pedidos, clientes=clientes, tecnicos=tecnicos, servicios=servicios
    )


def _obtener_o_crear_factura(pedido):
    """Devuelve la factura del pedido; si no existe, la crea con numeración correlativa."""
    factura = Factura.query.filter_by(id_pedido=pedido.id_pedido).first()
    if factura:
        return factura

    correlativo = Factura.query.count() + 1
    numero = f"{correlativo:08d}"

    factura = Factura(
        id_pedido=pedido.id_pedido,
        numero_control=f"00-{numero}",
        numero_factura=f"F-{numero}",
        rif_emisor=Config.EMPRESA_RIF,
        razon_social_emisor=Config.EMPRESA_RAZON_SOCIAL,
        direccion_fiscal_emisor=Config.EMPRESA_DIRECCION_FISCAL,
        id_cliente=pedido.id_cliente,
        rif_cliente_snapshot=pedido.cliente.rif,
        fecha_emision=datetime.utcnow().date(),
        subtotal=pedido.subtotal,
        base_imponible=pedido.subtotal,
        monto_exento=0,
        porcentaje_iva=Config.PORCENTAJE_IVA,
        monto_iva=pedido.monto_iva,
        total=pedido.total,
    )
    db.session.add(factura)
    db.session.commit()
    return factura


@app.route('/admin/pedidos/<int:id_pedido>/factura')
@admin_required
def generar_factura_pdf(id_pedido):
    pedido = Pedido.query.get_or_404(id_pedido)
    factura = _obtener_o_crear_factura(pedido)
    buffer = reportes.generar_factura_pdf(pedido, factura, Config)
    return send_file(
        buffer, mimetype='application/pdf', as_attachment=True,
        download_name=f"factura_{factura.numero_factura}.pdf"
    )


# ---------------------------------------------------------
# MÓDULO: Reportes Estadísticos
# ---------------------------------------------------------
@app.route('/admin/reportes')
@admin_required
def admin_reportes():
    return render_template('admin/reportes.html', activo='reportes')


@app.route('/admin/reportes/general.pdf')
@admin_required
def reporte_general_pdf():
    servicios = Servicio.query.all()
    clientes = Cliente.query.all()
    buffer = reportes.generar_reporte_general_pdf(servicios, clientes)
    return send_file(
        buffer, mimetype='application/pdf', as_attachment=True,
        download_name='reporte_general_innova_corp.pdf'
    )


@app.route('/admin/reportes/semanal.pdf')
@admin_required
def reporte_semanal_pdf():
    desde = datetime.utcnow() - timedelta(days=7)
    pedidos = Pedido.query.filter(Pedido.fecha_pedido >= desde).order_by(Pedido.fecha_pedido.desc()).all()
    buffer = reportes.generar_reporte_semanal_pdf(pedidos)
    return send_file(
        buffer, mimetype='application/pdf', as_attachment=True,
        download_name='reporte_semanal_pedidos.pdf'
    )


@app.route('/admin/reportes/inventario.xlsx')
@admin_required
def reporte_inventario_xlsx():
    servicios = Servicio.query.all()
    buffer = reportes.generar_inventario_xlsx(servicios)
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True, download_name='inventario_innova_corp.xlsx'
    )


@app.route('/admin/reportes/tecnicos.csv')
@admin_required
def reporte_tecnicos_csv():
    tecnicos = Tecnico.query.filter_by(activo=True).all()
    buffer = reportes.generar_tecnicos_csv(tecnicos)
    return send_file(
        io.BytesIO(buffer.getvalue().encode('utf-8')),
        mimetype='text/csv', as_attachment=True,
        download_name='tecnicos_disponibles.csv'
    )


# ---------------------------------------------------------
# Inicialización: crea las tablas y el usuario admin por defecto
# ---------------------------------------------------------
def inicializar_bd():
    with app.app_context():
        db.create_all()

        admin_existente = Usuario.query.filter_by(correo=Config.ADMIN_EMAIL).first()
        if not admin_existente:
            admin = Usuario(
                nombre_usuario=Config.ADMIN_USERNAME,
                correo=Config.ADMIN_EMAIL,
                rol='admin'
            )
            admin.set_password(Config.ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
            print(f"[OK] Usuario administrador creado -> {Config.ADMIN_EMAIL} / {Config.ADMIN_PASSWORD}")
        else:
            print("[OK] El usuario administrador ya existe.")

        # Datos de ejemplo para que el catálogo no se vea vacío en desarrollo local
        if Servicio.query.count() == 0:
            ejemplos = [
                Servicio(codigo_interno='SRV-001', nombre='Mantenimiento de PC',
                          descripcion='Limpieza física y optimización de software',
                          tipo='servicio', precio_unitario=15.00, stock=0),
                Servicio(codigo_interno='SRV-002', nombre='Instalación de Software',
                          descripcion='Instalación y configuración de programas',
                          tipo='servicio', precio_unitario=8.00, stock=0),
                Servicio(codigo_interno='PROD-001', nombre='Cable HDMI 2m',
                          descripcion='Cable HDMI de alta velocidad',
                          tipo='producto', precio_unitario=6.50, stock=25),
            ]
            db.session.bulk_save_objects(ejemplos)
            db.session.commit()
            print("[OK] Servicios de ejemplo insertados.")


if __name__ == '__main__':
    inicializar_bd()
    app.run(debug=True)
