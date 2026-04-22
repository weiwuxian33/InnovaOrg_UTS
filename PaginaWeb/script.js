/* --- VARIABLES --- */
const skillButton = document.getElementById('view-skill');
const icons = document.querySelectorAll('.icon-slot');
const audio = document.getElementById('bg-music');
const toggleBtn = document.getElementById('music-toggle');
let currentActiveIndex = 0;

/* --- CONFIGURACIÓN INICIAL DE AUDIO --- */
if (audio) {
    audio.volume = 0.3; // Volumen al 20% (ajusta de 0.0 a 1.0 según prefieras)
}

/* --- LÓGICA DE LOS ICONOS DE HABILIDADES --- */
if (skillButton && icons.length > 0) {
    skillButton.addEventListener('click', () => {
        // 1. Quita el brillo del icono actual
        icons[currentActiveIndex].classList.remove('active');
        
        // 2. Pasa al siguiente icono
        currentActiveIndex = (currentActiveIndex + 1) % icons.length;
        
        // 3. Pon el brillo al nuevo icono
        icons[currentActiveIndex].classList.add('active');
    });
}

/* --- LÓGICA DE LA MÚSICA Y MUTE --- */

// 1. Iniciar música al primer clic en cualquier parte de la página
window.addEventListener('click', () => {
    if (audio && audio.paused) {
        audio.play().catch(err => console.log("Interacción requerida para audio"));
    }
}, { once: true });

// 2. Botón de Mute (Previene que el volumen sea ensordecedor)
if (toggleBtn && audio) {
    toggleBtn.addEventListener('click', (e) => {
        // e.stopPropagation() evita que el clic "atraviese" el botón 
        // y active otras funciones de la página por error
        e.stopPropagation(); 
        
        if (audio.muted) {
            audio.muted = false;
            toggleBtn.innerText = '🔊';
        } else {
            audio.muted = true;
            toggleBtn.innerText = '🔇';
        }
    });
}