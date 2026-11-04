"""
Control por Voz — Miguel Ruiz
Interfaz multimodal + IoT: hablas un comando, la app lo transcribe,
lo interpreta y lo publica por MQTT para que un ESP32 (simulado en Wokwi)
encienda las luces o abra la puerta.
"""

import io
import re
import json
import hashlib
import unicodedata
import uuid
from datetime import datetime

import streamlit as st
import paho.mqtt.client as mqtt
import speech_recognition as sr
from gtts import gTTS
from PIL import Image


# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
try:
    _icon = Image.open('logo_mr.png')
except Exception:
    _icon = "🎙️"
st.set_page_config(
    page_title="Control por Voz · Miguel Ruiz",
    page_icon=_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

for k, v in {"historial": [], "ultimo_audio": "", "luces": False, "puerta": False, "transcripcion": ""}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# ESTILOS — sistema de mis apps (azul petróleo + terracota + ámbar)
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background: linear-gradient(135deg, #1b3a4b 0%, #14303d 100%); }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stToolbar"] { right: 1rem; }
    .block-container { padding-top: 2.6rem !important; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #12272f !important; border-right: 1px solid #2a4b57; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #e07a5f !important; font-family: 'Montserrat', 'Inter', sans-serif !important;
        font-weight: 700 !important; font-size: 0.95rem !important;
        text-transform: uppercase !important; letter-spacing: 0.8px !important;
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] label p {
        color: #e8eef0 !important; font-size: 0.85rem !important; font-weight: 500 !important;
    }
    [data-testid="stSidebar"] p { color: #c4d0d6 !important; font-size: 0.88rem !important; }
    [data-testid="stSidebar"] hr { border-color: #2a4b57 !important; margin: 16px 0 !important; }

    /* Inputs */
    textarea, input[type="text"], input[type="number"] {
        background-color: #ffffff !important; color: #111827 !important;
        font-family: 'Inter', sans-serif !important; font-size: 0.9rem !important;
    }
    [data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"] {
        background: #ffffff !important; border: 1px solid #d1d5db !important; border-radius: 6px !important;
    }
    [data-testid="stTextInputRootElement"] input, [data-testid="stNumberInputContainer"] input { border: none !important; }
    [data-testid="stNumberInputContainer"] button { background: #f3f6f7 !important; color: #14303d !important; }
    input::placeholder { color: #6b7280 !important; }

    /* Títulos */
    h1 { font-family: 'Montserrat', 'Inter', sans-serif !important; color: #f2cc8f !important; font-weight: 700 !important; letter-spacing: -0.5px !important; }
    h2, h3 { font-family: 'Montserrat', 'Inter', sans-serif !important; color: #e07a5f !important; font-weight: 600 !important; }
    h4 { font-family: 'Montserrat', 'Inter', sans-serif !important; color: #f2cc8f !important; font-weight: 600 !important; }
    p, li { color: #e8eef0 !important; font-size: 0.95rem !important; line-height: 1.65 !important; }
    strong { color: #f2cc8f; }

    /* Botón principal — terracota */
    .stButton button {
        background: #e07a5f !important; color: #ffffff !important; border: none !important;
        border-radius: 6px !important; font-family: 'Montserrat', 'Inter', sans-serif !important;
        font-weight: 600 !important; font-size: 0.9rem !important; letter-spacing: 0.3px !important;
        padding: 0.6rem 1.4rem !important; width: 100% !important;
        transition: background 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stButton button p { color: #ffffff !important; font-weight: 600 !important; }
    .stButton button:hover { background: #c9583c !important; box-shadow: 0 2px 12px rgba(224,122,95,0.35) !important; }
    .stButton button[kind="secondary"] {
        background: #24485a !important; border: 1px solid rgba(242,204,143,0.2) !important;
        padding: 0.6rem 0.5rem !important; white-space: nowrap;
    }
    .stButton button[kind="secondary"]:hover { background: #2c5568 !important; box-shadow: none !important; }

    /* Métricas */
    [data-testid="stMetric"] {
        background: #1d3f4e; border: 1px solid rgba(242,204,143,0.15); border-top: 3px solid #e07a5f;
        border-radius: 12px; padding: 18px 22px; box-shadow: 0 4px 18px rgba(0,0,0,0.22);
    }
    [data-testid="stMetricLabel"] p {
        color: #a9c0ca !important; font-size: 0.78rem !important; font-weight: 600 !important;
        text-transform: uppercase !important; letter-spacing: 0.6px !important;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
        color: #f2cc8f !important; font-weight: 700 !important; font-size: 1.35rem !important;
    }

    /* Header */
    .header-card {
        background: linear-gradient(135deg, #1d3f4e 0%, #1a3947 100%);
        border: 1px solid rgba(242,204,143,0.15); border-left: 5px solid #e07a5f;
        border-radius: 14px; padding: 28px 36px; margin-bottom: 24px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.25);
        display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap;
    }
    .conexion {
        background: #24485a; border: 1px solid rgba(242,204,143,0.25); border-radius: 20px;
        padding: 6px 14px; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: #e8eef0;
    }
    .conexion b { color: #7bd88f; }

    /* Tarjetas de sección */
    .st-key-card_voz, .st-key-card_estado, .st-key-card_historial, .st-key-card_comandos {
        background: #1d3f4e; border: 1px solid rgba(242,204,143,0.15); border-radius: 14px;
        padding: 24px 28px; box-shadow: 0 4px 18px rgba(0,0,0,0.20);
    }

    /* Grabadora */
    [data-testid="stAudioInput"] {
        background: #24485a !important; border: 1px solid rgba(242,204,143,0.2) !important; border-radius: 12px !important;
    }
    [data-testid="stAudioInput"] * { color: #e8eef0 !important; }

    /* Transcripción */
    .transcripcion {
        background: #24485a; border: 1px solid rgba(242,204,143,0.15); border-left: 4px solid #f2cc8f;
        border-radius: 10px; padding: 14px 18px; margin: 10px 0;
    }
    .transcripcion small {
        display: block; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #a9c0ca;
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;
    }
    .transcripcion span { font-size: 1.15rem; color: #e8eef0; font-weight: 500; }

    /* Etiquetas */
    .uso-tag {
        display: inline-block; background: #24485a; border: 1px solid rgba(242,204,143,0.18);
        border-radius: 20px; padding: 5px 14px; font-size: 0.85rem; font-weight: 500; color: #e8eef0; margin: 4px 3px;
    }

    /* Estado del circuito */
    .dispositivos { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .disp {
        background: #24485a; border: 1px solid rgba(242,204,143,0.12); border-radius: 12px;
        padding: 18px 12px; text-align: center; transition: all 0.3s ease;
    }
    .disp .ic { font-size: 2.3rem; display: block; margin-bottom: 6px; filter: grayscale(0.9) opacity(0.55); transition: all 0.3s ease; }
    .disp b { display: block; font-family: 'Montserrat', sans-serif; color: #e8eef0; font-size: 0.92rem; }
    .disp small { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #a9c0ca; }
    .disp.on { border-color: #f2cc8f; box-shadow: 0 0 24px rgba(242,204,143,0.25), inset 0 0 18px rgba(242,204,143,0.08); }
    .disp.on .ic { filter: none; }
    .disp.on small { color: #f2cc8f; }

    /* Filas del historial */
    .freq-row {
        display: flex; align-items: center; gap: 12px; padding: 8px 14px; margin: 4px 0;
        background: #24485a; border: 1px solid rgba(242,204,143,0.12); border-radius: 8px;
        color: #e8eef0; font-size: 0.88rem;
    }
    .freq-row .ic-row { font-size: 1.2rem; }
    .freq-row .txt { line-height: 1.3; }
    .freq-row .txt small { display: block; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #a9c0ca; }
    .freq-row .ok, .freq-row .no {
        margin-left: auto; width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center;
        font-size: 0.75rem; font-weight: 700; flex-shrink: 0;
    }
    .freq-row .ok { background: rgba(123,216,143,0.15); color: #7bd88f; }
    .freq-row .no { background: rgba(224,122,95,0.15); color: #e07a5f; }
    .rank-tag {
        background: #14303d; border: 1px solid rgba(242,204,143,0.2); border-radius: 6px; padding: 1px 8px;
        font-size: 0.75rem; font-weight: 700; color: #f2cc8f; font-family: 'IBM Plex Mono', monospace;
    }

    /* Código / payload */
    .payload {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; color: #f2cc8f;
        background: #14303d; border: 1px solid rgba(242,204,143,0.15); border-radius: 8px; padding: 8px 12px;
    }

    [data-testid="stAlert"] { border-radius: 10px !important; }
    div[data-testid="stExpander"] { border: 1px solid rgba(242,204,143,0.15) !important; border-radius: 12px !important; background: #1d3f4e !important; }
    hr { border-color: rgba(242,204,143,0.15) !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# COMANDOS (deben coincidir con el sketch del ESP32)
# ─────────────────────────────────────────────
COMANDOS = {
    "enciende las luces": ("💡", "Encender luces", "Encendiendo las luces"),
    "apaga las luces":    ("🌑", "Apagar luces",   "Apagando las luces"),
    "abre la puerta":     ("🚪", "Abrir puerta",   "Abriendo la puerta"),
    "cierra la puerta":   ("🔒", "Cerrar puerta",  "Cerrando la puerta"),
}


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zñ\s]", " ", texto)


def interpretar(texto):
    """Convierte lo que dijo la persona en uno de los 4 comandos exactos del ESP32."""
    t = normalizar(texto)
    palabras = set(t.split())
    luz = bool(palabras & {"luz", "luces", "bombillo", "bombillos", "led", "lampara", "foco"})
    puerta = "puerta" in palabras or "porton" in palabras
    encender = re.search(r"\b(enciend|encend|prend|activ)", t)
    apagar = re.search(r"\b(apag|desactiv)", t)
    abrir = re.search(r"\b(abr|abier)", t)
    cerrar = re.search(r"\b(cierr|cerr)", t)
    if luz and apagar:
        return "apaga las luces"
    if luz and encender:
        return "enciende las luces"
    if puerta and cerrar:
        return "cierra la puerta"
    if puerta and abrir:
        return "abre la puerta"
    return None


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎙️ Control por Voz")
    st.divider()

    st.markdown("### CONEXIÓN MQTT")
    broker = st.text_input("Broker:", value="broker.mqttdashboard.com")
    puerto = st.number_input("Puerto:", value=1883, step=1)
    topico = st.text_input("Tópico:", value="voice_ctrl_miguelruiz",
                           help="Debe ser el mismo tópico al que se suscribe el ESP32 en Wokwi.")

    st.divider()

    st.markdown("### RESPUESTA")
    hablar = st.toggle("Confirmar en voz alta", value=True)

    st.divider()

    st.markdown("### COMANDOS")
    st.markdown("".join(f'<span class="uso-tag">{ic} {cmd}</span>' for cmd, (ic, _, _) in COMANDOS.items()),
                unsafe_allow_html=True)
    st.caption("También entiende variaciones: «prende la luz», «cerrar la puerta», «apaga el bombillo»…")


# ─────────────────────────────────────────────
# MQTT
# ─────────────────────────────────────────────
def publicar(comando):
    payload = json.dumps({"Act1": comando})
    client_id = f"app-miguelruiz-{uuid.uuid4().hex[:6]}"
    try:
        try:
            cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        except AttributeError:  # paho-mqtt 1.x
            cliente = mqtt.Client(client_id=client_id)
        cliente.connect(broker, int(puerto), keepalive=30)
        cliente.loop_start()
        info = cliente.publish(topico, payload, qos=1)
        info.wait_for_publish(timeout=5)
        cliente.loop_stop()
        cliente.disconnect()
        ok = info.is_published()
        return ok, payload, None if ok else "El broker no confirmó la publicación."
    except Exception as e:
        return False, payload, str(e)


def voz(texto):
    try:
        buf = io.BytesIO()
        gTTS(texto, lang="es", tld="com.mx").write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None


def ejecutar(comando, origen, dicho=""):
    ok, payload, error = publicar(comando)
    st.session_state.historial.insert(0, {
        "hora": datetime.now().strftime("%H:%M:%S"), "comando": comando,
        "origen": origen, "dicho": dicho, "ok": ok, "payload": payload, "error": error,
    })
    if ok:
        if comando == "enciende las luces":
            st.session_state.luces = True
        elif comando == "apaga las luces":
            st.session_state.luces = False
        elif comando == "abre la puerta":
            st.session_state.puerta = True
        elif comando == "cierra la puerta":
            st.session_state.puerta = False
    return ok, payload, error


# ─────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="header-card">
    <div>
        <p style="margin:0 0 4px 0; color:#e07a5f !important; font-family:'Montserrat',sans-serif; font-weight:700; font-size:1.1rem;">Miguel Ruiz</p>
        <h1 style="margin:0; font-size:1.9rem; color:#f2cc8f !important;">🎙️ Control por Voz</h1>
        <p style="margin:6px 0 0 0; color:#a9c0ca !important; font-size:0.97rem;">
            Controla las luces y la puerta de un circuito IoT con tu voz · MQTT + ESP32 en Wokwi
        </p>
    </div>
    <span class="conexion"><b>●</b> {broker} · {topico}</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# VOZ + ESTADO
# ─────────────────────────────────────────────
col_izq, col_der = st.columns([1.2, 1], gap="large")
aviso = None

with col_izq:
    with st.container(key="card_voz"):
        st.markdown("### 🎤 Habla tu comando")
        st.markdown('<p style="margin:-6px 0 10px; color:#a9c0ca !important; font-size:0.9rem;">'
                    'Toca el micrófono, di por ejemplo <strong>«enciende las luces»</strong> y vuelve a tocarlo para enviar.</p>',
                    unsafe_allow_html=True)
        audio = st.audio_input("Graba tu comando", label_visibility="collapsed")

        if audio is not None:
            datos = audio.getvalue()
            huella = hashlib.md5(datos).hexdigest()
            if huella != st.session_state.ultimo_audio:
                st.session_state.ultimo_audio = huella
                with st.spinner("Transcribiendo tu voz..."):
                    try:
                        r = sr.Recognizer()
                        with sr.AudioFile(io.BytesIO(datos)) as fuente:
                            grabacion = r.record(fuente)
                        dicho = r.recognize_google(grabacion, language="es-CO")
                    except sr.UnknownValueError:
                        dicho = ""
                        aviso = ("warning", "No entendí lo que dijiste. Intenta hablar más cerca del micrófono.")
                    except Exception as e:
                        dicho = ""
                        aviso = ("error", f"No se pudo transcribir el audio: {e}")
                st.session_state.transcripcion = dicho
                if dicho:
                    comando = interpretar(dicho)
                    if comando:
                        ok, payload, error = ejecutar(comando, "voz", dicho)
                        aviso = ("success", f"Comando enviado: «{comando}»") if ok else ("error", f"No se pudo enviar: {error}")
                    else:
                        aviso = ("warning", f"Escuché «{dicho}», pero no corresponde a ningún comando.")

        if st.session_state.transcripcion:
            st.markdown(f'<div class="transcripcion"><small>Escuché</small><span>«{st.session_state.transcripcion}»</span></div>',
                        unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    with st.container(key="card_comandos"):
        st.markdown("### ⚡ Comandos rápidos")
        st.markdown('<p style="margin:-6px 0 10px; color:#a9c0ca !important; font-size:0.9rem;">'
                    'Por si no tienes micrófono a mano: envían exactamente el mismo mensaje.</p>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        for i, (cmd, (ic, nombre, _)) in enumerate(COMANDOS.items()):
            col = c1 if i % 2 == 0 else c2
            if col.button(f"{ic}  {nombre}", key=f"btn_{i}", type="secondary", use_container_width=True):
                ok, payload, error = ejecutar(cmd, "botón")
                aviso = ("success", f"Comando enviado: «{cmd}»") if ok else ("error", f"No se pudo enviar: {error}")

        escrito = st.text_input("Escribir comando", placeholder="o escríbelo: prende la luz, abre la puerta…")
        if st.button("ENVIAR COMANDO ↗", key="enviar_texto", type="primary", use_container_width=True):
            comando = interpretar(escrito or "")
            if comando:
                ok, payload, error = ejecutar(comando, "texto", escrito)
                aviso = ("success", f"Comando enviado: «{comando}»") if ok else ("error", f"No se pudo enviar: {error}")
            else:
                aviso = ("warning", "Ese texto no corresponde a ningún comando.")

with col_der:
    with st.container(key="card_estado"):
        st.markdown("### 🏠 Estado del circuito")
        luces, puerta = st.session_state.luces, st.session_state.puerta
        st.markdown(f"""
        <div class="dispositivos">
            <div class="disp {'on' if luces else ''}"><span class="ic">💡</span><b>Luces</b><small>{'ENCENDIDAS' if luces else 'APAGADAS'}</small></div>
            <div class="disp {'on' if puerta else ''}"><span class="ic">{'🚪' if puerta else '🔒'}</span><b>Puerta</b><small>{'ABIERTA · 180°' if puerta else 'CERRADA · 90°'}</small></div>
        </div>
        <p style="margin:12px 0 0; color:#a9c0ca !important; font-size:0.8rem !important;">
            Estado según los últimos comandos enviados con éxito. Compruébalo en la simulación de Wokwi.</p>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if aviso:
        tipo, texto = aviso
        getattr(st, tipo)(texto)
        if tipo == "success" and hablar:
            ultimo = st.session_state.historial[0]["comando"]
            sonido = voz(COMANDOS[ultimo][2])
            if sonido:
                st.audio(sonido, format="audio/mp3", autoplay=True)

    with st.container(key="card_historial"):
        st.markdown("### 📡 Mensajes enviados")
        hist = st.session_state.historial
        if hist:
            st.markdown(f'<div class="payload">tópico: {topico}<br>{hist[0]["payload"]}</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown(
                "".join(
                    f'<div class="freq-row"><span class="ic-row">{COMANDOS[h["comando"]][0]}</span>'
                    f'<div class="txt">{h["comando"]}<small>{h["hora"]} · {h["origen"]}</small></div>'
                    f'<span class="{"ok" if h["ok"] else "no"}">{"✓" if h["ok"] else "✕"}</span></div>'
                    for h in hist[:8]
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<p style="color:#a9c0ca !important; font-size:0.9rem;">Todavía no has enviado comandos.</p>',
                        unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÉTRICAS + AYUDA
# ─────────────────────────────────────────────
st.divider()
hist = st.session_state.historial
m1, m2, m3, m4 = st.columns(4)
m1.metric("Comandos enviados", sum(1 for h in hist if h["ok"]))
m2.metric("Por voz", sum(1 for h in hist if h["ok"] and h["origen"] == "voz"))
m3.metric("Último comando", f'{COMANDOS[hist[0]["comando"]][0]} {COMANDOS[hist[0]["comando"]][1].split()[0]}' if hist else "—")
m4.metric("Errores", sum(1 for h in hist if not h["ok"]))

with st.expander("¿Cómo se conecta con Wokwi?"):
    st.markdown(f"""
1. La app convierte tu voz en texto y la interpreta como uno de los 4 comandos.
2. Publica el mensaje `{{"Act1": "enciende las luces"}}` en el broker **{broker}**, tópico **{topico}**.
3. El ESP32 simulado en Wokwi está suscrito a ese mismo tópico: recibe el mensaje y enciende el LED (pin 2)
   o mueve el servo (pin 13).

Para que funcione, la simulación de Wokwi debe estar **corriendo** y usar el **mismo broker y tópico**.
""")
