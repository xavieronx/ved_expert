#!/usr/bin/env python3
"""
Расширенная система ВЭД Эксперт с полной интеграцией
"""

import json
import re
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ved_expert.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VEDExpert')

@dataclass
class SearchResult:
    """Результат поиска товара"""
    product: Optional[Dict]
    confidence: float
    search_type: str  # 'code', 'name', 'fuzzy'
    
@dataclass 
class VEDAnalysis:
    """Результат анализа через ВЭД систему"""
    official_data: Dict
    genspark_analysis: str
    confidence: float
    sources: List[str]

class EnhancedCache:
    """Расширенная система кэширования"""
    
    def __init__(self, ttl_minutes=60):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.stats = {"hits": 0, "misses": 0}
        logger.info(f"Cache initialized with TTL: {ttl_minutes} minutes")
    
    def _generate_key(self, query: str) -> str:
        return hashlib.md5(query.lower().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict]:
        key = self._generate_key(query)
        if key in self.cache:
            timestamp, value = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                self.stats["hits"] += 1
                logger.debug(f"Cache HIT for query: {query[:20]}...")
                return value
            else:
                del self.cache[key]
        
        self.stats["misses"] += 1
        logger.debug(f"Cache MISS for query: {query[:20]}...")
        return None
    
    def set(self, query: str, value: Dict):
        key = self._generate_key(query)
        self.cache[key] = (datetime.now(), value)
        logger.debug(f"Cached result for query: {query[:20]}...")

class SmartQueryParser:
    """Умный парсер пользовательских запросов"""
    
    def __init__(self):
        self.tnved_pattern = re.compile(r'\b\d{10}\b')
        self.hs_pattern = re.compile(r'\b\d{4,6}\b')
        
        # Расширенные синонимы и альтернативные названия
        self.synonyms = {
            'ноутбук': ['ноутбук', 'лэптоп', 'laptop', 'портативный компьютер'],
            'телефон': ['телефон', 'смартфон', 'мобильный', 'phone', 'smartphone'],
            'автомобиль': ['автомобиль', 'машина', 'авто', 'car', 'легковой автомобиль'],
            'свинина': ['свинина', 'мясо свиньи', 'свиное мясо', 'pork'],
            'говядина': ['говядина', 'мясо говядины', 'beef', 'телятина'],
            'молоко': ['молоко', 'milk', 'молочные продукты'],
            'рыба': ['рыба', 'fish', 'рыбные продукты'],
            'компьютер': ['компьютер', 'пк', 'pc', 'computer']
        }
        
        logger.info("SmartQueryParser initialized with extended synonyms")
    
    def parse_query(self, query: str) -> Dict:
        """Парсит запрос пользователя и определяет тип поиска"""
        query_lower = query.lower().strip()
        
        result = {
            'original_query': query,
            'normalized_query': query_lower,
            'search_type': 'unknown',
            'codes': [],
            'keywords': [],
            'confidence': 0.0
        }
        
        # Поиск кодов ТН ВЭД
        tnved_codes = self.tnved_pattern.findall(query)
        if tnved_codes:
            result['search_type'] = 'tnved_code'
            result['codes'] = tnved_codes
            result['confidence'] = 1.0
            logger.info(f"Detected TNVED codes: {tnved_codes}")
            return result
        
        # Поиск HS кодов
        hs_codes = self.hs_pattern.findall(query)
        if hs_codes:
            result['search_type'] = 'hs_code'
            result['codes'] = hs_codes
            result['confidence'] = 0.8
            logger.info(f"Detected HS codes: {hs_codes}")
            return result
        
        # Поиск по синонимам
        matched_categories = []
        for category, synonyms in self.synonyms.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    matched_categories.append(category)
                    result['keywords'].append(synonym)
                    break
        
        if matched_categories:
            result['search_type'] = 'category_match'
            result['keywords'] = matched_categories
            result['confidence'] = 0.9
            logger.info(f"Matched categories: {matched_categories}")
            return result
        
        # Общий текстовый поиск
        result['search_type'] = 'text_search'
        result['keywords'] = query_lower.split()
        result['confidence'] = 0.5
        logger.info(f"Text search with keywords: {result['keywords']}")
        
        return result

class EnhancedVEDDatabase:
    """Расширенная база данных ТН ВЭД с умным поиском"""
    
    def __init__(self, data_path=None):
        if data_path is None:
            data_path = Path(__file__).parent
        else:
            data_path = Path(data_path)
        
        self.data_path = data_path
        self.database = {}
        self.cache = EnhancedCache()
        self.parser = SmartQueryParser()
        
        self._load_database()
        logger.info("EnhancedVEDDatabase initialized successfully")
    
    def _load_database(self):
        """Загружает базу данных"""
        try:
            db_file = self.data_path / "tnved_database.json"
            with open(db_file, "r", encoding="utf-8") as f:
                self.database = json.load(f)
            
            codes_count = len(self.database.get("codes", []))
            logger.info(f"Database loaded: {codes_count} products")
            
        except FileNotFoundError as e:
            logger.error(f"Database file not found: {e}")
            self.database = {"codes": [], "groups": []}
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            self.database = {"codes": [], "groups": []}
    
    def smart_search(self, query: str) -> SearchResult:
        """Умный поиск товаров"""
        # Проверяем кэш
        cached_result = self.cache.get(query)
        if cached_result:
            return SearchResult(**cached_result)
        
        # Парсим запрос
        parsed = self.parser.parse_query(query)
        result = None
        confidence = 0.0
        search_type = parsed['search_type']
        
        # Поиск по типу запроса
        if search_type == 'tnved_code':
            result = self._search_by_code(parsed['codes'][0])
            confidence = 1.0 if result else 0.0
            
        elif search_type == 'category_match':
            result = self._search_by_category(parsed['keywords'])
            confidence = 0.9 if result else 0.0
            
        elif search_type == 'text_search':
            result = self._search_by_text(parsed['keywords'])
            confidence = 0.7 if result else 0.0
        
        search_result = SearchResult(
            product=result,
            confidence=confidence,
            search_type=search_type
        )
        
        # Кэшируем результат
        self.cache.set(query, {
            'product': result,
            'confidence': confidence,
            'search_type': search_type
        })
        
        logger.info(f"Search completed: {search_type}, confidence: {confidence}")
        return search_result
    
    def _search_by_code(self, code: str) -> Optional[Dict]:
        """Поиск по коду ТН ВЭД"""
        for product in self.database.get("codes", []):
            if product.get("code") == code:
                return product
        return None
    
    def _search_by_category(self, keywords: List[str]) -> Optional[Dict]:
        """Поиск по категории товара"""
        for product in self.database.get("codes", []):
            product_name = product.get("name", "").lower()
            for keyword in keywords:
                if keyword in product_name:
                    return product
        return None
    
    def _search_by_text(self, keywords: List[str]) -> Optional[Dict]:
        """Поиск по тексту"""
        best_match = None
        best_score = 0
        
        for product in self.database.get("codes", []):
            product_text = f"{product.get('name', '')} {product.get('description', '')}".lower()
            
            score = 0
            for keyword in keywords:
                if keyword in product_text:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = product
        
        return best_match if best_score > 0 else None

class GensparktVEDIntegration:
    """Интеграция с Genspark для профессионального анализа"""
    
    def __init__(self, genspark_agent):
        self.genspark_agent = genspark_agent
        logger.info("GensparktVEDIntegration initialized")
    
    def analyze_with_context(self, official_data: Dict, user_query: str) -> VEDAnalysis:
        """Анализ с контекстом официальных данных"""
        
        if not official_data:
            # Если нет официальных данных, используем только Genspark
            logger.warning("No official data found, using Genspark only")
            genspark_result = self._get_genspark_analysis(user_query)
            
            return VEDAnalysis(
                official_data={},
                genspark_analysis=genspark_result,
                confidence=0.3,
                sources=["Genspark AI"]
            )
        
        # Формируем контекст для Genspark
        context = self._format_official_context(official_data)
        enhanced_query = f"""
Официальные данные ТН ВЭД:
{context}

Пользователь спрашивает: {user_query}

Проанализируй и дополни официальную информацию:
1. Подтверди правильность классификации
2. Добавь практические советы по импорту/экспорту
3. Укажи возможные альтернативы или похожие товары
4. Предупреди о потенциальных сложностях
"""
        
        genspark_analysis = self._get_genspark_analysis(enhanced_query)
        
        return VEDAnalysis(
            official_data=official_data,
            genspark_analysis=genspark_analysis,
            confidence=0.95,
            sources=["Официальная база ТН ВЭД", "Genspark AI"]
        )
    
    def _format_official_context(self, data: Dict) -> str:
        """Форматирует официальные данные для контекста"""
        context_parts = [
            f"Код ТН ВЭД: {data.get('code', 'Н/Д')}",
            f"Наименование: {data.get('name', 'Н/Д')}",
            f"Описание: {data.get('description', 'Н/Д')}",
            f"Группа: {data.get('group', 'Н/Д')}"
        ]
        
        duties = data.get('duties', {})
        if duties:
            duties_text = "Пошлины: " + ", ".join([f"{k}: {v}%" for k, v in duties.items()])
            context_parts.append(duties_text)
        
        cert = data.get('certification', [])
        if cert:
            context_parts.append(f"Сертификация: {', '.join(cert)}")
        
        restrictions = data.get('restrictions', [])
        if restrictions:
            context_parts.append(f"Ограничения: {', '.join(restrictions)}")
        
        return "\n".join(context_parts)
    
    def _get_genspark_analysis(self, query: str) -> str:
        """Получает анализ от Genspark"""
        try:
            # Здесь должен быть вызов к вашему Genspark агенту
            # result = self.genspark_agent.analyze(query)
            
            # Заглушка для демонстрации
            result = f"Анализ Genspark AI для запроса: {query[:50]}... (интеграция с реальным агентом)"
            logger.info("Genspark analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Genspark analysis failed: {e}")
            return "Анализ Genspark AI временно недоступен"

def format_enhanced_response(analysis: VEDAnalysis) -> str:
    """Форматирует расширенный ответ пользователю"""
    
    blocks = []
    
    # Официальные данные (приоритет)
    if analysis.official_data:
        official_block = format_official_data(analysis.official_data)
        blocks.append(f"📊 *ОФИЦИАЛЬНЫЕ ДАННЫЕ ТН ВЭД:*\n{official_block}")
    
    # Анализ Genspark
    if analysis.genspark_analysis:
        blocks.append(f"🧠 *ЭКСПЕРТНЫЙ АНАЛИЗ:*\n{analysis.genspark_analysis}")
    
    # Источники и надежность
    confidence_text = f"🎯 *Достоверность:* {analysis.confidence*100:.0f}%"
    sources_text = f"📚 *Источники:* {', '.join(analysis.sources)}"
    blocks.extend([confidence_text, sources_text])
    
    return "\n\n".join(blocks)

def format_official_data(data: Dict) -> str:
    """Форматирует официальные данные"""
    lines = [
        f"📌 **{data.get('name', 'Товар')}**",
        f"🔢 Код: `{data.get('code', 'Н/Д')}`",
        f"📝 {data.get('description', 'Описание отсутствует')}"
    ]
    
    duties = data.get('duties', {})
    if duties:
        duties_lines = ["💰 **Пошлины:**"]
        for country, rate in duties.items():
            country_name = {
                'base': 'Базовая ставка',
                'china': 'Китай',
                'eu': 'ЕС',
                'usa': 'США'
            }.get(country, country.capitalize())
            duties_lines.append(f"  • {country_name}: {rate}%")
        lines.extend(duties_lines)
    
    cert = data.get('certification', [])
    if cert:
        lines.append(f"📄 **Сертификация:** {', '.join(cert)}")
    
    restrictions = data.get('restrictions', [])
    if restrictions:
        lines.append(f"⚠️ **Ограничения:** {', '.join(restrictions)}")
    else:
        lines.append("✅ **Ограничения:** отсутствуют")
    
    return "\n".join(lines)

# Основной класс системы
class EnhancedVEDExpertSystem:
    """Расширенная система ВЭД Эксперт"""
    
    def __init__(self, genspark_agent=None):
        self.database = EnhancedVEDDatabase()
        self.genspark_integration = GensparktVEDIntegration(genspark_agent) if genspark_agent else None
        logger.info("EnhancedVEDExpertSystem initialized")
    
    def process_query(self, query: str) -> str:
        """Обрабатывает запрос пользователя"""
        logger.info(f"Processing query: {query[:50]}...")
        
        # Поиск в официальной базе
        search_result = self.database.smart_search(query)
        
        # Анализ через Genspark (если доступен)
        if self.genspark_integration:
            analysis = self.genspark_integration.analyze_with_context(
                search_result.product, query
            )
            response = format_enhanced_response(analysis)
        else:
            # Только официальные данные
            if search_result.product:
                response = f"📊 *Найден товар:*\n{format_official_data(search_result.product)}"
            else:
                response = "❌ Товар не найден в официальной базе ТН ВЭД"
        
        logger.info(f"Query processed, confidence: {search_result.confidence}")
        return response

if __name__ == "__main__":
    # Тестирование системы
    system = EnhancedVEDExpertSystem()
    
    test_queries = [
        "ноутбук",
        "8471300000", 
        "свинина",
        "автомобиль легковой"
    ]
    
    for query in test_queries:
        print(f"\nЗапрос: {query}")
        print("-" * 50)
        result = system.process_query(query)
        print(result)
        print("=" * 50)