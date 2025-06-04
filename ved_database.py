import json
import logging
from typing import List, Dict, Optional, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VEDDatabase:
    def __init__(self, json_file: str = 'tnved_database.json'):
        """Инициализация базы данных ТН ВЭД"""
        self.json_file = json_file
        self.data = []
        self.load_database()
    
    def load_database(self):
        """Загрузка базы данных из JSON файла"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"Загружено {len(self.data)} кодов ТН ВЭД")
        except FileNotFoundError:
            logger.error(f"Файл {self.json_file} не найден")
            self.data = []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            self.data = []
        except Exception as e:
            logger.error(f"Ошибка загрузки базы: {e}")
            self.data = []
    
    def find_by_code(self, code: str) -> Optional[Dict]:
        """Поиск товара по коду ТН ВЭД (точное совпадение)"""
        if not code:
            return None
        
        # Очистка кода от пробелов и приведение к строке
        search_code = str(code).strip()
        
        try:
            for item in self.data:
                if str(item.get('код', '')).strip() == search_code:
                    logger.info(f"Найден товар по коду: {search_code}")
                    return item
        except Exception as e:
            logger.error(f"Ошибка поиска по коду {code}: {e}")
        
        logger.warning(f"Товар с кодом {search_code} не найден")
        return None
    
    def search_by_name(self, name: str, limit: int = 10) -> List[Dict]:
        """Поиск товаров по названию (частичное совпадение)"""
        if not name or len(name.strip()) < 2:
            return []
        
        search_name = name.strip().lower()
        results = []
        
        try:
            for item in self.data:
                item_name = str(item.get('название', '')).lower()
                item_desc = str(item.get('описание', '')).lower()
                
                # Поиск в названии или описании
                if search_name in item_name or search_name in item_desc:
                    results.append(item)
                    if len(results) >= limit:
                        break
        except Exception as e:
            logger.error(f"Ошибка поиска по названию {name}: {e}")
        
        logger.info(f"Найдено {len(results)} товаров по запросу: {name}")
        return results
    
    def get_all_products(self) -> List[Dict]:
        """Получить все товары"""
        return self.data
    
    def get_product_count(self) -> int:
        """Получить количество товаров в базе"""
        return len(self.data)
    
    # Методы совместимости со старым API
    def get_product_by_code(self, code: str) -> Optional[Dict]:
        """Совместимость: получить товар по коду"""
        return self.find_by_code(code)
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """Совместимость: поиск товаров"""
        return self.search_by_name(query, limit)
    
    def get_random_products(self, count: int = 5) -> List[Dict]:
        """Получить случайные товары"""
        import random
        if len(self.data) <= count:
            return self.data
        return random.sample(self.data, count)
    
    def get_products_by_group(self, group: str) -> List[Dict]:
        """Получить товары по группе"""
        if not group:
            return []
        
        results = []
        search_group = group.strip().lower()
        
        try:
            for item in self.data:
                item_group = str(item.get('группа', '')).lower()
                if search_group in item_group:
                    results.append(item)
        except Exception as e:
            logger.error(f"Ошибка поиска по группе {group}: {e}")
        
        return results
    
    def format_product_info(self, product: Dict) -> str:
        """Форматирование информации о товаре для отображения"""
        if not product:
            return "Товар не найден"
        
        try:
            code = product.get('код', 'Не указан')
            name = product.get('название', 'Не указано')
            description = product.get('описание', 'Не указано')
            group = product.get('группа', 'Не указана')
            duty = product.get('пошлина', 'Не указана')
            cert = product.get('сертификация', 'Не указана')
            
            return f"""📦 **Код ТН ВЭД:** {code}
📝 **Название:** {name}
📋 **Описание:** {description}
📂 **Группа:** {group}
💰 **Пошлина:** {duty}
✅ **Сертификация:** {cert}"""
        except Exception as e:
            logger.error(f"Ошибка форматирования товара: {e}")
            return "Ошибка форматирования данных"
    
    def format_search_results(self, results: List[Dict], query: str = "") -> str:
        """Форматирование результатов поиска"""
        if not results:
            return f"❌ Товары по запросу '{query}' не найдены в базе данных"
        
        if len(results) == 1:
            return self.format_product_info(results[0])
        
        formatted = f"🔍 Найдено {len(results)} товаров по запросу '{query}':\n\n"
        for i, product in enumerate(results[:10], 1):
            code = product.get('код', 'Не указан')
            name = product.get('название', 'Не указано')[:60]
            if len(product.get('название', '')) > 60:
                name += "..."
            formatted += f"{i}. **{code}** - {name}\n"
        
        if len(results) > 10:
            formatted += f"\n... и еще {len(results) - 10} товаров"
        
        return formatted

# Глобальный экземпляр для использования в других модулях
ved_db = VEDDatabase()

# Функции для обратной совместимости
def get_product_by_code(code: str) -> Optional[Dict]:
    """Глобальная функция поиска по коду"""
    return ved_db.find_by_code(code)

def search_by_name(name: str, limit: int = 10) -> List[Dict]:
    """Глобальная функция поиска по названию"""
    return ved_db.search_by_name(name, limit)

def get_all_products() -> List[Dict]:
    """Глобальная функция получения всех товаров"""
    return ved_db.get_all_products()
