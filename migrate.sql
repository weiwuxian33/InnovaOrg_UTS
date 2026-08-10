-- ============================================================
-- InnovaCorp - Migracion SQL para Supabase (PostgreSQL)
-- Ejecutar este script en: Supabase SQL Editor
-- ============================================================

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    correo VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'cliente',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente SERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES usuarios(id_usuario),
    nombre_razon_social VARCHAR(150) NOT NULL,
    tipo_documento VARCHAR(1) NOT NULL,
    numero_documento VARCHAR(15) NOT NULL,
    rif VARCHAR(20),
    direccion_fiscal TEXT NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(100),
    fecha_registro TIMESTAMP DEFAULT NOW()
);

-- Tabla de tecnicos
CREATE TABLE IF NOT EXISTS tecnicos (
    id_tecnico SERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES usuarios(id_usuario),
    nombre_completo VARCHAR(150) NOT NULL,
    cedula VARCHAR(15) NOT NULL UNIQUE,
    especialidad VARCHAR(100),
    telefono VARCHAR(20),
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de servicios/productos
CREATE TABLE IF NOT EXISTS servicios (
    id_servicio SERIAL PRIMARY KEY,
    codigo_interno VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(20) NOT NULL DEFAULT 'servicio',
    precio_unitario NUMERIC(12, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    exento_iva BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Tabla de pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido SERIAL PRIMARY KEY,
    id_cliente INTEGER NOT NULL REFERENCES clientes(id_cliente),
    id_tecnico INTEGER REFERENCES tecnicos(id_tecnico),
    id_usuario_crea INTEGER REFERENCES usuarios(id_usuario),
    fecha_pedido TIMESTAMP DEFAULT NOW(),
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    subtotal NUMERIC(12, 2) DEFAULT 0,
    monto_iva NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) DEFAULT 0,
    observaciones TEXT
);

-- Tabla de detalle de pedidos
CREATE TABLE IF NOT EXISTS detalle_pedido (
    id_detalle SERIAL PRIMARY KEY,
    id_pedido INTEGER NOT NULL REFERENCES pedidos(id_pedido),
    id_servicio INTEGER NOT NULL REFERENCES servicios(id_servicio),
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(12, 2) NOT NULL
);

-- Tabla de facturas
CREATE TABLE IF NOT EXISTS facturas (
    id_factura SERIAL PRIMARY KEY,
    id_pedido INTEGER NOT NULL UNIQUE REFERENCES pedidos(id_pedido),
    numero_control VARCHAR(20) NOT NULL UNIQUE,
    numero_factura VARCHAR(20) NOT NULL UNIQUE,
    rif_emisor VARCHAR(20) NOT NULL,
    razon_social_emisor VARCHAR(150) NOT NULL,
    direccion_fiscal_emisor TEXT NOT NULL,
    id_cliente INTEGER NOT NULL REFERENCES clientes(id_cliente),
    rif_cliente_snapshot VARCHAR(20) NOT NULL,
    fecha_emision DATE DEFAULT CURRENT_DATE,
    subtotal NUMERIC(12, 2) NOT NULL,
    base_imponible NUMERIC(12, 2) NOT NULL,
    monto_exento NUMERIC(12, 2) DEFAULT 0,
    porcentaje_iva NUMERIC(5, 2) DEFAULT 16.00,
    monto_iva NUMERIC(12, 2) NOT NULL,
    total NUMERIC(12, 2) NOT NULL,
    forma_pago VARCHAR(30) DEFAULT 'contado',
    estado VARCHAR(20) NOT NULL DEFAULT 'emitida',
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Usuario administrador por defecto
-- Password: Admin123! (hash generado con scrypt)
-- ============================================================
INSERT INTO usuarios (nombre_usuario, correo, password_hash, rol, activo)
VALUES (
    'admin',
    'admin@innovacorp.com',
    'scrypt:32768:8:1$00UKBAweYnNiqdh4$8668d890c898f554af1de8b2aa38ab97d5a825e6ba7d045ed58f9c7229e411684dc73cc417de85124b3da5ecae1ad7c4cb11e44d32efa2c0ff1e01d1a9476533',
    'admin',
    TRUE
)
ON CONFLICT (correo) DO NOTHING;

-- ============================================================
-- Servicios de ejemplo
-- ============================================================
INSERT INTO servicios (codigo_interno, nombre, descripcion, tipo, precio_unitario, stock)
VALUES
    ('SRV-001', 'Mantenimiento de PC', 'Limpieza fisica y optimizacion de software', 'servicio', 15.00, 0),
    ('SRV-002', 'Instalacion de Software', 'Instalacion y configuracion de programas', 'servicio', 8.00, 0),
    ('PROD-001', 'Cable HDMI 2m', 'Cable HDMI de alta velocidad', 'producto', 6.50, 25)
ON CONFLICT (codigo_interno) DO NOTHING;
