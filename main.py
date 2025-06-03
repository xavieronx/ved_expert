from fastapi import FastAPI, Request
import os
import telebot
import logging
import json
from ved_database import VEDDatabase
from ved_router import route_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VED_BOT")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = "https://vedexpert-production.up.railway.app/webhook"

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = FastAPI()

# Инициализируем базу данных
ved_db = VEDDatabase()

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    logger.info(f"📩 Сообщение от {message.from_user.id}: {message.text}")
    response = route_message(message.text, ved_db)
    bot.reply_to(message, response)

@app.post("/webhook")
async def webhook(request: Request):
    try:
        json_data = await request.json()
        logger.info(f"🛰️ Webhook получен")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
