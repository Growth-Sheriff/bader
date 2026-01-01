"""
BADER Derneği - Ayrılan Üyeler Sayfası
Ayrılan/silinen üyelerin listesi ve geçmişi
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QHeaderView, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import MessageBox
from database import Database
from models import UyeYoneticisi, AidatYoneticisi
from typing import Optional
from ui_helpers import setup_resizable_table


class AyrilanUyelerWidget(QWidget):
    """Ayrılan üyeler listesi"""
    
    uye_detay_ac = pyqtSignal(int)
    uye_aidat_ac = pyqtSignal(int)
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.aidat_yoneticisi = AidatYoneticisi(db)
        self.current_uye_id = None
        
        self.setup_ui()
        self.load_uyeler()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("AYRILAN ÜYELER")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Bilgi
        info_label = QLabel(
            "ℹ️ Bu listede 'Ayrıldı' durumundaki üyeler gösterilmektedir. "
            "Bu üyelerin aidat ve ödeme kayıtları korunmuştur."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 13px;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 6px;
                border-left: 3px solid #64B5F6;
            }
        """)
        layout.addWidget(info_label)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Arama
        self.arama_edit = QLineEdit()
        self.arama_edit.setPlaceholderText("🔍 Üye ara...")
        self.arama_edit.textChanged.connect(self.ara)
        self.arama_edit.setMaximumWidth(400)
        toolbar_layout.addWidget(self.arama_edit)
        
        toolbar_layout.addStretch()
        
        # Geri al butonu
        self.geri_al_btn = QPushButton("♻️ Aktif Yap")
        self.geri_al_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
        """)
        self.geri_al_btn.clicked.connect(self.uye_geri_al)
        self.geri_al_btn.setEnabled(False)
        toolbar_layout.addWidget(self.geri_al_btn)
        
        # Kalıcı sil butonu
        self.kalici_sil_btn = QPushButton("🗑️ Kalıcı Sil")
        self.kalici_sil_btn.setProperty("class", "danger")
        self.kalici_sil_btn.clicked.connect(self.uye_kalici_sil)
        self.kalici_sil_btn.setEnabled(False)
        toolbar_layout.addWidget(self.kalici_sil_btn)
        
        # Detay
        self.detay_btn = QPushButton("👁️ Detay")
        self.detay_btn.clicked.connect(self.uye_detay)
        self.detay_btn.setEnabled(False)
        toolbar_layout.addWidget(self.detay_btn)
        
        # Aidat
        self.aidat_btn = QPushButton("💳 Aidat")
        self.aidat_btn.clicked.connect(self.uye_aidat)
        self.aidat_btn.setEnabled(False)
        toolbar_layout.addWidget(self.aidat_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Üye No", "Ad Soyad", "Telefon", "E-posta", 
            "Kayıt Tarihi", "Ayrılma Tarihi", "Aidat Durumu"
        ])
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        setup_resizable_table(self.table, table_id="ayrilan_uyeler_tablosu", stretch_column=1)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.uye_detay)
        
        layout.addWidget(self.table)
        
        # İstatistikler
        stats_layout = QHBoxLayout()
        self.toplam_label = QLabel("Toplam Ayrılan: 0")
        stats_layout.addWidget(self.toplam_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        
    def load_uyeler(self):
        """Ayrılan üyeleri yükle"""
        uyeler = self.uye_yoneticisi.ayrilan_uyeler()
        
        self.table.setRowCount(len(uyeler))
        
        for row, uye in enumerate(uyeler):
            self.table.setItem(row, 0, QTableWidgetItem(str(uye['uye_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(uye['ad_soyad']))
            self.table.setItem(row, 2, QTableWidgetItem(uye['telefon'] or '-'))
            self.table.setItem(row, 3, QTableWidgetItem(uye['email'] or '-'))
            self.table.setItem(row, 4, QTableWidgetItem(str(uye['kayit_tarihi'])[:10]))
            self.table.setItem(row, 5, QTableWidgetItem(uye.get('ayrilma_tarihi') or '-'))
            
            # Aidat durumu
            ozet = self.uye_yoneticisi.uye_aidat_ozeti(uye['uye_id'])
            kalan = ozet.get('kalan_borc', 0) or 0
            if kalan > 0:
                durum_text = f"Borç: {kalan:,.2f} ₺"
                durum_item = QTableWidgetItem(durum_text)
                durum_item.setForeground(Qt.GlobalColor.darkRed)
            else:
                durum_text = "Borç Yok"
                durum_item = QTableWidgetItem(durum_text)
                durum_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 6, durum_item)
        
        self.toplam_label.setText(f"Toplam Ayrılan: {len(uyeler)}")
        
    def ara(self):
        """Arama yap"""
        arama_metni = self.arama_edit.text().strip().lower()
        
        for row in range(self.table.rowCount()):
            match = False
            for col in range(1, 4):
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
            self.geri_al_btn.setEnabled(True)
            self.kalici_sil_btn.setEnabled(True)
            self.detay_btn.setEnabled(True)
            self.aidat_btn.setEnabled(True)
        else:
            self.current_uye_id = None
            self.geri_al_btn.setEnabled(False)
            self.kalici_sil_btn.setEnabled(False)
            self.detay_btn.setEnabled(False)
            self.aidat_btn.setEnabled(False)
    
    def uye_geri_al(self):
        """Üyeyi aktif yap"""
        if not self.current_uye_id:
            return
            
        w = MessageBox("Üyeyi Aktif Yap", "Bu üyeyi tekrar 'Aktif' durumuna almak istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.db.cursor.execute("""
                    UPDATE uyeler 
                    SET durum = 'Aktif', ayrilma_tarihi = NULL,
                        guncelleme_tarihi = CURRENT_TIMESTAMP
                    WHERE uye_id = ?
                """, (self.current_uye_id,))
                self.db.commit()
                self.load_uyeler()
                self.current_uye_id = None
                MessageBox("Başarılı", "Üye tekrar aktif edildi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Hata: {str(e)}", self).show()
    
    def uye_kalici_sil(self):
        """Üyeyi kalıcı olarak sil"""
        if not self.current_uye_id:
            return
            
        w = MessageBox("Kalıcı Silme", 
                      "⚠️ DİKKAT!\n\n"
                      "Bu üyeyi ve TÜM aidat kayıtlarını KALICI olarak silmek istediğinizden emin misiniz?\n\n"
                      "Bu işlem GERİ ALINAMAZ!", 
                      self)
        if w.exec():
            try:
                self.db.cursor.execute("DELETE FROM uyeler WHERE uye_id = ?", (self.current_uye_id,))
                self.db.commit()
                self.load_uyeler()
                self.current_uye_id = None
                MessageBox("Başarılı", "Üye kalıcı olarak silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Hata: {str(e)}", self).show()
    
    def uye_detay(self):
        """Üye detay sayfasına git"""
        if self.current_uye_id:
            self.uye_detay_ac.emit(self.current_uye_id)
    
    def uye_aidat(self):
        """Üye aidat sayfasına git"""
        if self.current_uye_id:
            self.uye_aidat_ac.emit(self.current_uye_id)


