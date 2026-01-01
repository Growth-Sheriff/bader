"""
BADER Derneği - Aidat Takip UI
Otomatik gelir senkronizasyonu ile
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QDialog, QFormLayout, QSpinBox,
                             QDoubleSpinBox, QDateEdit, QHeaderView, QGroupBox,
                             QListWidget, QSplitter, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QIcon, QColor
from qfluentwidgets import MessageBox
from database import Database
from models import UyeYoneticisi, AidatYoneticisi
from datetime import datetime
from typing import Optional
from ui_drawer import DrawerPanel
from ui_form_fields import create_combo_box, create_spin_box, create_double_spin_box, create_date_edit, create_line_edit
from ui_helpers import export_table_to_excel, setup_resizable_table
from ui_login import session


class TopluAidatFormWidget(QWidget):
    """Toplu aidat kaydı oluşturma formu"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Bilgi
        info_label = QLabel("Tüm aktif üyeler için seçilen yıla ait aidat kaydı oluşturulacaktır.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 13px;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 6px;
            }
        """)
        layout.addWidget(info_label)
        
        # Yıl
        self.yil_spin = create_spin_box("Yıl")
        self.yil_spin[1].setMinimum(2020)
        self.yil_spin[1].setMaximum(2050)
        self.yil_spin[1].setValue(datetime.now().year)
        layout.addWidget(self.yil_spin[0])
        
        # Tutar
        self.tutar_spin = create_double_spin_box("Yıllık Aidat Tutarı")
        self.tutar_spin[1].setMinimum(0)
        self.tutar_spin[1].setMaximum(1000000)
        self.tutar_spin[1].setValue(1000)
        self.tutar_spin[1].setSuffix(" ₺")
        layout.addWidget(self.tutar_spin[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def get_data(self):
        return {
            'yil': self.yil_spin[1].value(),
            'tutar': self.tutar_spin[1].value()
        }


class AidatOdemeFormWidget(QWidget):
    """Aidat ödemesi ekleme formu - Yıl seçimi ile"""
    
    def __init__(self, kalan_tutar: float = 0, mevcut_yil: int = None, uye_yillari: list = None, db: Database = None, uye_id: int = None):
        super().__init__()
        self.kalan_tutar = kalan_tutar
        self.mevcut_yil = mevcut_yil or datetime.now().year
        self.uye_yillari = uye_yillari or []  # Üyenin borçlu olduğu yıllar
        self.db = db
        self.uye_id = uye_id
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Yıl seçimi
        self.yil_combo = create_combo_box("Ödeme Yapılacak Yıl *")
        
        # Borçlu yılları ekle
        if self.uye_yillari:
            for yil_bilgi in self.uye_yillari:
                if isinstance(yil_bilgi, dict):
                    yil = yil_bilgi.get('yil', 0)
                    kalan = yil_bilgi.get('kalan', 0)
                    self.yil_combo[1].addItem(f"{yil} (Borç: {kalan:,.2f} ₺)", yil_bilgi)
                else:
                    self.yil_combo[1].addItem(str(yil_bilgi), {'yil': yil_bilgi, 'kalan': 0})
        else:
            # Varsayılan olarak mevcut yıl
            self.yil_combo[1].addItem(str(self.mevcut_yil), {'yil': self.mevcut_yil, 'kalan': self.kalan_tutar})
        
        self.yil_combo[1].currentIndexChanged.connect(self.on_yil_changed)
        layout.addWidget(self.yil_combo[0])
        
        # Kalan borç bilgisi
        self.borc_label = QLabel(f"Kalan Borç: {self.kalan_tutar:.2f} ₺")
        self.borc_label.setStyleSheet("""
            QLabel {
                color: #E65100;
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
                background-color: #FFF3E0;
                border-radius: 6px;
                border-left: 3px solid #FF9800;
            }
        """)
        if self.kalan_tutar > 0:
            layout.addWidget(self.borc_label)
        
        # Tarih
        self.tarih_edit = create_date_edit("Tarih")
        self.tarih_edit[1].setDate(QDate.currentDate())
        layout.addWidget(self.tarih_edit[0])
        
        # Tutar
        self.tutar_spin = create_double_spin_box("Tutar *")
        self.tutar_spin[1].setMinimum(0.01)
        self.tutar_spin[1].setMaximum(1000000)
        self.tutar_spin[1].setValue(self.kalan_tutar if self.kalan_tutar > 0 else 100)
        self.tutar_spin[1].setSuffix(" ₺")
        layout.addWidget(self.tutar_spin[0])
        
        # Tahsilat Türü
        self.tahsilat_combo = create_combo_box("Tahsilat Türü")
        self.tahsilat_combo[1].addItems(["Nakit", "Banka Transferi", "Kredi Kartı", "Havale/EFT", "Çek"])
        layout.addWidget(self.tahsilat_combo[0])
        
        # Banka Bilgisi
        self.banka_edit = create_line_edit("Banka/Şube", "Banka adı ve şube...")
        layout.addWidget(self.banka_edit[0])
        
        # Dekont Numarası
        self.dekont_edit = create_line_edit("Dekont No", "Dekont numarası...")
        layout.addWidget(self.dekont_edit[0])
        
        # Açıklama
        self.aciklama_edit = create_line_edit("Açıklama", "Ödeme ile ilgili notlar...")
        layout.addWidget(self.aciklama_edit[0])
        
        layout.addStretch()
        self.setLayout(layout)
    
    def on_yil_changed(self, index):
        """Yıl seçimi değiştiğinde borç bilgisini güncelle"""
        data = self.yil_combo[1].currentData()
        if data:
            kalan = data.get('kalan', 0)
            self.borc_label.setText(f"Kalan Borç: {kalan:,.2f} ₺")
            self.borc_label.setVisible(kalan > 0)
            if kalan > 0:
                self.tutar_spin[1].setValue(kalan)
        
    def get_data(self):
        yil_data = self.yil_combo[1].currentData() or {}
        return {
            'yil': yil_data.get('yil', self.mevcut_yil),
            'aidat_id': yil_data.get('aidat_id'),
            'tarih': self.tarih_edit[1].date().toString("yyyy-MM-dd"),
            'tutar': self.tutar_spin[1].value(),
            'tahsilat_turu': self.tahsilat_combo[1].currentText(),
            'banka': self.banka_edit[1].text().strip(),
            'dekont_no': self.dekont_edit[1].text().strip(),
            'aciklama': self.aciklama_edit[1].text().strip()
        }


class AidatKayitFormWidget(QWidget):
    """Tek üye için aidat kaydı oluşturma formu"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.setup_ui()
        self.load_uyeler()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Üye
        self.uye_combo = create_combo_box("Üye *")
        layout.addWidget(self.uye_combo[0])
        
        # Yıl
        self.yil_spin = create_spin_box("Yıl")
        self.yil_spin[1].setMinimum(2020)
        self.yil_spin[1].setMaximum(2050)
        self.yil_spin[1].setValue(datetime.now().year)
        layout.addWidget(self.yil_spin[0])
        
        # Tutar
        self.tutar_spin = create_double_spin_box("Yıllık Aidat Tutarı")
        self.tutar_spin[1].setMinimum(0)
        self.tutar_spin[1].setMaximum(1000000)
        self.tutar_spin[1].setValue(1000)
        self.tutar_spin[1].setSuffix(" ₺")
        layout.addWidget(self.tutar_spin[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_uyeler(self):
        uyeler = self.uye_yoneticisi.uye_listesi(durum='Aktif')
        self.uye_combo[1].clear()
        
        for uye in uyeler:
            self.uye_combo[1].addItem(uye['ad_soyad'], uye['uye_id'])
            
    def get_data(self):
        return {
            'uye_id': self.uye_combo[1].currentData(),
            'yil': self.yil_spin[1].value(),
            'tutar': self.tutar_spin[1].value()
        }


class AidatWidget(QWidget):
    """Aidat takip ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.aidat_yoneticisi = AidatYoneticisi(db)
        self.selected_aidat_id = None
        self.setup_ui()
        self.load_aidatlar()
        self.apply_permissions()
    
    def apply_permissions(self):
        """Kullanıcı izinlerine göre butonları ayarla"""
        can_edit = session.has_permission('aidat_duzenle')
        can_collect = session.has_permission('aidat_tahsilat')
        self.toplu_olustur_btn.setVisible(can_edit)
        self.tek_olustur_btn.setVisible(can_edit)
        self.odeme_ekle_btn.setVisible(can_collect)
        self.odeme_sil_btn.setVisible(can_edit)
        self.aidat_export_btn.setVisible(session.has_permission('rapor_export'))
        self.odeme_export_btn.setVisible(session.has_permission('rapor_export'))
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("AİDAT TAKİP SİSTEMİ")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Uyarı
        warning_label = QLabel(
            "⚙️ Aidat 'Tamamlandı' durumuna geldiğinde otomatik olarak Gelirler modülüne aktarılır."
        )
        warning_label.setProperty("class", "warning")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Filtreler
        toolbar_layout.addWidget(QLabel("Yıl:"))
        self.yil_filter = QComboBox()
        self.yil_filter.addItem("Tümü", None)
        # Tek yıl seçenekleri
        for yil in range(datetime.now().year + 2, 2019, -1):
            self.yil_filter.addItem(str(yil), yil)
        # Çoklu yıl seçenekleri
        self.yil_filter.addItem("─" * 10, None)  # Ayraç
        for yil in range(datetime.now().year + 1, 2021, -1):
            self.yil_filter.addItem(f"{yil}-{yil+1}", f"{yil}-{yil+1}")
        for yil in range(datetime.now().year, 2020, -1):
            self.yil_filter.addItem(f"{yil-2}-{yil}", f"{yil-2}-{yil}")
        self.yil_filter.currentIndexChanged.connect(self.load_aidatlar)
        self.yil_filter.setMinimumWidth(150)
        toolbar_layout.addWidget(self.yil_filter)
        
        toolbar_layout.addWidget(QLabel("Durum:"))
        self.durum_filter = QComboBox()
        self.durum_filter.addItems(["Tümü", "Tamamlandı", "Kısmi", "Eksik"])
        self.durum_filter.currentTextChanged.connect(self.load_aidatlar)
        self.durum_filter.setMaximumWidth(150)
        toolbar_layout.addWidget(self.durum_filter)
        
        toolbar_layout.addStretch()
        
        # Butonlar
        self.toplu_olustur_btn = QPushButton("📋 Toplu Aidat Oluştur")
        self.toplu_olustur_btn.clicked.connect(self.toplu_aidat_olustur)
        toolbar_layout.addWidget(self.toplu_olustur_btn)
        
        self.tek_olustur_btn = QPushButton("➕ Tek Kayıt Oluştur")
        self.tek_olustur_btn.clicked.connect(self.tek_aidat_olustur)
        toolbar_layout.addWidget(self.tek_olustur_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Splitter (üst: aidat listesi, alt: ödemeler)
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Üst panel: Aidat listesi
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.aidat_table = QTableWidget()
        self.aidat_table.setColumnCount(8)
        self.aidat_table.setHorizontalHeaderLabels([
            "ID", "Üye", "Yıl", "Yıllık Aidat", "Toplam Ödenen", 
            "Kalan", "Durum", "Aktarım"
        ])
        
        # Sütun genişliklerini responsive yap
        setup_resizable_table(self.aidat_table, table_id="aidat_tablosu", stretch_column=1)
        
        self.aidat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.aidat_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.aidat_table.setAlternatingRowColors(True)
        self.aidat_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Aidat tablosu için inline editing kapalı (karmaşık hesaplamalar var)
        self.aidat_table.itemSelectionChanged.connect(self.on_aidat_selected)
        
        top_layout.addWidget(self.aidat_table)
        top_widget.setLayout(top_layout)
        
        # Alt panel: Ödemeler
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        odeme_header_layout = QHBoxLayout()
        odeme_label = QLabel("ÖDEMELER")
        odeme_label.setProperty("class", "subtitle")
        odeme_header_layout.addWidget(odeme_label)
        odeme_header_layout.addStretch()
        
        self.odeme_ekle_btn = QPushButton("💰 Ödeme Ekle")
        self.odeme_ekle_btn.clicked.connect(self.odeme_ekle)
        self.odeme_ekle_btn.setEnabled(False)
        odeme_header_layout.addWidget(self.odeme_ekle_btn)
        
        self.odeme_sil_btn = QPushButton("🗑️ Ödeme Sil")
        self.odeme_sil_btn.setProperty("class", "danger")
        self.odeme_sil_btn.clicked.connect(self.odeme_sil)
        self.odeme_sil_btn.setEnabled(False)
        odeme_header_layout.addWidget(self.odeme_sil_btn)
        
        self.makbuz_btn = QPushButton("🖨️ Makbuz")
        self.makbuz_btn.setToolTip("Tahsilat makbuzu oluştur")
        self.makbuz_btn.clicked.connect(self.makbuz_yazdir)
        self.makbuz_btn.setEnabled(False)
        odeme_header_layout.addWidget(self.makbuz_btn)
        
        odeme_header_layout.addStretch()
        
        # Excel export
        self.aidat_export_btn = QPushButton("📊 Aidat Excel")
        self.aidat_export_btn.setToolTip("Aidat Listesini Excel'e Aktar")
        self.aidat_export_btn.clicked.connect(lambda: export_table_to_excel(self.aidat_table, "aidat_takip", self))
        odeme_header_layout.addWidget(self.aidat_export_btn)
        
        self.odeme_export_btn = QPushButton("📊 Ödeme Excel")
        self.odeme_export_btn.setToolTip("Ödeme Listesini Excel'e Aktar")
        self.odeme_export_btn.clicked.connect(lambda: export_table_to_excel(self.odeme_table, "aidat_odemeler", self))
        odeme_header_layout.addWidget(self.odeme_export_btn)
        
        bottom_layout.addLayout(odeme_header_layout)
        
        self.odeme_table = QTableWidget()
        self.odeme_table.setColumnCount(6)
        self.odeme_table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Tutar", "Tahsilat Türü", "Dekont No", "Açıklama"
        ])
        
        # Sütun genişliklerini responsive yap
        setup_resizable_table(self.odeme_table, table_id="aidat_odemeler_tablosu", stretch_column=5)
        
        self.odeme_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.odeme_table.setAlternatingRowColors(True)
        self.odeme_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Inline editing KAPALI
        self.odeme_table.itemSelectionChanged.connect(self.on_odeme_selected)
        
        bottom_layout.addWidget(self.odeme_table)
        bottom_widget.setLayout(bottom_layout)
        
        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # İstatistikler
        stats_layout = QHBoxLayout()
        self.toplam_label = QLabel("Toplam Kayıt: 0")
        self.tamamlanan_label = QLabel("Tamamlanan: 0")
        self.tamamlanan_label.setProperty("class", "success")
        self.eksik_label = QLabel("Eksik/Kısmi: 0")
        self.eksik_label.setProperty("class", "danger")
        
        stats_layout.addWidget(self.toplam_label)
        stats_layout.addWidget(self.tamamlanan_label)
        stats_layout.addWidget(self.eksik_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        
    def load_aidatlar(self):
        """Aidat kayıtlarını yükle"""
        yil_data = self.yil_filter.currentData()
        durum_text = self.durum_filter.currentText()
        
        # Çoklu yıl kontrolü
        if isinstance(yil_data, str) and '-' in yil_data:
            # Çoklu yıl aralığı: "2024-2026" formatı
            try:
                yillar = yil_data.split('-')
                baslangic_yil = int(yillar[0])
                bitis_yil = int(yillar[1])
                
                # Tüm yılları al ve filtrele
                aidatlar = self.aidat_yoneticisi.aidat_listesi()
                aidatlar = [a for a in aidatlar if baslangic_yil <= a['yil'] <= bitis_yil]
            except:
                aidatlar = self.aidat_yoneticisi.aidat_listesi()
        else:
            # Tek yıl veya tümü
            aidatlar = self.aidat_yoneticisi.aidat_listesi(yil=yil_data)
        
        # Durum filtreleme
        if durum_text != "Tümü":
            aidatlar = [a for a in aidatlar if a['durum'] == durum_text]
        
        self.aidat_table.setRowCount(0)
        
        for aidat in aidatlar:
            row = self.aidat_table.rowCount()
            self.aidat_table.insertRow(row)
            
            self.aidat_table.setItem(row, 0, QTableWidgetItem(str(aidat['aidat_id'])))
            self.aidat_table.setItem(row, 1, QTableWidgetItem(aidat['ad_soyad']))
            self.aidat_table.setItem(row, 2, QTableWidgetItem(str(aidat['yil'])))
            self.aidat_table.setItem(row, 3, QTableWidgetItem(f"{aidat['yillik_aidat_tutari']:.2f} ₺"))
            self.aidat_table.setItem(row, 4, QTableWidgetItem(f"{aidat['toplam_odenen']:.2f} ₺"))
            
            kalan = aidat['odenecek_tutar']
            kalan_item = QTableWidgetItem(f"{kalan:.2f} ₺")
            if kalan > 0:
                kalan_item.setForeground(Qt.GlobalColor.darkRed)
            else:
                kalan_item.setForeground(Qt.GlobalColor.darkGreen)
            self.aidat_table.setItem(row, 5, kalan_item)
            
            durum_item = QTableWidgetItem(aidat['durum'])
            if aidat['durum'] == 'Tamamlandı':
                durum_item.setForeground(Qt.GlobalColor.darkGreen)
            elif aidat['durum'] == 'Kısmi':
                durum_item.setForeground(QColor(255, 140, 0))
            else:
                durum_item.setForeground(Qt.GlobalColor.darkRed)
            self.aidat_table.setItem(row, 6, durum_item)
            
            aktarim_item = QTableWidgetItem(aidat['aktarim_durumu'])
            if aidat['aktarim_durumu'] == 'Aktarıldı':
                aktarim_item.setForeground(Qt.GlobalColor.darkGreen)
            self.aidat_table.setItem(row, 7, aktarim_item)
        
        # İstatistikleri güncelle
        self.update_stats()
        
        # Ödemeleri temizle
        self.odeme_table.setRowCount(0)
        self.selected_aidat_id = None
        self.odeme_ekle_btn.setEnabled(False)
        
    def update_stats(self):
        """İstatistikleri güncelle"""
        toplam = self.aidat_table.rowCount()
        tamamlanan = 0
        eksik = 0
        
        for row in range(toplam):
            durum = self.aidat_table.item(row, 6).text()
            if durum == "Tamamlandı":
                tamamlanan += 1
            else:
                eksik += 1
        
        self.toplam_label.setText(f"Toplam Kayıt: {toplam}")
        self.tamamlanan_label.setText(f"Tamamlanan: {tamamlanan}")
        self.eksik_label.setText(f"Eksik/Kısmi: {eksik}")
        
    def on_aidat_selected(self):
        """Aidat seçildiğinde ödemeleri yükle"""
        if not self.aidat_table.selectionModel().hasSelection():
            return
            
        row = self.aidat_table.currentRow()
        self.selected_aidat_id = int(self.aidat_table.item(row, 0).text())
        
        self.odeme_ekle_btn.setEnabled(True)
        self.load_odemeler()
        
    def load_odemeler(self):
        """Seçili aidatın ödemelerini yükle"""
        if not self.selected_aidat_id:
            return
        
        odemeler = self.aidat_yoneticisi.uye_aidat_odemeleri(self.selected_aidat_id)
        
        self.odeme_table.setRowCount(0)
        
        for odeme in odemeler:
            row = self.odeme_table.rowCount()
            self.odeme_table.insertRow(row)
            
            self.odeme_table.setItem(row, 0, QTableWidgetItem(str(odeme['odeme_id'])))
            self.odeme_table.setItem(row, 1, QTableWidgetItem(odeme['tarih']))
            self.odeme_table.setItem(row, 2, QTableWidgetItem(f"{odeme['tutar']:.2f} ₺"))
            self.odeme_table.setItem(row, 3, QTableWidgetItem(odeme['tahsilat_turu']))
            self.odeme_table.setItem(row, 4, QTableWidgetItem(odeme.get('dekont_no', '') or '-'))
            self.odeme_table.setItem(row, 5, QTableWidgetItem(odeme['aciklama'] or '-'))
        
    def on_odeme_selected(self):
        """Ödeme seçildiğinde"""
        has_selection = self.odeme_table.selectionModel().hasSelection()
        self.odeme_sil_btn.setEnabled(has_selection)
        self.makbuz_btn.setEnabled(has_selection)
    
    def toplu_aidat_olustur(self):
        """Toplu aidat kaydı oluştur"""
        form_widget = TopluAidatFormWidget()
        drawer = DrawerPanel(self, "Toplu Aidat Kaydı Oluştur", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            w = MessageBox("Toplu Aidat Oluştur", 
                          f"Tüm aktif üyeler için {data['yil']} yılı aidatı ({data['tutar']:.2f} ₺) oluşturulsun mu?", 
                          self)
            if w.exec():
                try:
                    olusturulan = self.aidat_yoneticisi.toplu_aidat_olustur(data['yil'], data['tutar'])
                    self.load_aidatlar()
                    MessageBox("Başarılı", f"{olusturulan} adet aidat kaydı oluşturuldu!"
                    , 
                        self).show()
                    drawer.close()
                except Exception as e:
                    MessageBox("Hata", f"Hata oluştu:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def tek_aidat_olustur(self):
        """Tek üye için aidat kaydı oluştur"""
        form_widget = AidatKayitFormWidget(self.db)
        drawer = DrawerPanel(self, "Tek Kayıt Oluştur", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            try:
                self.aidat_yoneticisi.aidat_kaydi_olustur(
                    data['uye_id'], data['yil'], data['tutar']
                )
                self.load_aidatlar()
                MessageBox("Başarılı", "Aidat kaydı oluşturuldu!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Hata oluştu:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def odeme_ekle(self):
        """Ödeme ekle - Yıl seçimi ile"""
        if not self.selected_aidat_id:
            return
            
        # Seçili aidat kaydının üye bilgisini al
        row = self.aidat_table.currentRow()
        kalan_text = self.aidat_table.item(row, 5).text().replace(" ₺", "").replace(",", "")
        kalan = float(kalan_text)
        mevcut_yil = int(self.aidat_table.item(row, 2).text())
        
        # Üyenin tüm borçlu yıllarını bul
        uye_adi = self.aidat_table.item(row, 1).text()
        
        # Tüm aidat kayıtlarından bu üyenin borçlarını bul
        uye_yillari = []
        for i in range(self.aidat_table.rowCount()):
            if self.aidat_table.item(i, 1).text() == uye_adi:
                yil = int(self.aidat_table.item(i, 2).text())
                kalan_str = self.aidat_table.item(i, 5).text().replace(" ₺", "").replace(",", "")
                kalan_tutar = float(kalan_str)
                aidat_id = int(self.aidat_table.item(i, 0).text())
                durum = self.aidat_table.item(i, 6).text()
                
                if kalan_tutar > 0 or durum != "Tamamlandı":
                    uye_yillari.append({
                        'yil': yil,
                        'kalan': kalan_tutar,
                        'aidat_id': aidat_id
                    })
        
        # Seçili yılı en üste al
        uye_yillari.sort(key=lambda x: (x['aidat_id'] != self.selected_aidat_id, x['yil']))
        
        form_widget = AidatOdemeFormWidget(
            kalan_tutar=kalan,
            mevcut_yil=mevcut_yil,
            uye_yillari=uye_yillari,
            db=self.db
        )
        drawer = DrawerPanel(self, f"💰 Ödeme Ekle - {uye_adi}", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            aidat_id = data.get('aidat_id') or self.selected_aidat_id
            
            try:
                self.aidat_yoneticisi.aidat_odeme_ekle(
                    aidat_id,
                    data['tarih'],
                    data['tutar'],
                    data.get('aciklama', ''),
                    data.get('tahsilat_turu', 'Nakit')
                )
                self.load_aidatlar()
                # Aynı kaydı tekrar seç
                for i in range(self.aidat_table.rowCount()):
                    if int(self.aidat_table.item(i, 0).text()) == aidat_id:
                        self.aidat_table.selectRow(i)
                        break
                MessageBox("Başarılı", "Ödeme kaydedildi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Hata oluştu:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def odeme_sil(self):
        """Ödeme sil"""
        if not self.odeme_table.selectionModel().hasSelection():
            return
            
        row = self.odeme_table.currentRow()
        odeme_id = int(self.odeme_table.item(row, 0).text())
        tutar = self.odeme_table.item(row, 2).text()
        
        w = MessageBox("Ödeme Sil", f"{tutar} tutarındaki ödemeyi silmek istediğinize emin misiniz?", self)
        if w.exec():
            try:
                self.aidat_yoneticisi.aidat_odeme_sil(odeme_id)
                self.load_aidatlar()
                # Aynı kaydı tekrar seç
                for i in range(self.aidat_table.rowCount()):
                    if int(self.aidat_table.item(i, 0).text()) == self.selected_aidat_id:
                        self.aidat_table.selectRow(i)
                        break
                MessageBox("Başarılı", "Ödeme silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Hata oluştu:\n{e}", self).show()
    
    def makbuz_yazdir(self):
        """Seçili ödeme için makbuz oluştur"""
        if not self.odeme_table.selectionModel().hasSelection():
            return
        
        row = self.odeme_table.currentRow()
        odeme_id = int(self.odeme_table.item(row, 0).text())
        tarih = self.odeme_table.item(row, 1).text()
        tutar = self.odeme_table.item(row, 2).text().replace(' ₺', '').replace(',', '')
        odeme_sekli = self.odeme_table.item(row, 3).text()
        aciklama = self.odeme_table.item(row, 5).text()
        
        # Üye bilgisi
        if not self.selected_aidat_id:
            return
        
        aidat_row = self.aidat_table.currentRow()
        ad_soyad = self.aidat_table.item(aidat_row, 1).text() if aidat_row >= 0 else "-"
        yil = self.aidat_table.item(aidat_row, 2).text() if aidat_row >= 0 else "-"
        
        try:
            from pdf_generator import MakbuzGenerator
            
            makbuz_gen = MakbuzGenerator(self.db)
            odeme_data = {
                'tarih': tarih,
                'tutar': float(tutar) if tutar else 0,
                'ad_soyad': ad_soyad,
                'aciklama': aciklama if aciklama != '-' else f"{yil} yılı aidat ödemesi",
                'odeme_sekli': odeme_sekli
            }
            
            dosya = makbuz_gen.generate_makbuz(odeme_id, odeme_data)
            MessageBox("Başarılı", f"Makbuz oluşturuldu ve tarayıcıda açıldı.\n\nDosya: {dosya}"
            , 
                self).show()
        except Exception as e:
            MessageBox("Hata", f"Makbuz oluşturulurken hata:\n{e}", self).show()

