import os
import time
import json
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import openai
from datetime import datetime

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
load_dotenv()

EMAIL = os.getenv("GC_EMAIL")
PASSWORD = os.getenv("GC_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_KEY
TAREAS_FILE = "tareas.json"
STATE_FILE = "state.json"

# -----------------------------
# FUNCIONES AUXILIARES
# -----------------------------

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Error enviando Telegram: {e}")

def cargar_tareas():
    if os.path.exists(TAREAS_FILE):
        with open(TAREAS_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_tareas(tareas):
    with open(TAREAS_FILE, "w") as f:
        json.dump(tareas, f, indent=4)

def resolver_tarea(descripcion):
    prompt = f"Resuelve esta tarea de forma educativa y clara:\n{descripcion}\nRespuesta:"
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=250
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"No se pudo generar solución: {e}"

# -----------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------

def revisar_tareas():
    tareas_vistas = cargar_tareas()
    nuevas_tareas = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless en servidor
        if os.path.exists(STATE_FILE):
            context = browser.new_context(storage_state=STATE_FILE)
            page = context.new_page()
            page.goto("https://classroom.google.com/u/0/h")
            page.wait_for_load_state("networkidle", timeout=30000)
            print("✅ Sesión cargada correctamente desde state.json")
        else:
            print("❌ No se encontró state.json. Ejecuta localmente una vez para guardar sesión.")
            return

        try:
            tareas = page.query_selector_all("a.onkcGd.ARTZne")
            print(f"📋 Tareas encontradas: {len(tareas)}")

            for tarea in tareas:
                try:
                    titulo = tarea.inner_text().strip()
                    descripcion = tarea.get_attribute("aria-label")
                    if titulo not in tareas_vistas:
                        solucion = resolver_tarea(descripcion)
                        nuevas_tareas[titulo] = {
                            "descripcion": descripcion,
                            "solucion": solucion
                        }
                        print(f"✅ Nueva tarea procesada: {titulo}")
                except Exception as e:
                    print(f"No se pudo procesar una tarea: {e}")
                    continue

        except PlaywrightTimeoutError:
            print("⚠️ Timeout al cargar Classroom.")
        except Exception as e:
            print(f"Error general: {e}")
        finally:
            browser.close()

    # Guardar nuevas tareas
    tareas_vistas.update(nuevas_tareas)
    guardar_tareas(tareas_vistas)

    # Enviar notificación única
    if nuevas_tareas:
        mensaje = "✅ Revisión completada. Tareas nuevas resueltas:\n\n"
        for t, info in nuevas_tareas.items():
            mensaje += f"• {t}: {info['solucion']}\n\n"
        send_telegram(mensaje)
        print("📨 Notificación enviada a Telegram.")
    else:
        print("ℹ️ No se encontraron tareas nuevas hoy.")

# -----------------------------
# EJECUCIÓN AUTOMÁTICA 24/7
# -----------------------------

if __name__ == "__main__":
    while True:
        print(f"🔁 Ejecutando revisión diaria... {datetime.now()}")
        revisar_tareas()
        print("🕒 Esperando 24h para la próxima revisión...")
        time.sleep(86400)  # Espera 24 horas (86400 segundos)
