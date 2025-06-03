from fastapi import FastAPI
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification
import threading
import os
import telebot
from ved_router import route_message
import re

# FastAPI
app = FastAPI(title="WED Expert API")
genspark_agent = GensparktWEDAgent()

# Telegram Bot
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

@app.get("/")
def root():
    return {"message": "WED Expert + Genspark API работает!"}

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
        
        result = genspark_agent.determine_tn_ved(product)
        cost_calc = genspark_agent.calculate_total_cost(result, value)
        
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
            "requirements": result.requirements
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
            'турция': 'TR', 'турции': 'TR', 'turkey': 'TR'
        }
        
        self.default_values = {
            'кофемашина': {'material': 'металл, пластик', 'function': 'приготовление кофе', 'value': 25000},
            'телефон': {'material': 'алюминий, стекло', 'function': 'мобильная связь', 'value': 120000},
            'смартфон': {'material': 'алюминий, стекло', 'function': 'мобильная связь', 'value': 120000},
            'куртка': {'material': 'полиэстер, синтепон', 'function': 'защита от холода', 'value': 8000},
            'ноутбук': {'material': 'пластик, металл', 'function': 'вычисления', 'value': 80000},
            'часы': {'material': 'металл, стекло', 'function': 'показ времени', 'value': 15000},
            'книга': {'material': 'бумага', 'function': 'чтение', 'value': 1000},
            'шоколад': {'material': 'какао, сахар', 'function': 'питание', 'value': 500}
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
        for product in self.default_values.keys():
            if product in text:
                return product
        
        # Поиск по ключевым словам
        keywords = {
            'iphone': 'смартфон',
            'samsung': 'смартфон',
            'macbook': 'ноутбук',
            'lenovo': 'ноутбук',
            'delonghi': 'кофемашина',
            'rolex': 'часы',
            'adidas': 'куртка'
        }
        
        for keyword, product in keywords.items():
            if keyword in text:
                return product
        
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
            r'(\d+(?:\s?\d{3})*)\s*(?:юаней?|yuan|¥)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                value_str = match.group(1).replace(' ', '')
                return float(value_str)
        
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

# Улучшенные Bot handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """👋 Привет! Я WED Expert с поддержкой Genspark AI!

🎯 Что я умею:
• Классифицировать товары по ТН ВЭД
• Рассчитывать пошлины и налоги
• Определять требования для импорта

📝 Примеры запросов:
"Хочу импортировать кофемашину из Италии за 25000 рублей"
"Телефон iPhone из Китая"
"Куртка зимняя из Турции"

💡 Просто опишите товар и я всё посчитаю!"""
    
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """❓ Как пользоваться WED Expert:

1️⃣ Опишите товар простыми словами
2️⃣ Укажите страну происхождения
3️⃣ Добавьте стоимость (по желанию)

🔍 Поддерживаемые товары:
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

⚡ Powered by Genspark AI"""
    
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    try:
        text = message.text
        
        # Проверяем, можем ли распарсить как товар
        product = query_parser.parse_query(text)
        
        if product:
            # Получаем результат от Genspark
            result = genspark_agent.determine_tn_ved(product)
            cost_calc = genspark_agent.calculate_total_cost(result, product.value)
            
            # Форматируем детальный ответ
            response = f"""🤖 **Анализ Genspark AI**

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

⚡ *Powered by Genspark AI*"""
            
            bot.reply_to(message, response, parse_mode='Markdown')
            
        else:
            # Используем обычную RAG систему
            response = route_message(text)
            bot.reply_to(message, response)
            
    except Exception as e:
        error_text = f"""❌ Произошла ошибка: {str(e)}

💡 Попробуйте:
• Описать товар проще: "телефон из Китая"
• Указать конкретную категорию
• Использовать команду /help для примеров"""
        
        bot.reply_to(message, error_text)

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