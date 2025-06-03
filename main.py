from fastapi import FastAPI
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification
import threading
import os
import telebot
import time
from enhanced_ved_system import EnhancedVEDExpertSystem
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VEDBot')

# FastAPI
app = FastAPI(title="Enhanced WED Expert API")
genspark_agent = GensparktWEDAgent()

# Инициализация расширенной системы ВЭД
ved_system = EnhancedVEDExpertSystem(genspark_agent)

# Telegram Bot
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Статистика использования
usage_stats = {
    "total_queries": 0,
    "successful_queries": 0,
    "genspark_queries": 0,
    "cache_hits": 0
}

@app.get("/")
def read_root():
    return {
        "status": "running", 
        "service": "Enhanced WED Expert API",
        "version": "2.0.0"
    }

@app.get("/stats")
def get_statistics():
    """Получить статистику использования"""
    cache_stats = ved_system.database.cache.stats if ved_system.database.cache else {}
    
    return {
        **usage_stats,
        "cache_stats": cache_stats,
        "database_codes": len(ved_system.database.database.get("codes", []))
    }

@app.get("/classify")
def classify_product(
    name: str,
    material: str = "",
    function: str = "",
    processing_level: str = "",
    origin_country: str = "",
    value: float = 0.0
):
    """API endpoint для классификации товаров"""
    try:
        product = ProductClassification(
            name=name,
            material=material,
            function=function,
            processing_level=processing_level,
            origin_country=origin_country,
            value=value
        )
        
        result = genspark_agent.classify_product(product)
        usage_stats["genspark_queries"] += 1
        
        return {"result": result, "source": "genspark_api"}
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return {"error": str(e)}

def start_bot():
    """Запуск Telegram бота"""
    try:
        logger.info("Starting Telegram bot...")
        # Очистка webhook
        bot.remove_webhook()
        time.sleep(1)
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot error: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд start и help"""
    welcome_text = """Добро пожаловать в ВЭД Эксперт 2.0! 🚀

🎯 **Возможности:**
• Поиск по кодам ТН ВЭД (10 цифр)
• Поиск по названию товара
• Экспертный анализ через ИИ
• Официальные данные + рекомендации

📝 **Команды:**
/start - это сообщение
/help - справка
/stats - статистика системы
/genspark - ИИ анализ товара

💡 **Примеры запросов:**
• 8471300000
• ноутбук
• свинина замороженная
• автомобиль BMW

Просто введите название товара или код!"""
    
    bot.reply_to(message, welcome_text)
    logger.info(f"Welcome sent to user {message.from_user.id}")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Отправляет статистику использования"""
    cache_stats = ved_system.database.cache.stats
    
    stats_text = f"""📊 **Статистика ВЭД Эксперт:**

🔍 **Запросы:**
• Всего: {usage_stats['total_queries']}
• Успешных: {usage_stats['successful_queries']}
• ИИ анализов: {usage_stats['genspark_queries']}

💾 **Кэш:**
• Попаданий: {cache_stats['hits']}
• Промахов: {cache_stats['misses']}

📚 **База данных:**
• Товаров в базе: {len(ved_system.database.database.get('codes', []))}"""
    
    bot.reply_to(message, stats_text)

@bot.message_handler(commands=['genspark'])
def genspark_classify(message):
    """Принудительный анализ через Genspark"""
    bot.reply_to(message, "🧠 Отправьте название товара для углубленного ИИ-анализа\n\nПример: кофемашина DeLonghi 1200W")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Главный обработчик сообщений"""
    user_input = message.text
    user_id = message.from_user.id
    
    # Обновляем статистику
    usage_stats["total_queries"] += 1
    
    logger.info(f"Query from user {user_id}: {user_input[:50]}...")
    
    try:
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
            usage_stats["genspark_queries"] += 1
            
            response = f"🧠 **ИИ-АНАЛИЗ ТОВАРА:**\n\n{genspark_result}"
            
        else:
            # Обычный поиск через расширенную систему
            response = ved_system.process_query(user_input)
            usage_stats["successful_queries"] += 1
        
        # Отправляем ответ
        bot.reply_to(message, response, parse_mode="Markdown")
        logger.info(f"Response sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        error_response = f"❌ Произошла ошибка при обработке запроса: {str(e)}"
        bot.reply_to(message, error_response)

@app.on_event("startup")
def startup_event():
    """Событие запуска приложения"""
    logger.info("Starting Enhanced VED Expert System...")
    threading.Thread(target=start_bot, daemon=True).start()
    logger.info("System started successfully")

# Для прямого запуска
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting in standalone mode...")
    threading.Thread(target=start_bot, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)