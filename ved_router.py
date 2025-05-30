import requests
import os

# Основная функция маршрутизации сообщений
def route_message(text):
    try:
        res = requests.get("https://rag-tnved-production.up.railway.app/search", params={"query": text})
        res.raise_for_status()
        data = res.json()
        result = data.get("result", "❌ Нет ответа")
        matches = data.get("matches", [])

        blocks = []
        if matches:
            doc_texts = [f"- {m['code']}: {m['text']}" for m in matches]
            doc_block = "📂 *Официально из базы ТН ВЭД:*\n\n" + "\n\n".join(doc_texts)
            blocks.append(doc_block)

        blocks.append("🧠 *Мнение модели:*\n" + result)
        return "\n\n".join(blocks)

    except Exception as e:
        return f"❌ Ошибка при запросе к RAG: {e}"