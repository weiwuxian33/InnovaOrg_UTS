import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'

const SUPABASE_URL = 'https://tjwgiwfuidtptsjvyglk.supabase.co'
const SUPABASE_ANON_KEY = 'sb_publishable_TKO64m749jBBQCAbh4SVbA_aC0hplzx'
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

async function listarProductos() {
    // Pedimos todo (*) de la tabla productos
    const { data, error } = await supabase.from('productos').select('*')
    
    if (error) {
        console.error("Error al obtener datos:", error)
        return
    }
    
    const tabla = document.getElementById('tabla-productos')
    if (data && data.length > 0) {
        tabla.innerHTML = data.map(p => `
            <tr>
                <td>${p.nombre}</td>
                <td>${p.descripcion || '-'}</td>
                <td>$${p.precio}</td>
                <td>${p.stock}</td>
            </tr>
        `).join('')
    } else {
        tabla.innerHTML = "<tr><td colspan='4'>No hay datos disponibles</td></tr>"
    }
}

window.registrar = async function() {
    const email = document.getElementById('email').value
    const password = document.getElementById('password').value
    const { error } = await supabase.auth.signUp({ email, password })
    if (error) alert("Error: " + error.message)
    else alert("¡Registro exitoso! Revisa tu correo.")
}

listarProductos()