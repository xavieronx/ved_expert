"""
WED Expert + Genspark Integration Module
Интеграция системы WED Expert с базой знаний Genspark
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
        print("✅ WED Agent инициализирован с базой знаний Genspark")
        
    def _load_knowledge_base(self):
        """Загрузка базы знаний"""
        return {
            "coffee_machines": {
                "codes": ["8516710000", "8419812000"],
                "duties": ["8.5%", "0%"],
                "descriptions": [
                    "Приборы электронагревательные для приготовления кофе или чая",
                    "Кофеварки и другие приспособления для приготовления кофе"
                ]
            },
            "smartphones": {
                "codes": ["8517120000"],
                "duties": ["15%"],
                "descriptions": ["Телефонные аппараты"]
            }
        }

    def determine_tn_ved(self, product):
        """Основной метод определения кода ТН ВЭД"""
        
        if 'кофе' in product.name.lower() or 'кофемашина' in product.name.lower():
            if 'электр' in product.material.lower() or 'нагрев' in product.function.lower():
                code = '8516710000'
                duty_rate = '8.5%'
                description = 'Приборы электронагревательные для приготовления кофе или чая'
            else:
                code = '8419812000'
                duty_rate = '0%'
                description = 'Кофеварки и другие приспособления для приготовления кофе'
                
        elif any(word in product.name.lower() for word in ['телефон', 'смартфон', 'iphone']):
            code = '8517120000'
            duty_rate = '15%'
            description = 'Телефонные аппараты'
            
        else:
            code = '8500000000'
            duty_rate = '5%'
            description = 'Общая классификация электрооборудования'
        
        requirements = [
            "Декларация соответствия ТР ТС 004/2011",
            "Сертификат EAC",
            "Протокол испытаний"
        ]
        
        if code.startswith('85'):
            requirements.append("Сертификация ЭМС")
            
        reasoning = f"Товар '{product.name}' классифицирован как {description}"
        
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
        """Расчет общей стоимости импорта"""
        
        duty_rate_num = float(re.findall(r'\d+\.?\d*', tn_ved_result.duty_rate)[0]) / 100 if re.findall(r'\d+\.?\d*', tn_ved_result.duty_rate) else 0
        vat_rate_num = 0.20
        
        duty_amount = customs_value * duty_rate_num * quantity
        customs_value_with_duty = customs_value + duty_amount
        vat_amount = customs_value_with_duty * vat_rate_num * quantity
        
        total_taxes = duty_amount + vat_amount
        total_cost = customs_value * quantity + total_taxes
        
        return {
            'customs_value': customs_value * quantity,
            'duty_amount': duty_amount,
            'vat_amount': vat_amount,
            'total_taxes': total_taxes,
            'total_cost': total_cost
        }

    def validate_classification(self, product, suggested_code):
        """Валидация предложенного кода ТН ВЭД"""
        
        auto_result = self.determine_tn_ved(product)
        
        return {
            'suggested_code': suggested_code,
            'auto_determined_code': auto_result.code,
            'match': suggested_code == auto_result.code,
            'confidence': auto_result.confidence
        }
