"""
BADER Derneği - Yıl Sonu Devir İşlemleri
Kasaları bir yıldan diğerine aktarma
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QMessageBox, QGroupBox, QTableWidget,
                             QTableWidgetItem, QSpinBox, QDialog, QFormLayout,
                             QTextEdit, QHeaderView, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from qfluentwidgets import MessageBox
from database import Database
from models import KasaYoneticisi
from datetime import datetime
from ui_drawer import DrawerPanel
from ui_helpers import setup_resizable_table


class DevirThread(QThread):
    """Devir işlemi için thread"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, db: Database, eski_yil: int, yeni_yil: int):
        super().__init__()
        self.db = db
        self.eski_yil = eski_yil
        self.yeni_yil = yeni_yil
        
    def run(self):
        try:
            kasa_yoneticisi = KasaYoneticisi(self.db)
            
            self.progress.emit(20, "Kasa bakiyeleri hesaplanıyor...")
            
            # Tüm kasaların net bakiyesini hesapla
            kasalar = kasa_yoneticisi.tum_kasalar_ozet()
            
            self.progress.emit(40, "Devir bakiyeleri güncelleniyor...")
            
            devir_sayisi = 0
            for kasa in kasalar:
                # Net bakiyeyi yeni devir olarak kaydet
                self.db.cursor.execute("""
                    UPDATE kasalar
                    SET devir_bakiye = devir_bakiye + ?
                    WHERE kasa_id = ?
                """, (kasa['net_bakiye'] - kasa['devir_bakiye'], kasa['kasa_id']))
                
                devir_sayisi += 1
                
            self.progress.emit(60, "Log kaydı oluşturuluyor...")
            
            # Log kaydı
            self.db.log_islem(
                "Sistem",
                "DEVİR",
                "kasalar",
                0,
                f"{self.eski_yil} → {self.yeni_yil} yıl sonu devir işlemi tamamlandı. {devir_sayisi} kasa aktarıldı."
            )
            
            self.progress.emit(80, "Devir raporu hazırlanıyor...")
            
            # Devir raporu
            rapor = f"YIL SONU DEVİR İŞLEMİ\n"
            rapor += f"{'='*50}\n"
            rapor += f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            rapor += f"Devir: {self.eski_yil} → {self.yeni_yil}\n\n"
            
            for kasa in kasalar:
                rapor += f"{kasa['kasa_adi']}: {kasa['net_bakiye']:,.2f} {kasa['para_birimi']}\n"
            
            self.db.commit()
            
            self.progress.emit(100, "Tamamlandı!")
            self.finished.emit(True, rapor)
            
        except Exception as e:
            self.finished.emit(False, f"Devir hatası: {str(e)}")


class DevirOnayWidget(QWidget):
    """Devir işlemi onay widget'ı"""
    
    def __init__(self, kasa_ozet: list, eski_yil: int, yeni_yil: int):
        super().__init__()
        self.kasa_ozet = kasa_ozet
        self.eski_yil = eski_yil
        self.yeni_yil = yeni_yil
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Uyarı
        warning_label = QLabel(
            f"⚠️ {self.eski_yil} yılı kapanış ve {self.yeni_yil} yılı açılış işlemi yapılacak!\n\n"
            "Bu işlem sonrasında:\n"
            "• Tüm kasaların mevcut net bakiyeleri devir bakiyelerine eklenecek\n"
            "• Bu işlem GERİ ALINAMAZ\n"
            "• İşlemden önce veritabanını yedeklemeniz ÖNERİLİR"
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3E0;
                color: #E65100;
                padding: 15px;
                border-radius: 8px;
                border: 2px solid #FFB74D;
                font-weight: bold;
            }
        """)
        layout.addWidget(warning_label)
        
        # Kasa özeti
        ozet_label = QLabel(f"{self.eski_yil} Yılı Kasa Durumu")
        ozet_label.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 15px;
                font-weight: 600;
                padding-bottom: 8px;
            }
        """)
        layout.addWidget(ozet_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Kasa", "Para Birimi", "Mevcut Devir", "Net Bakiye", "Yeni Devir", "Fark"
        ])
        
        # Sütun genişliklerini responsive yap
        setup_resizable_table(self.table, table_id="devir_ozet_tablosu", stretch_column=0)
        
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(250)
        
        # Kasaları göster
        if self.kasa_ozet:
            for kasa in self.kasa_ozet:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                self.table.setItem(row, 0, QTableWidgetItem(kasa['kasa_adi']))
                self.table.setItem(row, 1, QTableWidgetItem(kasa['para_birimi']))
                self.table.setItem(row, 2, QTableWidgetItem(f"{kasa['devir_bakiye']:,.2f}"))
                
                net_item = QTableWidgetItem(f"{kasa['net_bakiye']:,.2f}")
                if kasa['net_bakiye'] < 0:
                    net_item.setForeground(QColor("#C62828"))
                else:
                    net_item.setForeground(QColor("#2E7D32"))
                self.table.setItem(row, 3, net_item)
                
                # Yeni devir = mevcut devir + (net bakiye - mevcut devir)
                yeni_devir = kasa['net_bakiye']
                fark = yeni_devir - kasa['devir_bakiye']
                
                self.table.setItem(row, 4, QTableWidgetItem(f"{yeni_devir:,.2f}"))
                
                fark_item = QTableWidgetItem(f"{fark:+,.2f}")
                if fark < 0:
                    fark_item.setForeground(QColor("#C62828"))
                else:
                    fark_item.setForeground(QColor("#2E7D32"))
                self.table.setItem(row, 5, fark_item)
        
        layout.addWidget(self.table)
        
        # Bilgi
        info_label = QLabel(
            "ℹ️ Bu işlem tamamlandıktan sonra, kasaların devir bakiyeleri güncellenecek\n"
            f"ve {self.yeni_yil} yılı için yeni bir dönem başlayacaktır."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                color: #1565C0;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #90CAF9;
            }
        """)
        layout.addWidget(info_label)
        
        layout.addStretch()
        self.setLayout(layout)


class DevirWidget(QWidget):
    """Yıl sonu devir işlemleri ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.devir_thread = None
        self.setup_ui()
        self.load_kasa_durumu()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("YIL SONU DEVİR İŞLEMLERİ")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        subtitle = QLabel("Kasaları bir yıldan diğerine aktarma")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)
        
        # Açıklama
        info_group = QGroupBox("ℹ️ Devir İşlemi Nedir?")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "Yıl sonu devir işlemi, mevcut yılın kasa bakiyelerini yeni yıla aktarmanızı sağlar.\n\n"
            "• Tüm kasaların net bakiyeleri hesaplanır\n"
            "• Bu bakiyeler, yeni yılın başlangıç devir bakiyeleri olur\n"
            "• Böylece yeni yılda temiz bir başlangıç yaparsınız\n"
            "• Önceki yıl kayıtları değişmez, sadece devir bakiyeleri güncellenir\n\n"
            "⚠️ Bu işlemi yılda bir kez, yıl kapanışında yapmanız önerilir."
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Devir ayarları
        ayar_group = QGroupBox("Devir Ayarları")
        ayar_layout = QFormLayout()
        
        self.eski_yil_spin = QSpinBox()
        self.eski_yil_spin.setMinimum(2020)
        self.eski_yil_spin.setMaximum(2050)
        self.eski_yil_spin.setValue(datetime.now().year)
        self.eski_yil_spin.valueChanged.connect(self.on_yil_degisti)
        ayar_layout.addRow("Kapanan Yıl:", self.eski_yil_spin)
        
        self.yeni_yil_spin = QSpinBox()
        self.yeni_yil_spin.setMinimum(2020)
        self.yeni_yil_spin.setMaximum(2050)
        self.yeni_yil_spin.setValue(datetime.now().year + 1)
        self.yeni_yil_spin.setEnabled(False)
        ayar_layout.addRow("Açılan Yıl:", self.yeni_yil_spin)
        
        ayar_group.setLayout(ayar_layout)
        layout.addWidget(ayar_group)
        
        # Kasa durumu
        durum_group = QGroupBox("Mevcut Kasa Durumu")
        durum_layout = QVBoxLayout()
        
        self.durum_table = QTableWidget()
        self.durum_table.setColumnCount(5)
        self.durum_table.setHorizontalHeaderLabels([
            "Kasa", "Para Birimi", "Devir Bakiye", "Net Bakiye", "Aktarılacak"
        ])
        
        # Sütun genişliklerini responsive yap
        setup_resizable_table(self.durum_table, table_id="devir_durum_tablosu", stretch_column=0)
        
        self.durum_table.setAlternatingRowColors(True)
        
        durum_layout.addWidget(self.durum_table)
        durum_group.setLayout(durum_layout)
        layout.addWidget(durum_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.yenile_btn = QPushButton("🔄 Yenile")
        self.yenile_btn.clicked.connect(self.load_kasa_durumu)
        button_layout.addWidget(self.yenile_btn)
        
        button_layout.addStretch()
        
        self.yedekle_btn = QPushButton("💾 Önce Yedek Al")
        self.yedekle_btn.setProperty("class", "warning")
        self.yedekle_btn.clicked.connect(self.yedek_al)
        button_layout.addWidget(self.yedekle_btn)
        
        self.devir_btn = QPushButton("➡️ Devir İşlemini Başlat")
        self.devir_btn.clicked.connect(self.devir_baslat)
        button_layout.addWidget(self.devir_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
    def on_yil_degisti(self):
        """Yıl değiştiğinde yeni yılı otomatik ayarla"""
        self.yeni_yil_spin.setValue(self.eski_yil_spin.value() + 1)
        self.load_kasa_durumu()
        
    def load_kasa_durumu(self):
        """Kasa durumunu yükle"""
        kasalar = self.kasa_yoneticisi.tum_kasalar_ozet()
        
        self.durum_table.setRowCount(0)
        
        for kasa in kasalar:
            row = self.durum_table.rowCount()
            self.durum_table.insertRow(row)
            
            self.durum_table.setItem(row, 0, QTableWidgetItem(kasa['kasa_adi']))
            self.durum_table.setItem(row, 1, QTableWidgetItem(kasa['para_birimi']))
            self.durum_table.setItem(row, 2, QTableWidgetItem(f"{kasa['devir_bakiye']:,.2f}"))
            
            net_item = QTableWidgetItem(f"{kasa['net_bakiye']:,.2f}")
            if kasa['net_bakiye'] < 0:
                net_item.setForeground(QColor("#C62828"))
            else:
                net_item.setForeground(QColor("#2E7D32"))
            self.durum_table.setItem(row, 3, net_item)
            
            aktarilacak = kasa['net_bakiye']
            akt_item = QTableWidgetItem(f"{aktarilacak:,.2f}")
            akt_item.setForeground(QColor("#1976D2"))
            akt_item.setFont(akt_item.font())
            font = akt_item.font()
            font.setBold(True)
            akt_item.setFont(font)
            self.durum_table.setItem(row, 4, akt_item)
            
    def yedek_al(self):
        """Yedek alma dialogunu aç"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Yedekleme Dosyası Kaydet",
            f"BADER_Devir_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database Files (*.db)"
        )
        
        if file_path:
            if self.db.backup_database(file_path):
                MessageBox("Başarılı", "Yedekleme tamamlandı!\nŞimdi devir işlemine devam edebilirsiniz.", self).show()
            else:
                MessageBox("Hata", "Yedekleme başarısız!", self).show()
                
    def devir_baslat(self):
        """Devir işlemini başlat"""
        eski_yil = self.eski_yil_spin.value()
        yeni_yil = self.yeni_yil_spin.value()
        
        # Onay paneli
        kasalar = self.kasa_yoneticisi.tum_kasalar_ozet()
        onay_widget = DevirOnayWidget(kasalar, eski_yil, yeni_yil)
        drawer = DrawerPanel(self, "Yıl Sonu Devir Onayı", onay_widget)
        drawer.submit_btn.setText("✓ Devri Onayla ve Başlat")
        drawer.submit_btn.setProperty("class", "success")
        drawer.submit_btn.setStyleSheet(drawer.submit_btn.styleSheet())  # Refresh style
        
        def on_confirmed():
            drawer.close()
            
            # Progress göster
            self.progress_bar.setVisible(True)
            self.progress_label.setVisible(True)
            self.devir_btn.setEnabled(False)
            self.yedekle_btn.setEnabled(False)
            
            # Thread başlat
            self.devir_thread = DevirThread(self.db, eski_yil, yeni_yil)
            self.devir_thread.progress.connect(self.on_progress)
            self.devir_thread.finished.connect(self.on_finished)
            self.devir_thread.start()
        
        drawer.accepted.connect(on_confirmed)
        drawer.show()
            
    def on_progress(self, value: int, message: str):
        """Progress güncelle"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def on_finished(self, success: bool, message: str):
        """Devir tamamlandı"""
        self.devir_btn.setEnabled(True)
        self.yedekle_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        if success:
            MessageBox("Devir Tamamlandı", f"Yıl sonu devir işlemi başarıyla tamamlandı!\n\n{message}"
            , 
                self).show()
            self.load_kasa_durumu()
        else:
            MessageBox("Hata", message, self).show()

