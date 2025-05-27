import requests
import json
import uuid
import urllib3

# Отключаем предупреждения по HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🔧 Данные от GigaChat
AUTH_KEY = "NTI4YWQ5YzItYmJlYi00MjQxLTk1ZjgtZmJiMjFmZDEzZWE2OjQyNDNkZmExLTYwYjQtNDE0OC1hZDc2LTE2YTU3OGEwYWIyNw=="
SCOPE = "GIGACHAT_API_PERS"
TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
TOKEN_PATH = ".env"  # можно .json или .txt — как хочешь

def get_gigachat_token():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),  # 🔥 ВАЖНО! Уникальный идентификатор запроса
        "Authorization": f"Basic {AUTH_KEY}"
    }

    data = {
        "scope": SCOPE
    }

    try:
        response = requests.post(
            TOKEN_URL,
            headers=headers,
            data=data,
            verify=False  # можно True, если скачаешь серт с сайта sbcloud
        )

        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise Exception("access_token не найден в ответе")

        # 💾 Сохраняем токен в .env
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(f"GIGACHAT_TOKEN={access_token}\n")

        print("✅ access_token получен и сохранён в .env")
        return access_token

    except Exception as e:
        print(f"❌ Ошибка при получении токена: {e}")
        return None

if __name__ == "__main__":
    get_gigachat_token()
