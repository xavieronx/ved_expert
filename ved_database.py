import json
import os
from pathlib import Path

class VEDDatabase:
    """Класс для работы с базой данных ТН ВЭД"""
    
    def __init__(self, data_path=None):
        if data_path is None:
            # Путь к файлам базы данных в том же каталоге
            data_path = Path(__file__).parent
        else:
            data_path = Path(data_path)
        
        self.data_path = data_path
        self.database = {}
        self.duties = {}
        self.certification = {}
        self.restrictions = {}
        self.product_certification = {}
        self.antidumping = {}
        
        self._load_database()
    
    def _load_database(self):
        """Загружает все компоненты базы данных"""
        try:
            # Основная база данных
            with open(self.data_path / "tnved_database.json", "r", encoding="utf-8") as f:
                self.database = json.load(f)
            
            # Сертификация (может не существовать)
            cert_file = self.data_path / "certification.json"
            if cert_file.exists():
                with open(cert_file, "r", encoding="utf-8") as f:
                    self.certification = json.load(f)
            
            print("✅ VEDDatabase loaded successfully")
            
        except FileNotFoundError as e:
            print(f"❌ Database file not found: {e}")
            self.database = {"codes": [], "groups": []}
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            self.database = {"codes": [], "groups": []}
    
    def search_product(self, query):
        """Поиск товара по коду или названию"""
        query = query.strip().lower()
        
        if not self.database.get("codes"):
            return None
        
        # Поиск по коду
        for product in self.database["codes"]:
            code = product.get("code", "").lower()
            name = product.get("name", "").lower()
            
            if query in code or query in name:
                return {"product": product}
        
        return None
    
    def get_product_by_code(self, code):
        """Получение информации о товаре по коду ТН ВЭД"""
        if not self.database.get("codes"):
            return None
            
        for product in self.database["codes"]:
            if product.get("code") == code:
                return product
        return None
    
    def get_duties(self, code, country=None):
        """Получение информации о пошлинах"""
        product = self.get_product_by_code(code)
        if product and "duties" in product:
            duties = product["duties"]
            if country:
                return duties.get(country)
            return duties
        return None
    
    def get_certification_requirements(self, code):
        """Получение требований сертификации для товара"""
        product = self.get_product_by_code(code)
        if product:
            return product.get("certification", [])
        return []
    
    def check_restrictions(self, code):
        """Проверка ограничений для товара"""
        product = self.get_product_by_code(code)
        if product:
            return product.get("restrictions", [])
        return []
    
    def get_all_groups(self):
        """Получение всех групп ТН ВЭД"""
        return self.database.get("groups", [])