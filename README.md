# Innova Corp — Sistema de Gestión (Flask + SQLite)

Sistema completo 100% local: backend Flask, base de datos SQLite (sin
Supabase, sin PostgreSQL, sin credenciales externas), panel administrativo
con sidebar, dashboard con gráficos, gestión de usuarios/clientes/productos/
técnicos/pedidos, y reportes exportables (PDF, Excel, CSV) cumpliendo reglas
fiscales venezolanas (RIF, IVA 16%, número de control).

## Estructura

```
innova_corp/
├── app.py              # Todas las rutas: sitio público + panel admin + API
├── models.py            # Modelos SQLAlchemy (Usuarios, Clientes, Técnicos,
│                         #   Servicios, Pedidos, Detalle, Facturas)
├── reportes.py           # Generación de PDF (reportlab), Excel (openpyxl) y CSV
├── config.py             # Configuración: SQLite local + datos fiscales del emisor
├── requirements.txt
├── .env.example
├── templates/
│   ├── index.html        # Sitio público (mismo diseño original)
│   ├── login.html
│   └── admin/
│       ├── base.html      # Plantilla base con sidebar oscuro
│       ├── dashboard.html  # Panel de Control (stats + gráficos Chart.js)
│       ├── usuarios.html    # Gestión de Usuarios ("Hacer admin")
│       ├── clientes.html
│       ├── productos.html
│       ├── tecnicos.html
│       ├── pedidos.html      # Con botón "Generar Factura"
│       └── reportes.html      # Tarjetas de exportación
└── static/
    ├── style.css          # Diseño del sitio público (glass/gradiente)
    ├── admin.css           # Diseño del panel admin (sidebar oscuro + cards)
    └── app.js
```

## Pasos para ejecutarlo

```bash
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Esto crea automáticamente:
- El archivo `innova_corp.db` (SQLite) con todas las tablas.
- El usuario administrador por defecto: `admin@innovacorp.com` / `Admin123!`
  (cámbialo en `.env` antes de entregar el proyecto — copia `.env.example` a `.env`).
- 3 servicios/productos de ejemplo para que el catálogo no se vea vacío.

Abre `http://127.0.0.1:5000/` para el sitio público, o entra con el usuario
admin y ve a `http://127.0.0.1:5000/admin/dashboard` para el panel.

## Módulos del panel administrativo

| Sección                | Ruta                     | Qué hace |
|-------------------------|---------------------------|----------|
| Panel de Control          | `/admin/dashboard`          | Tarjetas de estadísticas + 3 gráficos (Chart.js): pedidos por estado, catálogo por tipo, pedidos de la semana |
| Clientes                   | `/admin/clientes`             | Alta de clientes con RIF/cédula y dirección fiscal (RIF se arma automático) |
| Productos                   | `/admin/productos`             | Alta y listado de servicios/productos con valor total de inventario |
| Gestión de Pedidos            | `/admin/pedidos`                | Crear pedidos y botón **Generar Factura** (descarga PDF) |
| Asignación de Técnicos          | `/admin/tecnicos`                 | Alta y listado de técnicos |
| Usuarios                         | `/admin/usuarios`                   | Lista de cuentas + botón **Hacer admin** para clientes/técnicos |
| Reportes                          | `/admin/reportes`                    | Tarjetas con los 4 exports abajo |

## Reportes y exportaciones

| Reporte                              | Formato | Ruta |
|----------------------------------------|---------|------|
| Reporte General del Sistema               | PDF     | `/admin/reportes/general.pdf` |
| Reporte Semanal de Pedidos (últimos 7 días) | PDF   | `/admin/reportes/semanal.pdf` |
| Listado de Inventario (ID, nombre, descripción, precio, stock, valor total) | Excel (.xlsx) | `/admin/reportes/inventario.xlsx` |
| Técnicos Disponibles (activos)              | CSV     | `/admin/reportes/tecnicos.csv` |
| Factura individual por pedido (RIF, IVA 16%, número de control) | PDF | `/admin/pedidos/<id>/factura` |

Todos se generan en memoria con `reportlab` (PDF) y `openpyxl` (Excel) —
no se guardan archivos temporales en el servidor.

## Reglas fiscales venezolanas implementadas

- **RIF**: se construye automáticamente como `TIPO-NÚMERO` (V, E, J, G o P) al
  registrar un cliente.
- **IVA 16%**: configurable en `config.py` (`PORCENTAJE_IVA`), se calcula
  automáticamente al crear un pedido y se desglosa en la factura.
- **Número de Control y Número de Factura**: campos separados y correlativos,
  generados automáticamente la primera vez que se solicita la factura de un pedido
  (`00-00000001`, `F-00000001`, etc.).
- **Datos del emisor**: razón social, RIF y dirección fiscal de tu empresa se
  configuran en `.env` (`EMPRESA_RAZON_SOCIAL`, `EMPRESA_RIF`,
  `EMPRESA_DIRECCION_FISCAL`) y aparecen en cada factura.

## Identidad visual

- El **sitio público** (`/`, `/login`) conserva el diseño original: fondo con
  degradado morado/azul, tarjetas glassmorphism.
- El **panel admin** usa un sidebar oscuro fijo con el menú solicitado
  (Panel de Control, Clientes, Productos, Gestión de Pedidos, Asignación de
  Técnicos, Usuarios, Reportes), área principal gris claro, tarjetas con
  bordes redondeados, y tablas minimalistas con encabezados en mayúsculas
  (`static/admin.css`).

## Pendiente / sugerido para la entrega final

- Despliegue en Vercel/Netlify/Render con las credenciales de administrador
  documentadas en PDF (ya lo tienes resuelto según indicaste).
- Ajustar `EMPRESA_RIF` y demás datos fiscales a los reales de tu proyecto
  antes de generar las facturas de muestra para el jurado.
