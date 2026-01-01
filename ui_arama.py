"""
BADER Derneği - Gelişmiş Arama Modülü
Tüm modüllerde kullanılabilir global arama widget'ı
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QLabel, QTableWidget, QTableWidgetItem, QPushButton,
                             QComboBox, QFrame, QStackedWidget, QHeaderView,
                             QDateEdit, QDoubleSpinBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt5.QtGui import QColor
from database import Database
from models import (UyeYoneticisi, GelirYoneticisi, GiderYoneticisi, 
                    KasaYoneticisi, AidatYoneticisi)
from typing import List, Dict, Optional
from datetime import datetime


class GelismisAramaWidget(QWidget):
    """Gelişmiş arama widget'ı - Tüm modüllerde arama yapabilir"""
    
    # Sinyaller
    uye_secildi = pyqtSignal(int)  # Üye seçildiğinde uye_id gönder
    gelir_secildi = pyqtSignal(int)  # Gelir seçildiğinde gelir_id gönder
    gider_secildi = pyqtSignal(int)  # Gider seçildiğinde gider_id gönder
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.gelir_yoneticisi = GelirYoneticisi(db)
        self.gider_yoneticisi = GiderYoneticisi(db)
        self.aidat_yoneticisi = AidatYoneticisi(db)
        
        # Debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Arama Başlık
        title = QLabel("🔍 GELİŞMİŞ ARAMA")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #444050;")
        layout.addWidget(title)
        
        # Arama Alanı
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.1);
                border-radius: 10px;
            }
        """)
        search_layout = QVBoxLayout()
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_layout.setSpacing(15)
        
        # Üst satır: Arama kutusu + modül seçimi
        top_row = QHBoxLayout()
        
        # Arama kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Aramak için yazın... (En az 2 karakter)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                background: #fafafa;
            }
            QLineEdit:focus {
                border-color: #64B5F6;
                background: white;
            }
        """)
        self.search_input.textChanged.connect(self._on_text_changed)
        top_row.addWidget(self.search_input, 3)
        
        # Modül seçimi
        top_row.addWidget(QLabel("Modül:"))
        self.modul_combo = QComboBox()
        self.modul_combo.addItems(['Tümü', 'Üyeler', 'Gelirler', 'Giderler', 'Aidatlar'])
        self.modul_combo.currentIndexChanged.connect(self._trigger_search)
        self.modul_combo.setMinimumWidth(120)
        top_row.addWidget(self.modul_combo)
        
        # Ara butonu
        self.ara_btn = QPushButton("🔍 Ara")
        self.ara_btn.setStyleSheet("""
            QPushButton {
                background-color: #64B5F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.ara_btn.clicked.connect(self._do_search)
        top_row.addWidget(self.ara_btn)
        
        search_layout.addLayout(top_row)
        
        # Gelişmiş filtreler
        filter_group = QGroupBox("Gelişmiş Filtreler")
        filter_group.setCheckable(True)
        filter_group.setChecked(False)
        filter_layout = QHBoxLayout()
        
        # Tarih aralığı
        filter_layout.addWidget(QLabel("Tarih:"))
        self.tarih_baslangic = QDateEdit()
        self.tarih_baslangic.setDate(QDate.currentDate().addMonths(-12))
        self.tarih_baslangic.setCalendarPopup(True)
        filter_layout.addWidget(self.tarih_baslangic)
        
        filter_layout.addWidget(QLabel("-"))
        self.tarih_bitis = QDateEdit()
        self.tarih_bitis.setDate(QDate.currentDate())
        self.tarih_bitis.setCalendarPopup(True)
        filter_layout.addWidget(self.tarih_bitis)
        
        # Tutar aralığı
        filter_layout.addWidget(QLabel("Tutar:"))
        self.tutar_min = QDoubleSpinBox()
        self.tutar_min.setRange(0, 10000000)
        self.tutar_min.setPrefix("₺ ")
        filter_layout.addWidget(self.tutar_min)
        
        filter_layout.addWidget(QLabel("-"))
        self.tutar_max = QDoubleSpinBox()
        self.tutar_max.setRange(0, 10000000)
        self.tutar_max.setValue(10000000)
        self.tutar_max.setPrefix("₺ ")
        filter_layout.addWidget(self.tutar_max)
        
        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        search_layout.addWidget(filter_group)
        
        search_frame.setLayout(search_layout)
        layout.addWidget(search_frame)
        
        # Sonuç sayısı
        self.sonuc_label = QLabel("Aramak için en az 2 karakter girin...")
        self.sonuc_label.setStyleSheet("color: #666; font-size: 13px; padding: 5px;")
        layout.addWidget(self.sonuc_label)
        
        # Sonuç Tablosu
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "ID", "Modül", "Tip", "Ad/Açıklama", "Detay", "Tutar", "Tarih"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setColumnHidden(0, True)  # ID gizli
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.doubleClicked.connect(self._on_item_double_clicked)
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.08);
                border-radius: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
        """)
        layout.addWidget(self.results_table)
        
        self.setLayout(layout)
    
    def _on_text_changed(self, text: str):
        """Metin değiştiğinde debounce ile arama yap"""
        self.search_timer.stop()
        if len(text) >= 2:
            self.search_timer.start(300)  # 300ms bekle
        else:
            self.results_table.setRowCount(0)
            self.sonuc_label.setText("Aramak için en az 2 karakter girin...")
    
    def _trigger_search(self):
        """Arama tetikle"""
        if len(self.search_input.text()) >= 2:
            self._do_search()
    
    def _do_search(self):
        """Aramayı gerçekleştir"""
        query = self.search_input.text().strip()
        if len(query) < 2:
            return
        
        modul = self.modul_combo.currentText()
        results = []
        
        # Üyelerde ara
        if modul in ['Tümü', 'Üyeler']:
            results.extend(self._search_uyeler(query))
        
        # Gelirlerde ara
        if modul in ['Tümü', 'Gelirler']:
            results.extend(self._search_gelirler(query))
        
        # Giderlerde ara
        if modul in ['Tümü', 'Giderler']:
            results.extend(self._search_giderler(query))
        
        # Aidatlarda ara
        if modul in ['Tümü', 'Aidatlar']:
            results.extend(self._search_aidatlar(query))
        
        self._display_results(results)
    
    def _search_uyeler(self, query: str) -> List[Dict]:
        """Üyelerde ara"""
        results = []
        try:
            uyeler = self.uye_yoneticisi.uye_ara(query)
            for uye in uyeler:
                results.append({
                    'id': uye['uye_id'],
                    'modul': 'Üye',
                    'tip': uye.get('durum', 'Aktif'),
                    'ad': uye['ad_soyad'],
                    'detay': uye.get('telefon', ''),
                    'tutar': '',
                    'tarih': str(uye.get('kayit_tarihi', ''))[:10]
                })
        except:
            pass
        return results
    
    def _search_gelirler(self, query: str) -> List[Dict]:
        """Gelirlerde ara"""
        results = []
        try:
            # Tüm gelirleri al ve filtrele
            gelirler = self.gelir_yoneticisi.gelir_listesi()
            q_lower = query.lower()
            
            for gelir in gelirler:
                aciklama = (gelir.get('aciklama') or '').lower()
                gelir_turu = (gelir.get('gelir_turu') or '').lower()
                tahsil_eden = (gelir.get('tahsil_eden') or '').lower()
                
                if q_lower in aciklama or q_lower in gelir_turu or q_lower in tahsil_eden:
                    results.append({
                        'id': gelir['gelir_id'],
                        'modul': 'Gelir',
                        'tip': gelir['gelir_turu'],
                        'ad': gelir['aciklama'],
                        'detay': gelir.get('kasa_adi', ''),
                        'tutar': f"{gelir['tutar']:,.2f} ₺",
                        'tarih': gelir['tarih']
                    })
        except:
            pass
        return results
    
    def _search_giderler(self, query: str) -> List[Dict]:
        """Giderlerde ara"""
        results = []
        try:
            giderler = self.gider_yoneticisi.gider_listesi()
            q_lower = query.lower()
            
            for gider in giderler:
                aciklama = (gider.get('aciklama') or '').lower()
                gider_turu = (gider.get('gider_turu') or '').lower()
                odeyen = (gider.get('odeyen') or '').lower()
                
                if q_lower in aciklama or q_lower in gider_turu or q_lower in odeyen:
                    results.append({
                        'id': gider['gider_id'],
                        'modul': 'Gider',
                        'tip': gider['gider_turu'],
                        'ad': gider['aciklama'],
                        'detay': gider.get('kasa_adi', ''),
                        'tutar': f"-{gider['tutar']:,.2f} ₺",
                        'tarih': gider['tarih']
                    })
        except:
            pass
        return results
    
    def _search_aidatlar(self, query: str) -> List[Dict]:
        """Aidatlarda ara (üye adına göre)"""
        results = []
        try:
            # Üye ara ve aidat bilgilerini al
            uyeler = self.uye_yoneticisi.uye_ara(query)
            for uye in uyeler[:10]:  # İlk 10 üye
                ozet = self.uye_yoneticisi.uye_aidat_ozeti(uye['uye_id'])
                kalan = ozet.get('kalan_borc', 0) or 0
                
                results.append({
                    'id': uye['uye_id'],
                    'modul': 'Aidat',
                    'tip': 'Borçlu' if kalan > 0 else 'Temiz',
                    'ad': uye['ad_soyad'],
                    'detay': f"{ozet.get('toplam_yil', 0) or 0} yıl kayıt",
                    'tutar': f"{kalan:,.2f} ₺ borç" if kalan > 0 else "Borç yok",
                    'tarih': ''
                })
        except:
            pass
        return results
    
    def _display_results(self, results: List[Dict]):
        """Sonuçları tabloya yaz"""
        self.results_table.setRowCount(len(results))
        self.sonuc_label.setText(f"🔍 {len(results)} sonuç bulundu")
        
        for row, item in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            
            # Modül - renkli
            modul_item = QTableWidgetItem(item['modul'])
            if item['modul'] == 'Üye':
                modul_item.setForeground(QColor("#2196F3"))
            elif item['modul'] == 'Gelir':
                modul_item.setForeground(QColor("#4CAF50"))
            elif item['modul'] == 'Gider':
                modul_item.setForeground(QColor("#F44336"))
            elif item['modul'] == 'Aidat':
                modul_item.setForeground(QColor("#FF9800"))
            self.results_table.setItem(row, 1, modul_item)
            
            self.results_table.setItem(row, 2, QTableWidgetItem(item['tip']))
            self.results_table.setItem(row, 3, QTableWidgetItem(item['ad']))
            self.results_table.setItem(row, 4, QTableWidgetItem(item['detay']))
            self.results_table.setItem(row, 5, QTableWidgetItem(item['tutar']))
            self.results_table.setItem(row, 6, QTableWidgetItem(item['tarih']))
    
    def _on_item_double_clicked(self):
        """Çift tıklandığında ilgili sayfaya git"""
        row = self.results_table.currentRow()
        if row < 0:
            return
        
        item_id = int(self.results_table.item(row, 0).text())
        modul = self.results_table.item(row, 1).text()
        
        if modul == 'Üye':
            self.uye_secildi.emit(item_id)
        elif modul == 'Gelir':
            self.gelir_secildi.emit(item_id)
        elif modul == 'Gider':
            self.gider_secildi.emit(item_id)
        elif modul == 'Aidat':
            self.uye_secildi.emit(item_id)


class HizliAramaWidget(QWidget):
    """Hızlı arama widget'ı - Header'da kullanılır"""
    
    sonuc_secildi = pyqtSignal(str, int)  # (modul, id) sinyali
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Hızlı ara...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 20px;
                font-size: 13px;
                background: #f5f5f5;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #64B5F6;
                background: white;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        self.setLayout(layout)
    
    def _on_search(self):
        """Enter'a basıldığında ara"""
        query = self.search_input.text().strip()
        if len(query) < 2:
            return
        
        # İlk üyeyi bul
        uyeler = self.uye_yoneticisi.uye_ara(query)
        if uyeler:
            self.sonuc_secildi.emit('uye', uyeler[0]['uye_id'])
