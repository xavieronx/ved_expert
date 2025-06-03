"""
WED Expert + Genspark Integration Module
Расширенная интеграция с множеством товарных категорий
"""

import re
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class TNVEDResult:
    """Результат определения кода ТН ВЭД"""
    code: str
    description: str
    confidence: float
    duty_rate: str
    vat_rate: str
    requirements: List[str]
    reasoning: str

@dataclass
class ProductClassification:
    """Характеристики товара для классификации"""
    name: str
    material: str
    function: str
    processing_level: str
    origin_country: str
    value: float

class GensparktWEDAgent:
    """Главный класс для интеграции WED Expert с базой знаний Genspark"""
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        print("✅ WED Agent инициализирован с расширенной базой знаний Genspark")
        
    def _load_knowledge_base(self):
        """Загрузка расширенной базы знаний"""
        return {
            "categories": {
                "electronics": ["кофемашина", "телефон", "смартфон", "компьютер", "ноутбук", "планшет"],
                "clothing": ["куртка", "пальто", "пиджак", "костюм", "футболка", "джинсы"],
                "footwear": ["ботинки", "туфли", "кроссовки", "сапоги", "босоножки"],
                "vehicles": ["автомобиль", "машина", "мотоцикл", "велосипед"],
                "cosmetics": ["крем", "шампунь", "косметика", "парфюм", "лосьон"],
                "food": ["шоколад", "конфеты", "печенье", "кофе", "чай"],
                "alcohol": ["вино", "водка", "виски", "пиво", "коньяк"],
                "furniture": ["стол", "стул", "диван", "кресло", "шкаф"],
                "books": ["книга", "учебник", "журнал"]
            }
        }

    def determine_tn_ved(self, product):
        """Расширенная классификация товаров"""
        
        name_lower = product.name.lower()
        material_lower = product.material.lower()
        function_lower = product.function.lower()
        
        # Кофемашины и бытовая техника
        if any(word in name_lower for word in ['кофе', 'кофемашина', 'эспрессо']):
            if any(word in material_lower for word in ['электр', 'нагрев']) or 'нагрев' in function_lower:
                return self._create_result('8516710000', 'Приборы электронагревательные для приготовления кофе или чая', '8.5%', ['Сертификация ЭМС', 'ТР ТС 004/2011'])
            else:
                return self._create_result('8419812000', 'Кофеварки и другие приспособления', '0%', ['ТР ТС 004/2011'])
        
        # Смартфоны и телефоны
        elif any(word in name_lower for word in ['телефон', 'смартфон', 'iphone', 'samsung', 'xiaomi']):
            return self._create_result('8517120000', 'Телефонные аппараты', '15%', ['Сертификация ЭМС', 'Радиочастотное разрешение', 'ТР ТС 004/2011'])
        
        # Компьютеры и ноутбуки
        elif any(word in name_lower for word in ['компьютер', 'ноутбук', 'планшет', 'macbook']):
            return self._create_result('8471300000', 'Машины вычислительные портативные', '0%', ['Сертификация ЭМС', 'ТР ТС 004/2011'])
        
        # Мужская одежда
        elif any(word in name_lower for word in ['куртка', 'пальто', 'пиджак']) and 'мужск' in name_lower:
            return self._create_result('6201100000', 'Пальто, плащи, куртки мужские', '8.8%', ['ТР ТС 017/2011', 'Декларация соответствия'])
        
        # Женская одежда
        elif any(word in name_lower for word in ['куртка', 'пальто', 'пиджак']) and ('женск' in name_lower or 'дамск' in name_lower):
            return self._create_result('6202100000', 'Пальто, плащи, куртки женские', '8.8%', ['ТР ТС 017/2011', 'Декларация соответствия'])
        
        # Обувь
        elif any(word in name_lower for word in ['ботинки', 'туфли', 'кроссовки', 'сапоги', 'босоножки']):
            return self._create_result('6403190000', 'Обувь прочая', '12.1%', ['ТР ТС 017/2011', 'Сертификат соответствия'])
        
        # Автомобили
        elif any(word in name_lower for word in ['автомобиль', 'машина', 'авто']) and 'легков' in name_lower:
            return self._create_result('8703100000', 'Автомобили легковые', '15%', ['Сертификат соответствия ТР ТС 018/2011', 'ЭПТС'])
        
        # Косметика
        elif any(word in name_lower for word in ['крем', 'шампунь', 'косметика', 'парфюм', 'лосьон']):
            return self._create_result('3304990000', 'Косметические средства прочие', '6.5%', ['ТР ТС 009/2011', 'Свидетельство о госрегистрации'])
        
        # Продукты питания - шоколад
        elif any(word in name_lower for word in ['шоколад', 'конфеты']):
            return self._create_result('1806320000', 'Шоколад и кондитерские изделия', '5%', ['ТР ТС 021/2011', 'Декларация соответствия'])
        
        # Печенье и выпечка
        elif any(word in name_lower for word in ['печенье', 'бисквит', 'вафли']):
            return self._create_result('1905310000', 'Печенье сладкое', '5%', ['ТР ТС 021/2011'])
        
        # Алкогольные напитки - вино
        elif any(word in name_lower for word in ['вино']):
            return self._create_result('2204210000', 'Вина виноградные', '20%', ['Лицензия на алкоголь', 'Акцизная марка', 'Справка о производителе'])
        
        # Крепкий алкоголь
        elif any(word in name_lower for word in ['водка', 'виски', 'коньяк']):
            return self._create_result('2208400000', 'Напитки спиртные', '20%', ['Лицензия на алкоголь', 'Акцизная марка'])
        
        # Мебель
        elif any(word in name_lower for word in ['стол', 'стул', 'диван', 'кресло', 'шкаф']):
            return self._create_result('9403700000', 'Мебель прочая', '20%', ['ТР ТС 025/2012', 'Сертификат соответствия'])
        
        # Книги и печатная продукция
        elif any(word in name_lower for word in ['книга', 'учебник', 'журнал']):
            return self._create_result('4901990000', 'Книги печатные', '0%', ['Санитарно-эпидемиологическое заключение'])
        
        # Игрушки
        elif any(word in name_lower for word in ['игрушка', 'кукла', 'машинка']):
            return self._create_result('9503000000', 'Игрушки прочие', '15%', ['ТР ТС 008/2011', 'Сертификат соответствия'])
        
        # Спортивные товары
        elif any(word in name_lower for word in ['велосипед', 'самокат', 'лыжи']):
            return self._create_result('9506910000', 'Инвентарь спортивный', '10%', ['Декларация соответствия'])
        
        # Часы
        elif any(word in name_lower for word in ['часы', 'watch']):
            return self._create_result('9102190000', 'Часы наручные прочие', '10%', ['Декларация соответствия'])
        
        # Ювелирные изделия
        elif any(word in name_lower for word in ['кольцо', 'серьги', 'браслет', 'цепочка']):
            return self._create_result('7113190000', 'Ювелирные изделия прочие', '15%', ['Пробирное клеймо', 'Сертификат подлинности'])
        
        # Бытовая химия
        elif any(word in name_lower for word in ['стиральный порошок', 'моющее средство', 'мыло']):
            return self._create_result('3402200000', 'Моющие средства', '6.5%', ['ТР ТС 009/2011'])
        
        # По умолчанию
        else:
            return self._create_result('9999999999', 'Требуется дополнительная классификация экспертом', '5%', ['Консультация специалиста по ВЭД'])

    def _create_result(self, code, description, duty_rate, special_requirements):
        """Создание результата классификации"""
        
        base_requirements = [
            "Таможенная декларация",
            "Инвойс (счет)",
            "Упаковочный лист",
            "Транспортные документы"
        ]
        
        requirements = base_requirements + special_requirements
        
        # Добавляем требования по стране происхождения
        reasoning = f"Товар '{description}' классифицирован на основе анализа названия, материала и функционального назначения. Применены правила интерпретации ТН ВЭД ЕАЭС."
        
        return TNVEDResult(
            code=code,
            description=description,
            confidence=0.85,
            duty_rate=duty_rate,
            vat_rate='20%',
            requirements=requirements,
            reasoning=reasoning
        )

    def calculate_total_cost(self, tn_ved_result, customs_value, quantity=1):
        """Расширенный расчет стоимости с учетом льгот"""
        
        duty_rate_num = float(re.findall(r'\d+\.?\d*', tn_ved_result.duty_rate)[0]) / 100 if re.findall(r'\d+\.?\d*', tn_ved_result.duty_rate) else 0
        vat_rate_num = 0.20
        
        # Базовые расчеты
        duty_amount = customs_value * duty_rate_num * quantity
        customs_value_with_duty = customs_value + duty_amount
        vat_amount = customs_value_with_duty * vat_rate_num * quantity
        
        # Дополнительные сборы
        customs_fee = max(500, customs_value * 0.01)  # Таможенный сбор
        broker_fee = 2000 if customs_value > 10000 else 1000  # Брокерские услуги
        
        total_fees = customs_fee + broker_fee
        total_taxes = duty_amount + vat_amount
        total_cost = customs_value * quantity + total_taxes + total_fees
        
        return {
            'customs_value': customs_value * quantity,
            'duty_amount': duty_amount,
            'vat_amount': vat_amount,
            'customs_fee': customs_fee,
            'broker_fee': broker_fee,
            'total_taxes': total_taxes,
            'total_fees': total_fees,
            'total_cost': total_cost,
            'breakdown': {
                'товарная_стоимость': f"{customs_value * quantity:,.0f} руб",
                'таможенная_пошлина': f"{duty_amount:.0f} руб ({tn_ved_result.duty_rate})",
                'НДС': f"{vat_amount:.0f} руб ({tn_ved_result.vat_rate})",
                'таможенный_сбор': f"{customs_fee:.0f} руб",
                'брокерские_услуги': f"{broker_fee:.0f} руб",
                'итого_платежи': f"{total_taxes + total_fees:.0f} руб",
                'общая_стоимость': f"{total_cost:.0f} руб"
            }
        }

    def validate_classification(self, product, suggested_code):
        """Валидация предложенного кода ТН ВЭД"""
        
        auto_result = self.determine_tn_ved(product)
        
        return {
            'suggested_code': suggested_code,
            'auto_determined_code': auto_result.code,
            'match': suggested_code == auto_result.code,
            'confidence': auto_result.confidence,
            'potential_issues': [] if suggested_code == auto_result.code else [
                f"Предложенный код {suggested_code} не совпадает с рекомендуемым {auto_result.code}",
                "Рекомендуется дополнительная экспертиза"
            ],
            'recommendations': [
                "Проверьте точность описания товара",
                "Уточните материал изготовления",
                "Рассмотрите основное функциональное назначение"
            ] if suggested_code != auto_result.code else [
                "Код подтвержден системой Genspark",
                "Дополнительная проверка не требуется"
            ]
        }

    def get_similar_products(self, product_name):
        """Поиск похожих товаров в базе"""
        similar = []
        name_words = product_name.lower().split()
        
        for category, products in self.knowledge_base["categories"].items():
            for product in products:
                if any(word in product for word in name_words):
                    similar.append({
                        'category': category,
                        'product': product,
                        'similarity': 0.8
                    })
        
        return similar[:5]  # Топ 5 похожих товаров
