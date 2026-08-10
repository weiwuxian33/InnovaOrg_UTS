import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'

const SUPABASE_URL = 'https://tjwgiwfuidtptsjvyglk.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRqd2dpd2Z1aWR0cHRzanZ5Z2xrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIzNTA5ODYsImV4cCI6MjA5NzkyNjk4Nn0.x2YJ0xgixCICq9Tpt8qOcjK_LutRnHOi40Pf5FwSptI'
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

async function listarProductos() {
    const { data, error } = await supabase.from('productos').select('*')
    
    if (error) {
        console.error("Error:", error.message)
        return
    }
    
    const tabla = document.getElementById('tabla-productos')
    if (data) {
        tabla.innerHTML = data.map(p => `
            <tr>
                <td>${p.nombre}</td>
                <td>${p.descripcion || '-'}</td>
                <td>$${p.precio}</td>
                <td>${p.stock}</td>
            </tr>
        `).join('')
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