"""
BADER Derneği - Ana Pencere
Tüm modülleri birleştiren ana uygulama penceresi
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QPushButton, QLabel, QMenuBar,
                             QMenu, QToolBar, QStatusBar, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
                             QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QAction, QIcon
from database import Database
from ui_uyeler import UyeWidget
from ui_aidat import AidatWidget
from ui_gelir import GelirWidget
from ui_gider import GiderWidget
from ui_virman import VirmanWidget
from ui_kasa import KasaWidget
from ui_dashboard import DashboardWidget
from ui_export import ExportWidget
from ui_devir import DevirWidget
from ui_sidebar import Sidebar
from ui_styles import MODERN_STYLESHEET
from ui_drawer import DrawerPanel
from ui_form_fields import create_line_edit, create_double_spin_box
from ui_uye_detay import UyeDetayWidget
from ui_uye_aidat import UyeAidatWidget
from ui_uyeler_ayrilan import AyrilanUyelerWidget
from ui_koy_dashboard import KoyDashboardWidget
from ui_koy_islemler import KoyGelirWidget, KoyGiderWidget, KoyKasaWidget, KoyVirmanWidget
from ui_raporlar import RaporlarWidget
from ui_etkinlik import EtkinlikWidget
from ui_toplanti import ToplantiWidget
from ui_butce import ButceWidget
from ui_kullanicilar import KullanicilarWidget
from ui_belgeler import BelgelerWidget
from ui_tahakkuk_rapor import TahakkukRaporWidget


class AyarlarFormWidget(QWidget):
    """Ayarlar formu"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_ayarlar()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Dernek Bilgileri
        dernek_label = QLabel("Dernek Bilgileri")
        dernek_label.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 15px;
                font-weight: 600;
                padding-bottom: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        layout.addWidget(dernek_label)
        
        self.dernek_adi_edit = create_line_edit("Dernek Adı", "")
        layout.addWidget(self.dernek_adi_edit[0])
        
        self.dernek_adres_edit = create_line_edit("Dernek Adresi", "")
        layout.addWidget(self.dernek_adres_edit[0])
        
        self.dernek_telefon_edit = create_line_edit("Dernek Telefon", "")
        layout.addWidget(self.dernek_telefon_edit[0])
        
        self.dernek_email_edit = create_line_edit("Dernek E-posta", "")
        layout.addWidget(self.dernek_email_edit[0])
        
        # Mali Ayarlar
        mali_label = QLabel("Mali Ayarlar")
        mali_label.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 15px;
                font-weight: 600;
                padding-bottom: 8px;
                border-bottom: 1px solid #e0e0e0;
                margin-top: 20px;
            }
        """)
        layout.addWidget(mali_label)
        
        self.varsayilan_aidat_spin = create_double_spin_box("Varsayılan Aidat")
        self.varsayilan_aidat_spin[1].setMinimum(0)
        self.varsayilan_aidat_spin[1].setMaximum(1000000)
        self.varsayilan_aidat_spin[1].setSuffix(" ₺")
        layout.addWidget(self.varsayilan_aidat_spin[0])
        
        self.usd_kur_spin = create_double_spin_box("USD Kuru (TL)")
        self.usd_kur_spin[1].setMinimum(0)
        self.usd_kur_spin[1].setMaximum(1000)
        layout.addWidget(self.usd_kur_spin[0])
        
        self.eur_kur_spin = create_double_spin_box("EUR Kuru (TL)")
        self.eur_kur_spin[1].setMinimum(0)
        self.eur_kur_spin[1].setMaximum(1000)
        layout.addWidget(self.eur_kur_spin[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_ayarlar(self):
        """Ayarları yükle"""
        ayarlar = {
            'dernek_adi': 'BADER Derneği',
            'dernek_adres': '',
            'dernek_telefon': '',
            'dernek_email': '',
            'varsayilan_aidat_tutari': '1000',
            'usd_kuru': '30.0',
            'eur_kuru': '33.0'
        }
        
        for ayar_adi in ayarlar.keys():
            self.db.cursor.execute(
                "SELECT ayar_degeri FROM ayarlar WHERE ayar_adi = ?",
                (ayar_adi,)
            )
            result = self.db.cursor.fetchone()
            if result:
                ayarlar[ayar_adi] = result[0]
        
        self.dernek_adi_edit[1].setText(ayarlar['dernek_adi'])
        self.dernek_adres_edit[1].setText(ayarlar['dernek_adres'])
        self.dernek_telefon_edit[1].setText(ayarlar['dernek_telefon'])
        self.dernek_email_edit[1].setText(ayarlar['dernek_email'])
        self.varsayilan_aidat_spin[1].setValue(float(ayarlar['varsayilan_aidat_tutari']))
        self.usd_kur_spin[1].setValue(float(ayarlar['usd_kuru']))
        self.eur_kur_spin[1].setValue(float(ayarlar['eur_kuru']))
        
    def get_data(self):
        """Ayar verilerini al"""
        return {
            'dernek_adi': self.dernek_adi_edit[1].text(),
            'dernek_adres': self.dernek_adres_edit[1].text(),
            'dernek_telefon': self.dernek_telefon_edit[1].text(),
            'dernek_email': self.dernek_email_edit[1].text(),
            'varsayilan_aidat_tutari': str(self.varsayilan_aidat_spin[1].value()),
            'usd_kuru': str(self.usd_kur_spin[1].value()),
            'eur_kuru': str(self.eur_kur_spin[1].value())
        }
    
    def kaydet(self):
        """Ayarları kaydet"""
        ayarlar = self.get_data()
        
        for ayar_adi, ayar_degeri in ayarlar.items():
            self.db.cursor.execute("""
                UPDATE ayarlar SET ayar_degeri = ? WHERE ayar_adi = ?
            """, (ayar_degeri, ayar_adi))
        
        self.db.commit()
        return True


class MainWindow(QMainWindow):
    """Ana uygulama penceresi"""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.initialize_database()
        self.setup_ui()
        self.show_dashboard()
        
    def setup_ui(self):
        self.setWindowTitle("BADER Derneği - Yönetim Sistemi")
        self.setMinimumSize(1400, 900)
        
        # Stylesheet uygula
        self.setStyleSheet(MODERN_STYLESHEET)
        
        # Menu bar'ı gizle (Sidebar kullanacağız)
        self.menuBar().setVisible(False)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout: Sidebar + Content
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar oluştur
        self.sidebar = Sidebar()
        self.sidebar.menu_clicked.connect(self.on_sidebar_menu_click)
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f7fa;
                border: none;
            }
        """)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top header bar (kullanıcı bilgisi, bildirimler için)
        self.create_top_header(content_layout)
        
        # Stack widget (sayfa geçişleri için)
        self.stack = QStackedWidget()
        
        # Widget'ları oluştur
        self.dashboard_widget = DashboardWidget(self.db)
        self.uyeler_widget = UyeWidget(self.db)
        self.aidat_widget = AidatWidget(self.db)
        self.gelir_widget = GelirWidget(self.db)
        self.gider_widget = GiderWidget(self.db)
        self.virman_widget = VirmanWidget(self.db)
        self.kasa_widget = KasaWidget(self.db)
        self.devir_widget = DevirWidget(self.db)
        self.export_widget = ExportWidget(self.db)
        
        # Yeni sayfalar
        self.uye_detay_widget = UyeDetayWidget(self.db)
        self.uye_aidat_widget = UyeAidatWidget(self.db)
        self.ayrilan_uyeler_widget = AyrilanUyelerWidget(self.db)
        
        # Köy modülü sayfaları
        self.koy_dashboard_widget = KoyDashboardWidget(self.db)
        self.koy_gelir_widget = KoyGelirWidget(self.db)
        self.koy_gider_widget = KoyGiderWidget(self.db)
        self.koy_kasa_widget = KoyKasaWidget(self.db)
        self.koy_virman_widget = KoyVirmanWidget(self.db)
        
        # Yeni modüller
        self.raporlar_widget = RaporlarWidget(self.db)
        self.tahakkuk_rapor_widget = TahakkukRaporWidget(self.db)
        self.etkinlik_widget = EtkinlikWidget(self.db)
        self.toplanti_widget = ToplantiWidget(self.db)
        self.butce_widget = ButceWidget(self.db)
        self.kullanicilar_widget = KullanicilarWidget(self.db)
        self.belgeler_widget = BelgelerWidget(self.db)
        
        # Sinyal bağlantıları - Üye detay/aidat sayfası geçişleri
        self.uyeler_widget.uye_detay_ac.connect(self.show_uye_detay)
        self.uyeler_widget.uye_aidat_ac.connect(self.show_uye_aidat)
        self.uye_detay_widget.geri_don.connect(self.show_uyeler)
        self.uye_detay_widget.aidat_sayfasi_ac.connect(self.show_uye_aidat)
        self.uye_aidat_widget.geri_don.connect(self.show_uyeler)
        self.ayrilan_uyeler_widget.uye_detay_ac.connect(self.show_uye_detay)
        self.ayrilan_uyeler_widget.uye_aidat_ac.connect(self.show_uye_aidat)
        
        # Stack'e ekle (sidebar ile aynı sırada)
        self.stack.addWidget(self.dashboard_widget)  # 0: dashboard
        self.stack.addWidget(self.uyeler_widget)     # 1: uyeler
        self.stack.addWidget(self.aidat_widget)      # 2: aidat
        self.stack.addWidget(self.gelir_widget)      # 3: gelir
        self.stack.addWidget(self.gider_widget)      # 4: gider
        self.stack.addWidget(self.virman_widget)     # 5: virman
        self.stack.addWidget(self.kasa_widget)       # 6: kasa
        self.stack.addWidget(self.devir_widget)      # 7: devir
        self.stack.addWidget(self.export_widget)     # 8: export
        self.stack.addWidget(self.uye_detay_widget)  # 9: uye_detay
        self.stack.addWidget(self.uye_aidat_widget)  # 10: uye_aidat
        self.stack.addWidget(self.ayrilan_uyeler_widget)  # 11: ayrilan_uyeler
        
        # Köy modülü sayfaları
        self.stack.addWidget(self.koy_dashboard_widget)  # 12: koy_dashboard
        self.stack.addWidget(self.koy_gelir_widget)      # 13: koy_gelir
        self.stack.addWidget(self.koy_gider_widget)      # 14: koy_gider
        self.stack.addWidget(self.koy_virman_widget)     # 15: koy_virman
        self.stack.addWidget(self.koy_kasa_widget)       # 16: koy_kasa
        
        # Yeni modüller
        self.stack.addWidget(self.raporlar_widget)       # 17: raporlar
        self.stack.addWidget(self.tahakkuk_rapor_widget) # 18: tahakkuk
        self.stack.addWidget(self.etkinlik_widget)       # 19: etkinlikler
        self.stack.addWidget(self.toplanti_widget)       # 20: toplantilar
        self.stack.addWidget(self.butce_widget)          # 21: butce
        self.stack.addWidget(self.kullanicilar_widget)   # 22: kullanicilar
        self.stack.addWidget(self.belgeler_widget)       # 23: belgeler
        
        content_layout.addWidget(self.stack)
        content_frame.setLayout(content_layout)
        
        main_layout.addWidget(content_frame, 1)  # Content stretch
        
        central_widget.setLayout(main_layout)
        
        # Status Bar
        self.statusBar().showMessage("Hazır")
        
    def create_top_header(self, parent_layout):
        """Üst header bar oluştur"""
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid rgba(47, 43, 61, 0.08);
            }
        """)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(32, 0, 32, 0)
        
        # Sol taraf - Sayfa başlığı (dinamik olacak)
        self.page_title = QLabel("Dashboard")
        self.page_title.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 22px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(self.page_title)
        
        header_layout.addStretch()
        
        # Sağ taraf - Hızlı aksiyonlar
        yenile_btn = QPushButton("🔄 Yenile")
        yenile_btn.setProperty("class", "secondary")
        yenile_btn.setFixedHeight(38)
        yenile_btn.clicked.connect(self.refresh_current_page)
        header_layout.addWidget(yenile_btn)
        
        ayarlar_btn = QPushButton("⚙️ Ayarlar")
        ayarlar_btn.setProperty("class", "secondary")
        ayarlar_btn.setFixedHeight(38)
        ayarlar_btn.clicked.connect(self.show_ayarlar)
        header_layout.addWidget(ayarlar_btn)
        
        header.setLayout(header_layout)
        parent_layout.addWidget(header)
        
    def on_sidebar_menu_click(self, menu_id: str):
        """Sidebar menüsü tıklandığında"""
        menu_map = {
            # BADER modülü
            "dashboard": (0, "Dashboard"),
            "uyeler": (1, "Üye Yönetimi"),
            "ayrilanlar": (11, "Ayrılan Üyeler"),
            "aidat": (2, "Aidat Takip"),
            "gelir": (3, "Gelir Yönetimi"),
            "gider": (4, "Gider Yönetimi"),
            "virman": (5, "Virman İşlemleri"),
            "kasa": (6, "Kasa Yönetimi"),
            "devir": (7, "Yıl Sonu Devir"),
            "export": (8, "Export & Yedekleme"),
            "ayarlar": (None, "Ayarlar"),
            # Yeni modüller
            "raporlar": (17, "Raporlar"),
            "tahakkuk": (18, "Tahakkuk Raporu"),
            "etkinlikler": (19, "Etkinlikler"),
            "toplantilar": (20, "Toplantılar"),
            "butce": (21, "Bütçe Planlama"),
            "kullanicilar": (22, "Kullanıcı Yönetimi"),
            "belgeler": (23, "Belge Yönetimi"),
            # KÖY modülü
            "koy_dashboard": (12, "Köy Dashboard"),
            "koy_gelir": (13, "Köy Gelirleri"),
            "koy_gider": (14, "Köy Giderleri"),
            "koy_virman": (15, "Köy Virmanları"),
            "koy_kasa": (16, "Köy Kasaları"),
        }
        
        if menu_id in menu_map:
            index, title = menu_map[menu_id]
            self.page_title.setText(title)
            
            if menu_id == "ayarlar":
                self.show_ayarlar()
            elif index is not None:
                self.stack.setCurrentIndex(index)
                self.statusBar().showMessage(f"{title} - Hazır")
                
    def refresh_current_page(self):
        """Aktif sayfayı yenile"""
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, 'load_data') or hasattr(current_widget, 'load_dashboard'):
            if hasattr(current_widget, 'load_dashboard'):
                current_widget.load_dashboard()
            elif hasattr(current_widget, 'load_data'):
                current_widget.load_data()
            self.statusBar().showMessage("Sayfa yenilendi", 2000)
        
    def create_menu_bar(self):
        """Menü bar oluştur"""
        menubar = self.menuBar()
        
        # Dosya Menüsü
        dosya_menu = menubar.addMenu("Dosya")
        
        export_action = QAction("Excel'e Export Et", self)
        export_action.triggered.connect(self.show_export)
        dosya_menu.addAction(export_action)
        
        yedekle_action = QAction("Veritabanını Yedekle", self)
        yedekle_action.triggered.connect(self.yedekle)
        dosya_menu.addAction(yedekle_action)
        
        dosya_menu.addSeparator()
        
        cikis_action = QAction("Çıkış", self)
        cikis_action.triggered.connect(self.close)
        dosya_menu.addAction(cikis_action)
        
        # Modüller Menüsü
        moduller_menu = menubar.addMenu("Modüller")
        
        dashboard_action = QAction("Dashboard", self)
        dashboard_action.triggered.connect(self.show_dashboard)
        moduller_menu.addAction(dashboard_action)
        
        moduller_menu.addSeparator()
        
        uyeler_action = QAction("Üyeler", self)
        uyeler_action.triggered.connect(self.show_uyeler)
        moduller_menu.addAction(uyeler_action)
        
        aidat_action = QAction("Aidat Takip", self)
        aidat_action.triggered.connect(self.show_aidat)
        moduller_menu.addAction(aidat_action)
        
        moduller_menu.addSeparator()
        
        gelir_action = QAction("Gelirler", self)
        gelir_action.triggered.connect(self.show_gelir)
        moduller_menu.addAction(gelir_action)
        
        gider_action = QAction("Giderler", self)
        gider_action.triggered.connect(self.show_gider)
        moduller_menu.addAction(gider_action)
        
        virman_action = QAction("Virman", self)
        virman_action.triggered.connect(self.show_virman)
        moduller_menu.addAction(virman_action)
        
        moduller_menu.addSeparator()
        
        kasa_action = QAction("Kasa Yönetimi", self)
        kasa_action.triggered.connect(self.show_kasa)
        moduller_menu.addAction(kasa_action)
        
        moduller_menu.addSeparator()
        
        devir_action = QAction("Yıl Sonu Devir", self)
        devir_action.triggered.connect(self.show_devir)
        moduller_menu.addAction(devir_action)
        
        # Ayarlar Menüsü
        ayarlar_menu = menubar.addMenu("Ayarlar")
        
        sistem_ayarlari_action = QAction("Sistem Ayarları", self)
        sistem_ayarlari_action.triggered.connect(self.show_ayarlar)
        ayarlar_menu.addAction(sistem_ayarlari_action)
        
        # Yardım Menüsü
        yardim_menu = menubar.addMenu("Yardım")
        
        hakkinda_action = QAction("Hakkında", self)
        hakkinda_action.triggered.connect(self.show_hakkinda)
        yardim_menu.addAction(hakkinda_action)
        
    def create_toolbar(self):
        """Toolbar oluştur"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # Dashboard
        dashboard_btn = QPushButton("📊 Dashboard")
        dashboard_btn.clicked.connect(self.show_dashboard)
        toolbar.addWidget(dashboard_btn)
        
        toolbar.addSeparator()
        
        # Üyeler
        uyeler_btn = QPushButton("👥 Üyeler")
        uyeler_btn.clicked.connect(self.show_uyeler)
        toolbar.addWidget(uyeler_btn)
        
        # Aidat
        aidat_btn = QPushButton("💳 Aidat")
        aidat_btn.clicked.connect(self.show_aidat)
        toolbar.addWidget(aidat_btn)
        
        toolbar.addSeparator()
        
        # Gelir
        gelir_btn = QPushButton("💰 Gelir")
        gelir_btn.clicked.connect(self.show_gelir)
        toolbar.addWidget(gelir_btn)
        
        # Gider
        gider_btn = QPushButton("💸 Gider")
        gider_btn.clicked.connect(self.show_gider)
        toolbar.addWidget(gider_btn)
        
        # Virman
        virman_btn = QPushButton("🔄 Virman")
        virman_btn.clicked.connect(self.show_virman)
        toolbar.addWidget(virman_btn)
        
        toolbar.addSeparator()
        
        # Kasa
        kasa_btn = QPushButton("🏦 Kasa")
        kasa_btn.clicked.connect(self.show_kasa)
        toolbar.addWidget(kasa_btn)
        
        toolbar.addSeparator()
        
        # Devir
        devir_btn = QPushButton("📅 Devir")
        devir_btn.clicked.connect(self.show_devir)
        toolbar.addWidget(devir_btn)
        
        # Export
        export_btn = QPushButton("📥 Export")
        export_btn.clicked.connect(self.show_export)
        toolbar.addWidget(export_btn)
        
    def show_dashboard(self):
        self.stack.setCurrentWidget(self.dashboard_widget)
        self.dashboard_widget.load_dashboard()
        self.statusBar().showMessage("Dashboard")
        
    def show_uyeler(self):
        self.stack.setCurrentWidget(self.uyeler_widget)
        self.uyeler_widget.load_uyeler()
        self.page_title.setText("Üye Yönetimi")
        self.statusBar().showMessage("Üye Yönetimi")
        
    def show_uye_detay(self, uye_id: int):
        """Üye detay sayfasını göster"""
        self.uye_detay_widget.load_uye(uye_id)
        self.stack.setCurrentWidget(self.uye_detay_widget)
        self.page_title.setText("Üye Detay")
        self.statusBar().showMessage("Üye Detay")
        
    def show_uye_aidat(self, uye_id: int):
        """Üye aidat sayfasını göster"""
        self.uye_aidat_widget.load_uye(uye_id)
        self.stack.setCurrentWidget(self.uye_aidat_widget)
        self.page_title.setText("Üye Aidat Takip")
        self.statusBar().showMessage("Üye Aidat Takip")
        
    def show_aidat(self):
        self.stack.setCurrentWidget(self.aidat_widget)
        self.aidat_widget.load_aidatlar()
        self.statusBar().showMessage("Aidat Takip")
        
    def show_gelir(self):
        self.stack.setCurrentWidget(self.gelir_widget)
        self.gelir_widget.load_gelirler()
        self.statusBar().showMessage("Gelir Yönetimi")
        
    def show_gider(self):
        self.stack.setCurrentWidget(self.gider_widget)
        self.gider_widget.load_giderler()
        self.statusBar().showMessage("Gider Yönetimi")
        
    def show_virman(self):
        self.stack.setCurrentWidget(self.virman_widget)
        self.virman_widget.load_virmanlar()
        self.statusBar().showMessage("Virman İşlemleri")
        
    def show_kasa(self):
        self.stack.setCurrentWidget(self.kasa_widget)
        self.kasa_widget.load_kasalar()
        self.statusBar().showMessage("Kasa Yönetimi")
        
    def show_devir(self):
        self.stack.setCurrentWidget(self.devir_widget)
        self.devir_widget.load_kasa_durumu()
        self.statusBar().showMessage("Yıl Sonu Devir İşlemleri")
        
    def show_export(self):
        self.stack.setCurrentWidget(self.export_widget)
        self.statusBar().showMessage("Export & Yedekleme")
        
    def yedekle(self):
        """Hızlı yedekleme"""
        from PyQt5.QtWidgets import QFileDialog
        from datetime import datetime
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Yedekleme Dosyası Kaydet",
            f"BADER_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database Files (*.db)"
        )
        
        if file_path:
            success = self.db.backup_database(file_path)
            if success:
                QMessageBox.information(self, "Başarılı", "Veritabanı başarıyla yedeklendi!")
            else:
                QMessageBox.critical(self, "Hata", "Yedekleme başarısız!")
                
    def show_ayarlar(self):
        """Ayarlar panelini göster"""
        form_widget = AyarlarFormWidget(self.db)
        drawer = DrawerPanel(self, "Sistem Ayarları", form_widget)
        
        def on_submit():
            if form_widget.kaydet():
                QMessageBox.information(self, "Başarılı", "Ayarlar kaydedildi!")
                drawer.close()
            else:
                QMessageBox.critical(self, "Hata", "Ayarlar kaydedilemedi!")
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def show_hakkinda(self):
        """Hakkında dialogunu göster"""
        QMessageBox.about(
            self,
            "Hakkında",
            "<h2>BADER Derneği</h2>"
            "<h3>Aidat - Gelir - Gider - Kasa Takip Sistemi</h3>"
            "<p><b>Versiyon:</b> 1.0.0</p>"
            "<p><b>Tarih:</b> 2025</p>"
            "<hr>"
            "<p>Bu yazılım dernek yönetimlerinin finansal işlemlerini "
            "kolayca takip edebilmeleri için geliştirilmiştir.</p>"
            "<p><b>Özellikler:</b></p>"
            "<ul>"
            "<li>Üye yönetimi</li>"
            "<li>Aidat takibi (otomatik gelir entegrasyonu)</li>"
            "<li>Gelir-gider yönetimi</li>"
            "<li>Çoklu kasa takibi</li>"
            "<li>Detaylı raporlama ve grafikler</li>"
            "<li>Excel export & Veritabanı yedekleme</li>"
            "</ul>"
        )
        
    def closeEvent(self, event):
        """Kapanış olayı"""
        reply = QMessageBox.question(
            self,
            "Çıkış",
            "Programdan çıkmak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()

