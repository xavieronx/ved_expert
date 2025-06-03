from fastapi import FastAPI
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification
import threading
import os
import telebot
from ved_router import route_message
import re
import hashlib
import json
from datetime import datetime, timedelta

# FastAPI
app = FastAPI(title="WED Expert API")
genspark_agent = GensparktWEDAgent()

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
        return hashlib.md5(data.lower().encode()).hexdigest()
    
    def get(self, product):
        """Получает результат из кэша"""
        key = self._generate_key(product)
        
        if key in self.cache:
            cached_item = self.cache[key]
            if datetime.now() - cached_item['timestamp'] < self.ttl:
                self.stats["hits"] += 1
                return cached_item['result']
            else:
                # Удаляем устаревший элемент
                del self.cache[key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, product, result):
        """Сохраняет результат в кэш"""
        key = self._generate_key(product)
        self.cache[key] = {
            'result': result,
            'timestamp': datetime.now()
        }
    
    def clear_expired(self):
        """Очищает устаревшие элементы кэша"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self.cache.items()
            if now - item['timestamp'] > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get_stats(self):
        """Возвращает статистику кэша"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total * 100 if total > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": f"{hit_rate:.1f}%"
        }

# Инициализируем кэш
cache = ResultCache(ttl_minutes=60)

@app.get("/")
def root():
    return {"message": "WED Expert + Genspark API работает!", "cache_stats": cache.get_stats()}

@app.get("/api/cache/stats")
def get_cache_stats():
    """Получить статистику кэша"""
    return cache.get_stats()

@app.post("/api/cache/clear")
def clear_cache():
    """Очистить кэш"""
    cache.cache.clear()
    cache.stats = {"hits": 0, "misses": 0}
    return {"message": "Кэш очищен"}

@app.post("/api/genspark/classify")
async def classify_with_genspark(
    name: str,
    material: str,
    function: str,
    origin_country: str,
    value: float
):
    try:
        product = ProductClassification(
            name=name, material=material, function=function,
            processing_level="готовое изделие",
            origin_country=origin_country, value=value
        )
        
        # Проверяем кэш
        cached_result = cache.get(product)
        if cached_result:
            # Пересчитываем стоимость для актуальной цены
            cost_calc = genspark_agent.calculate_total_cost(cached_result, value)
            
            return {
                "success": True,
                "tn_ved_code": cached_result.code,
                "description": cached_result.description,
                "confidence": f"{cached_result.confidence*100:.1f}%",
                "total_cost": cost_calc['total_cost'],
                "duty_amount": cost_calc['duty_amount'],
                "vat_amount": cost_calc['vat_amount'],
                "customs_fee": cost_calc['customs_fee'],
                "broker_fee": cost_calc['broker_fee'],
                "breakdown": cost_calc['breakdown'],
                "requirements": cached_result.requirements,
                "cached": True
            }
        
        # Если нет в кэше - классифицируем
        result = genspark_agent.determine_tn_ved(product)
        cost_calc = genspark_agent.calculate_total_cost(result, value)
        
        # Сохраняем в кэш
        cache.set(product, result)
        
        return {
            "success": True,
            "tn_ved_code": result.code,
            "description": result.description,
            "confidence": f"{result.confidence*100:.1f}%",
            "total_cost": cost_calc['total_cost'],
            "duty_amount": cost_calc['duty_amount'],
            "vat_amount": cost_calc['vat_amount'],
            "customs_fee": cost_calc['customs_fee'],
            "broker_fee": cost_calc['broker_fee'],
            "breakdown": cost_calc['breakdown'],
            "requirements": result.requirements,
            "cached": False
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/genspark/validate")
async def validate_tn_ved(
    name: str,
    material: str,
    function: str,
    origin_country: str,
    value: float,
    suggested_code: str
):
    try:
        product = ProductClassification(
            name=name, material=material, function=function,
            processing_level="готовое изделие",
            origin_country=origin_country, value=value
        )
        
        validation = genspark_agent.validate_classification(product, suggested_code)
        
        return {
            "success": True,
            "validation": validation
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Улучшенный парсер пользовательских запросов
class SmartQueryParser:
    """Умный парсер пользовательских запросов"""
    
    def __init__(self):
        self.country_codes = {
            'китай': 'CN', 'китая': 'CN', 'china': 'CN',
            'германия': 'DE', 'германии': 'DE', 'germany': 'DE',
            'италия': 'IT', 'италии': 'IT', 'italy': 'IT',
            'сша': 'US', 'америка': 'US', 'usa': 'US',
            'япония': 'JP', 'японии': 'JP', 'japan': 'JP',
            'корея': 'KR', 'кореи': 'KR', 'korea': 'KR',
            'франция': 'FR', 'франции': 'FR', 'france': 'FR',
            'турция': 'TR', 'турции': 'TR', 'turkey': 'TR',
            'вьетнам': 'VN', 'вьетнама': 'VN', 'vietnam': 'VN',
            'индия': 'IN', 'индии': 'IN', 'india': 'IN',
            'польша': 'PL', 'польши': 'PL', 'poland': 'PL'
        }
        
        self.default_values = {
            'кофемашина': {'material': 'металл, пластик', 'function': 'приготовление кофе', 'value': 25000},
            'телефон': {'material': 'алюминий, стекло', 'function': 'мобильная связь', 'value': 120000},
            'смартфон': {'material': 'алюминий, стекло', 'function': 'мобильная связь', 'value': 120000},
            'куртка': {'material': 'полиэстер, синтепон', 'function': 'защита от холода', 'value': 8000},
            'ноутбук': {'material': 'пластик, металл', 'function': 'вычисления', 'value': 80000},
            'компьютер': {'material': 'пластик, металл', 'function': 'вычисления', 'value': 60000},
            'планшет': {'material': 'алюминий, стекло', 'function': 'вычисления', 'value': 40000},
            'часы': {'material': 'металл, стекло', 'function': 'показ времени', 'value': 15000},
            'книга': {'material': 'бумага', 'function': 'чтение', 'value': 1000},
            'шоколад': {'material': 'какао, сахар', 'function': 'питание', 'value': 500},
            'вино': {'material': 'виноград', 'function': 'алкогольный напиток', 'value': 2000},
            'водка': {'material': 'этиловый спирт', 'function': 'алкогольный напиток', 'value': 1500},
            'ботинки': {'material': 'кожа, резина', 'function': 'обувь', 'value': 12000},
            'кроссовки': {'material': 'текстиль, резина', 'function': 'спортивная обувь', 'value': 8000},
            'автомобиль': {'material': 'металл, пластик', 'function': 'транспорт', 'value': 1500000},
            'косметика': {'material': 'химические соединения', 'function': 'уход за кожей', 'value': 3000},
            'игрушка': {'material': 'пластик', 'function': 'игра', 'value': 2000}
        }
        
        # Расширенные синонимы
        self.synonyms = {
            'iphone': 'смартфон',
            'samsung': 'смартфон',
            'xiaomi': 'смартфон',
            'huawei': 'смартфон',
            'macbook': 'ноутбук',
            'lenovo': 'ноутбук',
            'dell': 'ноутбук',
            'asus': 'ноутбук',
            'delonghi': 'кофемашина',
            'nespresso': 'кофемашина',
            'rolex': 'часы',
            'omega': 'часы',
            'casio': 'часы',
            'nike': 'кроссовки',
            'adidas': 'кроссовки',
            'puma': 'кроссовки',
            'toyota': 'автомобиль',
            'bmw': 'автомобиль',
            'mercedes': 'автомобиль'
        }
    
    def parse_query(self, text):
        """Парсит пользовательский запрос и извлекает информацию о товаре"""
        text_lower = text.lower()
        
        # Извлекаем название товара
        product_name = self._extract_product_name(text_lower)
        if not product_name:
            return None
        
        # Извлекаем страну происхождения
        country = self._extract_country(text_lower)
        
        # Извлекаем стоимость
        value = self._extract_value(text)
        
        # Получаем параметры по умолчанию для товара
        defaults = self._get_defaults(product_name)
        
        return ProductClassification(
            name=product_name,
            material=defaults['material'],
            function=defaults['function'],
            processing_level="готовое изделие",
            origin_country=country,
            value=value or defaults['value']
        )
    
    def _extract_product_name(self, text):
        """Извлекает название товара из текста"""
        # Сначала проверяем прямые совпадения
        for product in self.default_values.keys():
            if product in text:
                return product
        
        # Затем проверяем синонимы
        for synonym, product in self.synonyms.items():
            if synonym in text:
                return product
        
        # Дополнительные паттерны
        if any(word in text for word in ['кофе', 'эспрессо', 'капучино']):
            return 'кофемашина'
        
        if any(word in text for word in ['мобильный', 'phone', 'android', 'ios']):
            return 'смартфон'
            
        if any(word in text for word in ['laptop', 'notebook']):
            return 'ноутбук'
            
        if any(word in text for word in ['авто', 'машина', 'car']):
            return 'автомобиль'
        
        return None
    
    def _extract_country(self, text):
        """Извлекает страну происхождения"""
        for country_name, code in self.country_codes.items():
            if country_name in text:
                return code
        return 'CN'  # По умолчанию Китай
    
    def _extract_value(self, text):
        """Извлекает стоимость из текста"""
        # Ищем числа с указанием валюты
        patterns = [
            r'(\d+(?:\s?\d{3})*)\s*(?:руб|рублей?)',
            r'(\d+(?:\s?\d{3})*)\s*(?:долларов?|usd|\$)',
            r'(\d+(?:\s?\d{3})*)\s*(?:евро|eur|€)',
            r'(\d+(?:\s?\d{3})*)\s*(?:юаней?|yuan|¥)',
            r'(\d+(?:\s?\d{3})*)\s*(?:тысяч?|к|k)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                value_str = match.group(1).replace(' ', '')
                value = float(value_str)
                
                # Если указаны тысячи
                if 'тысяч' in pattern or 'к' in pattern or 'k' in pattern:
                    value *= 1000
                
                return value
        
        return None
    
    def _get_defaults(self, product_name):
        """Получает параметры по умолчанию для товара"""
        return self.default_values.get(product_name, {
            'material': 'разные материалы',
            'function': 'бытовое назначение',
            'value': 10000
        })

# Инициализируем парсер
query_parser = SmartQueryParser()

# Статистика использования
usage_stats = {
    "total_queries": 0,
    "successful_classifications": 0,
    "cache_hits": 0,
    "start_time": datetime.now()
}

@app.get("/api/stats")
def get_usage_stats():
    """Получить статистику использования"""
    uptime = datetime.now() - usage_stats["start_time"]
    
    return {
        "uptime_hours": uptime.total_seconds() / 3600,
        "total_queries": usage_stats["total_queries"],
        "successful_classifications": usage_stats["successful_classifications"],
        "success_rate": f"{usage_stats['successful_classifications'] / max(usage_stats['total_queries'], 1) * 100:.1f}%",
        "cache_stats": cache.get_stats()
    }

# Улучшенные Bot handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """👋 Привет! Я WED Expert с поддержкой Genspark AI!

🎯 **Что я умею:**
• Классифицировать товары по ТН ВЭД
• Рассчитывать пошлины и налоги
• Определять требования для импорта
• Кэшировать результаты для быстрого ответа

📝 **Примеры запросов:**
"Хочу импортировать кофемашину из Италии за 25000 рублей"
"iPhone из Китая стоимостью 120к рублей"
"Куртка зимняя из Турции"
"Автомобиль BMW из Германии"

💡 Просто опишите товар и я всё посчитаю!

⚡ *Powered by Genspark AI с кэшированием*"""
    
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """❓ **Как пользоваться WED Expert:**

1️⃣ Опишите товар простыми словами
2️⃣ Укажите страну происхождения
3️⃣ Добавьте стоимость (по желанию)

🔍 **Поддерживаемые товары:**
📱 Электроника: телефоны, ноутбуки, планшеты
☕ Бытовая техника: кофемашины, чайники
👕 Одежда: куртки, пальто, костюмы
👟 Обувь: кроссовки, ботинки, туфли
🚗 Транспорт: автомобили, велосипеды
💄 Косметика: кремы, парфюм, шампуни
📚 Книги и журналы
🍫 Продукты питания
🍷 Алкогольные напитки
🪑 Мебель

🌍 **Поддерживаемые страны:**
🇨🇳 Китай • 🇩🇪 Германия • 🇮🇹 Италия • 🇺🇸 США
🇯🇵 Япония • 🇰🇷 Корея • 🇫🇷 Франция • 🇹🇷 Турция
🇻🇳 Вьетнам • 🇮🇳 Индия • 🇵🇱 Польша

⚡ *Результаты кэшируются для быстрого ответа!*"""
    
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Показать статистику бота"""
    stats = cache.get_stats()
    uptime = datetime.now() - usage_stats["start_time"]
    
    stats_text = f"""📊 **Статистика WED Expert:**

⏱️ **Время работы:** {uptime.days} дн. {uptime.seconds//3600} ч.
📈 **Всего запросов:** {usage_stats['total_queries']}
✅ **Успешных классификаций:** {usage_stats['successful_classifications']}
🎯 **Процент успеха:** {usage_stats['successful_classifications'] / max(usage_stats['total_queries'], 1) * 100:.1f}%

💾 **Кэш:**
• Размер: {stats['cache_size']} записей
• Попаданий: {stats['hits']}
• Промахов: {stats['misses']}
• Эффективность: {stats['hit_rate']}

⚡ *Система работает оптимально!*"""
    
    bot.reply_to(message, stats_text)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    try:
        text = message.text
        usage_stats["total_queries"] += 1
        
        # Проверяем, можем ли распарсить как товар
        product = query_parser.parse_query(text)
        
        if product:
            # Проверяем кэш
            cached_result = cache.get(product)
            cache_indicator = "💾" if cached_result else "🔄"
            
            # Получаем результат (из кэша или новый)
            if cached_result:
                result = cached_result
                usage_stats["cache_hits"] += 1
            else:
                result = genspark_agent.determine_tn_ved(product)
                cache.set(product, result)
            
            cost_calc = genspark_agent.calculate_total_cost(result, product.value)
            usage_stats["successful_classifications"] += 1
            
            # Форматируем детальный ответ
            response = f"""{cache_indicator} **Анализ Genspark AI**

📦 **Товар:** {product.name.title()}
🌍 **Страна:** {product.origin_country}
💰 **Стоимость:** {product.value:,.0f} руб

🎯 **Классификация ТН ВЭД:**
• Код: `{result.code}`
• Описание: {result.description}
• Уверенность: {result.confidence*100:.0f}%

💵 **Расчёт платежей:**
• Товарная стоимость: {cost_calc['customs_value']:,.0f} руб
• Пошлина ({result.duty_rate}): {cost_calc['duty_amount']:,.0f} руб
• НДС ({result.vat_rate}): {cost_calc['vat_amount']:,.0f} руб
• Таможенный сбор: {cost_calc['customs_fee']:,.0f} руб
• Брокерские услуги: {cost_calc['broker_fee']:,.0f} руб

💸 **Итого к доплате: {cost_calc['total_taxes'] + cost_calc['total_fees']:,.0f} руб**
🏆 **Общая стоимость: {cost_calc['total_cost']:,.0f} руб**

📋 **Основные требования:**
{chr(10).join(['• ' + req for req in result.requirements[:4]])}

⚡ *{'Из кэша' if cached_result else 'Новый расчёт'} • Powered by Genspark AI*"""
            
            bot.reply_to(message, response, parse_mode='Markdown')
            
        else:
            # Используем обычную RAG систему
            response = route_message(text)
            bot.reply_to(message, response)
            
    except Exception as e:
        error_text = f"""❌ Произошла ошибка: {str(e)}

💡 **Попробуйте:**
• Описать товар проще: "телефон из Китая"
• Указать конкретную категорию
• Использовать команду /help для примеров
• Проверить статистику: /stats"""
        
        bot.reply_to(message, error_text)

# Автоматическая очистка кэша каждые 10 минут
def cache_cleanup():
    while True:
        import time
        time.sleep(600)  # 10 минут
        cache.clear_expired()

# Запуск очистки кэша в отдельном потоке
cleanup_thread = threading.Thread(target=cache_cleanup, daemon=True)
cleanup_thread.start()

# Запуск бота в отдельном потоке
def start_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # Запускаем бота в фоне
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем FastAPI
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))