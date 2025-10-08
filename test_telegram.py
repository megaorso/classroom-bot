import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    mensaje = "✅ Test: el bot de Telegram funciona correctamente"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje)
    print("Mensaje de prueba enviado. Revisa tu Telegram.")

asyncio.run(main())
