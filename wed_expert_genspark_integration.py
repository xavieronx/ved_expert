"""
WED Expert + Genspark Integration Module
Интеграция системы WED Expert с базой знаний Genspark
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

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

class ClassificationStep(Enum):
    """Этапы классификации товара"""
    MATERIAL_ANALYSIS = 1
    FUNCTION_DETERMINATION = 2
    PROCESSING_ASSESSMENT = 3
    SECTION_IDENTIFICATION = 4
    GROUP_SELECTION = 5
    CODE_FINALIZATION = 6

class GensparktWEDAgent:
    """Главный класс для интеграции WED Expert с базой знаний Genspark"""
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.algorithm_steps = self._load_algorithm()
        self.common_mistakes = self._load_mistakes()
        
    def _load_knowledge_base(self) -> pd.DataFrame:
        """Загрузка основной базы знаний"""
        # В реальной реализации - загрузка из CSV файлов Genspark
        data = [
            {
                "section": "XVI", "group_code": "85", 
                "group_name": "Электрические машины и аппаратура",
                "typical_goods": "Телефоны, компьютеры, электродвигатели",
                "classification_rules": "По функции, напряжению, мощности",
                "typical_duty_rate": "0-15%", "vat_rate": "20%",
                "special_requirements": "Сертификация ЭМС, радиочастотное разрешение"
            },
            {
                "section": "XVI", "group_code": "84",
                "group_name": "Машины, оборудование и механизмы", 
                "typical_goods": "Двигатели, насосы, станки, бытовая техника",
                "classification_rules": "По функциональному назначению, принципу работы",
                "typical_duty_rate": "0-15%", "vat_rate": "20%",
                "special_requirements": "Сертификация соответствия, техрегламенты"
            }
        ]
        return pd.DataFrame(data)
    
    def _load_algorithm(self) -> Dict:
        """Загрузка алгоритма определения ТН ВЭД"""
        return {
            1: "Определить основной материал или сырьё",
            2: "Выявить функциональное назначение", 
            3: "Оценить принцип работы или способ изготовления",
            4: "Найти соответствующий раздел ТН ВЭД",
            5: "Уточнить группу в разделе",
            6: "Определить дополнительные характеристики для финального кода"
        }
    
    def _load_mistakes(self) -> Dict:
        """Загрузка базы типичных ошибок"""
        return {
            "classification_by_name": {
                "description": "Классификация только по названию товара",
                "solution": "Анализировать материал, функцию и назначение"
            },
            "material_error": {
                "description": "Ошибка в определении основного материала",
                "solution": "Определять по весу/объёму, а не внешнему виду"
            }
        }

    def determine_tn_ved(self, product: ProductClassification) -> TNVEDResult:
        """
        Основной метод определения кода ТН ВЭД
        
        Args:
            product: Характеристики товара
            
        Returns:
            TNVEDResult: Результат классификации
        """
        
        # Шаг 1: Анализ материала
        material_analysis = self._analyze_material(product.material)
        
        # Шаг 2: Определение функции
        function_analysis = self._analyze_function(product.function)
        
        # Шаг 3: Определение раздела
        section = self._determine_section(material_analysis, function_analysis)
        
        # Шаг 4: Определение группы
        group = self._determine_group(section, product)
        
        # Шаг 5: Финальный код (упрощенная логика)
        final_code = self._determine_final_code(group, product)
        
        # Шаг 6: Получение тарифных данных
        duty_info = self._get_duty_info(final_code)
        
        # Шаг 7: Требования сертификации
        requirements = self._get_requirements(final_code, product.origin_country)
        
        return TNVEDResult(
            code=final_code,
            description=self._get_code_description(final_code),
            confidence=0.85,  # В реальности - более сложная логика
            duty_rate=duty_info['duty'],
            vat_rate=duty_info['vat'],
            requirements=requirements,
            reasoning=self._generate_reasoning(product, final_code)
        )

    def _analyze_material(self, material: str) -> Dict:
        """Анализ материала товара"""
        material_map = {
            'металл': {'section': 'XV', 'priority': 'high'},
            'пластик': {'section': 'VII', 'priority': 'medium'},
            'электроника': {'section': 'XVI', 'priority': 'high'},
            'текстиль': {'section': 'XI', 'priority': 'high'}
        }
        
        for key, value in material_map.items():
            if key.lower() in material.lower():
                return value
        
        return {'section': 'unknown', 'priority': 'low'}

    def _analyze_function(self, function: str) -> Dict:
        """Анализ функционального назначения"""
        function_map = {
            'нагрев': {'group': '85', 'subgroup': 'heating'},
            'приготовление': {'group': '84', 'subgroup': 'food_prep'},
            'связь': {'group': '85', 'subgroup': 'communication'},
            'обработка': {'group': '84', 'subgroup': 'processing'}
        }
        
        for key, value in function_map.items():
            if key in function.lower():
                return value
                
        return {'group': 'unknown', 'subgroup': 'general'}

    def _determine_section(self, material_analysis: Dict, function_analysis: Dict) -> str:
        """Определение раздела ТН ВЭД"""
        if material_analysis.get('section') == 'XVI' or function_analysis.get('group') in ['84', '85']:
            return 'XVI'
        elif material_analysis.get('section') == 'XI':
            return 'XI'
        else:
            return 'XVI'  # Default для машин и оборудования

    def _determine_group(self, section: str, product: ProductClassification) -> str:
        """Определение группы в разделе"""
        if section == 'XVI':
            if 'электр' in product.function.lower():
                return '85'
            else:
                return '84'
        return '85'  # Default

    def _determine_final_code(self, group: str, product: ProductClassification) -> str:
        """Определение финального 10-значного кода"""
        # Упрощенная логика для примера
        if group == '85' and 'кофе' in product.name.lower():
            if 'нагрев' in product.function.lower():
                return '8516710000'  # Электронагревательные приборы для кофе
            else:
                return '8419812000'  # Кофеварки общего назначения
        
        return f"{group}00000000"  # Общий код группы

    def _get_duty_info(self, code: str) -> Dict:
        """Получение информации о пошлинах"""
        duty_rates = {
            '8516710000': {'duty': '8.5%', 'vat': '20%'},
            '8419812000': {'duty': '0%', 'vat': '20%'},
        }
        
        return duty_rates.get(code, {'duty': '0%', 'vat': '20%'})

    def _get_requirements(self, code: str, origin_country: str) -> List[str]:
        """Получение требований сертификации"""
        base_requirements = [
            "Декларация соответствия ТР ТС 004/2011",
            "Сертификат EAC",
            "Протокол испытаний"
        ]
        
        if code.startswith('85'):
            base_requirements.append("Сертификация ЭМС")
            
        if origin_country not in ['BY', 'KZ', 'AM', 'KG']:
            base_requirements.append("Подтверждение страны происхождения")
            
        return base_requirements

    def _get_code_description(self, code: str) -> str:
        """Получение описания кода"""
        descriptions = {
            '8516710000': 'Приборы электронагревательные для приготовления кофе или чая',
            '8419812000': 'Кофеварки и другие приспособления для приготовления кофе'
        }
        return descriptions.get(code, 'Описание не найдено')

    def _generate_reasoning(self, product: ProductClassification, code: str) -> str:
        """Генерация объяснения логики классификации"""
        return f"""
        Классификация товара '{product.name}':
        1. Материал: {product.material} → определяет раздел
        2. Функция: {product.function} → определяет группу  
        3. Принцип работы → определяет подгруппу
        4. Результат: код {code}
        
        Логика: товар относится к электрическим приборам (раздел XVI), 
        предназначен для приготовления напитков, что определяет конкретную позицию.
        """

    def calculate_total_cost(self, tn_ved_result: TNVEDResult, 
                           customs_value: float, quantity: int = 1) -> Dict:
        """Расчет общей стоимости импорта"""
        
        # Извлечение числовых значений из строк
        duty_rate = float(re.findall(r'\d+\.?\d*', tn_ved_result.duty_rate)[0]) / 100 if re.findall(r'\d+\.?\d*', tn_ved_result.duty_rate) else 0
        vat_rate = float(re.findall(r'\d+\.?\d*', tn_ved_result.vat_rate)[0]) / 100 if re.findall(r'\d+\.?\d*', tn_ved_result.vat_rate) else 0
        
        duty_amount = customs_value * duty_rate * quantity
        customs_value_with_duty = customs_value + duty_amount
        vat_amount = customs_value_with_duty * vat_rate * quantity
        
        total_taxes = duty_amount + vat_amount
        total_cost = customs_value * quantity + total_taxes
        
        return {
            'customs_value': customs_value * quantity,
            'duty_amount': duty_amount,
            'vat_amount': vat_amount,
            'total_taxes': total_taxes,
            'total_cost': total_cost,
            'breakdown': {
                'товарная_стоимость': customs_value * quantity,
                'таможенная_пошлина': f"{duty_amount:.2f} руб ({tn_ved_result.duty_rate})",
                'НДС': f"{vat_amount:.2f} руб ({tn_ved_result.vat_rate})",
                'итого_к_доплате': f"{total_taxes:.2f} руб",
                'общая_стоимость': f"{total_cost:.2f} руб"
            }
        }

    def validate_classification(self, product: ProductClassification, 
                              suggested_code: str) -> Dict:
        """Валидация предложенного кода ТН ВЭД"""
        
        auto_result = self.determine_tn_ved(product)
        
        validation_result = {
            'suggested_code': suggested_code,
            'auto_determined_code': auto_result.code,
            'match': suggested_code == auto_result.code,
            'confidence': auto_result.confidence,
            'potential_issues': []
        }
        
        if not validation_result['match']:
            validation_result['potential_issues'].append(
                f"Предложенный код {suggested_code} не совпадает с автоматически определенным {auto_result.code}"
            )
            validation_result['recommendations'] = [
                "Проверьте основное назначение товара",
                "Уточните материал изготовления", 
                "Рассмотрите принцип работы изделия"
            ]
        
        return validation_result

def main():
    """Пример использования системы"""
    
    # Инициализация агента
    agent = GensparktWEDAgent()
    
    # Пример: Кофемашина из Италии
    coffee_machine = ProductClassification(
        name="Кофемашина бытовая электрическая",
        material="металл, пластик, электронные компоненты",
        function="приготовление кофе, нагрев воды",
        processing_level="готовое изделие",
        origin_country="IT",
        value=25000.0
    )
    
    # Определение ТН ВЭД
    result = agent.determine_tn_ved(coffee_machine)
    
    print("=== РЕЗУЛЬТАТ КЛАССИФИКАЦИИ ===")
    print(f"Код ТН ВЭД: {result.code}")
    print(f"Описание: {result.description}")
    print(f"Пошлина: {result.duty_rate}")
    print(f"НДС: {result.vat_rate}")
    print(f"Требования: {', '.join(result.requirements)}")
    
    # Расчет стоимости
    cost_calculation = agent.calculate_total_cost(result, 25000.0, 1)
    
    print("\n=== РАСЧЕТ СТОИМОСТИ ===")
    for key, value in cost_calculation['breakdown'].items():
        print(f"{key}: {value}")
    
    # Валидация
    validation = agent.validate_classification(coffee_machine, "8516710000")
    print(f"\n=== ВАЛИДАЦИЯ ===")
    print(f"Код корректен: {validation['match']}")
    
if __name__ == "__main__":
    main()