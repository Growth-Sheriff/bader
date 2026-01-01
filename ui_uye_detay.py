"""
BADER Derneği - Üye Detay Sayfası (Full Page)
Tek üyenin tüm bilgilerini gösteren tam sayfa
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QGridLayout, QScrollArea,
                             QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog, QFormLayout, QLineEdit,
                             QComboBox, QDateEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from qfluentwidgets import MessageBox
from PyQt5.QtGui import QFont
from database import Database
from models import UyeYoneticisi, AidatYoneticisi, AileUyeYoneticisi
from typing import Optional


class InfoCard(QFrame):
    """Bilgi kartı widget"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.08);
                border-radius: 10px;
            }
        """)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 16px;
                font-weight: 600;
                padding-bottom: 10px;
                border-bottom: 2px solid #64B5F6;
                background: transparent;
                border-radius: 0;
            }
        """)
        self.layout.addWidget(title_label)
        
        # İçerik için grid
        self.content_grid = QGridLayout()
        self.content_grid.setSpacing(10)
        self.layout.addLayout(self.content_grid)
        
        self.setLayout(self.layout)
        self.row_count = 0
        
    def add_field(self, label: str, value: str):
        """Alan ekle"""
        label_widget = QLabel(label + ":")
        label_widget.setStyleSheet("""
            QLabel {
                color: #6d6b77;
                font-size: 13px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
        """)
        
        value_widget = QLabel(value or "-")
        value_widget.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 14px;
                font-weight: 400;
                background: transparent;
                border: none;
            }
        """)
        value_widget.setWordWrap(True)
        
        self.content_grid.addWidget(label_widget, self.row_count, 0)
        self.content_grid.addWidget(value_widget, self.row_count, 1)
        self.row_count += 1


class UyeDetayWidget(QWidget):
    """Üye detay sayfası - Full Page"""
    
    geri_don = pyqtSignal()  # Listeye dön sinyali
    aidat_sayfasi_ac = pyqtSignal(int)  # Aidat sayfasına git sinyali
    
    def __init__(self, db: Database, uye_id: int = None):
        super().__init__()
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.aidat_yoneticisi = AidatYoneticisi(db)
        self.aile_yoneticisi = AileUyeYoneticisi(db)
        self.uye_id = uye_id
        self.uye_data = None
        
        self.setup_ui()
        
        if uye_id:
            self.load_uye(uye_id)
            
    def setup_ui(self):
        """UI'ı oluştur"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header Bar
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid rgba(47, 43, 61, 0.08);
            }
        """)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        # Geri butonu
        self.geri_btn = QPushButton("← Geri")
        self.geri_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64B5F6;
                border: none;
                font-size: 15px;
                font-weight: 500;
                padding: 10px 20px;
            }
            QPushButton:hover {
                color: #42A5F5;
                background-color: rgba(100, 181, 246, 0.1);
                border-radius: 8px;
            }
        """)
        self.geri_btn.clicked.connect(self.geri_don.emit)
        header_layout.addWidget(self.geri_btn)
        
        # Başlık
        self.title_label = QLabel("Üye Detay")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 20px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Düzenle butonu
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.uye_duzenle)
        header_layout.addWidget(self.duzenle_btn)
        
        # Aidat sayfasına git
        self.aidat_btn = QPushButton("💳 Aidat Detayı")
        self.aidat_btn.setStyleSheet("""
            QPushButton {
                background-color: #64B5F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.aidat_btn.clicked.connect(self.aidat_sayfasina_git)
        header_layout.addWidget(self.aidat_btn)
        
        header.setLayout(header_layout)
        main_layout.addWidget(header)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #f8f7fa;
                border: none;
            }
        """)
        
        # Content
        content = QWidget()
        content.setStyleSheet("background-color: #f8f7fa;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)
        
        # Üst satır: Kişisel + Adres
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        
        # Kişisel Bilgiler Kartı
        self.kisisel_card = InfoCard("KİŞİSEL BİLGİLER")
        self.kisisel_card.setMinimumWidth(350)
        top_row.addWidget(self.kisisel_card)
        
        # Adres Bilgileri Kartı
        self.adres_card = InfoCard("ADRES BİLGİLERİ")
        self.adres_card.setMinimumWidth(350)
        top_row.addWidget(self.adres_card)
        
        content_layout.addLayout(top_row)
        
        # Alt satır: İletişim + Aidat Özeti
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        
        # İletişim Kartı
        self.iletisim_card = InfoCard("İLETİŞİM BİLGİLERİ")
        self.iletisim_card.setMinimumWidth(350)
        bottom_row.addWidget(self.iletisim_card)
        
        # Aidat Özeti Kartı
        self.aidat_card = InfoCard("AİDAT ÖZETİ")
        self.aidat_card.setMinimumWidth(350)
        bottom_row.addWidget(self.aidat_card)
        
        content_layout.addLayout(bottom_row)
        
        # Aile Üyeleri Tablosu
        aile_group = QGroupBox("AİLE ÜYELERİ")
        aile_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.08);
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                color: #444050;
                padding-top: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        
        aile_layout = QVBoxLayout()
        aile_layout.setContentsMargins(15, 25, 15, 15)
        
        # Aile üyesi ekleme butonu
        aile_btn_layout = QHBoxLayout()
        aile_btn_layout.addStretch()
        
        self.aile_ekle_btn = QPushButton("➕ Aile Üyesi Ekle")
        self.aile_ekle_btn.setStyleSheet("""
            QPushButton {
                background-color: #66BB6A;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
            }
        """)
        self.aile_ekle_btn.clicked.connect(self.aile_uyesi_ekle)
        aile_btn_layout.addWidget(self.aile_ekle_btn)
        
        aile_layout.addLayout(aile_btn_layout)
        
        self.aile_table = QTableWidget()
        self.aile_table.setColumnCount(6)
        self.aile_table.setHorizontalHeaderLabels([
            "ID", "Yakınlık", "Ad Soyad", "Doğum Tarihi", "Telefon", "İşlemler"
        ])
        self.aile_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.aile_table.setColumnHidden(0, True)  # ID gizli
        self.aile_table.setAlternatingRowColors(True)
        self.aile_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.aile_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.aile_table.setMinimumHeight(150)
        
        aile_layout.addWidget(self.aile_table)
        aile_group.setLayout(aile_layout)
        content_layout.addWidget(aile_group)
        
        # Aidat Geçmişi Tablosu
        aidat_group = QGroupBox("AİDAT GEÇMİŞİ")
        aidat_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.08);
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                color: #444050;
                padding-top: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        
        aidat_layout = QVBoxLayout()
        aidat_layout.setContentsMargins(15, 25, 15, 15)
        
        self.aidat_table = QTableWidget()
        self.aidat_table.setColumnCount(5)
        self.aidat_table.setHorizontalHeaderLabels([
            "Yıl", "Yıllık Aidat", "Ödenen", "Kalan", "Durum"
        ])
        self.aidat_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.aidat_table.setAlternatingRowColors(True)
        self.aidat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.aidat_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.aidat_table.setMinimumHeight(200)
        
        aidat_layout.addWidget(self.aidat_table)
        aidat_group.setLayout(aidat_layout)
        content_layout.addWidget(aidat_group)
        
        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
        
    def load_uye(self, uye_id: int):
        """Üye verilerini yükle"""
        self.uye_id = uye_id
        self.uye_data = self.uye_yoneticisi.uye_getir(uye_id)
        
        if not self.uye_data:
            MessageBox("Hata", "Üye bulunamadı!", self).show()
            self.geri_don.emit()
            return
        
        # Başlığı güncelle
        self.title_label.setText(f"Üye Detay: {self.uye_data['ad_soyad']}")
        
        # Kartları temizle ve yeniden doldur
        self._clear_cards()
        self._fill_kisisel_bilgiler()
        self._fill_adres_bilgileri()
        self._fill_iletisim_bilgileri()
        self._fill_aidat_ozeti()
        self._fill_aile_uyeleri()
        self._fill_aidat_gecmisi()
        
    def _clear_cards(self):
        """Kartları temizle"""
        # Eski içerikleri kaldır
        for card in [self.kisisel_card, self.adres_card, self.iletisim_card, self.aidat_card]:
            while card.content_grid.count():
                item = card.content_grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            card.row_count = 0
            
    def _fill_kisisel_bilgiler(self):
        """Kişisel bilgileri doldur"""
        self.kisisel_card.add_field("Ad Soyad", self.uye_data.get('ad_soyad'))
        self.kisisel_card.add_field("Üye No", str(self.uye_data.get('uye_id', '')))
        self.kisisel_card.add_field("Durum", self.uye_data.get('durum'))
        self.kisisel_card.add_field("Kan Grubu", self.uye_data.get('kan_grubu'))
        self.kisisel_card.add_field("Aile Durumu", self.uye_data.get('aile_durumu'))
        self.kisisel_card.add_field("Çocuk Sayısı", str(self.uye_data.get('cocuk_sayisi', 0) or 0))
        self.kisisel_card.add_field("Doğum Tarihi", self.uye_data.get('dogum_tarihi'))
        self.kisisel_card.add_field("Kayıt Tarihi", str(self.uye_data.get('kayit_tarihi', ''))[:10])
        
        if self.uye_data.get('ayrilma_tarihi'):
            self.kisisel_card.add_field("Ayrılma Tarihi", self.uye_data.get('ayrilma_tarihi'))
        
    def _fill_adres_bilgileri(self):
        """Adres bilgilerini doldur"""
        self.adres_card.add_field("İl", self.uye_data.get('il'))
        self.adres_card.add_field("İlçe", self.uye_data.get('ilce'))
        self.adres_card.add_field("Mahalle", self.uye_data.get('mahalle'))
        self.adres_card.add_field("Adres", self.uye_data.get('adres'))
        self.adres_card.add_field("Posta Kodu", self.uye_data.get('posta_kodu'))
        
    def _fill_iletisim_bilgileri(self):
        """İletişim bilgilerini doldur"""
        self.iletisim_card.add_field("Telefon", self.uye_data.get('telefon'))
        self.iletisim_card.add_field("E-posta", self.uye_data.get('email'))
        self.iletisim_card.add_field("Notlar", self.uye_data.get('notlar'))
        
    def _fill_aidat_ozeti(self):
        """Aidat özetini doldur"""
        ozet = self.uye_yoneticisi.uye_aidat_ozeti(self.uye_id)
        
        toplam_yil = ozet.get('toplam_yil', 0) or 0
        odenen_yil = ozet.get('odenen_yil', 0) or 0
        toplam_borc = ozet.get('toplam_borc', 0) or 0
        odenen_toplam = ozet.get('odenen_toplam', 0) or 0
        kalan_borc = ozet.get('kalan_borc', 0) or 0
        
        self.aidat_card.add_field("Kayıtlı Yıl Sayısı", str(toplam_yil))
        self.aidat_card.add_field("Ödenen Yıl Sayısı", str(odenen_yil))
        self.aidat_card.add_field("Toplam Beklenen", f"{toplam_borc:,.2f} ₺")
        self.aidat_card.add_field("Toplam Ödenen", f"{odenen_toplam:,.2f} ₺")
        
        # Kalan borç - renkli
        kalan_label = QLabel("Kalan Borç:")
        kalan_label.setStyleSheet("color: #6d6b77; font-size: 13px; font-weight: 500; background: transparent; border: none;")
        
        if kalan_borc > 0:
            kalan_value = QLabel(f"{kalan_borc:,.2f} ₺")
            kalan_value.setStyleSheet("color: #f44336; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        else:
            kalan_value = QLabel("0.00 ₺ ✓")
            kalan_value.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        
        self.aidat_card.content_grid.addWidget(kalan_label, self.aidat_card.row_count, 0)
        self.aidat_card.content_grid.addWidget(kalan_value, self.aidat_card.row_count, 1)
        self.aidat_card.row_count += 1
        
    def _fill_aidat_gecmisi(self):
        """Aidat geçmişi tablosunu doldur"""
        yillar = self.uye_yoneticisi.uye_aidat_yillari(self.uye_id)
        
        self.aidat_table.setRowCount(len(yillar))
        
        for row, aidat in enumerate(yillar):
            self.aidat_table.setItem(row, 0, QTableWidgetItem(str(aidat['yil'])))
            self.aidat_table.setItem(row, 1, QTableWidgetItem(f"{aidat['yillik_aidat_tutari']:,.2f} ₺"))
            self.aidat_table.setItem(row, 2, QTableWidgetItem(f"{aidat['toplam_odenen']:,.2f} ₺"))
            self.aidat_table.setItem(row, 3, QTableWidgetItem(f"{aidat['odenecek_tutar']:,.2f} ₺"))
            
            durum_item = QTableWidgetItem(aidat['durum'])
            if aidat['durum'] == 'Tamamlandı':
                durum_item.setForeground(Qt.GlobalColor.darkGreen)
            elif aidat['durum'] == 'Kısmi':
                durum_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                durum_item.setForeground(Qt.GlobalColor.darkRed)
            self.aidat_table.setItem(row, 4, durum_item)
            
    def uye_duzenle(self):
        """Üyeyi düzenle - Drawer açılacak"""
        from ui_uyeler import UyeFormWidget
        from ui_drawer import DrawerPanel
        
        form_widget = UyeFormWidget(uye_data=self.uye_data)
        drawer = DrawerPanel(self, "Üye Düzenle", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            if not data['ad_soyad']:
                MessageBox("Uyarı", "Ad Soyad boş bırakılamaz!", self).show()
                return
            
            try:
                self.uye_yoneticisi.uye_guncelle(self.uye_id, **data)
                self.load_uye(self.uye_id)  # Yeniden yükle
                MessageBox("Başarılı", "Üye güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Güncelleme hatası:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def aidat_sayfasina_git(self):
        """Aidat sayfasına git"""
        self.aidat_sayfasi_ac.emit(self.uye_id)
    
    def _fill_aile_uyeleri(self):
        """Aile üyeleri tablosunu doldur"""
        aile_uyeleri = self.aile_yoneticisi.aile_uyeleri_listesi(self.uye_id)
        
        self.aile_table.setRowCount(len(aile_uyeleri))
        
        for row, aile in enumerate(aile_uyeleri):
            self.aile_table.setItem(row, 0, QTableWidgetItem(str(aile['aile_uye_id'])))
            self.aile_table.setItem(row, 1, QTableWidgetItem(aile['yakinlik']))
            self.aile_table.setItem(row, 2, QTableWidgetItem(aile['ad_soyad']))
            self.aile_table.setItem(row, 3, QTableWidgetItem(aile.get('dogum_tarihi') or '-'))
            self.aile_table.setItem(row, 4, QTableWidgetItem(aile.get('telefon') or '-'))
            
            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(5, 2, 5, 2)
            btn_layout.setSpacing(5)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 26)
            edit_btn.setStyleSheet("QPushButton { background: #64B5F6; color: white; border: none; border-radius: 4px; } QPushButton:hover { background: #42A5F5; }")
            edit_btn.clicked.connect(lambda checked, aid=aile['aile_uye_id']: self.aile_uyesi_duzenle(aid))
            btn_layout.addWidget(edit_btn)
            
            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(30, 26)
            del_btn.setStyleSheet("QPushButton { background: #EF5350; color: white; border: none; border-radius: 4px; } QPushButton:hover { background: #F44336; }")
            del_btn.clicked.connect(lambda checked, aid=aile['aile_uye_id']: self.aile_uyesi_sil(aid))
            btn_layout.addWidget(del_btn)
            
            btn_layout.addStretch()
            btn_widget.setLayout(btn_layout)
            self.aile_table.setCellWidget(row, 5, btn_widget)
    
    def aile_uyesi_ekle(self):
        """Yeni aile üyesi ekle"""
        dialog = AileUyeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.aile_yoneticisi.aile_uyesi_ekle(
                    uye_id=self.uye_id,
                    yakinlik=data['yakinlik'],
                    ad_soyad=data['ad_soyad'],
                    dogum_tarihi=data['dogum_tarihi'],
                    telefon=data['telefon'],
                    meslek=data['meslek'],
                    notlar=data['notlar']
                )
                self._fill_aile_uyeleri()
                MessageBox("Başarılı", "Aile üyesi eklendi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Ekleme hatası:\n{e}", self).show()
    
    def aile_uyesi_duzenle(self, aile_uye_id: int):
        """Aile üyesi düzenle"""
        aile_data = self.aile_yoneticisi.aile_uyesi_getir(aile_uye_id)
        if not aile_data:
            return
        
        dialog = AileUyeDialog(self, aile_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.aile_yoneticisi.aile_uyesi_guncelle(
                    aile_uye_id=aile_uye_id,
                    yakinlik=data['yakinlik'],
                    ad_soyad=data['ad_soyad'],
                    dogum_tarihi=data['dogum_tarihi'],
                    telefon=data['telefon'],
                    meslek=data['meslek'],
                    notlar=data['notlar']
                )
                self._fill_aile_uyeleri()
                MessageBox("Başarılı", "Aile üyesi güncellendi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Güncelleme hatası:\n{e}", self).show()
    
    def aile_uyesi_sil(self, aile_uye_id: int):
        """Aile üyesi sil"""
        msg = MessageBox("Silme Onayı", "Bu aile üyesini silmek istediğinize emin misiniz?", self)
        if msg.exec():
            try:
                self.aile_yoneticisi.aile_uyesi_sil(aile_uye_id)
                self._fill_aile_uyeleri()
                MessageBox("Başarılı", "Aile üyesi silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Silme hatası:\n{e}", self).show()


class AileUyeDialog(QDialog):
    """Aile üyesi ekleme/düzenleme dialog'u"""
    
    def __init__(self, parent=None, aile_data: dict = None):
        super().__init__(parent)
        self.aile_data = aile_data
        self.setWindowTitle("Aile Üyesi Ekle" if not aile_data else "Aile Üyesi Düzenle")
        self.setMinimumWidth(400)
        self.setup_ui()
        
        if aile_data:
            self.load_data()
    
    def setup_ui(self):
        layout = QFormLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Yakınlık
        self.yakinlik_combo = QComboBox()
        self.yakinlik_combo.addItems(['Eş', 'Çocuk', 'Anne', 'Baba', 'Kardeş', 'Diğer'])
        layout.addRow("Yakınlık:", self.yakinlik_combo)
        
        # Ad Soyad
        self.ad_soyad_edit = QLineEdit()
        self.ad_soyad_edit.setPlaceholderText("Ad Soyad")
        layout.addRow("Ad Soyad:", self.ad_soyad_edit)
        
        # Doğum Tarihi
        self.dogum_tarihi_edit = QDateEdit()
        self.dogum_tarihi_edit.setCalendarPopup(True)
        self.dogum_tarihi_edit.setDate(QDate(1990, 1, 1))
        layout.addRow("Doğum Tarihi:", self.dogum_tarihi_edit)
        
        # Telefon
        self.telefon_edit = QLineEdit()
        self.telefon_edit.setPlaceholderText("05XX XXX XX XX")
        layout.addRow("Telefon:", self.telefon_edit)
        
        # Meslek
        self.meslek_edit = QLineEdit()
        self.meslek_edit.setPlaceholderText("Meslek")
        layout.addRow("Meslek:", self.meslek_edit)
        
        # Notlar
        self.notlar_edit = QLineEdit()
        self.notlar_edit.setPlaceholderText("Notlar")
        layout.addRow("Notlar:", self.notlar_edit)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        iptal_btn = QPushButton("İptal")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        
        kaydet_btn = QPushButton("Kaydet")
        kaydet_btn.setStyleSheet("background-color: #64B5F6; color: white; border: none; padding: 10px 20px; border-radius: 6px;")
        kaydet_btn.clicked.connect(self.validate_and_accept)
        btn_layout.addWidget(kaydet_btn)
        
        layout.addRow("", btn_layout)
        self.setLayout(layout)
    
    def load_data(self):
        """Mevcut verileri yükle"""
        if self.aile_data:
            self.yakinlik_combo.setCurrentText(self.aile_data.get('yakinlik', 'Diğer'))
            self.ad_soyad_edit.setText(self.aile_data.get('ad_soyad', ''))
            
            if self.aile_data.get('dogum_tarihi'):
                self.dogum_tarihi_edit.setDate(QDate.fromString(self.aile_data['dogum_tarihi'], "yyyy-MM-dd"))
            
            self.telefon_edit.setText(self.aile_data.get('telefon', ''))
            self.meslek_edit.setText(self.aile_data.get('meslek', ''))
            self.notlar_edit.setText(self.aile_data.get('notlar', ''))
    
    def validate_and_accept(self):
        """Doğrulama ve kabul"""
        if not self.ad_soyad_edit.text().strip():
            MessageBox("Uyarı", "Ad Soyad alanı zorunludur!", self).show()
            return
        self.accept()
    
    def get_data(self) -> dict:
        """Form verilerini döndür"""
        return {
            'yakinlik': self.yakinlik_combo.currentText(),
            'ad_soyad': self.ad_soyad_edit.text().strip(),
            'dogum_tarihi': self.dogum_tarihi_edit.date().toString("yyyy-MM-dd"),
            'telefon': self.telefon_edit.text().strip(),
            'meslek': self.meslek_edit.text().strip(),
            'notlar': self.notlar_edit.text().strip()
        }
