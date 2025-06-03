import os
import json
import csv

class VEDDatabase:
    """Класс для работы с базой данных ТН ВЭД"""

    def __init__(self, data_path):
        """Инициализация с путем к файлам базы данных"""
        self.data_path = data_path
        self.tnved_data = {}
        self.duties = {}
        self.certification_reqs = {}
        self.product_certification = {}
        self.restrictions = {}
        self.antidumping = {}

        # Загрузка данных
        self._load_data()

    def _load_data(self):
        """Загрузка всех данных из файлов"""
        # Загрузка основной базы ТН ВЭД
        with open(os.path.join(self.data_path, 'tnved_database.json'), 'r', encoding='utf-8') as f:
            self.tnved_data = json.load(f)

        # Загрузка пошлин
        with open(os.path.join(self.data_path, 'duties.json'), 'r', encoding='utf-8') as f:
            self.duties = json.load(f)

        # Загрузка сертификации
        with open(os.path.join(self.data_path, 'certification.json'), 'r', encoding='utf-8') as f:
            self.certification_reqs = json.load(f)

        # Загрузка сертификации по товарам
        with open(os.path.join(self.data_path, 'product_certification.json'), 'r', encoding='utf-8') as f:
            self.product_certification = json.load(f)

        # Загрузка ограничений
        with open(os.path.join(self.data_path, 'restrictions.json'), 'r', encoding='utf-8') as f:
            self.restrictions = json.load(f)

        # Загрузка антидемпинга
        with open(os.path.join(self.data_path, 'antidumping.json'), 'r', encoding='utf-8') as f:
            self.antidumping = json.load(f)

    def get_product_by_code(self, code):
        """Получение информации о товаре по коду ТН ВЭД"""
        return self.tnved_data.get('codes', {}).get(code, None)

    def get_duties(self, code, country=None):
        """Получение пошлин для товара по коду и стране"""
        product_duties = self.duties.get(code, {})
        if country:
            return product_duties.get(country, {})
        return product_duties

    def get_certification_requirements(self, code):
        """Получение требований сертификации для товара"""
        # Получаем коды требований
        cert_codes = self.product_certification.get(code, [])
        # Преобразуем коды в полное описание
        cert_details = []
        for cert_code in cert_codes:
            detail = self.certification_reqs.get('requirements', {}).get(cert_code, '')
            if detail:
                cert_details.append({
                    'code': cert_code,
                    'description': detail
                })
        return cert_details

    def check_restrictions(self, code):
        """Проверка ограничений для кода ТН ВЭД"""
        result = []

        for restriction in self.restrictions.get('items', []):
            pattern = restriction.get('code_pattern', '')
            # Проверка соответствия кода шаблону
            if pattern.endswith('*'):
                if code.startswith(pattern[:-1]):
                    result.append(restriction)
            elif code == pattern:
                result.append(restriction)

        return result

    def get_antidumping(self, code, country=None):
        """Получение антидемпинговых пошлин"""
        antidump_measures = self.antidumping.get(code, [])
        if country:
            return [m for m in antidump_measures if m.get('country') == country]
        return antidump_measures
