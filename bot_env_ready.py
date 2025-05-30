import os
from dotenv import load_dotenv
import telebot
from ved_router import route_message

load_dotenv()  # Загружаем переменные из .env

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Здравствуйте! Я — ВЭД Эксперт. Задавайте ваш вопрос.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_input = message.text
    response = route_message(user_input)
    bot.reply_to(message, response)

if __name__ == "__main__":
    bot.infinity_polling()