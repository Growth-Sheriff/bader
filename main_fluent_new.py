"""
🎨 BADER - WINDOWS 11 FLUENT DESIGN
Tam entegrasyon - Tüm özellikler aktif
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import (FluentWindow, NavigationItemPosition, MessageBox,
                            setTheme, Theme, setThemeColor, FluentIcon as FIF)
from database import Database
from ui_dashboard import DashboardWidget
from ui_uyeler import UyeWidget
from ui_aidat import AidatWidget
from ui_gelir import GelirWidget
from ui_gider import GiderWidget
from ui_kasa import KasaWidget
from ui_virman import VirmanWidget
from ui_devir import DevirWidget
from ui_export import ExportWidget
from ui_uye_detay import UyeDetayWidget
from ui_uye_aidat import UyeAidatWidget
from ui_uyeler_ayrilan import AyrilanUyelerWidget
from ui_raporlar import RaporlarWidget
from ui_etkinlik import EtkinlikWidget
from ui_toplanti import ToplantiWidget
from ui_butce import ButceWidget
from ui_kullanicilar import KullanicilarWidget
from ui_belgeler import BelgelerWidget
from ui_mali_tablolar import MaliTablolarWidget
from ui_alacak_verecek import AlacakVerecekWidget
from ui_tahakkuk_rapor import TahakkukRaporWidget
from ui_koy_dashboard import KoyDashboardWidget
from ui_koy_islemler import KoyGelirWidget, KoyGiderWidget, KoyKasaWidget, KoyVirmanWidget
from ui_ayarlar import AyarlarWidget
import sys


class FluentBADERWindow(FluentWindow):
    """Windows 11 Fluent Design ile BADER"""
    
    def __init__(self, db: Database, kullanici: dict):
        super().__init__()
        self.db = db
        self.kullanici = kullanici
        
        # Pencere ayarları
        self.setWindowTitle("BADER - Dernek Yönetim Sistemi")
        self.resize(1400, 800)
        
        # Mica/Acrylic effect (Windows 11)
        self.setMicaEffectEnabled(True)
        
        # 🎯 GERÇEK WIDGET'LAR - Tüm özellikler aktif
        self.dashboard_widget = DashboardWidget(db)
        self.uye_widget = UyeWidget(db)
        self.aidat_widget = AidatWidget(db)
        self.gelir_widget = GelirWidget(db)
        self.gider_widget = GiderWidget(db)
        self.kasa_widget = KasaWidget(db)
        self.virman_widget = VirmanWidget(db)
        self.devir_widget = DevirWidget(db)
        self.export_widget = ExportWidget(db)
        
        # Detay sayfaları
        self.uye_detay_widget = UyeDetayWidget(db)
        self.uye_aidat_widget = UyeAidatWidget(db)
        self.ayrilan_uyeler_widget = AyrilanUyelerWidget(db)
        
        # Ek modüller
        self.raporlar_widget = RaporlarWidget(db)
        self.mali_tablolar_widget = MaliTablolarWidget(db)
        self.alacak_verecek_widget = AlacakVerecekWidget(db)
        self.tahakkuk_rapor_widget = TahakkukRaporWidget(db)
        self.etkinlik_widget = EtkinlikWidget(db)
        self.toplanti_widget = ToplantiWidget(db)
        self.butce_widget = ButceWidget(db)
        self.kullanicilar_widget = KullanicilarWidget(db)
        self.belgeler_widget = BelgelerWidget(db)
        
        # Köy modülü sayfaları
        self.koy_dashboard_widget = KoyDashboardWidget(db)
        self.koy_gelir_widget = KoyGelirWidget(db)
        self.koy_gider_widget = KoyGiderWidget(db)
        self.koy_kasa_widget = KoyKasaWidget(db)
        self.koy_virman_widget = KoyVirmanWidget(db)
        
        # Ayarlar
        self.ayarlar_widget = AyarlarWidget(db)
        
        # Sinyal bağlantıları
        self.setup_signals()
        
        # Navigation
        self.init_navigation()
    
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
        self.ayrilan_uyeler_widget.uye_detay_ac.connect(self.show_uye_detay)
        self.ayrilan_uyeler_widget.uye_aidat_ac.connect(self.show_uye_aidat)
    
    def show_uye_detay(self, uye_id: int):
        """Üye detay sayfasını göster"""
        self.uye_detay_widget.load_uye(uye_id)
        self.stackedWidget.setCurrentWidget(self.uye_detay_widget)
    
    def show_uye_aidat(self, uye_id: int):
        """Üye aidat sayfasını göster"""
        self.uye_aidat_widget.load_uye(uye_id)
        self.stackedWidget.setCurrentWidget(self.uye_aidat_widget)
        
    def init_navigation(self):
        """Navigation bar'ı kur"""
        
        # ObjectName ekle (Fluent gereksinimi)
        self.dashboard_widget.setObjectName("dashboard_widget")
        self.uye_widget.setObjectName("uye_widget")
        self.aidat_widget.setObjectName("aidat_widget")
        self.gelir_widget.setObjectName("gelir_widget")
        self.gider_widget.setObjectName("gider_widget")
        self.kasa_widget.setObjectName("kasa_widget")
        self.virman_widget.setObjectName("virman_widget")
        self.devir_widget.setObjectName("devir_widget")
        self.export_widget.setObjectName("export_widget")
        self.raporlar_widget.setObjectName("raporlar_widget")
        self.mali_tablolar_widget.setObjectName("mali_tablolar_widget")
        self.alacak_verecek_widget.setObjectName("alacak_verecek_widget")
        self.etkinlik_widget.setObjectName("etkinlik_widget")
        self.toplanti_widget.setObjectName("toplanti_widget")
        self.butce_widget.setObjectName("butce_widget")
        self.kullanicilar_widget.setObjectName("kullanicilar_widget")
        self.belgeler_widget.setObjectName("belgeler_widget")
        self.tahakkuk_rapor_widget.setObjectName("tahakkuk_rapor_widget")
        self.uye_detay_widget.setObjectName("uye_detay_widget")
        self.uye_aidat_widget.setObjectName("uye_aidat_widget")
        self.ayrilan_uyeler_widget.setObjectName("ayrilan_uyeler_widget")
        self.koy_dashboard_widget.setObjectName("koy_dashboard_widget")
        self.koy_gelir_widget.setObjectName("koy_gelir_widget")
        self.koy_gider_widget.setObjectName("koy_gider_widget")
        self.koy_kasa_widget.setObjectName("koy_kasa_widget")
        self.koy_virman_widget.setObjectName("koy_virman_widget")
        self.ayarlar_widget.setObjectName("ayarlar_widget")
        
        # Ana menüler
        self.addSubInterface(
            self.dashboard_widget, 
            FIF.HOME, 
            'Dashboard',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.uye_widget,
            FIF.PEOPLE,
            'Üyeler',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.ayrilan_uyeler_widget,
            FIF.DELETE,
            'Ayrılan Üyeler',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.aidat_widget,
            FIF.CERTIFICATE,
            'Aidat',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.gelir_widget,
            FIF.ADD,
            'Gelir',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.gider_widget,
            FIF.REMOVE,
            'Gider',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.kasa_widget,
            FIF.MARKET,
            'Kasa',
            NavigationItemPosition.TOP
        )
        
        # İşlemler
        self.addSubInterface(
            self.virman_widget,
            FIF.SYNC,
            'Virman',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.devir_widget,
            FIF.CALENDAR,
            'Devir',
            NavigationItemPosition.TOP
        )
        
        # Raporlar & Diğer
        self.addSubInterface(
            self.raporlar_widget,
            FIF.DOCUMENT,
            'Raporlar',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.mali_tablolar_widget,
            FIF.DOCUMENT,
            'Mali Tablolar',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.tahakkuk_rapor_widget,
            FIF.CALENDAR,
            'Tahakkuk Raporu',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.alacak_verecek_widget,
            FIF.LABEL,
            'Alacak-Verecek',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.etkinlik_widget,
            FIF.DATE_TIME,
            'Etkinlikler',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.toplanti_widget,
            FIF.CHAT,
            'Toplantılar',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.butce_widget,
            FIF.CERTIFICATE,
            'Bütçe',
            NavigationItemPosition.TOP
        )
        
        # === KÖY MODÜLÜ ===
        self.navigationInterface.addSeparator(NavigationItemPosition.TOP)
        
        self.addSubInterface(
            self.koy_dashboard_widget,
            FIF.VIEW,
            'Köy Dashboard',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.koy_gelir_widget,
            FIF.ADD,
            'Köy Gelir',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.koy_gider_widget,
            FIF.REMOVE,
            'Köy Gider',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.koy_kasa_widget,
            FIF.MARKET,
            'Köy Kasa',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.koy_virman_widget,
            FIF.SYNC,
            'Köy Virman',
            NavigationItemPosition.TOP
        )
        
        # Alt menüler - addSubInterface ile ekle
        self.addSubInterface(
            self.belgeler_widget,
            FIF.FOLDER,
            'Belgeler',
            NavigationItemPosition.BOTTOM
        )
        
        self.addSubInterface(
            self.kullanicilar_widget,
            FIF.PEOPLE,
            'Kullanıcılar',
            NavigationItemPosition.BOTTOM
        )
        
        self.addSubInterface(
            self.export_widget,
            FIF.SHARE,
            'Dışa Aktar',
            NavigationItemPosition.BOTTOM
        )
        
        self.addSubInterface(
            self.ayarlar_widget,
            FIF.SETTING,
            'Ayarlar',
            NavigationItemPosition.BOTTOM
        )
        
        self.navigationInterface.addItem(
            routeKey='logout',
            icon=FIF.POWER_BUTTON,
            text='Çıkış',
            onClick=self.logout,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )
        
        # 🔴 BETA RESET BUTONU
        self.navigationInterface.addItem(
            routeKey='beta_reset',
            icon=FIF.DELETE,
            text='🔴 BETA RESET',
            onClick=self.beta_reset,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )
        
        # Gizli detay sayfalarını stack'e ekle (navigasyonda görünmez)
        self.stackedWidget.addWidget(self.uye_detay_widget)
        self.stackedWidget.addWidget(self.uye_aidat_widget)
        self.stackedWidget.addWidget(self.ayrilan_uyeler_widget)
        
    def logout(self):
        """Çıkış yap"""
        w = MessageBox("Çıkış", "Çıkış yapmak istediğinize emin misiniz?", self)
        if w.exec():
            self.close()
    
    def beta_reset(self):
        """🔴 BETA RESET - Tüm veritabanını sıfırla"""
        w = MessageBox(
            "🔴 BETA RESET - DİKKAT!",
            "⚠️ TÜM VERİLER SİLİNECEK!\n\n"
            "Bu işlem geri alınamaz:\n"
            "• Tüm üyeler\n"
            "• Tüm gelir/gider kayıtları\n"
            "• Tüm aidat kayıtları\n"
            "• Tüm kasa hareketleri\n"
            "• Tüm belgeler\n\n"
            "Devam etmek istiyor musunuz?",
            self
        )
        
        if w.exec():
            # İkinci onay
            w2 = MessageBox(
                "🔴 SON UYARI",
                "Bu işlem GERİ ALINAMAZ!\n\n"
                "Tüm veriler kalıcı olarak silinecek.\n\n"
                "ONAYLIYOR MUSUNUZ?",
                self
            )
            
            if w2.exec():
                try:
                    # Tüm tabloları temizle
                    tables = [
                        'uyeler', 'aidat_tanimlari', 'aidatlar', 
                        'gelirler', 'giderler', 'kasalar', 'virmanlar',
                        'belgeler', 'etkinlikler', 'toplantilar',
                        'butce_kalemleri', 'alacak_verecek',
                        'koy_gelirler', 'koy_giderler', 'koy_kasalar', 'koy_virmanlar'
                    ]
                    
                    for table in tables:
                        try:
                            self.db.cursor.execute(f"DELETE FROM {table}")
                        except Exception as e:
                            print(f"Tablo temizlenemedi ({table}): {e}")
                    
                    self.db.commit()
                    
                    # Başarı mesajı
                    success = MessageBox(
                        "✅ RESET TAMAMLANDI",
                        "Tüm veriler silindi.\n\n"
                        "Uygulama yeniden başlatılacak.",
                        self
                    )
                    success.exec()
                    
                    # Uygulamayı yeniden başlat
                    import os
                    os.execl(sys.executable, sys.executable, *sys.argv)
                    
                except Exception as e:
                    error = MessageBox(
                        "❌ HATA",
                        f"Reset sırasında hata oluştu:\n{e}",
                        self
                    )
                    error.exec()


if __name__ == '__main__':
    # Test için
    app = QApplication(sys.argv)
    
    # Windows 11 tema
    setTheme(Theme.AUTO)
    setThemeColor('#005BD3')
    
    db = Database()
    db.connect()  # 🔧 Kritik: Database bağlantısını aç
    
    window = FluentBADERWindow(db, {'id': 1, 'username': 'admin'})
    window.show()
    
    sys.exit(app.exec())
