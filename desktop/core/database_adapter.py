"""
BADER Database Adapter
Tek interface ile SQLite ve API backend desteği
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import json
import requests


class DatabaseBackend(ABC):
    """Veritabanı backend interface"""
    
    @abstractmethod
    def get_members(self, status: str = "Aktif") -> List[Dict]:
        pass
    
    @abstractmethod
    def get_member(self, member_id: int) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def add_member(self, data: Dict) -> int:
        pass
    
    @abstractmethod
    def update_member(self, member_id: int, data: Dict) -> bool:
        pass
    
    @abstractmethod
    def delete_member(self, member_id: int) -> bool:
        pass
    
    @abstractmethod
    def get_incomes(self, year: int = None) -> List[Dict]:
        pass
    
    @abstractmethod
    def add_income(self, data: Dict) -> int:
        pass
    
    @abstractmethod
    def get_expenses(self, year: int = None) -> List[Dict]:
        pass
    
    @abstractmethod
    def add_expense(self, data: Dict) -> int:
        pass
    
    @abstractmethod
    def get_dues(self, year: int = None) -> List[Dict]:
        pass
    
    @abstractmethod
    def update_due(self, member_id: int, year: int, paid_amount: float) -> bool:
        pass
    
    @abstractmethod
    def get_cash_accounts(self) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_settings(self) -> Dict:
        pass
    
    @abstractmethod
    def update_setting(self, key: str, value: Any) -> bool:
        pass


class SQLiteBackend(DatabaseBackend):
    """SQLite veritabanı backend - LOCAL ve DEMO lisanslar için"""
    
    def __init__(self, db_path: str = "bader.db"):
        from database import Database
        self.db = Database(db_path)
        self.db.connect()
    
    def get_members(self, status: str = "Aktif") -> List[Dict]:
        return self.db.get_members(status=status)
    
    def get_member(self, member_id: int) -> Optional[Dict]:
        return self.db.get_member(member_id)
    
    def add_member(self, data: Dict) -> int:
        return self.db.add_member(**data)
    
    def update_member(self, member_id: int, data: Dict) -> bool:
        return self.db.update_member(member_id, **data)
    
    def delete_member(self, member_id: int) -> bool:
        return self.db.delete_member(member_id)
    
    def get_incomes(self, year: int = None) -> List[Dict]:
        return self.db.get_incomes(year=year)
    
    def add_income(self, data: Dict) -> int:
        return self.db.add_income(**data)
    
    def get_expenses(self, year: int = None) -> List[Dict]:
        return self.db.get_expenses(year=year)
    
    def add_expense(self, data: Dict) -> int:
        return self.db.add_expense(**data)
    
    def get_dues(self, year: int = None) -> List[Dict]:
        return self.db.get_dues(year=year)
    
    def update_due(self, member_id: int, year: int, paid_amount: float) -> bool:
        return self.db.update_due_payment(member_id, year, paid_amount)
    
    def get_cash_accounts(self) -> List[Dict]:
        return self.db.get_cash_accounts()
    
    def get_settings(self) -> Dict:
        return self.db.get_settings()
    
    def update_setting(self, key: str, value: Any) -> bool:
        return self.db.update_setting(key, value)


class APIBackend(DatabaseBackend):
    """API veritabanı backend - ONLINE lisanslar için"""
    
    def __init__(self, customer_id: str, token: str, api_url: str = None):
        self.customer_id = customer_id
        self.token = token
        self.api_url = api_url or "https://api.bfrdernek.com"
        # self.api_url = "http://157.90.154.48:8080/api"  # Dev
    
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """API isteği gönder"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Customer-ID": self.customer_id,
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Geçersiz method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise DatabaseError(f"API hatası: {str(e)}")
    
    def get_members(self, status: str = "Aktif") -> List[Dict]:
        result = self._request("GET", f"/web/members?status={status}")
        return result.get("members", [])
    
    def get_member(self, member_id: int) -> Optional[Dict]:
        result = self._request("GET", f"/web/members/{member_id}/detail")
        return result.get("member")
    
    def add_member(self, data: Dict) -> int:
        result = self._request("POST", "/web/members", data)
        return result.get("id", 0)
    
    def update_member(self, member_id: int, data: Dict) -> bool:
        self._request("PUT", f"/web/members/{member_id}", data)
        return True
    
    def delete_member(self, member_id: int) -> bool:
        self._request("DELETE", f"/web/members/{member_id}")
        return True
    
    def get_incomes(self, year: int = None) -> List[Dict]:
        endpoint = f"/web/incomes?year={year}" if year else "/web/incomes"
        result = self._request("GET", endpoint)
        return result.get("incomes", [])
    
    def add_income(self, data: Dict) -> int:
        result = self._request("POST", "/web/incomes", data)
        return result.get("id", 0)
    
    def get_expenses(self, year: int = None) -> List[Dict]:
        endpoint = f"/web/expenses?year={year}" if year else "/web/expenses"
        result = self._request("GET", endpoint)
        return result.get("expenses", [])
    
    def add_expense(self, data: Dict) -> int:
        result = self._request("POST", "/web/expenses", data)
        return result.get("id", 0)
    
    def get_dues(self, year: int = None) -> List[Dict]:
        endpoint = f"/web/dues?year={year}" if year else "/web/dues"
        result = self._request("GET", endpoint)
        return result.get("dues", [])
    
    def update_due(self, member_id: int, year: int, paid_amount: float) -> bool:
        self._request("POST", f"/web/dues/{member_id}/pay", {
            "year": year,
            "amount": paid_amount
        })
        return True
    
    def get_cash_accounts(self) -> List[Dict]:
        result = self._request("GET", "/web/cash-accounts")
        return result.get("accounts", [])
    
    def get_settings(self) -> Dict:
        result = self._request("GET", "/web/settings")
        return result.get("settings", {})
    
    def update_setting(self, key: str, value: Any) -> bool:
        self._request("PUT", "/web/settings", {key: value})
        return True


class HybridBackend(DatabaseBackend):
    """
    Hybrid veritabanı backend
    - Offline: SQLite kullan
    - Online: Değişiklikleri senkronize et
    """
    
    def __init__(self, customer_id: str, token: str, db_path: str = "bader.db"):
        self.local = SQLiteBackend(db_path)
        self.remote = APIBackend(customer_id, token)
        self.is_online = self._check_connection()
        self.pending_sync = []  # Senkronize edilecek işlemler
    
    def _check_connection(self) -> bool:
        """Sunucu bağlantısını kontrol et"""
        try:
            self.remote._request("GET", "/health")
            return True
        except:
            return False
    
    def _queue_sync(self, operation: str, entity: str, data: Dict):
        """Senkronizasyon kuyruğuna ekle"""
        self.pending_sync.append({
            "operation": operation,
            "entity": entity,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def sync(self) -> Dict:
        """Bekleyen işlemleri senkronize et"""
        if not self._check_connection():
            return {"success": False, "error": "Bağlantı yok"}
        
        synced = 0
        errors = []
        
        for item in self.pending_sync[:]:
            try:
                # İşlemi sunucuya gönder
                if item["operation"] == "add":
                    if item["entity"] == "member":
                        self.remote.add_member(item["data"])
                    elif item["entity"] == "income":
                        self.remote.add_income(item["data"])
                    elif item["entity"] == "expense":
                        self.remote.add_expense(item["data"])
                
                self.pending_sync.remove(item)
                synced += 1
            except Exception as e:
                errors.append(str(e))
        
        return {
            "success": len(errors) == 0,
            "synced": synced,
            "pending": len(self.pending_sync),
            "errors": errors
        }
    
    # Hybrid metodlar - önce local, sonra sync kuyruğuna
    def get_members(self, status: str = "Aktif") -> List[Dict]:
        return self.local.get_members(status)
    
    def get_member(self, member_id: int) -> Optional[Dict]:
        return self.local.get_member(member_id)
    
    def add_member(self, data: Dict) -> int:
        result = self.local.add_member(data)
        self._queue_sync("add", "member", data)
        return result
    
    def update_member(self, member_id: int, data: Dict) -> bool:
        result = self.local.update_member(member_id, data)
        self._queue_sync("update", "member", {"id": member_id, **data})
        return result
    
    def delete_member(self, member_id: int) -> bool:
        result = self.local.delete_member(member_id)
        self._queue_sync("delete", "member", {"id": member_id})
        return result
    
    def get_incomes(self, year: int = None) -> List[Dict]:
        return self.local.get_incomes(year)
    
    def add_income(self, data: Dict) -> int:
        result = self.local.add_income(data)
        self._queue_sync("add", "income", data)
        return result
    
    def get_expenses(self, year: int = None) -> List[Dict]:
        return self.local.get_expenses(year)
    
    def add_expense(self, data: Dict) -> int:
        result = self.local.add_expense(data)
        self._queue_sync("add", "expense", data)
        return result
    
    def get_dues(self, year: int = None) -> List[Dict]:
        return self.local.get_dues(year)
    
    def update_due(self, member_id: int, year: int, paid_amount: float) -> bool:
        result = self.local.update_due(member_id, year, paid_amount)
        self._queue_sync("update", "due", {"member_id": member_id, "year": year, "amount": paid_amount})
        return result
    
    def get_cash_accounts(self) -> List[Dict]:
        return self.local.get_cash_accounts()
    
    def get_settings(self) -> Dict:
        return self.local.get_settings()
    
    def update_setting(self, key: str, value: Any) -> bool:
        return self.local.update_setting(key, value)


class DatabaseAdapter:
    """
    Ana veritabanı adapter
    Lisans tipine göre doğru backend'i kullanır
    """
    
    def __init__(self, mode: str, customer_id: str = None, token: str = None, db_path: str = "bader.db"):
        """
        Args:
            mode: 'sqlite', 'api' veya 'hybrid'
            customer_id: ONLINE/HYBRID için müşteri ID
            token: ONLINE/HYBRID için JWT token
            db_path: LOCAL/HYBRID için SQLite dosya yolu
        """
        self.mode = mode
        
        if mode == "sqlite":
            self.backend = SQLiteBackend(db_path)
        elif mode == "api":
            if not customer_id or not token:
                raise ValueError("ONLINE mod için customer_id ve token gerekli")
            self.backend = APIBackend(customer_id, token)
        elif mode == "hybrid":
            if not customer_id or not token:
                raise ValueError("HYBRID mod için customer_id ve token gerekli")
            self.backend = HybridBackend(customer_id, token, db_path)
        else:
            raise ValueError(f"Geçersiz mod: {mode}")
    
    # Proxy metodları
    def get_members(self, status: str = "Aktif") -> List[Dict]:
        return self.backend.get_members(status)
    
    def get_member(self, member_id: int) -> Optional[Dict]:
        return self.backend.get_member(member_id)
    
    def add_member(self, **data) -> int:
        return self.backend.add_member(data)
    
    def update_member(self, member_id: int, **data) -> bool:
        return self.backend.update_member(member_id, data)
    
    def delete_member(self, member_id: int) -> bool:
        return self.backend.delete_member(member_id)
    
    def get_incomes(self, year: int = None) -> List[Dict]:
        return self.backend.get_incomes(year)
    
    def add_income(self, **data) -> int:
        return self.backend.add_income(data)
    
    def get_expenses(self, year: int = None) -> List[Dict]:
        return self.backend.get_expenses(year)
    
    def add_expense(self, **data) -> int:
        return self.backend.add_expense(data)
    
    def get_dues(self, year: int = None) -> List[Dict]:
        return self.backend.get_dues(year)
    
    def update_due(self, member_id: int, year: int, paid_amount: float) -> bool:
        return self.backend.update_due(member_id, year, paid_amount)
    
    def get_cash_accounts(self) -> List[Dict]:
        return self.backend.get_cash_accounts()
    
    def get_settings(self) -> Dict:
        return self.backend.get_settings()
    
    def update_setting(self, key: str, value: Any) -> bool:
        return self.backend.update_setting(key, value)
    
    def sync(self) -> Dict:
        """HYBRID mod için senkronizasyon"""
        if hasattr(self.backend, 'sync'):
            return self.backend.sync()
        return {"success": True, "message": "Sync not needed for this mode"}


class DatabaseError(Exception):
    """Veritabanı hatası"""
    pass


# Test
if __name__ == "__main__":
    # SQLite test
    adapter = DatabaseAdapter("sqlite", db_path="test.db")
    print(f"SQLite backend: {type(adapter.backend).__name__}")
    
    # Üye listesi al
    members = adapter.get_members()
    print(f"Üye sayısı: {len(members)}")
