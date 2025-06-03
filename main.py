from fastapi import FastAPI
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification
import threading
import os
import telebot
import time
from ved_router import route_message
from ved_database import VEDDatabase
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VEDBot')

# FastAPI
app = FastAPI(title="WED Expert API")
genspark_agent = GensparktWEDAgent()

# Initialize VEDDatabase
ved_db = VEDDatabase()

# Telegram Bot
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ КОНТРОЛЯ БОТА
bot_instance = None
bot_thread = None
is_bot_running = False

def create_bot():
    """Создает экземпляр бота"""
    global bot_instance
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return None
    
    try:
        bot_instance = telebot.TeleBot(BOT_TOKEN)
        logger.info("Bot instance created successfully")
        return bot_instance
    except Exception as e:
        logger.error(f"Failed to create bot: {e}")
        return None

def start_bot():
    """Запуск бота"""
    global is_bot_running
    
    if is_bot_running:
        logger.warning("Bot is already running")
        return
    
    try:
        bot = create_bot()
        if not bot:
            logger.error("Failed to create bot instance")
            return
        
        logger.info("Starting bot...")
        
        # Очистка webhook перед стартом
        try:
            bot.remove_webhook()
            time.sleep(2)
            logger.info("Webhook cleared")
        except Exception as e:
            logger.warning(f"Failed to clear webhook: {e}")
        
        # Устанавливаем флаг
        is_bot_running = True
        
        # Запускаем polling
        logger.info("Starting polling...")
        bot.infinity_polling(none_stop=True, interval=1)
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        is_bot_running = False

# Создаем бота
bot = create_bot()

if bot:
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
    return {
        "status": "running", 
        "service": "WED Expert API",
        "bot_running": is_bot_running
    }

@app.get("/bot/status")
def bot_status():
    """Статус бота"""
    return {
        "bot_running": is_bot_running,
        "bot_instance_exists": bot_instance is not None,
        "bot_token_configured": BOT_TOKEN is not None
    }

@app.get("/bot/restart")
def restart_bot():
    """Перезапуск бота"""
    global bot_instance, is_bot_running, bot_thread
    
    try:
        # Останавливаем текущий бот
        is_bot_running = False
        time.sleep(3)
        
        # Создаем новый экземпляр
        bot_instance = None
        
        # Запускаем в новом потоке
        if bot_thread and bot_thread.is_alive():
            bot_thread.join(timeout=5)
        
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        
        return {"status": "bot restarted"}
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        return {"error": str(e)}

# Для прямого запуска
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting in standalone mode...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)