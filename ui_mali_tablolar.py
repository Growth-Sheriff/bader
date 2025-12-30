"""
BADER Derneği - Mali Tablolar Modülü
Bilanço, Gelir Tablosu, Nakit Akış raporları
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDateEdit, QFrame, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from qfluentwidgets import PushButton, TitleLabel, SubtitleLabel, BodyLabel, CardWidget
from database import Database
from models import MaliTabloYoneticisi, RaporYoneticisi
from datetime import datetime
from ui_helpers import export_table_to_excel


class StatCardLarge(CardWidget):
    """Büyük istatistik kartı"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#64B5F6"):
        super().__init__()
        self.color = color
        self.setMinimumHeight(120)
        self.setMinimumWidth(220)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Başlık
        title_label = BodyLabel(title)
        title_label.setStyleSheet(f"""
            color: #666;
            font-size: 12px;
            font-weight: 600;
        """)
        layout.addWidget(title_label)
        
        # Değer
        self.value_label = TitleLabel(value)
        self.value_label.setStyleSheet(f"""
            color: {color};
            font-size: 28px;
            font-weight: 700;
        """)
        layout.addWidget(self.value_label)
        
        # Alt yazı
        if subtitle:
            subtitle_label = BodyLabel(subtitle)
            subtitle_label.setStyleSheet("""
                color: #999;
                font-size: 11px;
            """)
            layout.addWidget(subtitle_label)
        
        self.setLayout(layout)
    
    def set_value(self, value: str):
        self.value_label.setText(value)


class BilancoWidget(QWidget):
    """Bilanço raporu"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.mali_tablo_yoneticisi = MaliTabloYoneticisi(db)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Başlık ve tarih seçici
        header_layout = QHBoxLayout()
        
        title = TitleLabel("BİLANÇO RAPORU")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        header_layout.addWidget(BodyLabel("Tarih:"))
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        self.tarih_edit.dateChanged.connect(self.load_data)
        header_layout.addWidget(self.tarih_edit)
        
        self.yenile_btn = PushButton("🔄 Yenile")
        self.yenile_btn.clicked.connect(self.load_data)
        header_layout.addWidget(self.yenile_btn)
        
        layout.addLayout(header_layout)
        
        # Ana grid
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        
        # Sol: VARLIKLAR
        varlik_group = QGroupBox("VARLIKLAR (AKTİF)")
        varlik_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #2E7D32;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        varlik_layout = QVBoxLayout()
        varlik_layout.setSpacing(10)
        
        # Dönen Varlıklar
        varlik_layout.addWidget(SubtitleLabel("Dönen Varlıklar"))
        
        self.kasalar_table = QTableWidget()
        self.kasalar_table.setColumnCount(2)
        self.kasalar_table.setHorizontalHeaderLabels(["Kasa", "Tutar"])
        self.kasalar_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.kasalar_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.kasalar_table.setMaximumHeight(200)
        self.kasalar_table.setAlternatingRowColors(True)
        varlik_layout.addWidget(self.kasalar_table)
        
        self.aidat_alacak_label = BodyLabel("Aidat Alacakları: 0.00 ₺")
        varlik_layout.addWidget(self.aidat_alacak_label)
        
        self.diger_alacak_label = BodyLabel("Diğer Alacaklar: 0.00 ₺")
        varlik_layout.addWidget(self.diger_alacak_label)
        
        self.donen_toplam_label = TitleLabel("Toplam: 0.00 ₺")
        self.donen_toplam_label.setStyleSheet("color: #2E7D32; border-top: 2px solid #4CAF50; padding-top: 10px;")
        varlik_layout.addWidget(self.donen_toplam_label)
        
        varlik_layout.addStretch()
        
        # Toplam Varlık
        self.toplam_varlik_label = TitleLabel("TOPLAM VARLIK: 0.00 ₺")
        self.toplam_varlik_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1B5E20;
            background-color: #E8F5E9;
            padding: 15px;
            border-radius: 6px;
        """)
        varlik_layout.addWidget(self.toplam_varlik_label)
        
        varlik_group.setLayout(varlik_layout)
        main_layout.addWidget(varlik_group)
        
        # Sağ: KAYNAKLAR
        kaynak_group = QGroupBox("KAYNAKLAR (PASİF)")
        kaynak_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1565C0;
                border: 2px solid #2196F3;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        kaynak_layout = QVBoxLayout()
        kaynak_layout.setSpacing(10)
        
        kaynak_layout.addWidget(SubtitleLabel("Kısa Vadeli Yükümlülükler"))
        
        self.verecekler_label = BodyLabel("Borçlar: 0.00 ₺")
        kaynak_layout.addWidget(self.verecekler_label)
        
        kaynak_layout.addWidget(SubtitleLabel("Öz Kaynaklar"))
        
        self.sermaye_label = BodyLabel("Dernek Sermayesi: 0.00 ₺")
        kaynak_layout.addWidget(self.sermaye_label)
        
        kaynak_layout.addWidget(SubtitleLabel("Dönem Sonuçları"))
        
        self.gelir_label = BodyLabel("Toplam Gelir: 0.00 ₺")
        kaynak_layout.addWidget(self.gelir_label)
        
        self.gider_label = BodyLabel("Toplam Gider: 0.00 ₺")
        kaynak_layout.addWidget(self.gider_label)
        
        self.kar_zarar_label = TitleLabel("Net Sonuç: 0.00 ₺")
        self.kar_zarar_label.setStyleSheet("color: #1565C0; border-top: 2px solid #2196F3; padding-top: 10px;")
        kaynak_layout.addWidget(self.kar_zarar_label)
        
        kaynak_layout.addStretch()
        
        # Toplam Kaynak
        self.toplam_kaynak_label = TitleLabel("TOPLAM KAYNAK: 0.00 ₺")
        self.toplam_kaynak_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #0D47A1;
            background-color: #E3F2FD;
            padding: 15px;
            border-radius: 6px;
        """)
        kaynak_layout.addWidget(self.toplam_kaynak_label)
        
        kaynak_group.setLayout(kaynak_layout)
        main_layout.addWidget(kaynak_group)
        
        layout.addLayout(main_layout)
        
        # Denge kontrolü
        self.denge_label = BodyLabel("")
        self.denge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.denge_label)
        
        self.setLayout(layout)
        
    def load_data(self):
        """Bilanço verilerini yükle"""
        tarih = self.tarih_edit.date().toString("yyyy-MM-dd")
        bilanco = self.mali_tablo_yoneticisi.bilanco_raporu(tarih)
        
        # Kasalar
        kasalar = bilanco['varliklar']['donen_varliklar']['kasalar']['detay']
        self.kasalar_table.setRowCount(len(kasalar))
        
        for row, kasa in enumerate(kasalar):
            self.kasalar_table.setItem(row, 0, QTableWidgetItem(f"{kasa['kasa_adi']} ({kasa['para_birimi']})"))
            
            tutar_item = QTableWidgetItem(f"{kasa['net_bakiye']:,.2f}")
            tutar_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if kasa['net_bakiye'] < 0:
                tutar_item.setForeground(QColor("#C62828"))
            self.kasalar_table.setItem(row, 1, tutar_item)
        
        # Aidat alacakları
        aidat_alacak = bilanco['varliklar']['donen_varliklar']['aidat_alacaklari']
        self.aidat_alacak_label.setText(f"Aidat Alacakları: {aidat_alacak:,.2f} ₺")
        
        # Diğer alacaklar
        diger_alacak = bilanco['varliklar']['donen_varliklar']['diger_alacaklar']
        self.diger_alacak_label.setText(f"Diğer Alacaklar: {diger_alacak:,.2f} ₺")
        
        # Dönen varlıklar toplam
        donen_toplam = bilanco['varliklar']['donen_varliklar']['toplam']
        self.donen_toplam_label.setText(f"Toplam: {donen_toplam:,.2f} ₺")
        
        # Toplam varlık
        toplam_varlik = bilanco['varliklar']['toplam']
        self.toplam_varlik_label.setText(f"TOPLAM VARLIK: {toplam_varlik:,.2f} ₺")
        
        # Verecekler
        verecekler = bilanco['kaynaklar']['kisa_vadeli_yukumlulukler']
        self.verecekler_label.setText(f"Borçlar: {verecekler:,.2f} ₺")
        
        # Dernek sermayesi
        sermaye = bilanco['kaynaklar']['dernek_sermayesi']
        self.sermaye_label.setText(f"Dernek Sermayesi: {sermaye:,.2f} ₺")
        
        # Gelir-Gider
        gelir = bilanco['kaynaklar']['donem_sonucu']['toplam_gelir']
        gider = bilanco['kaynaklar']['donem_sonucu']['toplam_gider']
        net = bilanco['kaynaklar']['donem_sonucu']['net']
        
        self.gelir_label.setText(f"Toplam Gelir: {gelir:,.2f} ₺")
        self.gider_label.setText(f"Toplam Gider: {gider:,.2f} ₺")
        
        kar_zarar_text = f"Net Sonuç: {net:,.2f} ₺"
        if net > 0:
            self.kar_zarar_label.setText(f"✅ {kar_zarar_text} (KAR)")
            self.kar_zarar_label.setStyleSheet("color: #2E7D32; border-top: 2px solid #4CAF50; padding-top: 10px;")
        elif net < 0:
            self.kar_zarar_label.setText(f"⚠️ {kar_zarar_text} (ZARAR)")
            self.kar_zarar_label.setStyleSheet("color: #C62828; border-top: 2px solid #F44336; padding-top: 10px;")
        else:
            self.kar_zarar_label.setText(f"➖ {kar_zarar_text} (BAŞABAŞ)")
        
        # Toplam kaynak
        toplam_kaynak = bilanco['kaynaklar']['toplam']
        self.toplam_kaynak_label.setText(f"TOPLAM KAYNAK: {toplam_kaynak:,.2f} ₺")
        
        # Denge kontrolü
        if bilanco['denge']['dengeli']:
            self.denge_label.setText("✅ Bilanço dengeli")
            self.denge_label.setStyleSheet("color: #2E7D32; font-weight: 600; padding: 10px;")
        else:
            fark = bilanco['denge']['fark']
            self.denge_label.setText(f"⚠️ Bilanço dengesiz! Fark: {fark:,.2f} ₺")
            self.denge_label.setStyleSheet("color: #C62828; font-weight: 600; padding: 10px; background-color: #FFEBEE; border-radius: 6px;")


class GelirTablosuWidget(QWidget):
    """Gelir tablosu"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.mali_tablo_yoneticisi = MaliTabloYoneticisi(db)
        self.rapor_yoneticisi = RaporYoneticisi(db)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Başlık ve tarih seçici
        header_layout = QHBoxLayout()
        
        title = TitleLabel("GELİR TABLOSU")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        header_layout.addWidget(BodyLabel("Başlangıç:"))
        self.baslangic_edit = QDateEdit()
        self.baslangic_edit.setDate(QDate(QDate.currentDate().year(), 1, 1))
        self.baslangic_edit.setCalendarPopup(True)
        self.baslangic_edit.dateChanged.connect(self.load_data)
        header_layout.addWidget(self.baslangic_edit)
        
        header_layout.addWidget(BodyLabel("Bitiş:"))
        self.bitis_edit = QDateEdit()
        self.bitis_edit.setDate(QDate.currentDate())
        self.bitis_edit.setCalendarPopup(True)
        self.bitis_edit.dateChanged.connect(self.load_data)
        header_layout.addWidget(self.bitis_edit)
        
        self.yenile_btn = PushButton("🔄 Yenile")
        self.yenile_btn.clicked.connect(self.load_data)
        header_layout.addWidget(self.yenile_btn)
        
        layout.addLayout(header_layout)
        
        # İstatistik kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.gelir_card = StatCardLarge("TOPLAM GELİRLER", "0.00 ₺", "", "#4CAF50")
        cards_layout.addWidget(self.gelir_card)
        
        self.gider_card = StatCardLarge("TOPLAM GİDERLER", "0.00 ₺", "", "#F44336")
        cards_layout.addWidget(self.gider_card)
        
        self.sonuc_card = StatCardLarge("NET SONUÇ", "0.00 ₺", "", "#2196F3")
        cards_layout.addWidget(self.sonuc_card)
        
        cards_layout.addStretch()
        layout.addLayout(cards_layout)
        
        # Tablolar
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(20)
        
        # Gelirler tablosu
        gelir_group = QGroupBox("GELİRLER")
        gelir_layout = QVBoxLayout()
        
        self.gelir_table = QTableWidget()
        self.gelir_table.setColumnCount(3)
        self.gelir_table.setHorizontalHeaderLabels(["Gelir Türü", "Adet", "Tutar"])
        self.gelir_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.gelir_table.setAlternatingRowColors(True)
        gelir_layout.addWidget(self.gelir_table)
        
        gelir_group.setLayout(gelir_layout)
        tables_layout.addWidget(gelir_group)
        
        # Giderler tablosu
        gider_group = QGroupBox("GİDERLER")
        gider_layout = QVBoxLayout()
        
        self.gider_table = QTableWidget()
        self.gider_table.setColumnCount(3)
        self.gider_table.setHorizontalHeaderLabels(["Gider Türü", "Adet", "Tutar"])
        self.gider_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.gider_table.setAlternatingRowColors(True)
        gider_layout.addWidget(self.gider_table)
        
        gider_group.setLayout(gider_layout)
        tables_layout.addWidget(gider_group)
        
        layout.addLayout(tables_layout)
        
        self.setLayout(layout)
        
    def load_data(self):
        """Gelir tablosu verilerini yükle"""
        baslangic = self.baslangic_edit.date().toString("yyyy-MM-dd")
        bitis = self.bitis_edit.date().toString("yyyy-MM-dd")
        
        gelir_tablosu = self.mali_tablo_yoneticisi.gelir_tablosu(baslangic, bitis)
        
        # Gelirler
        gelir_detay = gelir_tablosu['gelirler']['detay']
        self.gelir_table.setRowCount(len(gelir_detay))
        
        for row, item in enumerate(gelir_detay):
            self.gelir_table.setItem(row, 0, QTableWidgetItem(item['gelir_turu']))
            self.gelir_table.setItem(row, 1, QTableWidgetItem(str(item['adet'])))
            
            tutar_item = QTableWidgetItem(f"{item['tutar']:,.2f} ₺")
            tutar_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.gelir_table.setItem(row, 2, tutar_item)
        
        # Giderler
        gider_detay = gelir_tablosu['giderler']['detay']
        self.gider_table.setRowCount(len(gider_detay))
        
        for row, item in enumerate(gider_detay):
            self.gider_table.setItem(row, 0, QTableWidgetItem(item['gider_turu']))
            self.gider_table.setItem(row, 1, QTableWidgetItem(str(item['adet'])))
            
            tutar_item = QTableWidgetItem(f"{item['tutar']:,.2f} ₺")
            tutar_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.gider_table.setItem(row, 2, tutar_item)
        
        # Kartları güncelle
        toplam_gelir = gelir_tablosu['gelirler']['toplam']
        toplam_gider = gelir_tablosu['giderler']['toplam']
        net_sonuc = gelir_tablosu['sonuc']['net']
        durum = gelir_tablosu['sonuc']['durum']
        
        self.gelir_card.set_value(f"{toplam_gelir:,.2f} ₺")
        self.gider_card.set_value(f"{toplam_gider:,.2f} ₺")
        self.sonuc_card.set_value(f"{net_sonuc:,.2f} ₺ ({durum})")
        
        # Sonuç kartının rengini değiştir
        if durum == 'KAR':
            self.sonuc_card.value_label.setStyleSheet("color: #2E7D32; font-size: 28px; font-weight: 700;")
        elif durum == 'ZARAR':
            self.sonuc_card.value_label.setStyleSheet("color: #C62828; font-size: 28px; font-weight: 700;")
        else:
            self.sonuc_card.value_label.setStyleSheet("color: #757575; font-size: 28px; font-weight: 700;")


class NakitAkisWidget(QWidget):
    """Nakit akış tablosu"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.mali_tablo_yoneticisi = MaliTabloYoneticisi(db)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Başlık ve tarih seçici
        header_layout = QHBoxLayout()
        
        title = TitleLabel("NAKİT AKIŞ TABLOSU")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        header_layout.addWidget(BodyLabel("Başlangıç:"))
        self.baslangic_edit = QDateEdit()
        self.baslangic_edit.setDate(QDate(QDate.currentDate().year(), 1, 1))
        self.baslangic_edit.setCalendarPopup(True)
        self.baslangic_edit.dateChanged.connect(self.load_data)
        header_layout.addWidget(self.baslangic_edit)
        
        header_layout.addWidget(BodyLabel("Bitiş:"))
        self.bitis_edit = QDateEdit()
        self.bitis_edit.setDate(QDate.currentDate())
        self.bitis_edit.setCalendarPopup(True)
        self.bitis_edit.dateChanged.connect(self.load_data)
        header_layout.addWidget(self.bitis_edit)
        
        self.yenile_btn = PushButton("🔄 Yenile")
        self.yenile_btn.clicked.connect(self.load_data)
        header_layout.addWidget(self.yenile_btn)
        
        layout.addLayout(header_layout)
        
        # Nakit akış özeti
        ozet_group = QGroupBox("NAKİT AKIŞ ÖZETİ")
        ozet_layout = QVBoxLayout()
        ozet_layout.setSpacing(15)
        
        self.donem_basi_label = TitleLabel("Dönem Başı Nakit: 0.00 ₺")
        ozet_layout.addWidget(self.donem_basi_label)
        
        ozet_layout.addWidget(SubtitleLabel("İşletme Faaliyetleri:"))
        
        self.nakit_giris_label = BodyLabel("  (+) Nakit Girişleri: 0.00 ₺")
        ozet_layout.addWidget(self.nakit_giris_label)
        
        self.nakit_cikis_label = BodyLabel("  (-) Nakit Çıkışları: 0.00 ₺")
        ozet_layout.addWidget(self.nakit_cikis_label)
        
        self.net_akis_label = TitleLabel("  (=) Net Nakit Akışı: 0.00 ₺")
        self.net_akis_label.setStyleSheet("border-top: 2px solid #ccc; padding-top: 10px; margin-top: 10px;")
        ozet_layout.addWidget(self.net_akis_label)
        
        self.donem_sonu_label = TitleLabel("Dönem Sonu Nakit: 0.00 ₺")
        self.donem_sonu_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1565C0;
            background-color: #E3F2FD;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
        """)
        ozet_layout.addWidget(self.donem_sonu_label)
        
        # Doğrulama
        self.dogrulama_label = BodyLabel("")
        self.dogrulama_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ozet_layout.addWidget(self.dogrulama_label)
        
        ozet_group.setLayout(ozet_layout)
        layout.addWidget(ozet_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_data(self):
        """Nakit akış verilerini yükle"""
        baslangic = self.baslangic_edit.date().toString("yyyy-MM-dd")
        bitis = self.bitis_edit.date().toString("yyyy-MM-dd")
        
        nakit_akis = self.mali_tablo_yoneticisi.nakit_akis_tablosu(baslangic, bitis)
        
        # Dönem başı
        donem_basi = nakit_akis['donem_basi_nakit']
        self.donem_basi_label.setText(f"Dönem Başı Nakit: {donem_basi:,.2f} ₺")
        
        # İşletme faaliyetleri
        nakit_giris = nakit_akis['isletme_faaliyetleri']['nakit_giris']
        nakit_cikis = nakit_akis['isletme_faaliyetleri']['nakit_cikis']
        net_akis = nakit_akis['isletme_faaliyetleri']['net']
        
        self.nakit_giris_label.setText(f"  (+) Nakit Girişleri: {nakit_giris:,.2f} ₺")
        self.nakit_cikis_label.setText(f"  (-) Nakit Çıkışları: {nakit_cikis:,.2f} ₺")
        
        net_akis_text = f"  (=) Net Nakit Akışı: {net_akis:,.2f} ₺"
        if net_akis > 0:
            self.net_akis_label.setText(f"✅ {net_akis_text}")
            self.net_akis_label.setStyleSheet("color: #2E7D32; border-top: 2px solid #4CAF50; padding-top: 10px; margin-top: 10px;")
        elif net_akis < 0:
            self.net_akis_label.setText(f"⚠️ {net_akis_text}")
            self.net_akis_label.setStyleSheet("color: #C62828; border-top: 2px solid #F44336; padding-top: 10px; margin-top: 10px;")
        else:
            self.net_akis_label.setText(f"➖ {net_akis_text}")
            self.net_akis_label.setStyleSheet("border-top: 2px solid #ccc; padding-top: 10px; margin-top: 10px;")
        
        # Dönem sonu
        donem_sonu = nakit_akis['donem_sonu_nakit']
        self.donem_sonu_label.setText(f"Dönem Sonu Nakit: {donem_sonu:,.2f} ₺")
        
        # Doğrulama
        if nakit_akis['dogrulama']['dogru']:
            self.dogrulama_label.setText("✅ Nakit akış hesaplaması doğru")
            self.dogrulama_label.setStyleSheet("color: #2E7D32; font-weight: 600; padding: 10px;")
        else:
            fark = nakit_akis['dogrulama']['fark']
            self.dogrulama_label.setText(f"⚠️ Hesaplama hatası! Fark: {fark:,.2f} ₺")
            self.dogrulama_label.setStyleSheet("color: #C62828; font-weight: 600; padding: 10px; background-color: #FFEBEE; border-radius: 6px;")


class MaliTablolarWidget(QWidget):
    """Mali tablolar ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(15)
        
        # Başlık
        title_label = TitleLabel("MALİ TABLOLAR")
        layout.addWidget(title_label)
        
        subtitle = BodyLabel("Bilanço, Gelir Tablosu ve Nakit Akış raporları")
        subtitle.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(subtitle)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Bilanço
        self.bilanco_widget = BilancoWidget(self.db)
        self.tabs.addTab(self.bilanco_widget, "📊 Bilanço")
        
        # Gelir Tablosu
        self.gelir_tablosu_widget = GelirTablosuWidget(self.db)
        self.tabs.addTab(self.gelir_tablosu_widget, "💰 Gelir Tablosu")
        
        # Nakit Akış
        self.nakit_akis_widget = NakitAkisWidget(self.db)
        self.tabs.addTab(self.nakit_akis_widget, "💵 Nakit Akış")
        
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
