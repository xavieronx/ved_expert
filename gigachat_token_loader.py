import requests
import uuid
import base64
import os

def get_gigachat_token():
    client_id = os.getenv("GIGACHAT_CLIENT_ID")
    client_secret = os.getenv("GIGACHAT_CLIENT_SECRET")
    scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

    if not client_id or not client_secret:
        raise ValueError("GIGACHAT_CLIENT_ID or GIGACHAT_CLIENT_SECRET not set")

    auth_str = f"{client_id}:{client_secret}"
    basic_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {basic_auth}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "scope": scope
    }

    response = requests.post(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        headers=headers,
        data=data,
        verify=False  # отключаем проверку сертификатов (в dev)
    )

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Ошибка при получении токена GigaChat: {response.text}")
