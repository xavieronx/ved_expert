import json
import os
import re

def route_message(text, ved_db=None):
    try:
        if not ved_db:
            return "🧠 Запрос обработан: " + text + "\n\nДля получения информации укажите код ТН ВЭД или название товара."
        
        # Поиск кода ТН ВЭД в тексте (10 цифр)
        tnved_pattern = r'\b\d{10}\b'
        tnved_match = re.search(tnved_pattern, text)
        
        if tnved_match:
            code = tnved_match.group()
            product = ved_db.get_product_by_code(code)
            
            if product:
                return format_product_info(product)
            else:
                return f"❌ Код ТН ВЭД {code} не найден в базе данных."
        
        # Поиск по названию товара
        result = ved_db.search_product(text)
        if result and result.get('product'):
            return format_product_info(result['product'])
        
        # Если ничего не найдено
        return f"🧠 Запрос обработан: {text}\n\nДля получения информации укажите:\n• Код ТН ВЭД (10 цифр)\n• Название товара\n\nПример: 8471300000 или ноутбук"
            
    except Exception as e:
        return f"❌ Ошибка при обработке запроса: {e}"

def format_product_info(product):
    """Форматирует информацию о товаре для вывода"""
    blocks = []
    
    # Основная информация
    title = f"📊 *{product.get('name', 'Товар')}*"
    code_block = f"📌 Код ТН ВЭД: `{product.get('code', 'Н/Д')}`"
    desc_block = f"📝 {product.get('description', 'Описание отсутствует')}"
    group_block = f"🔍 Группа: {product.get('group', 'Н/Д')}"
    
    blocks.extend([title, code_block, desc_block, group_block])
    
    # Пошлины
    duties = product.get('duties', {})
    if duties:
        duties_text = "💰 *Пошлины:*"
        for country, rate in duties.items():
            country_name = {
                'base': 'Базовая ставка',
                'china': 'Китай', 
                'eu': 'ЕС',
                'usa': 'США'
            }.get(country.lower(), country.capitalize())
            duties_text += f"\n• {country_name}: {rate}%"
        blocks.append(duties_text)
    
    # Сертификация
    cert = product.get('certification', [])
    if cert:
        cert_text = "📄 *Сертификация:*\n• " + "\n• ".join(cert)
        blocks.append(cert_text)
    
    # Ограничения
    restrictions = product.get('restrictions', [])
    if restrictions:
        rest_text = "⚠️ *Ограничения:*\n• " + "\n• ".join(restrictions)
        blocks.append(rest_text)
    else:
        blocks.append("✅ *Ограничения:* отсутствуют")
    
    return "\n\n".join(blocks)