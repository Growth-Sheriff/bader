"""
BADER License Manager
Lisans doğrulama, önbellek yönetimi ve offline mod desteği
"""

import json
import os
import sys
import platform
import hashlib
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import requests


@dataclass
class LicenseInfo:
    """Lisans bilgisi"""
    customer_id: str
    organization_name: str
    license_type: str  # LOCAL, ONLINE, HYBRID, DEMO
    license_status: str  # ACTIVE, SUSPENDED, EXPIRED
    license_end: str
    days_remaining: int
    max_users: int
    max_members: int
    features: Dict[str, Any]
    
    def is_valid(self) -> bool:
        return self.license_status == "ACTIVE" and self.days_remaining > 0
    
    def is_online(self) -> bool:
        return self.license_type in ["ONLINE", "HYBRID"]
    
    def is_local(self) -> bool:
        return self.license_type in ["LOCAL", "DEMO"]
    
    def to_dict(self) -> dict:
        return asdict(self)


class LicenseManager:
    """
    Lisans yönetimi
    - Online doğrulama
    - Offline önbellek
    - Lisans tipine göre veritabanı modu
    """
    
    API_URL = "https://api.bfrdernek.com"  # Production
    # API_URL = "http://157.90.154.48:8080/api"  # Development
    
    CACHE_FILE = "license_cache.json"
    OFFLINE_DAYS = 30  # Offline çalışma süresi
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Args:
            config_dir: Yapılandırma dosyalarının saklanacağı dizin
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Platform'a göre varsayılan konum
            if sys.platform == "win32":
                self.config_dir = Path(os.environ.get("APPDATA", "")) / "BADER"
            elif sys.platform == "darwin":
                self.config_dir = Path.home() / "Library" / "Application Support" / "BADER"
            else:
                self.config_dir = Path.home() / ".bader"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = self.config_dir / self.CACHE_FILE
        
        self.current_license: Optional[LicenseInfo] = None
        self.is_offline = False
        self.last_error: Optional[str] = None
    
    def verify(self, customer_id: str, app_version: str = "3.0.0") -> LicenseInfo:
        """
        Lisansı doğrula
        
        1. Online doğrulamayı dene
        2. Başarısız olursa önbellekten kontrol et
        
        Returns:
            LicenseInfo: Doğrulanmış lisans bilgisi
            
        Raises:
            LicenseError: Lisans geçersiz veya bulunamadı
        """
        self.last_error = None
        
        # Önce online doğrulamayı dene
        try:
            license_info = self._verify_online(customer_id, app_version)
            self._cache_license(license_info)
            self.current_license = license_info
            self.is_offline = False
            return license_info
        except requests.RequestException as e:
            # Ağ hatası - offline moda geç
            self.is_offline = True
            self.last_error = f"Ağ hatası: {str(e)}"
        except LicenseError:
            raise
        
        # Önbellekten kontrol et
        cached = self._get_cached_license()
        if cached and cached.customer_id == customer_id:
            if self._is_cache_valid(cached):
                self.current_license = cached
                return cached
            else:
                raise LicenseError(
                    "OFFLINE_EXPIRED",
                    f"Offline süre doldu. İnternet bağlantısı gerekli."
                )
        
        raise LicenseError("VERIFICATION_FAILED", "Lisans doğrulanamadı")
    
    def _verify_online(self, customer_id: str, app_version: str) -> LicenseInfo:
        """API üzerinden lisans doğrula"""
        os_info = f"{platform.system()} {platform.release()}"
        
        response = requests.post(
            f"{self.API_URL}/license/verify",
            json={
                "customer_id": customer_id,
                "app_version": app_version,
                "os_info": os_info
            },
            timeout=10
        )
        
        data = response.json()
        
        if not data.get("valid"):
            error_code = data.get("error", "UNKNOWN")
            message = data.get("message", "Bilinmeyen hata")
            raise LicenseError(error_code, message)
        
        license_data = data["license"]
        
        return LicenseInfo(
            customer_id=license_data["customer_id"],
            organization_name=license_data["organization_name"],
            license_type=license_data["license_type"],
            license_status=license_data["license_status"],
            license_end=license_data["license_end"],
            days_remaining=license_data["days_remaining"],
            max_users=license_data["max_users"],
            max_members=license_data["max_members"],
            features=license_data.get("features", {})
        )
    
    def _cache_license(self, license_info: LicenseInfo):
        """Lisans bilgisini önbelleğe kaydet"""
        cache_data = {
            "license": license_info.to_dict(),
            "cached_at": datetime.now().isoformat(),
            "machine_id": self._get_machine_id()
        }
        
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    def _get_cached_license(self) -> Optional[LicenseInfo]:
        """Önbellekten lisans bilgisi al"""
        if not self.cache_path.exists():
            return None
        
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # Makine kontrolü
            if cache_data.get("machine_id") != self._get_machine_id():
                return None
            
            license_data = cache_data["license"]
            return LicenseInfo(**license_data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
    
    def _is_cache_valid(self, cached: LicenseInfo) -> bool:
        """Önbelleğin geçerli olup olmadığını kontrol et"""
        if not self.cache_path.exists():
            return False
        
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            cached_at = datetime.fromisoformat(cache_data["cached_at"])
            offline_limit = datetime.now() - timedelta(days=self.OFFLINE_DAYS)
            
            # LOCAL lisanslar için daha uzun offline süre
            if cached.license_type == "LOCAL":
                offline_limit = datetime.now() - timedelta(days=90)
            
            return cached_at > offline_limit and cached.is_valid()
        except (json.JSONDecodeError, KeyError, ValueError):
            return False
    
    def _get_machine_id(self) -> str:
        """Benzersiz makine kimliği oluştur"""
        info = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
        return hashlib.md5(info.encode()).hexdigest()[:16]
    
    def get_database_mode(self) -> str:
        """
        Lisans tipine göre veritabanı modunu belirle
        
        Returns:
            str: 'sqlite', 'api' veya 'hybrid'
        """
        if not self.current_license:
            return "sqlite"  # Varsayılan
        
        if self.current_license.license_type in ["LOCAL", "DEMO"]:
            return "sqlite"
        elif self.current_license.license_type == "ONLINE":
            return "api"
        else:  # HYBRID
            return "hybrid"
    
    def get_license_type(self) -> str:
        """Aktif lisans tipini döndür"""
        if self.current_license:
            return self.current_license.license_type
        return "UNKNOWN"
    
    def get_organization_name(self) -> str:
        """Kurum adını döndür"""
        if self.current_license:
            return self.current_license.organization_name
        return ""
    
    def get_days_remaining(self) -> int:
        """Kalan gün sayısını döndür"""
        if self.current_license:
            return self.current_license.days_remaining
        return 0
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Belirli bir özelliğin aktif olup olmadığını kontrol et"""
        if not self.current_license:
            return False
        return self.current_license.features.get(feature, False)
    
    def clear_cache(self):
        """Önbelleği temizle"""
        if self.cache_path.exists():
            self.cache_path.unlink()
        self.current_license = None


class LicenseError(Exception):
    """Lisans hatası"""
    
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")
    
    def get_user_message(self) -> str:
        """Kullanıcıya gösterilecek mesaj"""
        messages = {
            "LICENSE_NOT_FOUND": "Lisans bulunamadı. Lütfen lisans kodunuzu kontrol edin.",
            "LICENSE_EXPIRED": "Lisans süreniz dolmuş. Lütfen lisansınızı yenileyin.",
            "LICENSE_SUSPENDED": "Lisansınız askıya alınmış. Destek ile iletişime geçin.",
            "OFFLINE_EXPIRED": "Offline kullanım süresi doldu. İnternet bağlantısı gerekli.",
            "VERIFICATION_FAILED": "Lisans doğrulanamadı. İnternet bağlantınızı kontrol edin.",
            "NETWORK_ERROR": "Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin."
        }
        return messages.get(self.code, self.message)


# Test
if __name__ == "__main__":
    manager = LicenseManager()
    
    try:
        # Test lisansı
        license_info = manager.verify("BADER-2024-DEMO-0001", "3.0.0")
        print(f"✅ Lisans doğrulandı:")
        print(f"   Kurum: {license_info.organization_name}")
        print(f"   Tip: {license_info.license_type}")
        print(f"   Kalan gün: {license_info.days_remaining}")
        print(f"   Veritabanı modu: {manager.get_database_mode()}")
    except LicenseError as e:
        print(f"❌ Lisans hatası: {e.get_user_message()}")
