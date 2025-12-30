"""
BADER - Server İstemci Modülü
Desktop uygulaması ile server arasındaki iletişimi yönetir.
"""

import os
import json
import hashlib
import platform
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass


# Uygulama Versiyonu
APP_VERSION = "1.0.0"

# Server Yapılandırması
DEFAULT_SERVER_URL = "http://157.90.154.48:8080/api"
CONFIG_FILE = "bader_config.json"


@dataclass
class ServerConfig:
    """Server yapılandırma bilgileri"""
    server_url: str = DEFAULT_SERVER_URL
    customer_id: Optional[str] = None
    api_key: Optional[str] = None
    auto_backup: bool = True
    auto_update: bool = True
    last_backup: Optional[str] = None
    last_update_check: Optional[str] = None


class ServerClient:
    """
    BADER Server İstemcisi
    - Müşteri kimlik doğrulama
    - Yedekleme gönderme
    - Güncelleme kontrolü
    - OCR hizmeti
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_config_path()
        self.config = self._load_config()
        self._session = requests.Session()
        
    def _get_config_path(self) -> str:
        """Yapılandırma dosya yolunu al"""
        # Uygulama dizininde
        app_dir = Path(__file__).parent
        return str(app_dir / CONFIG_FILE)
    
    def _load_config(self) -> ServerConfig:
        """Yapılandırmayı yükle"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return ServerConfig(**data)
            except Exception:
                pass
        return ServerConfig()
    
    def _save_config(self):
        """Yapılandırmayı kaydet"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'server_url': self.config.server_url,
                    'customer_id': self.config.customer_id,
                    'api_key': self.config.api_key,
                    'auto_backup': self.config.auto_backup,
                    'auto_update': self.config.auto_update,
                    'last_backup': self.config.last_backup,
                    'last_update_check': self.config.last_update_check,
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Config kaydetme hatası: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """API istekleri için header'lar"""
        headers = {'Content-Type': 'application/json'}
        if self.config.api_key:
            headers['X-API-Key'] = self.config.api_key
        return headers
    
    def _get_device_info(self) -> Dict[str, str]:
        """Cihaz bilgilerini al"""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'machine': platform.machine(),
            'hostname': platform.node(),
        }
    
    # ==================== Bağlantı Yönetimi ====================
    
    def is_configured(self) -> bool:
        """Server yapılandırılmış mı?"""
        return bool(self.config.customer_id and self.config.api_key)
    
    def test_connection(self) -> Tuple[bool, str]:
        """Server bağlantısını test et"""
        try:
            response = self._session.get(
                f"{self.config.server_url}/health",
                timeout=10
            )
            if response.status_code == 200:
                return True, "Bağlantı başarılı"
            return False, f"Server hatası: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Server'a bağlanılamadı"
        except requests.exceptions.Timeout:
            return False, "Bağlantı zaman aşımına uğradı"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    # ==================== Müşteri Kayıt/Aktivasyon ====================
    
    def activate_license(self, license_key: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Lisans anahtarı ile aktivasyon
        Returns: (başarılı, mesaj, müşteri_bilgisi)
        """
        try:
            response = self._session.post(
                f"{self.config.server_url}/activate",
                json={
                    'license_key': license_key,
                    'device_info': self._get_device_info()
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Yapılandırmayı güncelle
                self.config.customer_id = data.get('customer_id')
                self.config.api_key = data.get('api_key')
                self._save_config()
                return True, "Aktivasyon başarılı!", data
            else:
                error = response.json().get('detail', 'Bilinmeyen hata')
                return False, f"Aktivasyon hatası: {error}", None
                
        except requests.exceptions.ConnectionError:
            return False, "Server'a bağlanılamadı", None
        except Exception as e:
            return False, f"Hata: {str(e)}", None
    
    def validate_api_key(self) -> Tuple[bool, str]:
        """Mevcut API anahtarını doğrula"""
        if not self.config.api_key:
            return False, "API anahtarı yapılandırılmamış"
        
        try:
            response = self._session.get(
                f"{self.config.server_url}/validate",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "API anahtarı geçerli"
            elif response.status_code == 401:
                return False, "API anahtarı geçersiz"
            else:
                return False, f"Doğrulama hatası: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Server'a bağlanılamadı"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    # ==================== Yedekleme ====================
    
    def upload_backup(self, db_path: str) -> Tuple[bool, str]:
        """
        Veritabanı yedeğini server'a gönder
        """
        if not self.is_configured():
            return False, "Server yapılandırılmamış"
        
        if not os.path.exists(db_path):
            return False, "Veritabanı dosyası bulunamadı"
        
        try:
            # Dosya hash'i
            with open(db_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Dosyayı gönder
            with open(db_path, 'rb') as f:
                files = {'file': ('backup.db', f, 'application/octet-stream')}
                headers = {'X-API-Key': self.config.api_key}
                
                response = self._session.post(
                    f"{self.config.server_url}/backup",
                    files=files,
                    headers=headers,
                    data={'file_hash': file_hash},
                    timeout=120
                )
            
            if response.status_code == 200:
                self.config.last_backup = datetime.now().isoformat()
                self._save_config()
                return True, "Yedekleme başarılı"
            else:
                error = response.json().get('detail', 'Bilinmeyen hata')
                return False, f"Yedekleme hatası: {error}"
                
        except requests.exceptions.ConnectionError:
            return False, "Server'a bağlanılamadı"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def get_backup_history(self) -> Tuple[bool, str, list]:
        """Yedekleme geçmişini al"""
        if not self.is_configured():
            return False, "Server yapılandırılmamış", []
        
        try:
            response = self._session.get(
                f"{self.config.server_url}/backup/history",
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, "Başarılı", data.get('backups', [])
            else:
                return False, f"Hata: {response.status_code}", []
                
        except Exception as e:
            return False, f"Hata: {str(e)}", []
    
    def restore_backup(self, backup_id: str, target_path: str) -> Tuple[bool, str]:
        """Server'dan yedek indir"""
        if not self.is_configured():
            return False, "Server yapılandırılmamış"
        
        try:
            response = self._session.get(
                f"{self.config.server_url}/backup/{backup_id}/download",
                headers=self._get_headers(),
                timeout=120,
                stream=True
            )
            
            if response.status_code == 200:
                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True, "Yedek indirildi"
            else:
                return False, f"İndirme hatası: {response.status_code}"
                
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    # ==================== Güncelleme ====================
    
    def check_update(self, current_version: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Güncelleme kontrolü
        Returns: (güncelleme_var, mesaj, güncelleme_bilgisi)
        """
        if not self.is_configured():
            return False, "Server yapılandırılmamış", None
        
        try:
            # GET request ile güncelleme kontrolü
            response = self._session.get(
                f"{self.config.server_url}/version/check",
                params={
                    'current_version': current_version,
                    'platform': platform.system().lower()
                },
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.config.last_update_check = datetime.now().isoformat()
                self._save_config()
                
                if data.get('has_update'):
                    return True, f"Yeni sürüm mevcut: {data.get('latest_version')}", data
                else:
                    return False, "Güncel sürümü kullanıyorsunuz", None
            else:
                return False, f"Kontrol hatası: {response.status_code}", None
                
        except requests.exceptions.ConnectionError:
            return False, "Server'a bağlanılamadı", None
        except Exception as e:
            return False, f"Hata: {str(e)}", None
    
    def download_update(self, download_url: str, target_path: str, 
                        progress_callback=None) -> Tuple[bool, str]:
        """Güncelleme dosyasını indir"""
        try:
            response = self._session.get(
                download_url,
                headers=self._get_headers(),
                timeout=300,
                stream=True
            )
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size:
                            progress = int((downloaded / total_size) * 100)
                            progress_callback(progress)
                
                return True, "Güncelleme indirildi"
            else:
                return False, f"İndirme hatası: {response.status_code}"
                
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    # ==================== OCR Hizmeti ====================
    
    def ocr_process(self, image_path: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Görüntüden OCR işlemi
        Returns: (başarılı, mesaj, sonuç)
        """
        if not self.is_configured():
            return False, "Server yapılandırılmamış", None
        
        if not os.path.exists(image_path):
            return False, "Dosya bulunamadı", None
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                headers = {'X-API-Key': self.config.api_key}
                
                response = self._session.post(
                    f"{self.config.server_url}/ocr",
                    files=files,
                    headers=headers,
                    timeout=120
                )
            
            if response.status_code == 200:
                data = response.json()
                return True, "OCR başarılı", data
            else:
                error = response.json().get('detail', 'Bilinmeyen hata')
                return False, f"OCR hatası: {error}", None
                
        except requests.exceptions.ConnectionError:
            return False, "Server'a bağlanılamadı", None
        except Exception as e:
            return False, f"Hata: {str(e)}", None
    
    # ==================== İstatistikler ====================
    
    def get_usage_stats(self) -> Tuple[bool, str, Optional[Dict]]:
        """Kullanım istatistiklerini al"""
        if not self.is_configured():
            return False, "Server yapılandırılmamış", None
        
        try:
            response = self._session.get(
                f"{self.config.server_url}/stats",
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return True, "Başarılı", response.json()
            else:
                return False, f"Hata: {response.status_code}", None
                
        except Exception as e:
            return False, f"Hata: {str(e)}", None
    
    # ==================== Yapılandırma ====================
    
    def set_server_url(self, url: str):
        """Server URL'ini değiştir"""
        self.config.server_url = url.rstrip('/')
        self._save_config()
    
    def set_auto_backup(self, enabled: bool):
        """Otomatik yedeklemeyi aç/kapat"""
        self.config.auto_backup = enabled
        self._save_config()
    
    def set_auto_update(self, enabled: bool):
        """Otomatik güncellemeyi aç/kapat"""
        self.config.auto_update = enabled
        self._save_config()
    
    def clear_credentials(self):
        """Kimlik bilgilerini temizle"""
        self.config.customer_id = None
        self.config.api_key = None
        self._save_config()
    
    def get_customer_info(self) -> Dict[str, Any]:
        """Müşteri bilgilerini döndür"""
        return {
            'customer_id': self.config.customer_id,
            'server_url': self.config.server_url,
            'auto_backup': self.config.auto_backup,
            'auto_update': self.config.auto_update,
            'last_backup': self.config.last_backup,
            'last_update_check': self.config.last_update_check,
            'is_configured': self.is_configured()
        }
    
    # ==================== Sunucu Senkronizasyonu ====================
    
    def sync_get_uyeler(self) -> Tuple[bool, list]:
        """Sunucudan üyeleri çek"""
        if not self.is_configured():
            return False, []
        try:
            response = self._session.get(
                f"{self.config.server_url}/dernek/uyeler",
                params={'customer_id': self.config.customer_id},
                headers=self._get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return True, response.json()
            return False, []
        except Exception as e:
            print(f"Sync uyeler hatası: {e}")
            return False, []
    
    def sync_get_gelirler(self) -> Tuple[bool, list]:
        """Sunucudan gelirleri çek"""
        if not self.is_configured():
            return False, []
        try:
            response = self._session.get(
                f"{self.config.server_url}/dernek/gelirler",
                params={'customer_id': self.config.customer_id},
                headers=self._get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return True, response.json()
            return False, []
        except Exception as e:
            print(f"Sync gelirler hatası: {e}")
            return False, []
    
    def sync_get_giderler(self) -> Tuple[bool, list]:
        """Sunucudan giderleri çek"""
        if not self.is_configured():
            return False, []
        try:
            response = self._session.get(
                f"{self.config.server_url}/dernek/giderler",
                params={'customer_id': self.config.customer_id},
                headers=self._get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return True, response.json()
            return False, []
        except Exception as e:
            print(f"Sync giderler hatası: {e}")
            return False, []
    
    def sync_get_ozet(self) -> Tuple[bool, dict]:
        """Sunucudan özet bilgileri çek"""
        if not self.is_configured():
            return False, {}
        try:
            response = self._session.get(
                f"{self.config.server_url}/dernek/ozet",
                params={'customer_id': self.config.customer_id},
                headers=self._get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return True, response.json()
            return False, {}
        except Exception as e:
            print(f"Sync özet hatası: {e}")
            return False, {}
    
    def sync_add_gelir(self, tarih: str, tur: str, aciklama: str, tutar: float) -> Tuple[bool, str]:
        """Sunucuya gelir ekle"""
        if not self.is_configured():
            return False, "Sunucu yapılandırılmamış"
        try:
            response = self._session.post(
                f"{self.config.server_url}/dernek/gelirler",
                params={'customer_id': self.config.customer_id},
                json={
                    'tarih': tarih,
                    'tur': tur,
                    'aciklama': aciklama,
                    'tutar': tutar,
                    'kaynak': 'desktop'
                },
                headers=self._get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return True, "Gelir sunucuya kaydedildi"
            return False, f"Hata: {response.status_code}"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def sync_add_gider(self, tarih: str, tur: str, aciklama: str, tutar: float) -> Tuple[bool, str]:
        """Sunucuya gider ekle"""
        if not self.is_configured():
            return False, "Sunucu yapılandırılmamış"
        try:
            response = self._session.post(
                f"{self.config.server_url}/dernek/giderler",
                params={'customer_id': self.config.customer_id},
                json={
                    'tarih': tarih,
                    'tur': tur,
                    'aciklama': aciklama,
                    'tutar': tutar,
                    'kaynak': 'desktop'
                },
                headers=self._get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return True, "Gider sunucuya kaydedildi"
            return False, f"Hata: {response.status_code}"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def sync_add_uye(self, uye_data: dict) -> Tuple[bool, str]:
        """Sunucuya üye ekle"""
        if not self.is_configured():
            return False, "Sunucu yapılandırılmamış"
        try:
            response = self._session.post(
                f"{self.config.server_url}/dernek/uyeler",
                params={'customer_id': self.config.customer_id},
                json=uye_data,
                headers=self._get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return True, "Üye sunucuya kaydedildi"
            return False, f"Hata: {response.status_code}"
        except Exception as e:
            return False, f"Hata: {str(e)}"


# Singleton instance
_server_client: Optional[ServerClient] = None


def get_server_client() -> ServerClient:
    """Global server client instance"""
    global _server_client
    if _server_client is None:
        _server_client = ServerClient()
    return _server_client
