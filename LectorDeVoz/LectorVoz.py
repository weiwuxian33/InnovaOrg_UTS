import customtkinter as ctk
import pyttsx3
import threading
import math
import random
from tkinter import filedialog, messagebox, Canvas
from PIL import Image, ImageDraw, ImageFilter, ImageTk

# ============================================================
# 1. DETECCIÓN DE VOCES (usamos un engine temporal solo para listarlas)
# ============================================================
def obtener_voces_disponibles():
    """Crea un engine temporal solo para listar voces, y lo descarta."""
    engine_temp = pyttsx3.init()
    voces = engine_temp.getProperty('voices')

    diccionario = {}
    for voz in voces:
        nombre = voz.name.lower()
        id_voz = voz.id.lower()
        es_espanol = (
            "spanish" in nombre or "español" in nombre or
            "es-" in id_voz or "es_" in id_voz
        )
        if es_espanol:
            nombre_limpio = voz.name.replace("Microsoft ", "").replace(" Desktop", "")

            # Heurística de género: SAPI5 en Windows suele exponer 'gender'
            # en voz.gender, pero muchas voces no lo declaran bien, así que
            # reforzamos con palabras clave típicas de nombres de voces ES.
            genero = "Desconocido"
            try:
                if voz.gender:
                    if "female" in str(voz.gender).lower():
                        genero = "Chica"
                    elif "male" in str(voz.gender).lower():
                        genero = "Chico"
            except Exception:
                pass

            if genero == "Desconocido":
                nombres_femeninos = ["helena", "sabina", "laura", "elvira", "monica",
                                      "raquel", "marisol", "paloma", "lucia", "sara", "esperanza"]
                nombres_masculinos = ["pablo", "jorge", "diego", "carlos", "raul",
                                      "tiago", "andres", "juan", "miguel"]
                if any(n in nombre for n in nombres_femeninos):
                    genero = "Chica"
                elif any(n in nombre for n in nombres_masculinos):
                    genero = "Chico"

            etiqueta = f"{nombre_limpio} ({genero})" if genero != "Desconocido" else nombre_limpio
            diccionario[etiqueta] = voz.id

    # Si no se detectó ninguna voz en español, mostramos todas las disponibles
    if not diccionario:
        diccionario = {voz.name: voz.id for voz in voces}

    try:
        engine_temp.stop()
    except Exception:
        pass
    del engine_temp

    return diccionario


diccionario_voces = obtener_voces_disponibles()
nombres_voces = list(diccionario_voces.keys())

# Bandera global simple para evitar reproducciones simultáneas
reproduciendo = False
engine_actual = None  # referencia al engine en uso, para poder detenerlo desde fuera


# ============================================================
# 2. FUNCIONES LÓGICAS
# ============================================================
def hablar(texto, velocidad, voz_id):
    """
    Se ejecuta en un hilo separado. Crea su PROPIO engine cada vez.
    Esto es la clave para evitar el bug de 'solo funciona una vez':
    reusar el mismo engine global entre hilos en pyttsx3 + SAPI5 (Windows)
    deja el motor en un estado inválido tras el primer runAndWait().
    """
    global reproduciendo, engine_actual
    try:
        engine_local = pyttsx3.init()
        engine_actual = engine_local

        engine_local.setProperty('rate', velocidad)
        engine_local.setProperty('voice', voz_id)

        engine_local.say(texto)
        engine_local.runAndWait()

        try:
            engine_local.stop()
        except Exception:
            pass

    except Exception as e:
        print(f"Error en el motor de voz: {e}")
    finally:
        engine_actual = None
        reproduciendo = False
        app.after(0, reactivar_controles)


def obtener_texto_a_leer():
    """
    Si el usuario tiene una porción de texto seleccionada (sombreada) en la
    caja, devolvemos SOLO esa selección. Si no hay nada seleccionado,
    devolvemos el texto completo. Así se puede re-escuchar un fragmento
    puntual sin tener que reproducir todo desde el inicio cada vez.
    """
    try:
        # tk.SEL son las marcas internas que deja una selección de texto
        seleccion = caja_texto.get("sel.first", "sel.last")
        if seleccion.strip():
            return seleccion.strip()
    except Exception:
        pass  # no había selección activa, seguimos con el texto completo

    return caja_texto.get("1.0", "end-1c").strip()


def reproducir_audio():
    global reproduciendo

    if reproduciendo:
        return  # ya hay una reproducción en curso, ignoramos el click

    texto = obtener_texto_a_leer()
    if texto and texto != PLACEHOLDER:
        velocidad = int(slider_velocidad.get())
        voz_seleccionada = combo_voces.get()
        voz_id = diccionario_voces.get(voz_seleccionada)

        if not voz_id:
            messagebox.showerror("Error", "No se encontró la voz seleccionada.")
            return

        reproduciendo = True
        boton_play.configure(state="disabled")
        slider_velocidad.configure(state="disabled")
        combo_voces.configure(state="disabled")

        # Avisamos si está leyendo solo un fragmento seleccionado o todo el texto
        hay_seleccion = texto != caja_texto.get("1.0", "end-1c").strip()
        texto_estado = "🔊 Leyendo selección..." if hay_seleccion else "🔊 Reproduciendo..."
        label_estado.configure(text=texto_estado, text_color="#5ec26a")

        threading.Thread(target=hablar, args=(texto, velocidad, voz_id), daemon=True).start()
    else:
        messagebox.showwarning("Atención", "Por favor, ingresa un texto primero.")


def detener_audio():
    """Detiene la reproducción actual, si existe."""
    global engine_actual, reproduciendo
    if engine_actual is not None:
        try:
            engine_actual.stop()
        except Exception:
            pass
    reproduciendo = False
    reactivar_controles()


def reactivar_controles():
    boton_play.configure(state="normal")
    slider_velocidad.configure(state="normal")
    combo_voces.configure(state="normal")
    label_estado.configure(text="✅ Listo", text_color="#9a9aa5")


def guardar_mp3():
    texto = obtener_texto_a_leer()
    if not texto or texto == PLACEHOLDER:
        return messagebox.showwarning("Atención", "No hay texto para guardar.")

    ruta_archivo = filedialog.asksaveasfilename(
        defaultextension=".mp3",
        filetypes=[("Archivo MP3", "*.mp3")],
        title="Guardar audio como..."
    )

    if ruta_archivo:
        velocidad = int(slider_velocidad.get())
        voz_seleccionada = combo_voces.get()
        voz_id = diccionario_voces.get(voz_seleccionada)

        def guardar_en_hilo():
            try:
                label_estado.configure(text="💾 Guardando...", text_color="#e0b03c")
                engine_local = pyttsx3.init()
                engine_local.setProperty('rate', velocidad)
                engine_local.setProperty('voice', voz_id)
                engine_local.save_to_file(texto, ruta_archivo)
                engine_local.runAndWait()
                try:
                    engine_local.stop()
                except Exception:
                    pass
                app.after(0, lambda: messagebox.showinfo("¡Éxito!", f"Audio guardado en:\n{ruta_archivo}"))
            except Exception as e:
                app.after(0, lambda: messagebox.showerror("Error", f"No se pudo guardar el audio:\n{e}"))
            finally:
                app.after(0, reactivar_controles)

        boton_mp3.configure(state="disabled")
        threading.Thread(target=guardar_en_hilo, daemon=True).start()


def actualizar_texto_velocidad(valor):
    label_valor_vel.configure(text=f"{int(valor)}")


# --- Placeholder inteligente ---
PLACEHOLDER = "Escribe o pega tu texto aquí..."

def al_obtener_foco(event):
    if caja_texto.get("1.0", "end-1c") == PLACEHOLDER:
        caja_texto.delete("1.0", "end")
        caja_texto.configure(text_color="#ffffff")

def al_perder_foco(event):
    if not caja_texto.get("1.0", "end-1c").strip():
        caja_texto.insert("1.0", PLACEHOLDER)
        caja_texto.configure(text_color="#7a7a85")


# ============================================================
# 3. INTERFAZ GRÁFICA
# ============================================================
ctk.set_appearance_mode("dark")
app = ctk.CTk()
ANCHO, ALTO = 700, 720
app.geometry(f"{ANCHO}x{ALTO}")
app.title("Lector de Voz Pro - Sin Límites")
app.resizable(False, False)  # Evita que se rompa el gradiente al redimensionar

# --- FONDO: MESH GRADIENT ANIMADO (blobs de color difuminados con PIL) ---
canvas_fondo = Canvas(app, width=ANCHO, height=ALTO, highlightthickness=0)
canvas_fondo.place(x=0, y=0, relwidth=1, relheight=1)

# Paleta de colores para los "blobs" (azules/morados/teal, tono premium oscuro)
PALETA_BLOBS = [
    (90, 70, 220),    # violeta
    (40, 130, 220),   # azul
    (30, 200, 180),   # teal
    (160, 60, 200),   # magenta suave
    (20, 90, 160),    # azul profundo
]
COLOR_BASE = (8, 8, 14)  # casi negro, color de fondo detrás de los blobs

random.seed(7)

class Blob:
    """Un círculo de color difuso que flota lentamente por el canvas."""
    def __init__(self, color):
        self.x = random.uniform(0, ANCHO)
        self.y = random.uniform(0, ALTO)
        self.radio = random.uniform(160, 260)
        self.color = color
        self.angulo = random.uniform(0, 2 * math.pi)
        self.velocidad = random.uniform(0.15, 0.35)
        # Cada blob deriva en una trayectoria ligeramente curva (Lissajous-like)
        self.fase_x = random.uniform(0, 2 * math.pi)
        self.fase_y = random.uniform(0, 2 * math.pi)
        self.freq_x = random.uniform(0.15, 0.3)
        self.freq_y = random.uniform(0.15, 0.3)
        self.centro_x = self.x
        self.centro_y = self.y
        self.radio_movimiento = random.uniform(120, 220)

    def actualizar(self, t):
        self.x = self.centro_x + math.sin(t * self.freq_x + self.fase_x) * self.radio_movimiento
        self.y = self.centro_y + math.cos(t * self.freq_y + self.fase_y) * self.radio_movimiento

blobs = [Blob(c) for c in PALETA_BLOBS]

# Escala reducida para renderizar rápido (luego se reescala hacia arriba con suavizado)
ESCALA_RENDER = 4
ANCHO_R = ANCHO // ESCALA_RENDER
ALTO_R = ALTO // ESCALA_RENDER

imagen_tk_fondo = None  # referencia viva para que no la recoja el garbage collector

def renderizar_fondo():
    """Dibuja los blobs en baja resolución y aplica blur para lograr el efecto mesh gradient."""
    img = Image.new("RGB", (ANCHO_R, ALTO_R), COLOR_BASE)
    draw = ImageDraw.Draw(img)

    for blob in blobs:
        x = blob.x / ESCALA_RENDER
        y = blob.y / ESCALA_RENDER
        r = blob.radio / ESCALA_RENDER
        draw.ellipse([x - r, y - r, x + r, y + r], fill=blob.color)

    img = img.filter(ImageFilter.GaussianBlur(radius=18))
    img = img.resize((ANCHO, ALTO), Image.BILINEAR)
    # Un segundo blur suave a tamaño completo para eliminar bordes del upscale
    img = img.filter(ImageFilter.GaussianBlur(radius=6))
    return img

def obtener_color_promedio_zona(img, x, y, w, h):
    """Calcula el color promedio de una región del fondo (para el efecto vidrio)."""
    caja = img.crop((max(0, x), max(0, y), min(ANCHO, x + w), min(ALTO, y + h)))
    if caja.width == 0 or caja.height == 0:
        return COLOR_BASE
    pixeles = list(caja.resize((1, 1), Image.BILINEAR).getdata())
    return pixeles[0]

tiempo_animacion = 0.0

def animar_fondo():
    global imagen_tk_fondo, tiempo_animacion
    tiempo_animacion += 0.05

    for blob in blobs:
        blob.actualizar(tiempo_animacion)

    img_fondo = renderizar_fondo()
    imagen_tk_fondo = ImageTk.PhotoImage(img_fondo)
    canvas_fondo.delete("fondo")
    canvas_fondo.create_image(0, 0, anchor="nw", image=imagen_tk_fondo, tags="fondo")

    # --- Efecto "vidrio esmerilado" simulado en el panel principal ---
    # Tomamos el color promedio de la zona del fondo donde está el panel
    # y lo mezclamos con un gris oscuro, para que el panel "responda"
    # sutilmente a los colores que tiene detrás sin ser realmente transparente.
    px, py = int(ANCHO * 0.05), int(ALTO * 0.04)
    pw, ph = int(ANCHO * 0.9), int(ALTO * 0.92)
    color_zona = obtener_color_promedio_zona(img_fondo, px, py, pw, ph)

    gris_panel = (30, 30, 36)
    mezcla = 0.16  # cuánto del color de fondo se filtra hacia el panel
    color_mezclado = tuple(
        int(gris_panel[i] * (1 - mezcla) + color_zona[i] * mezcla) for i in range(3)
    )
    hex_panel = "#{:02x}{:02x}{:02x}".format(*color_mezclado)
    frame_principal.configure(fg_color=hex_panel)

    app.after(30, animar_fondo)  # ~33 fps, más perceptible y fluido

# --- CONTENEDOR PRINCIPAL (estilo "vidrio esmerilado" sobre el mesh gradient) ---
frame_principal = ctk.CTkFrame(app, corner_radius=24, fg_color="#1e1e24", border_width=1, border_color="#4a4a5a")
frame_principal.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.92)

titulo = ctk.CTkLabel(frame_principal, text="✨ Lector Automático Premium", font=("Segoe UI", 24, "bold"))
titulo.pack(pady=(20, 15))

caja_texto = ctk.CTkTextbox(frame_principal, height=220, font=("Segoe UI", 14), corner_radius=15, fg_color="#15151a")
caja_texto.pack(fill="x", padx=20, pady=(0, 15))
caja_texto.insert("1.0", PLACEHOLDER)
caja_texto.configure(text_color="#7a7a85")
caja_texto.bind("<FocusIn>", al_obtener_foco)
caja_texto.bind("<FocusOut>", al_perder_foco)

# Etiqueta de estado
label_estado = ctk.CTkLabel(frame_principal, text="✅ Listo", font=("Segoe UI", 12), text_color="#9a9aa5")
label_estado.pack(pady=(0, 10))

# Panel de Controles
frame_controles = ctk.CTkFrame(frame_principal, fg_color="transparent")
frame_controles.pack(fill="x", padx=20, pady=5)

label_voz = ctk.CTkLabel(frame_controles, text="Selecciona la Voz:", font=("Segoe UI", 14))
label_voz.grid(row=0, column=0, padx=(0, 10), sticky="w")

combo_voces = ctk.CTkOptionMenu(frame_controles, values=nombres_voces, width=300, corner_radius=10, fg_color="#2b2b36")
combo_voces.grid(row=0, column=1, padx=10, sticky="w")
if nombres_voces:
    combo_voces.set(nombres_voces[0])

label_velocidad = ctk.CTkLabel(frame_controles, text="Velocidad:", font=("Segoe UI", 14))
label_velocidad.grid(row=1, column=0, padx=(0, 10), pady=20, sticky="w")

frame_slider = ctk.CTkFrame(frame_controles, fg_color="transparent")
frame_slider.grid(row=1, column=1, padx=10, pady=20, sticky="w")

slider_velocidad = ctk.CTkSlider(frame_slider, from_=50, to=300, number_of_steps=250, width=200, command=actualizar_texto_velocidad)
slider_velocidad.pack(side="left")
slider_velocidad.set(150)

label_valor_vel = ctk.CTkLabel(frame_slider, text="150", font=("Segoe UI", 14, "bold"))
label_valor_vel.pack(side="left", padx=(10, 0))

# Panel de Botones
frame_botones = ctk.CTkFrame(frame_principal, fg_color="transparent")
frame_botones.pack(pady=20)

boton_play = ctk.CTkButton(frame_botones, text="▶ Reproducir", font=("Segoe UI", 14, "bold"), height=40, corner_radius=10, command=reproducir_audio)
boton_play.grid(row=0, column=0, padx=10)

boton_stop = ctk.CTkButton(frame_botones, text="⏹ Detener", font=("Segoe UI", 14, "bold"), height=40, corner_radius=10, fg_color="#a83232", hover_color="#7a2424", command=detener_audio)
boton_stop.grid(row=0, column=1, padx=10)

boton_mp3 = ctk.CTkButton(frame_botones, text="💾 MP3", font=("Segoe UI", 14, "bold"), height=40, corner_radius=10, fg_color="#2b7a4b", hover_color="#1e5c38", command=guardar_mp3)
boton_mp3.grid(row=0, column=2, padx=10)

# Iniciamos el loop de animación del fondo (mesh gradient + efecto vidrio del panel)
animar_fondo()

app.mainloop()