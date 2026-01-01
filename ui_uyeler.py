"""
BADER Derneği - Üye Yönetimi UI (DRAWER PANEL) - v2 Genişletilmiş
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QHeaderView, QComboBox, QScrollArea, QFrame,
                             QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from qfluentwidgets import MessageBox
from database import Database
from models import UyeYoneticisi
from ui_drawer import DrawerPanel
from ui_login import session
from ui_form_fields import (FormField, create_line_edit, create_text_edit, create_combo_box,
                            create_spin_box, create_date_edit, create_double_spin_box)
from ui_helpers import make_searchable_combobox, export_table_to_excel, setup_resizable_table
from typing import Optional


class UyeFormWidget(QWidget):
    """Üye formu - Drawer içinde kullanılacak (Genişletilmiş v2)"""
    
    SECTION_STYLE = """
        QLabel {
            color: #64B5F6;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 8px 0 5px 0;
            border-bottom: 2px solid #64B5F6;
            margin-top: 10px;
        }
    """
    
    def __init__(self, parent=None, uye_data: Optional[dict] = None, db: Database = None):
        super().__init__(parent)
        self.uye_data = uye_data
        self.db = db
        self.setup_ui()
        
        if uye_data:
            self.load_data()
            
    def setup_ui(self):
        """UI'ı oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # === TEMEL BİLGİLER ===
        section1 = QLabel("TEMEL BİLGİLER")
        section1.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section1)
        
        # Üye No
        self.uye_no_edit = create_line_edit("Üye No", "Ör: 001")
        layout.addWidget(self.uye_no_edit[0])
        
        # TC Kimlik No
        self.tc_kimlik_edit = create_line_edit("TC Kimlik No", "11111111111")
        layout.addWidget(self.tc_kimlik_edit[0])
        
        # Ad Soyad
        self.ad_soyad_edit = create_line_edit("Ad Soyad *", "Üyenin adı ve soyadı")
        layout.addWidget(self.ad_soyad_edit[0])
        
        # Üyelik Tipi
        self.uyelik_tipi_combo = create_combo_box("Üyelik Tipi", searchable=False)
        self.uyelik_tipi_combo[1].addItems(["Asil", "Onursal", "Fahri", "Kurumsal"])
        layout.addWidget(self.uyelik_tipi_combo[0])
        
        # Durum
        self.durum_combo = create_combo_box("Durum", searchable=False)
        self.durum_combo[1].addItems(["Aktif", "Pasif"])
        layout.addWidget(self.durum_combo[0])
        
        # === İLETİŞİM BİLGİLERİ ===
        section2 = QLabel("İLETİŞİM BİLGİLERİ")
        section2.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section2)
        
        # Telefon
        self.telefon_edit = create_line_edit("Telefon", "0555 555 55 55")
        layout.addWidget(self.telefon_edit[0])
        
        # 2. Telefon
        self.telefon2_edit = create_line_edit("2. Telefon", "0555 555 55 55")
        layout.addWidget(self.telefon2_edit[0])
        
        # E-posta
        self.email_edit = create_line_edit("E-posta", "ornek@email.com")
        layout.addWidget(self.email_edit[0])
        
        # === KİŞİSEL BİLGİLER ===
        section3 = QLabel("KİŞİSEL BİLGİLER")
        section3.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section3)
        
        # Cinsiyet
        self.cinsiyet_combo = create_combo_box("Cinsiyet", searchable=False)
        self.cinsiyet_combo[1].addItems(["", "Erkek", "Kadın"])
        layout.addWidget(self.cinsiyet_combo[0])
        
        # Doğum Tarihi
        self.dogum_tarihi_edit = create_date_edit("Doğum Tarihi")
        layout.addWidget(self.dogum_tarihi_edit[0])
        
        # Doğum Yeri
        self.dogum_yeri_edit = create_line_edit("Doğum Yeri", "İstanbul")
        layout.addWidget(self.dogum_yeri_edit[0])
        
        # Kan Grubu
        self.kan_grubu_combo = create_combo_box("Kan Grubu", searchable=False)
        self.kan_grubu_combo[1].addItems(["", "A+", "A-", "B+", "B-", "AB+", "AB-", "0+", "0-"])
        layout.addWidget(self.kan_grubu_combo[0])
        
        # Aile Durumu
        self.aile_durumu_combo = create_combo_box("Aile Durumu", searchable=False)
        self.aile_durumu_combo[1].addItems(["Bekar", "Evli", "Dul", "Boşanmış"])
        layout.addWidget(self.aile_durumu_combo[0])
        
        # Çocuk Sayısı
        self.cocuk_sayisi_spin = create_spin_box("Çocuk Sayısı")
        self.cocuk_sayisi_spin[1].setMinimum(0)
        self.cocuk_sayisi_spin[1].setMaximum(20)
        layout.addWidget(self.cocuk_sayisi_spin[0])
        
        # === MESLEK BİLGİLERİ ===
        section4 = QLabel("MESLEK BİLGİLERİ")
        section4.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section4)
        
        # Eğitim Durumu
        self.egitim_combo = create_combo_box("Eğitim Durumu", searchable=False)
        self.egitim_combo[1].addItems(["", "İlkokul", "Ortaokul", "Lise", "Ön Lisans", "Lisans", "Yüksek Lisans", "Doktora"])
        layout.addWidget(self.egitim_combo[0])
        
        # Meslek
        self.meslek_edit = create_line_edit("Meslek", "Mühendis, Doktor, vb.")
        layout.addWidget(self.meslek_edit[0])
        
        # İş Yeri
        self.is_yeri_edit = create_line_edit("İş Yeri", "Çalıştığı kurum/şirket")
        layout.addWidget(self.is_yeri_edit[0])
        
        # === ADRES BİLGİLERİ ===
        section5 = QLabel("ADRES BİLGİLERİ")
        section5.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section5)
        
        # İl
        self.il_edit = create_line_edit("İl", "İstanbul")
        layout.addWidget(self.il_edit[0])
        
        # İlçe
        self.ilce_edit = create_line_edit("İlçe", "Kadıköy")
        layout.addWidget(self.ilce_edit[0])
        
        # Mahalle
        self.mahalle_edit = create_line_edit("Mahalle", "Caferağa")
        layout.addWidget(self.mahalle_edit[0])
        
        # Adres
        self.adres_edit = create_text_edit("Adres", "Açık adres...", max_height=50)
        layout.addWidget(self.adres_edit[0])
        
        # Posta Kodu
        self.posta_kodu_edit = create_line_edit("Posta Kodu", "34710")
        layout.addWidget(self.posta_kodu_edit[0])
        
        # === AİDAT BİLGİLERİ ===
        section6 = QLabel("AİDAT BİLGİLERİ")
        section6.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section6)
        
        # Özel Aidat Tutarı
        self.ozel_aidat_spin = create_double_spin_box("Özel Aidat Tutarı")
        self.ozel_aidat_spin[1].setMaximum(1000000)
        self.ozel_aidat_spin[1].setSuffix(" ₺")
        self.ozel_aidat_spin[1].setSpecialValueText("Varsayılan")
        layout.addWidget(self.ozel_aidat_spin[0])
        
        # Aidat İndirimi
        self.indirim_spin = create_double_spin_box("Aidat İndirimi %")
        self.indirim_spin[1].setMaximum(100)
        self.indirim_spin[1].setSuffix(" %")
        layout.addWidget(self.indirim_spin[0])
        
        # === DİĞER ===
        section7 = QLabel("DİĞER")
        section7.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section7)
        
        # Referans Üye (ComboBox - aranabilir)
        self.referans_combo = create_combo_box("Referans Üye", searchable=True)
        self.referans_combo[1].addItem("Seçiniz...", None)
        # Üyeleri yükle
        if self.db:
            try:
                uye_yoneticisi = UyeYoneticisi(self.db)
                uyeler = uye_yoneticisi.uye_listesi()
                for u in uyeler:
                    self.referans_combo[1].addItem(u['ad_soyad'], u['uye_id'])
            except:
                pass
        layout.addWidget(self.referans_combo[0])
        
        # Notlar
        self.notlar_edit = create_text_edit("Notlar", "Üye hakkında notlar...", max_height=60)
        layout.addWidget(self.notlar_edit[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_data(self):
        """Mevcut üye verilerini yükle"""
        if not self.uye_data:
            return
            
        # Temel bilgiler
        self.uye_no_edit[1].setText(self.uye_data.get('uye_no', '') or '')
        self.tc_kimlik_edit[1].setText(self.uye_data.get('tc_kimlik', '') or '')
        self.ad_soyad_edit[1].setText(self.uye_data.get('ad_soyad', ''))
        
        uyelik_tipi = self.uye_data.get('uyelik_tipi', 'Asil')
        idx = self.uyelik_tipi_combo[1].findText(uyelik_tipi or 'Asil')
        if idx >= 0:
            self.uyelik_tipi_combo[1].setCurrentIndex(idx)
        
        self.durum_combo[1].setCurrentText(self.uye_data.get('durum', 'Aktif'))
        
        # İletişim
        self.telefon_edit[1].setText(self.uye_data.get('telefon', '') or '')
        self.telefon2_edit[1].setText(self.uye_data.get('telefon2', '') or '')
        self.email_edit[1].setText(self.uye_data.get('email', '') or '')
        
        # Kişisel
        cinsiyet = self.uye_data.get('cinsiyet', '')
        idx = self.cinsiyet_combo[1].findText(cinsiyet or '')
        if idx >= 0:
            self.cinsiyet_combo[1].setCurrentIndex(idx)
        
        dogum = self.uye_data.get('dogum_tarihi')
        if dogum:
            self.dogum_tarihi_edit[1].setDate(QDate.fromString(dogum, "yyyy-MM-dd"))
        
        self.dogum_yeri_edit[1].setText(self.uye_data.get('dogum_yeri', '') or '')
        
        kan_grubu = self.uye_data.get('kan_grubu', '')
        idx = self.kan_grubu_combo[1].findText(kan_grubu or '')
        if idx >= 0:
            self.kan_grubu_combo[1].setCurrentIndex(idx)
        
        aile_durumu = self.uye_data.get('aile_durumu', 'Bekar')
        self.aile_durumu_combo[1].setCurrentText(aile_durumu or 'Bekar')
        
        self.cocuk_sayisi_spin[1].setValue(self.uye_data.get('cocuk_sayisi', 0) or 0)
        
        # Meslek
        egitim = self.uye_data.get('egitim_durumu', '')
        idx = self.egitim_combo[1].findText(egitim or '')
        if idx >= 0:
            self.egitim_combo[1].setCurrentIndex(idx)
        
        self.meslek_edit[1].setText(self.uye_data.get('meslek', '') or '')
        self.is_yeri_edit[1].setText(self.uye_data.get('is_yeri', '') or '')
        
        # Adres
        self.il_edit[1].setText(self.uye_data.get('il', '') or '')
        self.ilce_edit[1].setText(self.uye_data.get('ilce', '') or '')
        self.mahalle_edit[1].setText(self.uye_data.get('mahalle', '') or '')
        self.adres_edit[1].setPlainText(self.uye_data.get('adres', '') or '')
        self.posta_kodu_edit[1].setText(self.uye_data.get('posta_kodu', '') or '')
        
        # Aidat
        ozel_aidat = self.uye_data.get('ozel_aidat_tutari')
        if ozel_aidat:
            self.ozel_aidat_spin[1].setValue(ozel_aidat)
        
        indirim = self.uye_data.get('aidat_indirimi_yuzde', 0) or 0
        self.indirim_spin[1].setValue(indirim)
        
        # Referans
        referans_id = self.uye_data.get('referans_uye_id')
        if referans_id:
            for i in range(self.referans_combo[1].count()):
                if self.referans_combo[1].itemData(i) == referans_id:
                    self.referans_combo[1].setCurrentIndex(i)
                    break
        
        # Notlar
        self.notlar_edit[1].setPlainText(self.uye_data.get('notlar', '') or '')
            
    def get_data(self) -> dict:
        """Form verilerini al"""
        dogum = self.dogum_tarihi_edit[1].date().toString("yyyy-MM-dd")
        if dogum == "2000-01-01":
            dogum = None
        
        ozel_aidat = self.ozel_aidat_spin[1].value()
        if ozel_aidat == 0:
            ozel_aidat = None
            
        return {
            'uye_no': self.uye_no_edit[1].text().strip() or None,
            'tc_kimlik': self.tc_kimlik_edit[1].text().strip(),
            'ad_soyad': self.ad_soyad_edit[1].text().strip(),
            'uyelik_tipi': self.uyelik_tipi_combo[1].currentText(),
            'durum': self.durum_combo[1].currentText(),
            'telefon': self.telefon_edit[1].text().strip(),
            'telefon2': self.telefon2_edit[1].text().strip(),
            'email': self.email_edit[1].text().strip(),
            'cinsiyet': self.cinsiyet_combo[1].currentText(),
            'dogum_tarihi': dogum,
            'dogum_yeri': self.dogum_yeri_edit[1].text().strip(),
            'kan_grubu': self.kan_grubu_combo[1].currentText(),
            'aile_durumu': self.aile_durumu_combo[1].currentText(),
            'cocuk_sayisi': self.cocuk_sayisi_spin[1].value(),
            'egitim_durumu': self.egitim_combo[1].currentText(),
            'meslek': self.meslek_edit[1].text().strip(),
            'is_yeri': self.is_yeri_edit[1].text().strip(),
            'il': self.il_edit[1].text().strip(),
            'ilce': self.ilce_edit[1].text().strip(),
            'mahalle': self.mahalle_edit[1].text().strip(),
            'adres': self.adres_edit[1].toPlainText().strip(),
            'posta_kodu': self.posta_kodu_edit[1].text().strip(),
            'ozel_aidat_tutari': ozel_aidat,
            'aidat_indirimi_yuzde': self.indirim_spin[1].value(),
            'referans_uye_id': self.referans_combo[1].currentData(),
            'notlar': self.notlar_edit[1].toPlainText().strip()
        }
    
    def validate(self) -> bool:
        """Form validasyonu"""
        if not self.ad_soyad_edit[1].text().strip():
            MessageBox("Uyarı", "Ad Soyad alanı zorunludur!", self).show()
            return False
        
        # TC Kimlik kontrolü
        tc = self.tc_kimlik_edit[1].text().strip()
        if tc and (len(tc) != 11 or not tc.isdigit()):
            MessageBox("Uyarı", "TC Kimlik No 11 haneli olmalıdır!", self).show()
            return False
            
        return True


class UyeWidget(QWidget):
    """Üye yönetimi ana widget"""
    
    uye_secildi = pyqtSignal(int)
    uye_detay_ac = pyqtSignal(int)
    uye_aidat_ac = pyqtSignal(int)
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.current_uye_id = None
        
        self.setup_ui()
        self.load_uyeler()
        self.apply_permissions()
    
    def apply_permissions(self):
        """Kullanıcı izinlerine göre butonları ayarla"""
        self.ekle_btn.setVisible(session.has_permission('uye_ekle'))
        self.duzenle_btn.setVisible(session.has_permission('uye_duzenle'))
        self.sil_btn.setVisible(session.has_permission('uye_sil'))
        
    def setup_ui(self):
        """UI'ı oluştur"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("ÜYE YÖNETİMİ")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Arama
        self.arama_edit = QLineEdit()
        self.arama_edit.setPlaceholderText("🔍 Üye ara (isim, TC, telefon)...")
        self.arama_edit.textChanged.connect(self.ara)
        self.arama_edit.setMaximumWidth(300)
        toolbar_layout.addWidget(self.arama_edit)
        
        # Üyelik tipi filtresi
        toolbar_layout.addWidget(QLabel("Tip:"))
        self.tip_filter = QComboBox()
        self.tip_filter.addItems(["Tümü", "Asil", "Onursal", "Fahri", "Kurumsal"])
        self.tip_filter.currentIndexChanged.connect(self.load_uyeler)
        self.tip_filter.setMaximumWidth(100)
        toolbar_layout.addWidget(self.tip_filter)
        
        toolbar_layout.addStretch()
        
        # Butonlar
        self.ekle_btn = QPushButton("➕ Yeni Üye")
        self.ekle_btn.clicked.connect(self.uye_ekle)
        toolbar_layout.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.uye_duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar_layout.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.uye_sil)
        self.sil_btn.setEnabled(False)
        toolbar_layout.addWidget(self.sil_btn)
        
        self.detay_btn = QPushButton("👁️ Detay")
        self.detay_btn.setStyleSheet("""
            QPushButton {
                background-color: #64B5F6;
                color: white;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.detay_btn.clicked.connect(self.uye_detay)
        self.detay_btn.setEnabled(False)
        toolbar_layout.addWidget(self.detay_btn)
        
        self.aidat_btn = QPushButton("💳 Aidat")
        self.aidat_btn.clicked.connect(self.uye_aidat)
        self.aidat_btn.setEnabled(False)
        toolbar_layout.addWidget(self.aidat_btn)
        
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.setToolTip("Listeyi Excel'e Aktar")
        self.export_btn.clicked.connect(self.export_to_excel)
        toolbar_layout.addWidget(self.export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Üye No", "TC Kimlik", "Ad Soyad", "Telefon", "E-posta", "Üyelik Tipi", "Meslek", "Durum"
        ])
        
        # Responsive sütunlar - hareket ettirilebilir, sağ tık ile gizle/göster
        setup_resizable_table(self.table, table_id="uyeler_tablosu", stretch_column=3)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.uye_duzenle)
        
        layout.addWidget(self.table)
        
        # İstatistik
        self.stats_label = QLabel("Toplam: 0 üye")
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        
    def load_uyeler(self):
        """Üyeleri yükle"""
        # Tip filtresi
        tip = self.tip_filter.currentText() if self.tip_filter.currentIndex() > 0 else None
        
        uyeler = self.uye_yoneticisi.uye_listesi()
        
        # Tip filtreleme
        if tip:
            uyeler = [u for u in uyeler if u.get('uyelik_tipi') == tip]
        
        self.table.setRowCount(len(uyeler))
        
        for row, uye in enumerate(uyeler):
            self.table.setItem(row, 0, QTableWidgetItem(str(uye['uye_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(uye.get('uye_no', '') or '-'))
            
            # TC Kimlik - maskeleme
            tc = uye.get('tc_kimlik', '') or ''
            if tc and len(tc) == 11:
                tc = tc[:3] + '****' + tc[-2:]
            self.table.setItem(row, 2, QTableWidgetItem(tc or '-'))
            
            self.table.setItem(row, 3, QTableWidgetItem(uye['ad_soyad']))
            self.table.setItem(row, 4, QTableWidgetItem(uye['telefon'] or '-'))
            self.table.setItem(row, 5, QTableWidgetItem(uye['email'] or '-'))
            self.table.setItem(row, 6, QTableWidgetItem(uye.get('uyelik_tipi', 'Asil') or 'Asil'))
            self.table.setItem(row, 7, QTableWidgetItem(uye.get('meslek', '') or '-'))
            
            # Durum renklendirme
            durum_item = QTableWidgetItem(uye['durum'])
            if uye['durum'] == 'Aktif':
                durum_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                durum_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, 8, durum_item)
        
        # İstatistik güncelle
        aktif = len([u for u in uyeler if u['durum'] == 'Aktif'])
        self.stats_label.setText(f"Toplam: {len(uyeler)} üye ({aktif} aktif)")
        
    def ara(self):
        """Üye ara"""
        arama_metni = self.arama_edit.text().strip().lower()
        
        for row in range(self.table.rowCount()):
            match = False
            for col in [1, 2, 3, 4, 5, 7]:  # Üye No, TC, Ad, Telefon, Email, Meslek
                item = self.table.item(row, col)
                if item and arama_metni in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
            
    def on_selection_changed(self):
        """Seçim değiştiğinde"""
        selected = self.table.selectedItems()
        if selected:
            self.current_uye_id = int(self.table.item(selected[0].row(), 0).text())
            self.duzenle_btn.setEnabled(True)
            self.sil_btn.setEnabled(True)
            self.detay_btn.setEnabled(True)
            self.aidat_btn.setEnabled(True)
            self.uye_secildi.emit(self.current_uye_id)
        else:
            self.current_uye_id = None
            self.duzenle_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
            self.detay_btn.setEnabled(False)
            self.aidat_btn.setEnabled(False)
            
    def uye_ekle(self):
        """Yeni üye ekle"""
        form_widget = UyeFormWidget(db=self.db)
        drawer = DrawerPanel(self, "Yeni Üye Ekle", form_widget)
        
        def on_submit():
            if not form_widget.validate():
                return
                
            data = form_widget.get_data()
            try:
                self.uye_yoneticisi.uye_ekle(**data)
                self.load_uyeler()
                MessageBox("Başarılı", "Üye başarıyla eklendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def uye_duzenle(self):
        """Üye düzenle"""
        if not self.current_uye_id:
            return
            
        uye_data = self.uye_yoneticisi.uye_getir(self.current_uye_id)
        if not uye_data:
            return
            
        form_widget = UyeFormWidget(uye_data=uye_data, db=self.db)
        drawer = DrawerPanel(self, "Üye Düzenle", form_widget)
        
        def on_submit():
            if not form_widget.validate():
                return
                
            data = form_widget.get_data()
            try:
                self.uye_yoneticisi.uye_guncelle(self.current_uye_id, **data)
                self.load_uyeler()
                MessageBox("Başarılı", "Üye başarıyla güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Üye güncellenirken hata: {str(e)}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def uye_sil(self):
        """Üyeyi sil"""
        if not self.current_uye_id:
            return
        
        # Silme modu kontrolü
        self.db.cursor.execute("SELECT ayar_degeri FROM ayarlar WHERE ayar_adi = 'uye_silme_modu'")
        result = self.db.cursor.fetchone()
        silme_modu = result['ayar_degeri'] if result else 'soft_delete'
        
        if silme_modu == 'cascade':
            mesaj = ("Bu üyeyi KALICI olarak silmek istediğinizden emin misiniz?\n\n"
                    "⚠️ DİKKAT: Üyenin TÜM aidat kayıtları da silinecektir!\n"
                    "Bu işlem geri alınamaz!")
        else:
            mesaj = ("Bu üyeyi 'Ayrıldı' olarak işaretlemek istediğinizden emin misiniz?\n\n"
                    "Üyenin aidat ve ödeme kayıtları korunacaktır.")
            
        w = MessageBox("Üye Sil", mesaj, self)
        if w.exec():
            try:
                self.uye_yoneticisi.uye_sil(self.current_uye_id, mode=silme_modu)
                self.load_uyeler()
                self.current_uye_id = None
                
                if silme_modu == 'cascade':
                    MessageBox("Başarılı", "Üye kalıcı olarak silindi!", self).show()
                else:
                    MessageBox("Başarılı", "Üye 'Ayrıldı' olarak işaretlendi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Üye silinirken hata: {str(e)}", self).show()
    
    def uye_detay(self):
        """Üye detay sayfasına git"""
        if self.current_uye_id:
            self.uye_detay_ac.emit(self.current_uye_id)
    
    def uye_aidat(self):
        """Üye aidat sayfasına git"""
        if self.current_uye_id:
            self.uye_aidat_ac.emit(self.current_uye_id)
    
    def export_to_excel(self):
        """Üye listesini Excel'e aktar"""
        export_table_to_excel(self.table, "uyeler", self)
