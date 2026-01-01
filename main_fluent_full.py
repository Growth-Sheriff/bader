"""
BADER Derneği - Ana Pencere (Windows 11 Fluent Design - TAM ENTEGRASYON)
v1.0.0 - İzin kontrolü, OCR, Otomatik backup ve güncelleme
"""

import sys
import os

# Matplotlib backend'ini herhangi bir Qt import'undan ÖNCE ayarla
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from qfluentwidgets import (FluentWindow, NavigationItemPosition, FluentIcon as FIF,
                            MessageBox, setTheme, Theme, CardWidget, TitleLabel, 
                            SubtitleLabel, BodyLabel, PushButton, NavigationAvatarWidget)
from database import Database
from ui_login import LoginWidget, session

# Import tüm widget'lar
from ui_dashboard import DashboardWidget
from ui_uyeler import UyeWidget
from ui_uyeler_ayrilan import AyrilanUyelerWidget
from ui_uye_detay import UyeDetayWidget
from ui_uye_aidat import UyeAidatWidget
from ui_aidat import AidatWidget
from ui_gelir import GelirWidget
from ui_gider import GiderWidget
from ui_virman import VirmanWidget
from ui_kasa import KasaWidget
from ui_devir import DevirWidget
from ui_export import ExportWidget
from ui_raporlar import RaporlarWidget
from ui_tahakkuk_rapor import TahakkukRaporWidget
from ui_butce import ButceWidget
from ui_etkinlik import EtkinlikWidget
from ui_toplanti import ToplantiWidget
from ui_kullanicilar import KullanicilarWidget
from ui_ayarlar import AyarlarWidget
from ui_belgeler import BelgelerWidget
from ui_ocr import OCRWidget
from ui_arama import GelismisAramaWidget
# Köy modülleri
from ui_koy_dashboard import KoyDashboardWidget
from ui_koy_islemler import KoyGelirWidget, KoyGiderWidget, KoyKasaWidget, KoyVirmanWidget


class FluentBADERWindow(FluentWindow):
    """Ana BADER penceresi - Windows 11 Fluent Design"""
    
    def __init__(self, db: Database, kullanici: dict):
        super().__init__()
        self.db = db
        self.kullanici = kullanici
        session.set_user(kullanici)
        
        self.setWindowTitle("BADER - Dernek Yönetim Sistemi")
        
        # Ekran boyutuna göre pencere boyutu ayarla (MacBook 13" desteği)
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().availableGeometry()
        
        # Ekran genişliğinin %90'ı, yüksekliğinin %85'i
        width = min(1400, int(screen.width() * 0.90))
        height = min(850, int(screen.height() * 0.85))
        self.resize(width, height)
        
        # Minimum boyut (çok küçülmesin)
        self.setMinimumSize(1024, 600)
        
        # Windows 11 Mica effect
        self.setMicaEffectEnabled(True)
        
        # Sol menüyü varsayılan olarak açık tut
        self.navigationInterface.setExpandWidth(200)
        self.navigationInterface.expand(useAni=False)
        
        # Üye detay/aidat widget'ları (navigation dışı)
        self.uye_detay_widget = UyeDetayWidget(self.db)
        self.uye_detay_widget.setObjectName("uye_detay_widget")
        
        self.uye_aidat_widget = UyeAidatWidget(self.db)
        self.uye_aidat_widget.setObjectName("uye_aidat_widget")
        
        self.setup_navigation()
        self.setup_signals()
        
    def setup_navigation(self):
        """Navigasyon menüsünü oluştur - TAM MENÜ"""
        
        # ========== ANA MENÜ ==========
        self.navigationInterface.addSeparator()
        
        # Dashboard
        self.dashboard_widget = DashboardWidget(self.db)
        self.dashboard_widget.setObjectName("dashboard_widget")
        self.addSubInterface(
            self.dashboard_widget,
            FIF.HOME,
            'Dashboard',
            NavigationItemPosition.TOP
        )
        
        # Gelişmiş Arama
        self.arama_widget = GelismisAramaWidget(self.db)
        self.arama_widget.setObjectName("arama_widget")
        self.addSubInterface(
            self.arama_widget,
            FIF.SEARCH,
            'Arama',
            NavigationItemPosition.TOP
        )
        
        # ========== ÜYE İŞLEMLERİ ==========
        # Üyeler
        self.uye_widget = UyeWidget(self.db)
        self.uye_widget.setObjectName("uye_widget")
        self.addSubInterface(
            self.uye_widget,
            FIF.PEOPLE,
            'Üyeler',
            NavigationItemPosition.TOP
        )
        
        # Ayrılan Üyeler
        self.ayrilan_widget = AyrilanUyelerWidget(self.db)
        self.ayrilan_widget.setObjectName("ayrilan_widget")
        self.addSubInterface(
            self.ayrilan_widget,
            FIF.REMOVE_FROM,
            'Ayrılan Üyeler',
            NavigationItemPosition.TOP
        )
        
        # Aidat Takip
        self.aidat_widget = AidatWidget(self.db)
        self.aidat_widget.setObjectName("aidat_widget")
        self.addSubInterface(
            self.aidat_widget,
            FIF.CERTIFICATE,
            'Aidat Takip',
            NavigationItemPosition.TOP
        )
        
        # ========== MALİ İŞLEMLER ==========
        # Gelir
        self.gelir_widget = GelirWidget(self.db)
        self.gelir_widget.setObjectName("gelir_widget")
        self.addSubInterface(
            self.gelir_widget,
            FIF.CARE_UP_SOLID,
            'Gelir',
            NavigationItemPosition.TOP
        )
        
        # Gider
        self.gider_widget = GiderWidget(self.db)
        self.gider_widget.setObjectName("gider_widget")
        self.addSubInterface(
            self.gider_widget,
            FIF.CARE_DOWN_SOLID,
            'Gider',
            NavigationItemPosition.TOP
        )
        
        # Virman
        self.virman_widget = VirmanWidget(self.db)
        self.virman_widget.setObjectName("virman_widget")
        self.addSubInterface(
            self.virman_widget,
            FIF.SYNC,
            'Virman',
            NavigationItemPosition.TOP
        )
        
        # Kasa Yönetimi
        self.kasa_widget = KasaWidget(self.db)
        self.kasa_widget.setObjectName("kasa_widget")
        self.addSubInterface(
            self.kasa_widget,
            FIF.MARKET,
            'Kasa',
            NavigationItemPosition.TOP
        )
        
        # ========== ETKİNLİK & TOPLANTI ==========
        # Etkinlikler
        self.etkinlik_widget = EtkinlikWidget(self.db)
        self.etkinlik_widget.setObjectName("etkinlik_widget")
        self.addSubInterface(
            self.etkinlik_widget,
            FIF.DATE_TIME,
            'Etkinlikler',
            NavigationItemPosition.TOP
        )
        
        # Toplantılar
        self.toplanti_widget = ToplantiWidget(self.db)
        self.toplanti_widget.setObjectName("toplanti_widget")
        self.addSubInterface(
            self.toplanti_widget,
            FIF.BOOK_SHELF,
            'Toplantılar',
            NavigationItemPosition.TOP
        )
        
        # ========== RAPORLAR & BELGELER ==========
        # Raporlar
        self.raporlar_widget = RaporlarWidget(self.db)
        self.raporlar_widget.setObjectName("raporlar_widget")
        self.addSubInterface(
            self.raporlar_widget,
            FIF.PIE_SINGLE,
            'Raporlar',
            NavigationItemPosition.TOP
        )
        
        # Tahakkuk Raporu
        self.tahakkuk_widget = TahakkukRaporWidget(self.db)
        self.tahakkuk_widget.setObjectName("tahakkuk_widget")
        self.addSubInterface(
            self.tahakkuk_widget,
            FIF.CALORIES,
            'Tahakkuk Raporu',
            NavigationItemPosition.TOP
        )
        
        # Bütçe Planlama
        self.butce_widget = ButceWidget(self.db)
        self.butce_widget.setObjectName("butce_widget")
        self.addSubInterface(
            self.butce_widget,
            FIF.FOLDER,
            'Bütçe',
            NavigationItemPosition.TOP
        )
        
        # Belgeler
        self.belgeler_widget = BelgelerWidget(self.db)
        self.belgeler_widget.setObjectName("belgeler_widget")
        self.addSubInterface(
            self.belgeler_widget,
            FIF.DOCUMENT,
            'Belgeler',
            NavigationItemPosition.TOP
        )
        
        # Belge Tara (OCR)
        if session.has_permission('ocr_kullan'):
            self.ocr_widget = OCRWidget(self.db)
            self.ocr_widget.setObjectName("ocr_widget")
            self.addSubInterface(
                self.ocr_widget,
                FIF.CAMERA,
                'Belge Tara',
                NavigationItemPosition.TOP
            )
        
        # ========== SİSTEM ==========
        # Yıl Sonu Devir
        self.devir_widget = DevirWidget(self.db)
        self.devir_widget.setObjectName("devir_widget")
        self.addSubInterface(
            self.devir_widget,
            FIF.HISTORY,
            'Yıl Sonu Devir',
            NavigationItemPosition.TOP
        )
        
        # Export & Yedekleme
        self.export_widget = ExportWidget(self.db)
        self.export_widget.setObjectName("export_widget")
        self.addSubInterface(
            self.export_widget,
            FIF.SAVE_AS,
            'Export',
            NavigationItemPosition.TOP
        )
        
        # Kullanıcılar - Admin kontrolü
        if session.has_permission('kullanici_yonet'):
            self.kullanicilar_widget = KullanicilarWidget(self.db)
            self.kullanicilar_widget.setObjectName("kullanicilar_widget")
            self.addSubInterface(
                self.kullanicilar_widget,
                FIF.FINGERPRINT,
                'Kullanıcılar',
                NavigationItemPosition.TOP
            )
        
        # ========== KÖY MODÜLÜ ==========
        self.navigationInterface.addSeparator()
        
        # Köy Dashboard
        self.koy_dashboard_widget = KoyDashboardWidget(self.db)
        self.koy_dashboard_widget.setObjectName("koy_dashboard_widget")
        self.addSubInterface(
            self.koy_dashboard_widget,
            FIF.TILES,
            'Köy Dashboard',
            NavigationItemPosition.TOP
        )
        
        # Köy Gelirleri
        self.koy_gelir_widget = KoyGelirWidget(self.db)
        self.koy_gelir_widget.setObjectName("koy_gelir_widget")
        self.addSubInterface(
            self.koy_gelir_widget,
            FIF.LEAF,
            'Köy Gelir',
            NavigationItemPosition.TOP
        )
        
        # Köy Giderleri
        self.koy_gider_widget = KoyGiderWidget(self.db)
        self.koy_gider_widget.setObjectName("koy_gider_widget")
        self.addSubInterface(
            self.koy_gider_widget,
            FIF.CHECKBOX,
            'Köy Gider',
            NavigationItemPosition.TOP
        )
        
        # Köy Kasaları
        self.koy_kasa_widget = KoyKasaWidget(self.db)
        self.koy_kasa_widget.setObjectName("koy_kasa_widget")
        self.addSubInterface(
            self.koy_kasa_widget,
            FIF.SHOPPING_CART,
            'Köy Kasa',
            NavigationItemPosition.TOP
        )
        
        # Köy Virmanları
        self.koy_virman_widget = KoyVirmanWidget(self.db)
        self.koy_virman_widget.setObjectName("koy_virman_widget")
        self.addSubInterface(
            self.koy_virman_widget,
            FIF.UPDATE,
            'Köy Virman',
            NavigationItemPosition.TOP
        )
        
        # ========== GÜNCELLEME MENÜSÜ ==========
        self.navigationInterface.addSeparator()
        
        # ⭐ YENİ: A Menüsü (v1.1.0 ile eklendi)
        self.navigationInterface.addItem(
            routeKey='a_menu',
            icon=FIF.FONT,
            text='🅰️ A Menüsü',
            onClick=self.show_a_menu,
            selectable=False,
            position=NavigationItemPosition.TOP
        )
        
        # Güncelleme butonu (üstte, görünür)
        self.navigationInterface.addItem(
            routeKey='update_check',
            icon=FIF.SYNC,
            text='🔄 Güncelle',
            onClick=self.check_for_updates,
            selectable=False,
            position=NavigationItemPosition.TOP
        )
        
        # ========== ALT MENÜ ==========
        # Ayarlar
        self.ayarlar_widget = AyarlarWidget(self.db)
        self.ayarlar_widget.setObjectName("ayarlar_widget")
        self.addSubInterface(
            self.ayarlar_widget,
            FIF.SETTING,
            'Ayarlar',
            NavigationItemPosition.BOTTOM
        )
        
        # Çıkış butonu
        self.navigationInterface.addItem(
            routeKey='logout',
            icon=FIF.POWER_BUTTON,
            text='Çıkış',
            onClick=self.logout,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )
        
        # Dinamik menüler için konteyner
        self.dynamic_widgets = {}
        
        # Sunucudan dinamik menüleri yükle
        self.load_dynamic_menus()
    
    def setup_signals(self):
        """Tüm sinyal bağlantıları"""
        # Üye widget'ından detay sayfalarına geçişler
        self.uye_widget.uye_detay_ac.connect(self.show_uye_detay)
        self.uye_widget.uye_aidat_ac.connect(self.show_uye_aidat)
        
        # Detay sayfalarından geri dönüşler
        self.uye_detay_widget.geri_don.connect(lambda: self.switchTo(self.uye_widget))
        self.uye_detay_widget.aidat_sayfasi_ac.connect(self.show_uye_aidat)
        
        self.uye_aidat_widget.geri_don.connect(lambda: self.switchTo(self.uye_widget))
        
        # Ayrılan üyeler
        self.ayrilan_widget.uye_detay_ac.connect(self.show_uye_detay)
        self.ayrilan_widget.uye_aidat_ac.connect(self.show_uye_aidat)
        
        # Gelişmiş Arama sinyalleri
        self.arama_widget.uye_secildi.connect(self.show_uye_detay)
        self.arama_widget.gelir_secildi.connect(lambda gid: self.switchTo(self.gelir_widget))
        self.arama_widget.gider_secildi.connect(lambda gid: self.switchTo(self.gider_widget))
    
    def show_uye_detay(self, uye_id: int):
        """Üye detay sayfasını göster"""
        self.uye_detay_widget.load_uye(uye_id)
        # Detay widget'ını stackedWidget'a ekle (gerekirse)
        if self.uye_detay_widget not in [self.stackedWidget.widget(i) for i in range(self.stackedWidget.count())]:
            self.stackedWidget.addWidget(self.uye_detay_widget)
        self.stackedWidget.setCurrentWidget(self.uye_detay_widget)
    
    def show_uye_aidat(self, uye_id: int):
        """Üye aidat sayfasını göster"""
        self.uye_aidat_widget.load_uye(uye_id)
        # Aidat widget'ını stackedWidget'a ekle (gerekirse)
        if self.uye_aidat_widget not in [self.stackedWidget.widget(i) for i in range(self.stackedWidget.count())]:
            self.stackedWidget.addWidget(self.uye_aidat_widget)
        self.stackedWidget.setCurrentWidget(self.uye_aidat_widget)
    
    def check_for_updates(self):
        """Manuel güncelleme kontrolü - Progress dialog ile"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
        from PyQt5.QtCore import Qt, QObject, pyqtSignal
        import threading
        
        # Signal helper class
        class UpdateSignals(QObject):
            progress = pyqtSignal(str, str)
            finished = pyqtSignal(dict)
        
        self.update_signals = UpdateSignals()
        self.update_signals.progress.connect(self._update_progress)
        self.update_signals.finished.connect(self._show_update_result)
        
        # Progress Dialog oluştur
        self.update_dialog = QDialog(self)
        self.update_dialog.setWindowTitle("🔄 Güncelleme Kontrolü")
        self.update_dialog.setFixedSize(400, 200)
        self.update_dialog.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        
        layout = QVBoxLayout(self.update_dialog)
        layout.setSpacing(15)
        
        self.update_status_label = QLabel("⏳ Sunucuya bağlanılıyor...")
        self.update_status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.update_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.update_status_label)
        
        self.update_detail_label = QLabel("")
        self.update_detail_label.setStyleSheet("font-size: 12px; color: #666;")
        self.update_detail_label.setAlignment(Qt.AlignCenter)
        self.update_detail_label.setWordWrap(True)
        layout.addWidget(self.update_detail_label)
        
        self.update_progress = QProgressBar()
        self.update_progress.setRange(0, 0)  # Indeterminate
        self.update_progress.setTextVisible(False)
        layout.addWidget(self.update_progress)
        
        layout.addStretch()
        self.update_dialog.show()
        QApplication.processEvents()
        
        # Arka planda güncelleme kontrolü yap
        signals = self.update_signals
        
        def do_update_check():
            import time
            results = {
                'version_check': None,
                'menus': [],
                'error': None
            }
            
            try:
                from server_client import get_server_client
                client = get_server_client()
                
                if not client.is_configured():
                    results['error'] = "Server yapılandırılmamış!"
                    signals.finished.emit(results)
                    return
                
                # 1. Versiyon kontrolü
                signals.progress.emit("🔍 Versiyon kontrolü yapılıyor...", "")
                time.sleep(0.3)
                
                try:
                    has_update, message, data = client.check_update(APP_VERSION)
                    results['version_check'] = {
                        'has_update': has_update,
                        'message': message,
                        'data': data
                    }
                except Exception as e:
                    results['version_check'] = {'error': str(e)}
                
                # 2. Dinamik menüleri yükle
                signals.progress.emit("📋 Menüler güncelleniyor...", "Sunucudan yeni menüler alınıyor")
                time.sleep(0.3)
                
                try:
                    response = client._session.get(
                        f"{client.config.server_url}/app/menus",
                        headers=client._get_headers(),
                        timeout=10
                    )
                    if response.status_code == 200:
                        results['menus'] = response.json()
                except Exception as e:
                    pass  # Menü hatası kritik değil
                
                # 3. Tamamlandı
                signals.progress.emit("✅ Tamamlandı!", "")
                time.sleep(0.3)
                
            except Exception as e:
                results['error'] = str(e)
            
            # Sonucu ana thread'de göster
            signals.finished.emit(results)
        
        thread = threading.Thread(target=do_update_check, daemon=True)
        thread.start()
    
    def _update_progress(self, status: str, detail: str):
        """Progress dialog güncelle"""
        if hasattr(self, 'update_status_label'):
            self.update_status_label.setText(status)
        if hasattr(self, 'update_detail_label'):
            self.update_detail_label.setText(detail)
    
    def _show_update_result(self, results: dict):
        """Güncelleme sonuçlarını göster"""
        # Dialog'u kapat
        if hasattr(self, 'update_dialog') and self.update_dialog:
            self.update_dialog.close()
        
        # Hata varsa göster
        if results.get('error'):
            MessageBox("❌ Hata", f"Güncelleme kontrolü başarısız:\n{results['error']}", self).show()
            return
        
        # Dinamik menüleri uygula
        menus = results.get('menus', [])
        new_menus_added = 0
        for menu in menus:
            if menu.get('id') not in self.dynamic_widgets:
                try:
                    self.add_dynamic_menu(menu)
                    new_menus_added += 1
                except:
                    pass
        
        # Versiyon kontrolü sonucu
        version_info = results.get('version_check', {})
        
        if version_info.get('has_update') and version_info.get('data'):
            from ui_auto_operations import show_update_dialog
            show_update_dialog(self, version_info['data'])
        else:
            # Başarı mesajı
            summary = f"✅ Uygulamanız güncel!\n\n"
            summary += f"📌 Mevcut sürüm: {APP_VERSION}\n"
            
            if new_menus_added > 0:
                summary += f"📋 {new_menus_added} yeni duyuru eklendi\n"
            elif menus:
                summary += f"📋 {len(menus)} aktif duyuru mevcut\n"
            
            summary += f"\n🕐 Son kontrol: Şimdi"
            
            MessageBox("✅ Güncelleme Kontrolü", summary, self).show()
    
    def show_a_menu(self):
        """🅰️ A Menüsü - v1.1.0 ile eklenen yeni özellik"""
        MessageBox(
            "🅰️ A Menüsü - YENİ!",
            "Bu menü v1.1.0 güncellemesi ile eklendi!\n\n"
            "✅ Güncelleme başarılı!\n"
            "✅ Veritabanınız korundu!\n\n"
            "Eğer bu mesajı görüyorsanız güncelleme sistemi çalışıyor demektir.",
            self
        ).show()
    
    def load_dynamic_menus(self):
        """Sunucudan dinamik menüleri yükle - güvenli şekilde ana thread'de"""
        from PyQt5.QtCore import QTimer
        import threading
        
        def fetch_menus():
            """Arka planda menüleri çek"""
            try:
                from server_client import get_server_client
                client = get_server_client()
                
                if not client.is_configured():
                    return
                
                # Sunucudan menü konfigürasyonunu al
                response = client._session.get(
                    f"{client.config.server_url}/app/menus",
                    headers=client._get_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    menus = response.json()
                    # Ana thread'de UI güncellemesi yap
                    QTimer.singleShot(0, lambda: self._apply_dynamic_menus(menus))
                    
            except Exception as e:
                print(f"[BADER] Dinamik menü yükleme hatası: {e}")
        
        # Arka plan thread'i başlat
        thread = threading.Thread(target=fetch_menus, daemon=True)
        thread.start()
    
    def _apply_dynamic_menus(self, menus):
        """Dinamik menüleri ana thread'de uygula"""
        for menu in menus:
            try:
                self.add_dynamic_menu(menu)
            except Exception as e:
                print(f"[BADER] Menü ekleme hatası: {e}")
    
    def add_dynamic_menu(self, menu_config: dict):
        """Dinamik menü ekle"""
        menu_id = menu_config.get('id', '')
        menu_name = menu_config.get('name', 'Yeni Menü')
        menu_icon = menu_config.get('icon', 'INFO')
        menu_type = menu_config.get('type', 'info')
        menu_content = menu_config.get('content', '')
        
        # Zaten varsa ekleme
        if menu_id in self.dynamic_widgets:
            return
        
        # İkon eşleştirme
        icon_map = {
            'INFO': FIF.INFO,
            'UPDATE': FIF.UPDATE,
            'CERTIFICATE': FIF.CERTIFICATE,
            'GIFT': FIF.GIFT,
            'STAR': FIF.STAR_OFF,
            'CHECK': FIF.ACCEPT,
            'SUCCESS': FIF.ACCEPT_MEDIUM,
        }
        icon = icon_map.get(menu_icon, FIF.INFO)
        
        # Basit info widget oluştur
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
        widget = QWidget()
        widget.setObjectName(f"dynamic_{menu_id}")
        layout = QVBoxLayout(widget)
        
        title = QLabel(menu_name)
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        content = QLabel(menu_content)
        content.setWordWrap(True)
        content.setStyleSheet("font-size: 14px; line-height: 1.6;")
        layout.addWidget(content)
        
        layout.addStretch()
        
        # Menüye ekle
        self.addSubInterface(
            widget,
            icon,
            menu_name,
            NavigationItemPosition.TOP
        )
        
        self.dynamic_widgets[menu_id] = widget
        print(f"[BADER] Dinamik menü eklendi: {menu_name}")
        
    def logout(self):
        """Çıkış yap"""
        w = MessageBox(
            "Çıkış",
            "Çıkış yapmak istediğinize emin misiniz?",
            self
        )
        if w.exec():
            session.logout()
            self.close()
            # Login ekranına dön
            self.login_widget = LoginWidget(self.db)
            self.login_widget.login_successful.connect(self.on_login_success)
            self.login_widget.show()
    
    def on_login_success(self, kullanici):
        """Yeniden giriş başarılı"""
        self.kullanici = kullanici
        session.set_user(kullanici)
        new_window = FluentBADERWindow(self.db, kullanici)
        new_window.show()
        self.login_widget.close()


# Uygulama versiyonu
APP_VERSION = "1.1.0"

# Global değişkenler
_auto_ops = None
_main_window = None


def main():
    """Ana fonksiyon"""
    global _auto_ops
    
    # High DPI desteği (MacBook Retina ekranlar için)
    from PyQt5.QtCore import QCoreApplication
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Platform bazlı font ayarı
    from PyQt5.QtGui import QFont
    if sys.platform == "darwin":  # macOS
        font = QFont("SF Pro Text", 10)
    elif sys.platform == "win32":  # Windows
        font = QFont("Segoe UI", 10)
    else:  # Linux
        font = QFont("Ubuntu", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    
    # Fluent tema
    setTheme(Theme.AUTO)
    
    # Database
    db = Database()
    db.connect()
    db.initialize_database()  # Tabloları oluştur
    
    # Veritabanı yolu
    db_path = db.db_path if hasattr(db, 'db_path') else os.path.expanduser("~/Documents/BADER/bader.db")
    
    # Otomatik işlemler yöneticisi (backup on quit)
    from ui_auto_operations import AutoOperationsManager
    _auto_ops = AutoOperationsManager(app, db_path, APP_VERSION)
    
    # Kurulum kontrolü
    from ui_setup import check_setup_required, SetupWizard
    
    if check_setup_required(db):
        # İlk kurulum gerekli
        setup_wizard = SetupWizard(db)
        
        def on_setup_complete(admin_data):
            # Kurulum tamamlandı, login ekranını göster
            show_login(db, app)
        
        setup_wizard.setup_completed.connect(on_setup_complete)
        setup_wizard.exec()
        
        # Eğer wizard iptal edildiyse çık
        if check_setup_required(db):
            sys.exit(0)
        else:
            show_login(db, app)
    else:
        # Kurulum yapılmış, login göster
        show_login(db, app)
    
    sys.exit(app.exec())


def show_login(db, app):
    """Login ekranını göster"""
    global _main_window
    
    login_widget = LoginWidget(db)
    
    def on_login_success(kullanici):
        global _main_window
        login_widget.close()
        
        _main_window = FluentBADERWindow(db, kullanici)
        _main_window.show()
        
        # Başlangıçta güncelleme kontrolü (5 saniye sonra)
        from ui_auto_operations import startup_update_check
        startup_update_check(_main_window, APP_VERSION)
    
    login_widget.login_successful.connect(on_login_success)
    login_widget.show()


if __name__ == '__main__':
    main()
