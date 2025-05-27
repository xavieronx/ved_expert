from get_gigachat_token_final import get_gigachat_token
from openai import OpenAI
import os

# Получаем актуальный GigaChat токен
GIGACHAT_TOKEN = get_gigachat_token()

# Настройка GigaChat клиента (если используешь через OpenAI совместимый интерфейс)
client = OpenAI(
    api_key=GIGACHAT_TOKEN,
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    default_headers={
        "Authorization": f"Bearer {GIGACHAT_TOKEN}",
        "Content-Type": "application/json",
    }
)

# Основная функция маршрутизации сообщений
def route_message(text):
    if "таможня" in text.lower():
        return gigachat_answer(text)
    else:
        return gpt_answer(text)

def gigachat_answer(prompt):
    try:
        response = client.chat.completions.create(
            model="GigaChat:latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка GigaChat: {e}"

def gpt_answer(prompt):
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка GPT: {e}"
