from fastapi import FastAPI, Request
import os
import telebot
import logging
import json
from wed_expert_genspark_integration import GensparktWEDAgent
from enhanced_ved_system import EnhancedVEDExpertSystem

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VEDBot')

# FastAPI
app = FastAPI(title="WED Expert API Enhanced")

# Инициализация системы
genspark_agent = GensparktWEDAgent()
ved_system = EnhancedVEDExpertSystem(genspark_agent)

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
    welcome_text = """Добро пожаловать в ВЭД Эксперт 2.0! 🚀

🎯 **Возможности:**
• Умный поиск по кодам ТН ВЭД (10 цифр)
• Поиск по названию товара с синонимами
• Экспертный анализ через ИИ
• Кэширование для быстрых ответов

📝 **Команды:**
/start - это сообщение
/help - справка
/stats - статистика системы

💡 **Примеры запросов:**
• 8471300000
• ноутбук (найдет ноутбуки, лэптопы, laptop)
• свинина замороженная
• genspark анализ кофемашины

Просто введите название товара или код!"""
    
    try:
        bot.reply_to(message, welcome_text)
        logger.info(f"Welcome sent to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending welcome: {e}")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Статистика системы"""
    try:
        cache_stats = ved_system.database.cache.stats if hasattr(ved_system.database, 'cache') else {}
        
        stats_text = f"""📊 **Статистика ВЭД Эксперт 2.0:**

💾 **Кэш:**
• Попаданий: {cache_stats.get('hits', 0)}
• Промахов: {cache_stats.get('misses', 0)}

📚 **База данных:**
• Товаров в базе: {len(ved_system.database.database.get('codes', []))}
• Групп товаров: {len(ved_system.database.database.get('groups', []))}

🔍 **Последние запросы кэшированы**"""
        
        bot.reply_to(message, stats_text)
        logger.info(f"Stats sent to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending stats: {e}")
        bot.reply_to(message, "❌ Ошибка получения статистики")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """ГЛАВНЫЙ обработчик - использует EnhancedVEDExpertSystem"""
    try:
        user_input = message.text
        user_id = message.from_user.id
        
        logger.info(f"Запрос от пользователя {user_id}: {user_input[:50]}...")
        
        # Используем УМНУЮ систему вместо простой
        response = ved_system.process_query(user_input)
        
        # Отправляем ответ
        bot.reply_to(message, response, parse_mode="Markdown")
        logger.info(f"Ответ отправлен пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        try:
            error_response = "❌ Произошла ошибка при обработке запроса. Попробуйте еще раз."
            bot.reply_to(message, error_response)
        except:
            logger.error("Не удалось отправить сообщение об ошибке")

@app.get("/")
def read_root():
    return {
        "status": "running", 
        "service": "WED Expert API Enhanced v2.0",
        "mode": "webhook",
        "system": "EnhancedVEDExpertSystem"
    }

@app.get("/stats")
def api_stats():
    """API для статистики"""
    try:
        cache_stats = ved_system.database.cache.stats if hasattr(ved_system.database, 'cache') else {}
        
        return {
            "cache_stats": cache_stats,
            "database_codes": len(ved_system.database.database.get('codes', [])),
            "database_groups": len(ved_system.database.database.get('groups', [])),
            "system_type": "EnhancedVEDExpertSystem"
        }
    except Exception as e:
        return {"error": str(e)}

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
    logger.info("Starting Enhanced VED Expert System with webhook...")
    try:
        # Удаляем старый webhook
        bot.remove_webhook()
        
        # Устанавливаем новый webhook
        result = bot.set_webhook(url=WEBHOOK_URL)
        
        if result:
            logger.info(f"✅ Webhook set successfully: {WEBHOOK_URL}")
            logger.info("✅ Enhanced VED Expert System ready!")
        else:
            logger.error("❌ Failed to set webhook")
            
    except Exception as e:
        logger.error(f"❌ Error in startup: {e}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting in standalone mode with Enhanced VED System...")
    uvicorn.run(app, host="0.0.0.0", port=8000)