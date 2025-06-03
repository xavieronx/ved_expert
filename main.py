from fastapi import FastAPI
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification
import threading
import os
import telebot
from ved_router import route_message

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
            "vat_amount": cost_calc['vat_amount']
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Bot handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я работаю! Напиши 'кофемашина' для теста Genspark")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    try:
        if "кофе" in message.text.lower():
            product = ProductClassification(
                name="Кофемашина", material="металл, пластик",
                function="приготовление кофе", processing_level="готовое изделие",
                origin_country="IT", value=25000.0
            )
            result = genspark_agent.determine_tn_ved(product)
            cost_calc = genspark_agent.calculate_total_cost(result, 25000.0)
            
            response = f"🤖 Genspark AI:\n\nКод ТН ВЭД: {result.code}\nСтоимость: {cost_calc['total_cost']:,.0f} руб"
            bot.reply_to(message, response)
        else:
            response = route_message(message.text)
            bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

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
