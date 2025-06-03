import json
import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Настройка логирования
logger = logging.getLogger('VED_ROUTER')

# Статистика запросов
request_stats = {
    'total_requests': 0,
    'code_searches': 0,
    'name_searches': 0,
    'ai_requests': 0,
    'popular_codes': {}
}

def format_product_info(product: Dict) -> str:
    """Красивое форматирование информации о товаре"""
    try:
        code = product.get('code', 'Неизвестно')
        name = product.get('name', 'Название не найдено')
        description = product.get('description', '')
        group = product.get('group', '')
        duties = product.get('duties', {})
        certification = product.get('certification', [])
        restrictions = product.get('restrictions', [])
        
        # Основная информация
        result = f"🏷️ *{name}*\n"
        result += f"📋 Код ТН ВЭД: `{code}`\n"
        if description:
            result += f"📝 {description}\n"
        result += f"🔍 Группа: {group}\n\n"
        
        # Пошлины с эмодзи для быстрого понимания
        result += f"💰 *Пошлины:*\n"
        base_rate = duties.get('base', 0)
        result += f"• Базовая ставка: {base_rate}% {get_rate_emoji(base_rate)}\n"
        
        china_rate = duties.get('china', 0)
        result += f"• Китай: {china_rate}% {get_rate_emoji(china_rate)}\n"
        
        eu_rate = duties.get('eu', 0)
        result += f"• ЕС: {eu_rate}% {get_rate_emoji(eu_rate)}\n"
        
        usa_rate = duties.get('usa', 0)
        result += f"• США: {usa_rate}% {get_rate_emoji(usa_rate)}\n"
        
        result += f"• Беларусь: {duties.get('belarus', 0)}% 🆓\n"
        result += f"• Казахстан: {duties.get('kazakhstan', 0)}% 🆓\n\n"
        
        # Сертификация
        if certification:
            result += f"📜 *Сертификация:*\n"
            for cert in certification:
                result += f"• {cert} {get_cert_emoji(cert)}\n"
            result += "\n"
        
        # Ограничения
        if restrictions:
            result += f"⚠️ *Ограничения:*\n"
            for restriction in restrictions:
                result += f"• {restriction}\n"
            result += "\n"
        else:
            result += f"✅ *Ограничения:* отсутствуют\n\n"
        
        # Дополнительная информация
        result += f"🤖 Хотите AI-анализ? Напишите: `анализ {code}`\n"
        result += f"📊 Статистика: код запрашивался {request_stats['popular_codes'].get(code, 0)} раз"
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка форматирования: {e}")
        return f"❌ Ошибка обработки информации о товаре"

def get_rate_emoji(rate: float) -> str:
    """Возвращает эмодзи в зависимости от ставки пошлины"""
    if rate == 0:
        return "🆓"
    elif rate <= 5:
        return "💚"
    elif rate <= 15:
        return "💛"
    elif rate <= 25:
        return "🧡"
    else:
        return "🔴"

def get_cert_emoji(cert: str) -> str:
    """Возвращает эмодзи для типа сертификации"""
    cert_lower = cert.lower()
    if "тр тс" in cert_lower:
        return "🛡️"
    elif "сэс" in cert_lower:
        return "🩺"
    elif "ветеринарное" in cert_lower:
        return "🐾"
    elif "фитосанитарное" in cert_lower:
        return "🌱"
    else:
        return "📋"

def improved_search(query: str, ved_db) -> Optional[str]:
    """Улучшенный поиск с нечеткими совпадениями"""
    try:
        query_lower = query.lower().strip()
        
        # Поиск по коду ТН ВЭД
        tnved_pattern = r'\b\d{10}\b'
        tnved_match = re.search(tnved_pattern, query)
        if tnved_match:
            return handle_code_search(tnved_match.group(), ved_db)
        
        # Расширенный словарь ключевых слов
        keywords = {
            # Электроника
            'ноутбук': ['8471300000'],
            'смартфон': ['8517120000'],
            'телефон': ['8517120000'],
            'телевизор': ['8528720000'],
            'компьютер': ['8471410000', '8471300000'],
            
            # Автомобили
            'автомобиль': ['8703210000', '8703220000', '8703230000'],
            'машина': ['8703210000', '8703220000', '8703230000'],
            'авто': ['8703210000', '8703220000', '8703230000'],
            
            # Продукты питания
            'кофе': ['0901110000'],
            'молоко': ['0401100000'],
            'сахар': ['1701140000'],
            'вода': ['2202100000'],
            
            # Сырье
            'нефть': ['2709000000'],
            'пластик': ['3901100000'],
            'резина': ['4011100000'],
            
            # Лекарства
            'лекарство': ['3004200000'],
            'медикамент': ['3004200000'],
            'антибиотик': ['3004200000'],
        }
        
        # Поиск по ключевым словам
        for keyword, codes in keywords.items():
            if keyword in query_lower:
                return handle_multiple_codes(codes, ved_db, keyword)
        
        # Поиск по частичному совпадению в названии
        search_result = ved_db.search_product(query)
        if search_result and search_result.get('product'):
            return format_product_info(search_result['product'])
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        return None

def handle_code_search(code: str, ved_db) -> str:
    """Обработка поиска по коду"""
    try:
        # Обновляем статистику
        request_stats['code_searches'] += 1
        request_stats['popular_codes'][code] = request_stats['popular_codes'].get(code, 0) + 1
        
        product = ved_db.get_product_by_code(code)
        if product:
            return format_product_info(product)
        else:
            return f"❌ Код ТН ВЭД `{code}` не найден в базе данных.\n\n💡 *Возможные причины:*\n• Код введен неверно\n• Товар не включен в текущую базу\n• Используйте поиск по названию товара"
            
    except Exception as e:
        logger.error(f"Ошибка поиска по коду {code}: {e}")
        return f"❌ Ошибка при поиске кода {code}"

def handle_multiple_codes(codes: List[str], ved_db, keyword: str) -> str:
    """Обработка множественных результатов поиска"""
    try:
        results = []
        found_count = 0
        
        for code in codes:
            product = ved_db.get_product_by_code(code)
            if product:
                results.append(format_product_info(product))
                found_count += 1
        
        if results:
            header = f"🔍 Найдено {found_count} товар(ов) по запросу \"{keyword}\":\n\n"
            return header + "\n\n" + "─" * 50 + "\n\n".join(results)
        else:
            return f"❌ Товары по запросу \"{keyword}\" не найдены в базе данных"
            
    except Exception as e:
        logger.error(f"Ошибка обработки множественных кодов: {e}")
        return f"❌ Ошибка при поиске товаров для \"{keyword}\""

def handle_ai_analysis(text: str, ved_db) -> Optional[str]:
    """Обработка запроса на AI-анализ"""
    try:
        text_lower = text.lower()
        
        # Паттерны для AI-анализа
        ai_patterns = [
            r'анализ\s+(\d{10})',
            r'ai\s+(\d{10})',
            r'искусственный интеллект\s+(\d{10})',
            r'нейросеть\s+(\d{10})'
        ]
        
        for pattern in ai_patterns:
            match = re.search(pattern, text_lower)
            if match:
                code = match.group(1)
                
                # Обновляем статистику
                request_stats['ai_requests'] += 1
                
                # Получаем информацию о товаре
                product = ved_db.get_product_by_code(code)
                if not product:
                    return f"❌ Код ТН ВЭД `{code}` не найден для AI-анализа"
                
                # Формируем AI-анализ (пока заглушка)
                analysis = generate_ai_analysis(product)
                return f"🧠 *AI-анализ для {code}:*\n\n{analysis}"
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка AI-анализа: {e}")
        return None

def generate_ai_analysis(product: Dict) -> str:
    """Генерация AI-анализа товара"""
    try:
        code = product.get('code')
        name = product.get('name')
        duties = product.get('duties', {})
        certification = product.get('certification', [])
        restrictions = product.get('restrictions', [])
        
        analysis = f"📊 *Анализ товара:* {name}\n\n"
        
        # Анализ пошлин
        base_rate = duties.get('base', 0)
        if base_rate == 0:
            analysis += "💚 *Пошлины:* Отличная новость! Базовая ставка 0% - товар не облагается пошлиной.\n\n"
        elif base_rate <= 5:
            analysis += "💛 *Пошлины:* Низкая ставка - выгодно для импорта.\n\n"
        elif base_rate <= 15:
            analysis += "🧡 *Пошлины:* Средняя ставка - учитывайте в расчете себестоимости.\n\n"
        else:
            analysis += "🔴 *Пошлины:* Высокая ставка - рассмотрите альтернативные варианты.\n\n"
        
        # Анализ сертификации
        if certification:
            analysis += "📋 *Сертификация:* Требуется подготовка документов:\n"
            for cert in certification:
                analysis += f"  • {cert}\n"
            analysis += "\n"
        else:
            analysis += "✅ *Сертификация:* Дополнительные разрешения не требуются.\n\n"
        
        # Анализ ограничений
        if restrictions:
            analysis += "⚠️ *Внимание:* Есть ограничения на ввоз/вывоз.\n\n"
        else:
            analysis += "🚀 *Ограничения:* Товар свободно перемещается через границу.\n\n"
        
        # Рекомендации
        analysis += "💡 *Рекомендации:*\n"
        analysis += "• Уточните актуальные ставки на дату операции\n"
        analysis += "• Проконсультируйтесь с таможенным брокером\n"
        analysis += "• Подготовьте все необходимые документы заранее\n\n"
        
        analysis += "⏰ *Срок действия анализа:* данные актуальны на текущую дату"
        
        return analysis
        
    except Exception as e:
        logger.error(f"Ошибка генерации AI-анализа: {e}")
        return "❌ Ошибка при создании AI-анализа"

def get_statistics() -> str:
    """Получение статистики использования"""
    try:
        stats = f"📊 *Статистика ВЭД Эксперт:*\n\n"
        stats += f"🔢 Всего запросов: {request_stats['total_requests']}\n"
        stats += f"🔍 Поиск по кодам: {request_stats['code_searches']}\n"
        stats += f"📝 Поиск по названиям: {request_stats['name_searches']}\n"
        stats += f"🧠 AI-анализов: {request_stats['ai_requests']}\n\n"
        
        if request_stats['popular_codes']:
            stats += "🏆 *Популярные коды:*\n"
            sorted_codes = sorted(request_stats['popular_codes'].items(), 
                                key=lambda x: x[1], reverse=True)[:5]
            for code, count in sorted_codes:
                stats += f"• {code}: {count} запросов\n"
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return "❌ Ошибка получения статистики"

def route_message(text: str, ved_db=None) -> str:
    """Главная функция маршрутизации сообщений"""
    try:
        if not ved_db:
            return "🧠 Запрос обработан: " + text + "\n\nДля получения информации укажите код ТН ВЭД или название товара."
        
        # Обновляем общую статистику
        request_stats['total_requests'] += 1
        
        text = text.strip()
        
        # Специальные команды
        if text.lower() in ['статистика', 'stats', '/stats']:
            return get_statistics()
        
        if text.lower() in ['помощь', 'help', '/help']:
            return get_help_message()
        
        # Попытка AI-анализа
        ai_result = handle_ai_analysis(text, ved_db)
        if ai_result:
            return ai_result
        
        # Обычный поиск
        search_result = improved_search(text, ved_db)
        if search_result:
            return search_result
        
        # Если ничего не найдено
        request_stats['name_searches'] += 1
        return get_not_found_message(text)
        
    except Exception as e:
        logger.error(f"Ошибка маршрутизации: {e}")
        return f"❌ Произошла ошибка при обработке запроса: {str(e)}"

def get_help_message() -> str:
    """Сообщение помощи"""
    return """🤖 *ВЭД Эксперт - Помощь*

📋 *Как использовать:*
• Введите код ТН ВЭД (10 цифр): `8471300000`
• Введите название товара: `ноутбук`
• Запросите AI-анализ: `анализ 8471300000`
• Посмотрите статистику: `статистика`

🔍 *Примеры запросов:*
• `8517120000` - информация о смартфонах
• `автомобиль` - поиск кодов автомобилей  
• `анализ 2709000000` - AI-анализ нефти

⚡ *Быстрые команды:*
• `помощь` - это сообщение
• `статистика` - статистика использования

💡 *Совет:* Используйте точные названия товаров для лучших результатов поиска."""

def get_not_found_message(query: str) -> str:
    """Сообщение когда ничего не найдено"""
    return f"""❌ По запросу \"{query}\" ничего не найдено.

💡 *Попробуйте:*
• Указать 10-значный код ТН ВЭД
• Использовать более точное название товара
• Проверить правильность написания

🔍 *Популярные запросы:*
• `ноутбук` - портативные компьютеры
• `смартфон` - мобильные телефоны
• `автомобиль` - легковые автомобили
• `кофе` - кофейные зерна

❓ Напишите `помощь` для получения инструкций."""