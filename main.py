from fastapi import FastAPI, Request
import os
import telebot
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TEST_BOT")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = "https://vedexpert-production.up.railway.app/webhook"

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = FastAPI()

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.info(f"📩 Сообщение от {message.from_user.id}: {message.text}")
    bot.reply_to(message, f"✅ Принято: {message.text}")

@app.post("/webhook")
async def webhook(request: Request):
    try:
        json_data = await request.json()
        logger.info(f"🛰️ Webhook получен: {json_data}")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/set_webhook")
def set_webhook():
    try:
        bot.remove_webhook()
        result = bot.set_webhook(url=WEBHOOK_URL)
        if result:
            logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
            return {"status": "webhook set", "url": WEBHOOK_URL}
        else:
            logger.error("❌ Ошибка установки webhook")
            return {"status": "error", "message": "Не удалось установить webhook"}
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
def root():
    return {"status": "bot online"}