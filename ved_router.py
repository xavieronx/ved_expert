import os
import openai
import requests
from gigachat_token_loader import get_gigachat_token

openai.api_key = os.getenv("OPENAI_API_KEY")
GIGACHAT_TOKEN = get_gigachat_token()

GPT4_KEYWORDS = ["регистрация", "налог", "субсидия", "отчётность", "декларация"]
GIGACHAT_KEYWORDS = ["контракт", "договор", "сертификат", "инвойс", "таможня"]

def contains_keywords(text, keywords):
    return any(word in text.lower() for word in keywords)

def ask_gpt4(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

def ask_gpt35(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

def ask_gigachat(prompt):
    headers = {
        "Authorization": f"Bearer {GIGACHAT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://gigachat.api.sbercloud.ru/v1/chat/completions", headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

def route_message(message: str) -> str:
    try:
        if contains_keywords(message, GIGACHAT_KEYWORDS):
            return ask_gigachat(message)
        elif contains_keywords(message, GPT4_KEYWORDS):
            return ask_gpt4(message)
        else:
            return ask_gpt35(message)
    except Exception as e:
        return f"Ошибка при обработке запроса: {e}"
