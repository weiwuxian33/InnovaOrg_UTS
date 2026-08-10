// app.js — Innova Corp (catálogo público, consola de estado y registro)
// Habla con la API de Flask (app.py); no hay lógica de negocio ni credenciales aquí.

let CATALOGO = [];
let FILTRO_ACTUAL = 'todos';

const ICONOS = { servicio: '⚙', producto: '▧' };

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function tarjetaHTML(item) {
    const esServicio = item.tipo === 'servicio';
    let stockClase = 'stock-ok';
    let stockTexto = 'Disponible';

    if (!esServicio) {
        if (item.stock > 0) {
            stockTexto = `En stock: ${item.stock}`;
        } else {
            stockTexto = 'Agotado';
            stockClase = 'stock-out';
        }
    }

    return `
        <article class="cat-card" data-tipo="${item.tipo}">
            <div class="cat-card-top">
                <span class="cat-icon">${ICONOS[item.tipo] || '◆'}</span>
                <span class="cat-code">${escapeHtml(item.codigo || '')}</span>
            </div>
            <h3>${escapeHtml(item.nombre)}</h3>
            <p class="cat-desc">${escapeHtml(item.descripcion || 'Sin descripción disponible.')}</p>
            <div class="cat-card-bottom">
                <span class="cat-price">$${Number(item.precio).toFixed(2)}</span>
                <span class="cat-stock ${stockClase}">${stockTexto}</span>
            </div>
        </article>
    `;
}

function renderizarCatalogo() {
    const grid = document.getElementById('catalogoGrid');
    if (!grid) return;

    const buscador = document.getElementById('buscador');
    const texto = (buscador ? buscador.value : '').toLowerCase().trim();

    const filtrados = CATALOGO.filter(item => {
        const pasaFiltro = FILTRO_ACTUAL === 'todos' || item.tipo === FILTRO_ACTUAL;
        const pasaTexto = !texto ||
            item.nombre.toLowerCase().includes(texto) ||
            (item.descripcion || '').toLowerCase().includes(texto);
        return pasaFiltro && pasaTexto;
    });

    if (!filtrados.length) {
        grid.innerHTML = `<p class="catalog-empty">No encontramos nada con esos filtros. Prueba con otra búsqueda.</p>`;
        return;
    }

    grid.innerHTML = filtrados.map(tarjetaHTML).join('');
}

function actualizarConsola() {
    const total = CATALOGO.length;
    const servicios = CATALOGO.filter(i => i.tipo === 'servicio').length;
    const productos = CATALOGO.filter(i => i.tipo === 'producto').length;
    const stock = CATALOGO.reduce((acc, i) => acc + (i.tipo === 'producto' ? Number(i.stock || 0) : 0), 0);

    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };
    set('statTotal', total);
    set('statServicios', servicios);
    set('statProductos', productos);
    set('statStock', stock);
}

async function cargarCatalogo() {
    const grid = document.getElementById('catalogoGrid');
    try {
        const respuesta = await fetch('/api/servicios');
        CATALOGO = await respuesta.json();
        actualizarConsola();
        renderizarCatalogo();
    } catch (err) {
        console.error('Error al cargar el catálogo:', err);
        if (grid) grid.innerHTML = `<p class="catalog-empty">No se pudo cargar el catálogo. Intenta recargar la página.</p>`;
        actualizarConsola();
    }
}

function inicializarControles() {
    const buscador = document.getElementById('buscador');
    if (buscador) buscador.addEventListener('input', renderizarCatalogo);

    document.querySelectorAll('#filtroChips .chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('#filtroChips .chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            FILTRO_ACTUAL = chip.dataset.filtro;
            renderizarCatalogo();
        });
    });
}

function inicializarNav() {
    const toggle = document.getElementById('navToggle');
    const nav = document.querySelector('.site-nav');
    if (toggle && nav) {
        toggle.addEventListener('click', () => nav.classList.toggle('nav-open'));
        nav.querySelectorAll('.nav-links a').forEach(a => {
            a.addEventListener('click', () => nav.classList.remove('nav-open'));
        });
    }
}

window.registrar = async function () {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const caja = document.getElementById('mensaje-registro');

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email || !password) {
        mostrarMensaje(caja, 'Completa correo y contraseña.', 'error');
        return;
    }

    try {
        const respuesta = await fetch('/api/registrar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await respuesta.json();

        if (!respuesta.ok) {
            mostrarMensaje(caja, data.error || 'Ocurrió un error al registrar.', 'error');
            return;
        }

        mostrarMensaje(caja, data.mensaje, 'success');
        emailInput.value = '';
        passwordInput.value = '';
    } catch (err) {
        console.error('Error al registrar:', err);
        mostrarMensaje(caja, 'No se pudo conectar con el servidor.', 'error');
    }
};

function mostrarMensaje(caja, texto, tipo) {
    if (!caja) {
        alert(texto);
        return;
    }
    caja.textContent = texto;
    caja.className = `alerta alerta-${tipo}`;
    caja.style.display = 'block';
}

document.addEventListener('DOMContentLoaded', () => {
    inicializarControles();
    inicializarNav();
    cargarCatalogo();
});
