"""
BADER Auto Updater
Otomatik güncelleme kontrolü ve yükleme
"""

import os
import sys
import json
import hashlib
import tempfile
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import requests


@dataclass
class UpdateInfo:
    """Güncelleme bilgisi"""
    version: str
    download_url: str
    file_size: int
    release_notes: str
    is_mandatory: bool
    checksum: Optional[str] = None
    
    def size_mb(self) -> float:
        return self.file_size / (1024 * 1024) if self.file_size else 0


class AutoUpdater:
    """
    Otomatik güncelleme yöneticisi
    - Versiyon kontrolü
    - İndirme ve doğrulama
    - Kurulum başlatma
    """
    
    API_URL = "https://api.bfrdernek.com"
    # API_URL = "http://157.90.154.48:8080/api"  # Dev
    
    def __init__(self, current_version: str, config_dir: Optional[str] = None):
        """
        Args:
            current_version: Mevcut uygulama versiyonu (örn: "3.0.0")
            config_dir: İndirme klasörü
        """
        self.current_version = current_version
        self.platform = self._detect_platform()
        
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(tempfile.gettempdir()) / "bader_updates"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.latest_update: Optional[UpdateInfo] = None
        self.download_progress = 0
        self.is_downloading = False
    
    def _detect_platform(self) -> str:
        """Platform tespit et"""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        else:
            return "linux"
    
    def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Güncelleme kontrolü yap
        
        Returns:
            UpdateInfo: Yeni güncelleme varsa bilgisi, yoksa None
        """
        try:
            response = requests.get(
                f"{self.API_URL}/license/check-update",
                params={
                    "current_version": self.current_version,
                    "platform": self.platform
                },
                timeout=10
            )
            
            data = response.json()
            
            if data.get("update_available"):
                self.latest_update = UpdateInfo(
                    version=data["version"],
                    download_url=data["download_url"],
                    file_size=data.get("file_size", 0),
                    release_notes=data.get("release_notes", ""),
                    is_mandatory=data.get("is_mandatory", False),
                    checksum=data.get("checksum")
                )
                return self.latest_update
            
            return None
        except requests.RequestException as e:
            print(f"Güncelleme kontrolü hatası: {e}")
            return None
    
    def _parse_version(self, version: str) -> tuple:
        """Versiyon string'ini tuple'a çevir"""
        try:
            parts = version.replace("-", ".").split(".")
            return tuple(int(p) for p in parts[:3])
        except (ValueError, AttributeError):
            return (0, 0, 0)
    
    def is_update_available(self) -> bool:
        """Güncelleme mevcut mu?"""
        if not self.latest_update:
            self.check_for_updates()
        
        if self.latest_update:
            current = self._parse_version(self.current_version)
            latest = self._parse_version(self.latest_update.version)
            return latest > current
        
        return False
    
    def download_update(self, progress_callback=None) -> Optional[Path]:
        """
        Güncellemeyi indir
        
        Args:
            progress_callback: İlerleme callback fonksiyonu (percent, downloaded, total)
            
        Returns:
            Path: İndirilen dosya yolu
        """
        if not self.latest_update:
            raise UpdateError("İndirilecek güncelleme yok")
        
        self.is_downloading = True
        self.download_progress = 0
        
        # Dosya adını URL'den al
        filename = self.latest_update.download_url.split("/")[-1]
        if not filename.endswith((".dmg", ".exe", ".zip", ".tar.gz", ".AppImage")):
            filename = f"BADER_{self.latest_update.version}_{self.platform}"
            if self.platform == "windows":
                filename += ".exe"
            elif self.platform == "macos":
                filename += ".dmg"
            else:
                filename += ".tar.gz"
        
        download_path = self.config_dir / filename
        
        try:
            response = requests.get(
                self.latest_update.download_url,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            
            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            self.download_progress = int((downloaded / total_size) * 100)
                            if progress_callback:
                                progress_callback(self.download_progress, downloaded, total_size)
            
            # Checksum doğrulama
            if self.latest_update.checksum:
                if not self._verify_checksum(download_path, self.latest_update.checksum):
                    download_path.unlink()
                    raise UpdateError("Dosya doğrulaması başarısız")
            
            self.is_downloading = False
            return download_path
            
        except requests.RequestException as e:
            self.is_downloading = False
            raise UpdateError(f"İndirme hatası: {str(e)}")
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """SHA256 checksum doğrula"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest().lower() == expected_checksum.lower()
    
    def install_update(self, installer_path: Path, restart: bool = True) -> bool:
        """
        Güncellemeyi kur
        
        Args:
            installer_path: İndirilen dosya yolu
            restart: Kurulumdan sonra uygulamayı yeniden başlat
            
        Returns:
            bool: Başarılı mı
        """
        if not installer_path.exists():
            raise UpdateError("Kurulum dosyası bulunamadı")
        
        try:
            if self.platform == "windows":
                # Windows: Installer'ı çalıştır
                subprocess.Popen(
                    [str(installer_path)],
                    creationflags=subprocess.DETACHED_PROCESS
                )
                
            elif self.platform == "macos":
                # macOS: DMG'yi mount et veya app'i kopyala
                if installer_path.suffix == ".dmg":
                    # DMG mount et ve içindeki .app'i kopyala
                    mount_point = self._mount_dmg(installer_path)
                    if mount_point:
                        # Applications'a kopyala
                        app_path = list(Path(mount_point).glob("*.app"))[0]
                        dest = Path("/Applications") / app_path.name
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(app_path, dest)
                        self._unmount_dmg(mount_point)
                else:
                    # Doğrudan uygulama klasörüne kopyala
                    subprocess.run(["open", str(installer_path)])
                    
            else:
                # Linux: tar.gz veya AppImage
                if installer_path.suffix == ".AppImage":
                    os.chmod(installer_path, 0o755)
                    subprocess.Popen([str(installer_path)])
                else:
                    # tar.gz: Çıkart ve çalıştır
                    subprocess.run(["tar", "-xzf", str(installer_path), "-C", str(self.config_dir)])
            
            if restart:
                self._restart_app()
            
            return True
            
        except Exception as e:
            raise UpdateError(f"Kurulum hatası: {str(e)}")
    
    def _mount_dmg(self, dmg_path: Path) -> Optional[str]:
        """macOS: DMG mount et"""
        try:
            result = subprocess.run(
                ["hdiutil", "attach", str(dmg_path), "-nobrowse", "-quiet"],
                capture_output=True,
                text=True
            )
            # Mount point'i bul
            for line in result.stdout.split("\n"):
                if "/Volumes/" in line:
                    return line.split("\t")[-1].strip()
        except:
            pass
        return None
    
    def _unmount_dmg(self, mount_point: str):
        """macOS: DMG unmount et"""
        try:
            subprocess.run(["hdiutil", "detach", mount_point, "-quiet"])
        except:
            pass
    
    def _restart_app(self):
        """Uygulamayı yeniden başlat"""
        if self.platform == "windows":
            # Windows'ta yeniden başlat
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            # Unix: exec ile kendini yeniden çalıştır
            os.execl(sys.executable, sys.executable, *sys.argv)
    
    def cleanup(self):
        """Eski güncelleme dosyalarını temizle"""
        try:
            for file in self.config_dir.glob("*"):
                if file.is_file():
                    file.unlink()
        except:
            pass
    
    def get_release_notes(self) -> str:
        """Sürüm notlarını getir"""
        if self.latest_update:
            return self.latest_update.release_notes
        return ""


class UpdateError(Exception):
    """Güncelleme hatası"""
    pass


# GUI Dialog için yardımcı fonksiyonlar
def show_update_dialog(update_info: UpdateInfo) -> bool:
    """
    Güncelleme dialog'u göster (GUI entegrasyonu için)
    Bu fonksiyon GUI framework'üne göre override edilebilir
    """
    print(f"\n{'='*50}")
    print(f"YENİ GÜNCELLEME MEVCUT!")
    print(f"{'='*50}")
    print(f"Mevcut Versiyon: {update_info.version}")
    print(f"Boyut: {update_info.size_mb():.1f} MB")
    print(f"Zorunlu: {'Evet' if update_info.is_mandatory else 'Hayır'}")
    print(f"\nSürüm Notları:")
    print(update_info.release_notes or "Yeni özellikler ve hata düzeltmeleri")
    print(f"{'='*50}\n")
    
    if update_info.is_mandatory:
        return True
    
    response = input("Güncellemek ister misiniz? (E/H): ")
    return response.lower() in ["e", "evet", "y", "yes"]


# Test
if __name__ == "__main__":
    updater = AutoUpdater("2.9.0")
    
    print(f"Platform: {updater.platform}")
    print(f"Mevcut versiyon: {updater.current_version}")
    
    update = updater.check_for_updates()
    
    if update:
        print(f"\n✅ Güncelleme mevcut: v{update.version}")
        print(f"   Boyut: {update.size_mb():.1f} MB")
        print(f"   Zorunlu: {update.is_mandatory}")
        
        if show_update_dialog(update):
            def progress(percent, downloaded, total):
                mb_down = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                print(f"\r   İndiriliyor: {percent}% ({mb_down:.1f}/{mb_total:.1f} MB)", end="")
            
            try:
                path = updater.download_update(progress)
                print(f"\n   İndirildi: {path}")
            except UpdateError as e:
                print(f"\n   Hata: {e}")
    else:
        print("✅ Uygulama güncel")
