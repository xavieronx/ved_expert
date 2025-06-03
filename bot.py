import os
import telebot
from ved_router import route_message
from wed_expert_genspark_integration import GensparktWEDAgent, ProductClassification

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
genspark_agent = GensparktWEDAgent()

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
        if any(word in user_input.lower() for word in ['genspark', 'ai', 'кофемашина', 'смартфон']):
            
            if "кофе" in user_input.lower():
                product = ProductClassification(
                    name="Кофемашина", 
                    material="металл, пластик",
                    function="приготовление кофе", 
                    processing_level="готовое изделие",
                    origin_country="IT", 
                    value=25000.0
                )
            elif "телефон" in user_input.lower() or "смартфон" in user_input.lower():
                product = ProductClassification(
                    name="Смартфон", 
                    material="алюминий, стекло",
                    function="мобильная связь", 
                    processing_level="готовое изделие",
                    origin_country="CN", 
                    value=120000.0
                )
            else:
                bot.reply_to(message, "🤖 Укажите конкретный товар: кофемашина, смартфон")
                return
            
            result = genspark_agent.determine_tn_ved(product)
            cost_calc = genspark_agent.calculate_total_cost(result, product.value)
            
            response = f"""🤖 Анализ Genspark AI:

📦 Товар: {product.name}
🎯 Код ТН ВЭД: {result.code}
💰 Общая стоимость: {cost_calc['total_cost']:,.0f} руб
💸 К доплате: {cost_calc['total_taxes']:,.0f} руб

⚡ Powered by Genspark"""
            
            bot.reply_to(message, response)
            
        else:
            # Обычная логика через RAG
            response = route_message(user_input)
            bot.reply_to(message, response)
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()
