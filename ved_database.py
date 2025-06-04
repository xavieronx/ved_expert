import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("VED_DATABASE")

class VEDDatabase:
    """Оптимизированный класс для работы с большой базой данных ТН ВЭД"""

    def __init__(self, data_path=None):
        if data_path is None:
            data_path = Path(__file__).parent
        else:
            data_path = Path(data_path)

        self.data_path = data_path
        self.database = {}
        self.codes_index = {}  # Индекс для быстрого поиска по коду
        self.name_index = {}   # Индекс для поиска по названию
        self._cache = {}       # Кэш для поисковых запросов
        self._load_database()

    def _load_database(self):
        """Загружает базу данных с индексацией"""
        try:
            db_file = self.data_path / "tnved_database.json"
            logger.info(f"Загрузка базы из: {db_file}")

            with open(db_file, "r", encoding="utf-8") as f:
                self.database = json.load(f)

            # Создаем индексы для быстрого поиска
            self._build_indexes()

            codes_count = len(self.database.get("codes", []))
            logger.info(f"✅ VEDDatabase загружена: {codes_count} кодов")

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки базы: {e}")
            self.database = {"codes": [], "groups": []}

    def _build_indexes(self):
        """Строит индексы для оптимизации поиска"""
        codes = self.database.get("codes", [])

        for code_data in codes:
            code = code_data.get("code", "")
            name = code_data.get("name", "").lower()

            # Индекс по коду
            self.codes_index[code] = code_data

            # Индекс по словам в названии
            words = name.split()
            for word in words:
                if len(word) > 2:  # Игнорируем короткие слова
                    if word not in self.name_index:
                        self.name_index[word] = []
                    self.name_index[word].append(code_data)

    def find_by_code(self, code: str) -> Optional[Dict]:
        """Быстрый поиск по коду ТН ВЭД"""
        if not code:
            return None

        # Очистка кода от лишних символов
        clean_code = ''.join(filter(str.isdigit, code))

        # Точное совпадение
        if clean_code in self.codes_index:
            return self.codes_index[clean_code]

        # Поиск по началу кода (для неполных кодов)
        for indexed_code, data in self.codes_index.items():
            if indexed_code.startswith(clean_code):
                return data

        return None

    def search_by_name(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск по названию товара с ограничением результатов"""
        if not query or len(query) < 2:
            return []

        # Проверяем кэш
        cache_key = f"name_{query.lower()}_{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        query_lower = query.lower()
        results = []
        seen_codes = set()

        # Поиск по индексированным словам
        words = query_lower.split()
        for word in words:
            if word in self.name_index:
                for code_data in self.name_index[word]:
                    code = code_data.get("code", "")
                    if code not in seen_codes:
                        results.append(code_data)
                        seen_codes.add(code)
                        if len(results) >= limit:
                            break
            if len(results) >= limit:
                break

        # Если не нашли по индексу, ищем по содержанию
        if not results:
            for code_data in self.database.get("codes", []):
                name = code_data.get("name", "").lower()
                description = code_data.get("description", "").lower()

                if query_lower in name or query_lower in description:
                    code = code_data.get("code", "")
                    if code not in seen_codes:
                        results.append(code_data)
                        seen_codes.add(code)
                        if len(results) >= limit:
                            break

        # Кэшируем результат
        self._cache[cache_key] = results[:limit]
        return results[:limit]

    def get_group_info(self, group_id: str) -> Optional[Dict]:
        """Получить информацию о группе"""
        for group in self.database.get("groups", []):
            if group.get("id") == group_id:
                return group
        return None

    def get_statistics(self) -> Dict:
        """Получить статистику базы данных"""
        codes = self.database.get("codes", [])
        groups = self.database.get("groups", [])

        return {
            "total_codes": len(codes),
            "total_groups": len(groups),
            "index_size": len(self.codes_index),
            "cache_size": len(self._cache),
            "version": self.database.get("metadata", {}).get("version", "unknown")
        }

    def clear_cache(self):
        """Очистить кэш поиска"""
        self._cache.clear()
        logger.info("🗑️ Кэш очищен")