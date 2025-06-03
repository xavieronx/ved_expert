import json
import os

# Modified route_message function to use VEDDatabase instead of RAG API
def route_message(text, ved_db=None):
    try:
        # Check if text contains a valid TN VED code
        if ved_db and any(c.isdigit() for c in text):
            # Try to find tn_ved code in text
            result = ved_db.search_product(text)

            if result:
                code_info = result.get('product')
                if not code_info:
                    return f"❌ Код ТН ВЭД не найден: {text}"

                blocks = []

                # Format product info
                title = f"📊 *Информация о товаре:* {code_info.get('name', 'Н/Д')}"
                code_block = f"📌 Код ТН ВЭД: {code_info.get('code', 'Н/Д')}"
                desc_block = f"📝 Описание: {code_info.get('description', 'Н/Д')}"
                group_block = f"🔍 Группа: {code_info.get('group', 'Н/Д')}"

                blocks.append(title)
                blocks.append(code_block)
                blocks.append(desc_block)
                blocks.append(group_block)

                # Add duties info
                duties = code_info.get('duties', {})
                if duties:
                    duties_text = f"💰 *Пошлины:*\n- Базовая: {duties.get('base', 'Н/Д')}%"
                    for country, rate in duties.items():
                        if country != 'base':
                            duties_text += f"\n- {country.capitalize()}: {rate}%"
                    blocks.append(duties_text)

                # Add certification
                cert = code_info.get('certification', [])
                if cert:
                    cert_text = f"📄 *Требования сертификации:*\n- " + "\n- ".join(cert)
                    blocks.append(cert_text)

                # Add restrictions
                restrictions = code_info.get('restrictions', [])
                if restrictions:
                    rest_text = f"⚠️ *Ограничения:*\n- " + "\n- ".join(restrictions)
                    blocks.append(rest_text)
                else:
                    blocks.append("✅ *Ограничения:* отсутствуют")

                return "\n\n".join(blocks)

        # Fallback to simple response
        return f"🧠 Запрос обработан: {text}\n\nДля получения информации укажите код ТН ВЭД или название товара."

    except Exception as e:
        return f"❌ Ошибка при обработке запроса: {e}"
