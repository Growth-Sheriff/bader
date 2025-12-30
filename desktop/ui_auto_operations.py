"""
BADER - Otomatik İşlemler Modülü
Başlangıçta güncelleme kontrolü ve kapanışta yedekleme
"""

import os
import sys
from typing import Optional, Tuple
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication


class UpdateCheckWorker(QThread):
    """Güncelleme kontrolü için arka plan thread'i"""
    finished = pyqtSignal(bool, str, object)
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        try:
            from server_client import get_server_client
            client = get_server_client()
            
            if not client.is_configured():
                self.finished.emit(False, "Server yapılandırılmamış", None)
                return
            
            success, message, result = client.check_update(self.current_version)
            self.finished.emit(success, message, result)
            
        except Exception as e:
            self.finished.emit(False, str(e), None)


class BackupWorker(QThread):
    """Yedekleme için arka plan thread'i"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
    
    def run(self):
        try:
            self.progress.emit("Yedekleme hazırlanıyor...")
            
            from server_client import get_server_client
            client = get_server_client()
            
            if not client.is_configured():
                self.finished.emit(False, "Server yapılandırılmamış")
                return
            
            # Otomatik yedekleme açık mı kontrol et
            if not client.config.auto_backup:
                self.finished.emit(True, "Otomatik yedekleme kapalı")
                return
            
            self.progress.emit("Sunucuya gönderiliyor...")
            success, message = client.upload_backup(self.db_path)
            self.finished.emit(success, message)
            
        except Exception as e:
            self.finished.emit(False, str(e))


class AutoOperationsManager:
    """
    Otomatik işlemleri yöneten sınıf
    - Başlangıçta güncelleme kontrolü
    - Kapanışta yedekleme
    """
    
    def __init__(self, app: QApplication, db_path: str, version: str):
        self.app = app
        self.db_path = db_path
        self.version = version
        self.update_worker = None
        self.backup_worker = None
        self._update_available = None
        
        # Uygulama kapanırken yedekle
        self.app.aboutToQuit.connect(self.on_app_closing)
    
    def check_update_async(self, callback=None):
        """
        Arka planda güncelleme kontrolü yap
        callback(has_update: bool, version: str, url: str)
        """
        self.update_worker = UpdateCheckWorker(self.version)
        
        def on_finished(success, message, result):
            if success and result:
                has_update = result.get('has_update', False)
                new_version = result.get('latest_version', '')
                download_url = result.get('download_url', '')
                
                self._update_available = {
                    'has_update': has_update,
                    'version': new_version,
                    'url': download_url,
                    'changelog': result.get('changelog', '')
                }
                
                if callback:
                    callback(has_update, new_version, download_url)
            else:
                if callback:
                    callback(False, '', '')
        
        self.update_worker.finished.connect(on_finished)
        self.update_worker.start()
    
    def backup_sync(self) -> Tuple[bool, str]:
        """Senkron yedekleme (kapanışta kullanılır)"""
        try:
            from server_client import get_server_client
            client = get_server_client()
            
            if not client.is_configured():
                return False, "Server yapılandırılmamış"
            
            if not client.config.auto_backup:
                return True, "Otomatik yedekleme kapalı"
            
            return client.upload_backup(self.db_path)
            
        except Exception as e:
            return False, str(e)
    
    def on_app_closing(self):
        """Uygulama kapanırken çağrılır"""
        # Senkron yedekleme yap (kapanış engellenmez)
        try:
            success, message = self.backup_sync()
            if success:
                print(f"[BADER] Otomatik yedekleme: {message}")
            else:
                print(f"[BADER] Yedekleme hatası: {message}")
        except Exception as e:
            print(f"[BADER] Yedekleme exception: {e}")
    
    def get_update_info(self) -> Optional[dict]:
        """Güncelleme bilgisini al"""
        return self._update_available


def show_update_dialog(parent, update_info: dict):
    """Güncelleme diyaloğu göster"""
    from qfluentwidgets import MessageBox
    
    # Sunucudan gelen field isimleri
    version = update_info.get('latest_version') or update_info.get('version', '')
    changelog = update_info.get('changelog', '')
    url = update_info.get('download_url') or update_info.get('url', '')
    is_critical = update_info.get('is_critical', False)
    
    msg = f"🎉 Yeni sürüm mevcut: v{version}\n\n"
    if changelog:
        msg += f"📋 Değişiklikler:\n{changelog[:500]}\n\n"
    if is_critical:
        msg += "⚠️ Bu kritik bir güncelleme!\n\n"
    msg += "Şimdi güncellemek ister misiniz?"
    
    dialog = MessageBox(
        "🔄 Güncelleme Mevcut",
        msg,
        parent
    )
    
    if dialog.exec():
        # Güncelleme indir
        if url:
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(url))
            
            # Bilgi mesajı
            MessageBox(
                "İndirme Başlatıldı",
                f"Güncelleme indirme sayfası açıldı.\n\nURL: {url}",
                parent
            ).show()


def startup_update_check(parent, version: str, callback=None):
    """
    Başlangıçta güncelleme kontrolü yap
    5 saniye sonra arka planda çalışır
    """
    def delayed_check():
        try:
            from server_client import get_server_client
            client = get_server_client()
            
            if not client.is_configured():
                return
            
            if not client.config.auto_update:
                return
            
            success, message, result = client.check_update(version)
            
            if success and result and result.get('has_update'):
                # Ana thread'de dialog göster
                QTimer.singleShot(0, lambda: show_update_dialog(parent, result))
                
            if callback:
                callback(success, result)
                
        except Exception as e:
            print(f"[BADER] Güncelleme kontrolü hatası: {e}")
    
    # 5 saniye sonra kontrol et (uygulama açılsın)
    QTimer.singleShot(5000, delayed_check)
