from fastapi import FastAPI, Request
import os
import telebot
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Set
from collections import defaultdict
from ved_database import VEDDatabase
from ved_router import route_message, handle_ai_analysis

# Настройка логирования с ротацией
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('ved_bot.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VED_BOT")

# Конфигурация
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = "https://vedexpert-production.up.railway.app/webhook"
ADMIN_IDS = [181780572]  # ID администраторов

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = FastAPI()

# Статистика бота
class BotStats:
    def __init__(self):
        self.start_time = datetime.now()
        self.users: Set[int] = set()
        self.requests_count = 0
        self.popular_codes: Dict[str, int] = defaultdict(int)
        self.errors_count = 0
        self.ai_requests = 0
        
    def add_user(self, user_id: int):
        self.users.add(user_id)
        
    def add_request(self, code: str = None):
        self.requests_count += 1
        if code:
            self.popular_codes[code] += 1
            
    def add_error(self):
        self.errors_count += 1
        
    def add_ai_request(self):
        self.ai_requests += 1
        
    def get_stats(self) -> Dict:
        uptime = datetime.now() - self.start_time
        return {
            "uptime": str(uptime).split('.')[0],
            "users_count": len(self.users),
            "requests_count": self.requests_count,
            "errors_count": self.errors_count,
            "ai_requests": self.ai_requests,
            "popular_codes": dict(sorted(self.popular_codes.items(), 
                                       key=lambda x: x[1], reverse=True)[:5])
        }

stats = BotStats()

# Инициализируем базу данных
try:
    ved_db = VEDDatabase()
    logger.info("✅ VEDDatabase загружена успешно")
except Exception as e:
    logger.error(f"❌ Ошибка загрузки базы данных: {e}")
    ved_db = None

# Обработчики команд
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        stats.add_user(message.from_user.id)
        welcome_text = """
🤖 **Добро пожаловать в ВЭД Эксперт!**

Я помогу вам с кодами ТН ВЭД, пошлинами и требованиями сертификации.

📋 **Что я умею:**
• Поиск по коду ТН ВЭД (10 цифр)
• Поиск по названию товара
• Показать пошлины по странам
• Требования сертификации
• AI-анализ (команда: анализ XXXXXXXXXX)

💡 **Примеры запросов:**
• `8471300000` - ноутбуки
• `ноутбук` - поиск по названию
• `анализ 8471300000` - AI-анализ

🔍 Начните с ввода кода ТН ВЭД или названия товара!
"""
        bot.reply_to(message, welcome_text, parse_mode='Markdown')
        logger.info(f"👋 Новый пользователь: {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в /start: {e}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте позже.")

@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        stats.add_user(message.from_user.id)
        help_text = """
📖 **Справка по использованию:**

🔍 **Поиск товара:**
• Введите 10-значный код ТН ВЭД: `8471300000`
• Или название товара: `ноутбук`, `смартфон`, `кофе`

🧠 **AI-анализ:**
• `анализ 8471300000` - получить экспертное мнение

📊 **Команды:**
• `/start` - начать работу
• `/help` - эта справка
• `/stats` - статистика (для админов)

💰 **Что показывается:**
• Пошлины по странам (Россия, Китай, ЕС, США)
• Требования сертификации (ТР ТС, СЭС)
• Ограничения и лицензии

❓ **Проблемы?** Напишите администратору.
"""
        bot.reply_to(message, help_text, parse_mode='Markdown')
        logger.info(f"❓ Запрос справки от: {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в /help: {e}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте позже.")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    try:
        if message.from_user.id not in ADMIN_IDS:
            bot.reply_to(message, "❌ Доступ запрещен")
            return
            
        bot_stats = stats.get_stats()
        stats_text = f"""
📊 **Статистика бота:**

⏱️ **Время работы:** {bot_stats['uptime']}
👥 **Пользователей:** {bot_stats['users_count']}
📝 **Запросов:** {bot_stats['requests_count']}
🤖 **AI-запросов:** {bot_stats['ai_requests']}
❌ **Ошибок:** {bot_stats['errors_count']}

🔥 **Популярные коды:**
"""
        for code, count in bot_stats['popular_codes'].items():
            stats_text += f"• `{code}`: {count} раз\n"
            
        bot.reply_to(message, stats_text, parse_mode='Markdown')
        logger.info(f"📊 Статистика запрошена: {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в /stats: {e}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте позже.")

# Основной обработчик сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    start_time = time.time()
    try:
        stats.add_user(message.from_user.id)
        user_text = message.text.strip()
        
        logger.info(f"📩 Сообщение от {message.from_user.id}: {user_text}")
        
        if not ved_db:
            bot.reply_to(message, "❌ База данных недоступна. Обратитесь к администратору.")
            return
        
        # Проверка на AI-анализ
        if "анализ" in user_text.lower():
            stats.add_ai_request()
            response = handle_ai_analysis(user_text, ved_db)
            if response:
                bot.reply_to(message, response, parse_mode='Markdown')
                return
        
        # Обычная обработка
        response = route_message(user_text, ved_db)
        
        # Извлекаем код для статистики
        import re
        code_match = re.search(r'\b\d{10}\b', user_text)
        if code_match:
            stats.add_request(code_match.group())
        else:
            stats.add_request()
        
        # Отправляем ответ
        bot.reply_to(message, response, parse_mode='Markdown')
        
        # Логируем время обработки
        process_time = time.time() - start_time
        logger.info(f"⏱️ Обработка заняла: {process_time:.2f}с")
        
    except Exception as e:
        stats.add_error()
        error_msg = f"❌ Произошла ошибка при обработке запроса. Попробуйте позже."
        logger.error(f"❌ Ошибка обработки сообщения от {message.from_user.id}: {e}")
        
        try:
            bot.reply_to(message, error_msg)
        except:
            logger.error("❌ Не удалось отправить сообщение об ошибке")

# Webhook handler
@app.post("/webhook")
async def webhook(request: Request):
    try:
        json_data = await request.json()
        logger.debug(f"🛰️ Webhook получен")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return {"status": "ok"}
    except Exception as e:
        stats.add_error()
        logger.error(f"❌ Ошибка webhook: {e}")
        return {"status": "error"}

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        bot_stats = stats.get_stats()
        return {
            "status": "ok",
            "database": "connected" if ved_db else "disconnected",
            "stats": bot_stats
        }
    except Exception as e:
        logger.error(f"❌ Ошибка health check: {e}")
        return {"status": "error"}

# Статистика API для мониторинга
@app.get("/api/stats")
async def api_stats():
    try:
        return stats.get_stats()
    except Exception as e:
        logger.error(f"❌ Ошибка API статистики: {e}")
        return {"error": "Stats unavailable"}

if __name__ == "__main__":
    logger.info("🚀 Запуск ВЭД Эксперт бота...")
    logger.info(f"📊 База данных: {'✅ Подключена' if ved_db else '❌ Не подключена'}")
    
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 8000)),
        log_level="info"
    )