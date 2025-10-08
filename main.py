import os
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from telegram import Bot
from openai import OpenAI

# === CARGA DE VARIABLES DEL .ENV ===
load_dotenv()
GC_EMAIL = os.getenv("GC_EMAIL")
GC_PASSWORD = os.getenv("GC_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === INICIALIZAR BOT DE TELEGRAM ===
bot = Bot(token=TELEGRAM_TOKEN)

# === INICIALIZAR OPENAI ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === FUNCIÓN PARA ENVIAR MENSAJES DE TELEGRAM ===
def enviar_mensaje(mensaje: str):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje)
        print(f"📩 Mensaje enviado a Telegram: {mensaje}")
    except Exception as e:
        print(f"⚠️ Error al enviar mensaje a Telegram: {e}")

# === FUNCIÓN PARA GENERAR RESPUESTAS CON OPENAI ===
def generar_respuesta(texto_tarea):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente que ayuda a completar tareas de clase."},
                {"role": "user", "content": texto_tarea}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generando respuesta: {e}"

# === FUNCIÓN PRINCIPAL: REVISAR TAREAS PENDIENTES ===
def revisar_tareas():
    print(f"🔁 Ejecutando revisión de tareas pendientes... {datetime.now()}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Ir a Google Classroom
            print("🌐 Abriendo Google Classroom...")
            page.goto("https://classroom.google.com/u/3/h", timeout=60000)

            # Iniciar sesión si es necesario
            if "accounts.google.com" in page.url:
                print("🔐 Iniciando sesión...")
                page.fill("input[type='email']", GC_EMAIL)
                page.click("button:has-text('Siguiente')")
                page.wait_for_timeout(2000)
                page.fill("input[type='password']", GC_PASSWORD)
                page.click("button:has-text('Siguiente')")
                page.wait_for_load_state("networkidle")

            # Esperar a que cargue el contenido principal
            page.wait_for_selector("div[role='main']", timeout=60000)

            # Buscar todas las tareas pendientes
            tareas = page.query_selector_all("a.onkcGd.ARTZne")
            print(f"📋 {len(tareas)} tareas detectadas.")

            if not tareas:
                enviar_mensaje("🎉 No hay tareas pendientes.")
            else:
                for tarea in tareas:
                    try:
                        titulo = tarea.inner_text()
                        href = tarea.get_attribute("href")

                        if not href or not titulo.strip():
                            continue

                        print(f"📝 Procesando tarea: {titulo}")
                        page.goto(f"https://classroom.google.com{href}", timeout=60000)
                        page.wait_for_timeout(4000)

                        # Obtener el texto de la tarea
                        contenido = page.inner_text("div[role='main']")
                        respuesta = generar_respuesta(contenido)

                        # Crear un documento con la respuesta
                        print("📄 Creando documento...")
                        page.click("button:has-text('Agregar o crear')")
                        page.wait_for_timeout(2000)
                        page.click("div[role='menuitem']:has-text('Documentos')")
                        page.wait_for_timeout(5000)

                        # Cambiar al documento recién creado
                        paginas = context.pages
                        doc_page = paginas[-1]
                        doc_page.wait_for_load_state("domcontentloaded")
                        doc_page.keyboard.type(respuesta)
                        time.sleep(2)

                        enviar_mensaje(f"✅ Tarea '{titulo}' completada. Pendiente de entregar.")
                        page.bring_to_front()
                        page.wait_for_timeout(3000)
                    except Exception as e:
                        print(f"⚠️ Error con la tarea '{titulo if 'titulo' in locals() else 'desconocida'}': {e}")

            browser.close()
    except Exception as e:
        print(f"❌ Error general: {e}")
        enviar_mensaje(f"❌ Error general en la revisión: {e}")
    print("✅ Revisión completada.\n")

# === LOOP PRINCIPAL ===
if __name__ == "__main__":
    while True:
        revisar_tareas()
        print("⏳ Esperando 1 hora para la siguiente revisión...\n")
        time.sleep(3600)
