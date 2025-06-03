from fastapi import FastAPI, Request
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification
import os
import telebot
from ved_router import route_message
from ved_database import VEDDatabase
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VEDBot')

# FastAPI
app = FastAPI(title="WED Expert API")
genspark_agent = GensparktWEDAgent()
ved_db = VEDDatabase()

# Telegram Bot
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = "https://vedexpert-production.up.railway.app/webhook"

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд start и help"""
    welcome_text = """Добро пожаловать в ВЭД Эксперт! 🚀

🎯 **Возможности:**
• Поиск по кодам ТН ВЭД (10 цифр)
• Поиск по названию товара
• Экспертный анализ через ИИ

📝 **Команды:**
/start - это сообщение
/help - справка
/genspark - ИИ анализ товара

💡 **Примеры запросов:**
• 8471300000
• ноутбук
• свинина замороженная

Просто введите название товара или код!"""
    
    try:
        bot.reply_to(message, welcome_text)
        logger.info(f"Welcome sent to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending welcome: {e}")

@bot.message_handler(commands=['genspark'])
def genspark_classify(message):
    """Принудительный анализ через Genspark"""
    try:
        bot.reply_to(message, "🧠 Отправьте название товара для углубленного ИИ-анализа\n\nПример: кофемашина DeLonghi 1200W")
    except Exception as e:
        logger.error(f"Error in genspark command: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Главный обработчик сообщений"""
    try:
        user_input = message.text
        user_id = message.from_user.id
        
        logger.info(f"Query from user {user_id}: {user_input[:50]}...")
        
        # Проверяем, нужен ли принудительный Genspark анализ
        force_genspark = any(keyword.lower() in user_input.lower() 
                           for keyword in ['genspark', 'ai', 'нейросеть', 'анализ', 'ии'])
        
        if force_genspark:
            # Принудительный Genspark анализ
            logger.info("Force Genspark analysis requested")
            
            product = ProductClassification(
                name=user_input,
                material="",
                function="",
                processing_level="",
                origin_country="",
                value=0.0
            )
            
            genspark_result = genspark_agent.classify_product(product)
            response = f"🧠 **ИИ-АНАЛИЗ ТОВАРА:**\n\n{genspark_result}"
            
        else:
            # Обычный поиск через базу данных
            response = route_message(user_input, ved_db)
        
        # Отправляем ответ
        bot.reply_to(message, response, parse_mode="Markdown")
        logger.info(f"Response sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        try:
            error_response = f"❌ Произошла ошибка при обработке запроса: {str(e)}"
            bot.reply_to(message, error_response)
        except:
            logger.error("Failed to send error response")

@app.get("/")
def read_root():
    return {"status": "running", "service": "WED Expert API", "mode": "webhook"}

@app.post("/webhook")
async def webhook(request: Request):
    """Webhook для получения сообщений от Telegram"""
    try:
        json_data = await request.json()
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/set_webhook")
def set_webhook():
    """Установка webhook"""
    try:
        # Удаляем старый webhook
        bot.remove_webhook()
        
        # Устанавливаем новый
        result = bot.set_webhook(url=WEBHOOK_URL)
        
        if result:
            logger.info(f"Webhook set successfully: {WEBHOOK_URL}")
            return {"status": "webhook set", "url": WEBHOOK_URL}
        else:
            logger.error("Failed to set webhook")
            return {"status": "error", "message": "Failed to set webhook"}
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/webhook_info")
def webhook_info():
    """Информация о webhook"""
    try:
        info = bot.get_webhook_info()
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
            "max_connections": info.max_connections,
            "allowed_updates": info.allowed_updates
        }
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
async def startup():
    """Startup event - устанавливаем webhook"""
    logger.info("Setting up webhook on startup...")
    try:
        # Удаляем старый webhook
        bot.remove_webhook()
        
        # Устанавливаем новый webhook
        result = bot.set_webhook(url=WEBHOOK_URL)
        
        if result:
            logger.info(f"✅ Webhook set successfully: {WEBHOOK_URL}")
        else:
            logger.error("❌ Failed to set webhook")
            
    except Exception as e:
        logger.error(f"❌ Error in startup: {e}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting in standalone mode with webhook...")
    uvicorn.run(app, host="0.0.0.0", port=8000)