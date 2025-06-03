from fastapi import FastAPI
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification
import threading
import os
import telebot
from ved_router import route_message
from ved_database import VEDDatabase
import re
import hashlib
import json
from datetime import datetime, timedelta

# FastAPI
app = FastAPI(title="WED Expert API")
genspark_agent = GensparktWEDAgent()

# Initialize VEDDatabase
ved_db = VEDDatabase()

# Telegram Bot
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Кэш результатов
class ResultCache:
    """Простой кэш результатов классификации"""

    def __init__(self, ttl_minutes=60):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.stats = {"hits": 0, "misses": 0}

    def _generate_key(self, product):
        """Генерирует ключ для кэша на основе параметров товара"""
        data = f"{product.name}_{product.material}_{product.function}_{product.origin_country}"
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, product):
        """Получает результат из кэша если он существует и не устарел"""
        key = self._generate_key(product)
        if key in self.cache:
            timestamp, value = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                self.stats["hits"] += 1
                return value
        self.stats["misses"] += 1
        return None

    def set(self, product, value):
        """Добавляет результат в кэш"""
        key = self._generate_key(product)
        self.cache[key] = (datetime.now(), value)

    def get_stats(self):
        """Возвращает статистику использования кэша"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_ratio = self.stats["hits"] / total if total > 0 else 0
        return {
            "size": len(self.cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_ratio": hit_ratio
        }

# Инициализация кэша
cache = ResultCache()

@app.get("/")
def read_root():
    return {"status": "running", "service": "WED Expert API"}

@app.get("/classify")
def classify_product(
    name: str,
    material: str = "",
    function: str = "",
    processing_level: str = "",
    origin_country: str = "",
    value: float = 0.0
):
    product = ProductClassification(
        name=name,
        material=material,
        function=function,
        processing_level=processing_level,
        origin_country=origin_country,
        value=value
    )

    # Check cache first
    cached_result = cache.get(product)
    if cached_result:
        return {"result": cached_result, "source": "cache"}

    # If not in cache, perform classification
    result = genspark_agent.classify_product(product)

    # Save to cache
    cache.set(product, result)

    return {"result": result, "source": "api"}

@app.get("/cache/stats")
def cache_stats():
    return cache.get_stats()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Здравствуйте! Я — ВЭД Эксперт с поддержкой Genspark AI.\n\nКоманды:\n/start - начало\n/genspark - AI анализ\n\nИли просто задавайте вопросы!")

@bot.message_handler(commands=['genspark'])
def genspark_classify(message):
    bot.reply_to(message, "Отправьте название товара для анализа через Genspark AI\nПример: кофемашина DeLonghi")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_input = message.text

    try:
        # Если упоминается genspark или AI - используем Genspark
        if any(key.lower() in user_input.lower() for key in ['genspark', 'ai', 'нейросеть', 'анализ']):
            product = ProductClassification(
                name=user_input,
                material="",
                function="",
                processing_level="",
                origin_country="",
                value=0.0
            )

            # Check cache first
            cached_result = cache.get(product)
            if cached_result:
                bot.reply_to(message, f"🧠 *Анализ товара:*\n\n{cached_result}\n\n(результат из кэша)")
                return

            # If not in cache, perform classification
            result = genspark_agent.classify_product(product)

            # Save to cache
            cache.set(product, result)

            bot.reply_to(message, f"🧠 *Анализ товара через Genspark AI:*\n\n{result}")
            return

        # Иначе - используем базу данных через роутер
        response = route_message(user_input, ved_db)
        bot.reply_to(message, response, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка: {str(e)}")

def start_bot():
    bot.infinity_polling()

@app.on_event("startup")
def startup_event():
    threading.Thread(target=start_bot, daemon=True).start()

# For direct launching without FastAPI
if __name__ == "__main__":
    # Start bot on a separate thread
    import uvicorn
    threading.Thread(target=start_bot, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
