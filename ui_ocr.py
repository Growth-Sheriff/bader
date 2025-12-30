"""
BADER - OCR Belge Tarama Modülü
Tam Senaryo: Belge Yükle → OCR Tara → Düzenle → Onayla → Kaydet
"""

import os
import shutil
from datetime import datetime, date
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFileDialog, QDialog, QStackedWidget, QScrollArea,
                             QFrame, QGridLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSizePolicy, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QDate
from PyQt5.QtGui import QPixmap, QImage, QFont
from qfluentwidgets import (CardWidget, PushButton, PrimaryPushButton, SubtitleLabel,
                            BodyLabel, CaptionLabel, InfoBar, InfoBarPosition,
                            ProgressRing, FluentIcon as FIF, ComboBox, LineEdit,
                            DoubleSpinBox, DateEdit, TextEdit, MessageBox, TitleLabel,
                            StrongBodyLabel, CheckBox, SpinBox)
from database import Database


# ==================== Enum ve Data Sınıfları ====================

class BelgeTuru(Enum):
    """Belge türleri"""
    FATURA = "fatura"
    MAKBUZ = "makbuz"
    DEKONT = "dekont"
    FIS = "fis"
    SOZLESME = "sozlesme"
    DIGER = "diger"


class KayitTuru(Enum):
    """Kayıt türleri - belge hangi modüle gidecek"""
    GELIR = "gelir"
    GIDER = "gider"
    AIDAT = "aidat"
    SADECE_BELGE = "sadece_belge"


@dataclass
class OCRSonuc:
    """OCR tarama sonucu"""
    ham_metin: str = ""
    guven_skoru: float = 0.0
    algilanan_alanlar: Dict = field(default_factory=dict)
    gorsel_yolu: str = ""
    islem_zamani: datetime = field(default_factory=datetime.now)


@dataclass
class BelgeKayit:
    """Kaydedilecek belge bilgileri"""
    belge_turu: BelgeTuru = BelgeTuru.FATURA
    kayit_turu: KayitTuru = KayitTuru.GIDER
    
    # Temel bilgiler
    aciklama: str = ""
    tutar: float = 0.0
    tarih: date = field(default_factory=date.today)
    
    # Firma/Kişi bilgileri
    firma_adi: str = ""
    vergi_no: str = ""
    
    # Belge bilgileri
    belge_no: str = ""
    
    # Kategori
    kategori: str = ""
    
    # Kasa
    kasa_id: Optional[int] = None
    
    # Ek bilgiler
    notlar: str = ""
    
    # Dosya
    dosya_yolu: str = ""
    
    # Üye (aidat için)
    uye_id: Optional[int] = None
    uye_adi: str = ""


# ==================== Worker Thread ====================

class OCRWorker(QThread):
    """OCR işlemi için arka plan thread'i"""
    finished = pyqtSignal(bool, str, object)
    progress = pyqtSignal(str, int)  # mesaj, yüzde
    
    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path
    
    def run(self):
        try:
            self.progress.emit("Sunucuya bağlanılıyor...", 10)
            
            from server_client import get_server_client
            client = get_server_client()
            
            if not client.is_configured():
                self.finished.emit(False, "Sunucu yapılandırılmamış. Ayarlar > Server bölümünden yapılandırın.", None)
                return
            
            self.progress.emit("Görsel gönderiliyor...", 30)
            success, message, result = client.ocr_process(self.image_path)
            
            if success:
                self.progress.emit("Metin analiz ediliyor...", 70)
                
                # OCR sonucunu işle
                ocr_sonuc = OCRSonuc(
                    ham_metin=result.get('text', ''),
                    guven_skoru=result.get('confidence', 0),
                    algilanan_alanlar=result.get('fields', {}),
                    gorsel_yolu=self.image_path
                )
                
                self.progress.emit("Tamamlandı!", 100)
                self.finished.emit(True, "OCR başarılı", ocr_sonuc)
            else:
                self.finished.emit(False, message, None)
            
        except Exception as e:
            self.finished.emit(False, f"OCR hatası: {str(e)}", None)


# ==================== Wizard Adımları ====================

class Step1_BelgeYukle(CardWidget):
    """Adım 1: Belge Yükleme"""
    
    belge_secildi = pyqtSignal(str)  # dosya yolu
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Başlık
        header = QHBoxLayout()
        step_label = SubtitleLabel("1️⃣ Belge Yükle")
        header.addWidget(step_label)
        header.addStretch()
        layout.addLayout(header)
        
        desc = CaptionLabel("Fatura, makbuz, dekont veya fiş görselini yükleyin.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Yükleme alanı
        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                border: 3px dashed #0078D4;
                border-radius: 12px;
                background-color: #1a1a2e;
                min-height: 200px;
            }
            QFrame:hover {
                border-color: #00a8ff;
                background-color: #1e1e3e;
            }
        """)
        upload_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_frame.mousePressEvent = lambda e: self.select_file()
        
        upload_layout = QVBoxLayout(upload_frame)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: none; background: transparent;")
        self.set_empty_preview()
        upload_layout.addWidget(self.preview_label)
        
        layout.addWidget(upload_frame)
        
        # Butonlar
        btn_row = QHBoxLayout()
        
        self.file_btn = PushButton("📁 Dosya Seç")
        self.file_btn.clicked.connect(self.select_file)
        btn_row.addWidget(self.file_btn)
        
        btn_row.addStretch()
        
        self.clear_btn = PushButton("🗑️ Temizle")
        self.clear_btn.clicked.connect(self.clear_selection)
        self.clear_btn.setEnabled(False)
        btn_row.addWidget(self.clear_btn)
        
        layout.addLayout(btn_row)
    
    def set_empty_preview(self):
        self.preview_label.setText(
            "📤\n\n"
            "Belge görselini buraya sürükleyin\n"
            "veya tıklayarak seçin\n\n"
            "Desteklenen: PNG, JPG, PDF"
        )
        self.preview_label.setStyleSheet("border: none; background: transparent; color: #888;")
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Belge Seç",
            "",
            "Görseller (*.png *.jpg *.jpeg *.bmp *.webp);;PDF (*.pdf);;Tümü (*.*)"
        )
        
        if file_path:
            self.load_preview(file_path)
    
    def load_preview(self, path: str):
        self.current_path = path
        
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                320, 180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
        else:
            self.preview_label.setText(f"📄 {os.path.basename(path)}")
        
        self.clear_btn.setEnabled(True)
        self.belge_secildi.emit(path)
    
    def clear_selection(self):
        self.current_path = None
        self.set_empty_preview()
        self.clear_btn.setEnabled(False)


class Step2_OCRTarama(CardWidget):
    """Adım 2: OCR Tarama"""
    
    tarama_tamamlandi = pyqtSignal(object)  # OCRSonuc
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.image_path = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        step_label = SubtitleLabel("2️⃣ OCR Tarama")
        layout.addWidget(step_label)
        
        desc = CaptionLabel("Belgedeki metin ve bilgiler otomatik olarak algılanacak.")
        layout.addWidget(desc)
        
        # Durum alanı
        self.status_frame = QFrame()
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_ring = ProgressRing()
        self.progress_ring.setFixedSize(60, 60)
        self.progress_ring.hide()
        status_layout.addWidget(self.progress_ring, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = BodyLabel("Tarama için belge yükleyin")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        self.progress_text = CaptionLabel("")
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.progress_text)
        
        layout.addWidget(self.status_frame)
        
        self.scan_btn = PrimaryPushButton("🔍 Taramayı Başlat")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self.start_scan)
        layout.addWidget(self.scan_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def set_image(self, path: str):
        self.image_path = path
        self.scan_btn.setEnabled(True)
        self.status_label.setText("✅ Belge hazır - Taramayı başlatın")
    
    def start_scan(self):
        if not self.image_path:
            return
        
        self.scan_btn.setEnabled(False)
        self.progress_ring.show()
        self.status_label.setText("Taranıyor...")
        
        self.worker = OCRWorker(self.image_path)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def on_progress(self, message: str, percent: int):
        self.progress_text.setText(f"{message} ({percent}%)")
    
    def on_finished(self, success: bool, message: str, result):
        self.progress_ring.hide()
        self.scan_btn.setEnabled(True)
        
        if success:
            self.status_label.setText("✅ Tarama tamamlandı!")
            self.progress_text.setText("")
            self.tarama_tamamlandi.emit(result)
        else:
            self.status_label.setText(f"❌ Hata: {message}")


class Step3_Duzenleme(CardWidget):
    """Adım 3: Bilgileri Düzenleme"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.ocr_sonuc: Optional[OCRSonuc] = None
        self.dosya_yolu = ""
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        step_label = SubtitleLabel("3️⃣ Bilgileri Düzenle")
        layout.addWidget(step_label)
        
        desc = CaptionLabel("OCR ile algılanan bilgileri kontrol edin ve düzenleyin.")
        layout.addWidget(desc)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        form_layout = QGridLayout(content)
        form_layout.setSpacing(10)
        
        row = 0
        
        # Belge Türü
        form_layout.addWidget(StrongBodyLabel("Belge Türü:"), row, 0)
        self.belge_turu_combo = ComboBox()
        for bt in BelgeTuru:
            self.belge_turu_combo.addItem(bt.value.title(), bt)
        form_layout.addWidget(self.belge_turu_combo, row, 1)
        row += 1
        
        # Kayıt Türü
        form_layout.addWidget(StrongBodyLabel("Kayıt Türü:"), row, 0)
        self.kayit_turu_combo = ComboBox()
        self.kayit_turu_combo.addItem("💰 Gelir", KayitTuru.GELIR)
        self.kayit_turu_combo.addItem("💸 Gider", KayitTuru.GIDER)
        self.kayit_turu_combo.addItem("📋 Aidat Tahsilatı", KayitTuru.AIDAT)
        self.kayit_turu_combo.addItem("📁 Sadece Belge", KayitTuru.SADECE_BELGE)
        self.kayit_turu_combo.currentIndexChanged.connect(self.on_kayit_turu_changed)
        form_layout.addWidget(self.kayit_turu_combo, row, 1)
        row += 1
        
        # Tarih
        form_layout.addWidget(StrongBodyLabel("Tarih:"), row, 0)
        self.tarih_edit = DateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        form_layout.addWidget(self.tarih_edit, row, 1)
        row += 1
        
        # Tutar
        form_layout.addWidget(StrongBodyLabel("Tutar (₺):"), row, 0)
        self.tutar_spin = DoubleSpinBox()
        self.tutar_spin.setRange(0, 99999999)
        self.tutar_spin.setDecimals(2)
        form_layout.addWidget(self.tutar_spin, row, 1)
        row += 1
        
        # Firma/Kişi
        form_layout.addWidget(StrongBodyLabel("Firma/Kişi:"), row, 0)
        self.firma_edit = LineEdit()
        self.firma_edit.setPlaceholderText("Firma veya kişi adı")
        form_layout.addWidget(self.firma_edit, row, 1)
        row += 1
        
        # Vergi No
        form_layout.addWidget(StrongBodyLabel("Vergi No:"), row, 0)
        self.vergi_no_edit = LineEdit()
        self.vergi_no_edit.setPlaceholderText("Opsiyonel")
        form_layout.addWidget(self.vergi_no_edit, row, 1)
        row += 1
        
        # Belge No
        form_layout.addWidget(StrongBodyLabel("Belge No:"), row, 0)
        self.belge_no_edit = LineEdit()
        self.belge_no_edit.setPlaceholderText("Fatura/Makbuz numarası")
        form_layout.addWidget(self.belge_no_edit, row, 1)
        row += 1
        
        # Kategori
        form_layout.addWidget(StrongBodyLabel("Kategori:"), row, 0)
        self.kategori_combo = ComboBox()
        self.update_kategoriler()
        form_layout.addWidget(self.kategori_combo, row, 1)
        row += 1
        
        # Açıklama
        form_layout.addWidget(StrongBodyLabel("Açıklama:"), row, 0)
        self.aciklama_edit = LineEdit()
        self.aciklama_edit.setPlaceholderText("İşlem açıklaması")
        form_layout.addWidget(self.aciklama_edit, row, 1)
        row += 1
        
        # Kasa seçimi
        form_layout.addWidget(StrongBodyLabel("Kasa:"), row, 0)
        self.kasa_combo = ComboBox()
        self.load_kasalar()
        form_layout.addWidget(self.kasa_combo, row, 1)
        row += 1
        
        # Üye seçimi (Aidat için)
        self.uye_label = StrongBodyLabel("Üye:")
        self.uye_label.hide()
        form_layout.addWidget(self.uye_label, row, 0)
        self.uye_combo = ComboBox()
        self.uye_combo.hide()
        self.load_uyeler()
        form_layout.addWidget(self.uye_combo, row, 1)
        row += 1
        
        # Notlar
        form_layout.addWidget(StrongBodyLabel("Notlar:"), row, 0)
        self.notlar_edit = TextEdit()
        self.notlar_edit.setPlaceholderText("Ek notlar...")
        self.notlar_edit.setMaximumHeight(60)
        form_layout.addWidget(self.notlar_edit, row, 1)
        row += 1
        
        # OCR Ham Metin
        form_layout.addWidget(StrongBodyLabel("OCR Çıktısı:"), row, 0)
        self.ocr_text = TextEdit()
        self.ocr_text.setReadOnly(True)
        self.ocr_text.setMaximumHeight(80)
        self.ocr_text.setStyleSheet("background-color: #2d2d2d;")
        form_layout.addWidget(self.ocr_text, row, 1)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def on_kayit_turu_changed(self, index):
        kayit_turu = self.kayit_turu_combo.itemData(index)
        is_aidat = kayit_turu == KayitTuru.AIDAT
        self.uye_label.setVisible(is_aidat)
        self.uye_combo.setVisible(is_aidat)
        self.update_kategoriler()
    
    def update_kategoriler(self):
        self.kategori_combo.clear()
        kayit_turu = self.kayit_turu_combo.currentData()
        
        if kayit_turu == KayitTuru.GELIR:
            kategoriler = ["Aidat", "Bağış", "Faiz", "Kira", "Etkinlik", "Diğer"]
        elif kayit_turu == KayitTuru.GIDER:
            kategoriler = ["Kira", "Fatura", "Maaş", "Malzeme", "Hizmet", "Bakım", "Diğer"]
        elif kayit_turu == KayitTuru.AIDAT:
            kategoriler = ["Aylık Aidat", "Yıllık Aidat", "Ek Aidat"]
        else:
            kategoriler = ["Genel"]
        
        for kat in kategoriler:
            self.kategori_combo.addItem(kat)
    
    def load_uyeler(self):
        """Üyeleri yükle"""
        try:
            from models import UyeYoneticisi
            uye_yoneticisi = UyeYoneticisi(self.db)
            uyeler = uye_yoneticisi.uye_listesi()
            self.uye_combo.clear()
            self.uye_combo.addItem("-- Üye Seçin --", None)
            for uye in uyeler:
                self.uye_combo.addItem(uye['ad_soyad'], uye['uye_id'])
        except Exception as e:
            print(f"Üye listesi yüklenemedi: {e}")
    
    def load_kasalar(self):
        """Kasaları yükle"""
        try:
            from models import KasaYoneticisi
            kasa_yoneticisi = KasaYoneticisi(self.db)
            kasalar = kasa_yoneticisi.kasa_listesi()
            self.kasa_combo.clear()
            for kasa in kasalar:
                self.kasa_combo.addItem(
                    f"{kasa['kasa_adi']} ({kasa['para_birimi']})",
                    kasa['kasa_id']
                )
        except:
            self.kasa_combo.addItem("Varsayılan Kasa", 1)
    
    def set_dosya_yolu(self, path: str):
        self.dosya_yolu = path
    
    def set_ocr_sonuc(self, sonuc: OCRSonuc):
        self.ocr_sonuc = sonuc
        self.dosya_yolu = sonuc.gorsel_yolu
        
        self.ocr_text.setPlainText(sonuc.ham_metin)
        
        alanlar = sonuc.algilanan_alanlar
        
        if 'tutar' in alanlar:
            try:
                self.tutar_spin.setValue(float(alanlar['tutar']))
            except:
                pass
        
        if 'firma' in alanlar:
            self.firma_edit.setText(str(alanlar['firma']))
        
        if 'vergi_no' in alanlar:
            self.vergi_no_edit.setText(str(alanlar['vergi_no']))
        
        if 'belge_no' in alanlar:
            self.belge_no_edit.setText(str(alanlar['belge_no']))
    
    def get_belge_kayit(self) -> BelgeKayit:
        """Form verilerini BelgeKayit olarak döndür"""
        kayit = BelgeKayit()
        
        kayit.belge_turu = self.belge_turu_combo.currentData()
        kayit.kayit_turu = self.kayit_turu_combo.currentData()
        kayit.tarih = self.tarih_edit.date().toPyDate()
        kayit.tutar = self.tutar_spin.value()
        kayit.firma_adi = self.firma_edit.text()
        kayit.vergi_no = self.vergi_no_edit.text()
        kayit.belge_no = self.belge_no_edit.text()
        kayit.kategori = self.kategori_combo.currentText()
        kayit.aciklama = self.aciklama_edit.text()
        kayit.kasa_id = self.kasa_combo.currentData()
        kayit.notlar = self.notlar_edit.toPlainText()
        kayit.uye_id = self.uye_combo.currentData()
        kayit.dosya_yolu = self.dosya_yolu
        
        # Üye adı
        if kayit.uye_id:
            kayit.uye_adi = self.uye_combo.currentText()
        
        return kayit


class Step4_Onay(CardWidget):
    """Adım 4: Onay ve Kayıt"""
    
    kayit_onaylandi = pyqtSignal(object)  # BelgeKayit
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.belge_kayit: Optional[BelgeKayit] = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        step_label = SubtitleLabel("4️⃣ Onayla ve Kaydet")
        layout.addWidget(step_label)
        
        desc = CaptionLabel("Kayıt öncesi bilgileri son kez kontrol edin.")
        layout.addWidget(desc)
        
        # Özet tablosu
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(["Alan", "Değer"])
        self.summary_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.summary_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.summary_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.summary_table)
        
        # Onay checkbox
        self.onay_check = CheckBox("Yukarıdaki bilgilerin doğruluğunu onaylıyorum")
        self.onay_check.stateChanged.connect(self.on_onay_changed)
        layout.addWidget(self.onay_check)
        
        # Kaydet butonu
        self.kaydet_btn = PrimaryPushButton("💾 Sisteme Kaydet")
        self.kaydet_btn.setEnabled(False)
        self.kaydet_btn.clicked.connect(self.on_kaydet)
        layout.addWidget(self.kaydet_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def set_belge_kayit(self, kayit: BelgeKayit):
        self.belge_kayit = kayit
        self.onay_check.setChecked(False)
        
        rows = [
            ("Belge Türü", kayit.belge_turu.value.title()),
            ("Kayıt Türü", kayit.kayit_turu.value.title()),
            ("Tarih", kayit.tarih.strftime("%d.%m.%Y")),
            ("Tutar", f"₺ {kayit.tutar:,.2f}"),
            ("Firma/Kişi", kayit.firma_adi or "-"),
            ("Belge No", kayit.belge_no or "-"),
            ("Kategori", kayit.kategori),
            ("Açıklama", kayit.aciklama or "-"),
            ("Belge", os.path.basename(kayit.dosya_yolu) if kayit.dosya_yolu else "-"),
        ]
        
        if kayit.kayit_turu == KayitTuru.AIDAT and kayit.uye_adi:
            rows.insert(4, ("Üye", kayit.uye_adi))
        
        self.summary_table.setRowCount(len(rows))
        for i, (alan, deger) in enumerate(rows):
            self.summary_table.setItem(i, 0, QTableWidgetItem(alan))
            self.summary_table.setItem(i, 1, QTableWidgetItem(str(deger)))
    
    def on_onay_changed(self, state):
        self.kaydet_btn.setEnabled(state == 2)  # Qt.CheckState.Checked
    
    def on_kaydet(self):
        if self.belge_kayit:
            self.kayit_onaylandi.emit(self.belge_kayit)


# ==================== Ana OCR Widget ====================

class OCRWidget(QWidget):
    """OCR Ana Widget - 4 Adımlı Sihirbaz"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_step = 0
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QHBoxLayout()
        title = TitleLabel("📷 Belge Tarama Sihirbazı")
        header.addWidget(title)
        header.addStretch()
        
        self.step_label = BodyLabel("Adım 1/4")
        self.step_label.setStyleSheet("color: #64B5F6; font-weight: bold;")
        header.addWidget(self.step_label)
        layout.addLayout(header)
        
        # Ana içerik - Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sol: Adımlar stack
        self.steps_stack = QStackedWidget()
        
        # Step 1: Belge Yükle
        self.step1 = Step1_BelgeYukle()
        self.step1.belge_secildi.connect(self.on_belge_secildi)
        self.steps_stack.addWidget(self.step1)
        
        # Step 2: OCR Tarama
        self.step2 = Step2_OCRTarama()
        self.step2.tarama_tamamlandi.connect(self.on_tarama_tamamlandi)
        self.steps_stack.addWidget(self.step2)
        
        # Step 3: Düzenleme
        self.step3 = Step3_Duzenleme(self.db)
        self.steps_stack.addWidget(self.step3)
        
        # Step 4: Onay
        self.step4 = Step4_Onay()
        self.step4.kayit_onaylandi.connect(self.on_kayit_onaylandi)
        self.steps_stack.addWidget(self.step4)
        
        splitter.addWidget(self.steps_stack)
        
        # Sağ: Önizleme
        preview_card = CardWidget()
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.addWidget(SubtitleLabel("📄 Belge Önizleme"))
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(280, 350)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """)
        self.preview_label.setText("Belge önizlemesi\nburada görünecek")
        preview_layout.addWidget(self.preview_label)
        
        splitter.addWidget(preview_card)
        splitter.setSizes([550, 280])
        
        layout.addWidget(splitter, 1)
        
        # Alt navigasyon butonları
        nav_layout = QHBoxLayout()
        
        self.back_btn = PushButton("◀ Geri")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        nav_layout.addWidget(self.back_btn)
        
        nav_layout.addStretch()
        
        self.reset_btn = PushButton("🔄 Yeni Tarama")
        self.reset_btn.clicked.connect(self.reset_wizard)
        nav_layout.addWidget(self.reset_btn)
        
        self.next_btn = PrimaryPushButton("İleri ▶")
        self.next_btn.clicked.connect(self.go_next)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
    
    def update_step_label(self):
        labels = [
            "Adım 1/4: Belge Yükle",
            "Adım 2/4: OCR Tarama",
            "Adım 3/4: Bilgileri Düzenle",
            "Adım 4/4: Onayla ve Kaydet"
        ]
        self.step_label.setText(labels[self.current_step])
    
    def on_belge_secildi(self, path: str):
        # Önizlemeyi güncelle
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                260, 330,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
        
        self.step2.set_image(path)
        self.step3.set_dosya_yolu(path)
        self.next_btn.setEnabled(True)
    
    def on_tarama_tamamlandi(self, sonuc: OCRSonuc):
        self.step3.set_ocr_sonuc(sonuc)
        self.go_next()
    
    def on_kayit_onaylandi(self, kayit: BelgeKayit):
        try:
            self.save_to_database(kayit)
            InfoBar.success(
                "Başarılı", 
                "Kayıt başarıyla oluşturuldu!",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
            self.reset_wizard()
        except Exception as e:
            InfoBar.error(
                "Hata",
                f"Kayıt hatası: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000
            )
    
    def save_to_database(self, kayit: BelgeKayit):
        """Kaydı veritabanına ekle"""
        from models import GelirYoneticisi, GiderYoneticisi, KasaYoneticisi, BelgeYoneticisi, AidatYoneticisi
        
        # Belgeyi kopyala
        belge_klasoru = os.path.expanduser("~/Documents/BADER_Belgeler")
        os.makedirs(belge_klasoru, exist_ok=True)
        
        hedef_yol = ""
        if kayit.dosya_yolu and os.path.exists(kayit.dosya_yolu):
            dosya_adi = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(kayit.dosya_yolu)}"
            hedef_yol = os.path.join(belge_klasoru, dosya_adi)
            shutil.copy2(kayit.dosya_yolu, hedef_yol)
        
        # Kasa ID - formdan seçilen veya varsayılan
        kasa_id = kayit.kasa_id
        if not kasa_id:
            kasa_yoneticisi = KasaYoneticisi(self.db)
            kasalar = kasa_yoneticisi.kasa_listesi()
            kasa_id = kasalar[0]['kasa_id'] if kasalar else 1
        
        if kayit.kayit_turu == KayitTuru.GELIR:
            gelir_yoneticisi = GelirYoneticisi(self.db)
            gelir_yoneticisi.gelir_ekle(
                tarih=kayit.tarih.isoformat(),
                gelir_turu=kayit.kategori or "DİĞER",
                aciklama=kayit.aciklama or f"{kayit.firma_adi} - {kayit.kategori}",
                tutar=kayit.tutar,
                kasa_id=kasa_id,
                tahsil_eden="",
                notlar=kayit.notlar,
                dekont_no=kayit.belge_no
            )
        elif kayit.kayit_turu == KayitTuru.GIDER:
            gider_yoneticisi = GiderYoneticisi(self.db)
            gider_yoneticisi.gider_ekle(
                tarih=kayit.tarih.isoformat(),
                gider_turu=kayit.kategori or "DİĞER",
                aciklama=kayit.aciklama or f"{kayit.firma_adi} - {kayit.kategori}",
                tutar=kayit.tutar,
                kasa_id=kasa_id,
                odeyen="",
                notlar=kayit.notlar
            )
        elif kayit.kayit_turu == KayitTuru.AIDAT:
            if kayit.uye_id:
                aidat_yoneticisi = AidatYoneticisi(self.db)
                # Mevcut yılın aidat kaydını bul veya oluştur
                yil = kayit.tarih.year
                aidat_id = aidat_yoneticisi.aidat_kaydi_olustur(
                    uye_id=kayit.uye_id,
                    yil=yil,
                    yillik_tutar=kayit.tutar
                )
                if aidat_id > 0:
                    # Ödeme ekle
                    aidat_yoneticisi.aidat_odeme_ekle(
                        aidat_id=aidat_id,
                        tarih=kayit.tarih.isoformat(),
                        tutar=kayit.tutar,
                        aciklama=kayit.aciklama or "OCR ile eklenen ödeme"
                    )
        elif kayit.kayit_turu == KayitTuru.SADECE_BELGE:
            # Sadece belge kaydet
            try:
                yonetici = BelgeYoneticisi(self.db)
                yonetici.belge_ekle(
                    belge_adi=os.path.basename(hedef_yol) if hedef_yol else "OCR Belgesi",
                    dosya_yolu=hedef_yol,
                    belge_turu=kayit.belge_turu.value,
                    aciklama=kayit.aciklama,
                    dosya_boyutu=os.path.getsize(hedef_yol) if hedef_yol else 0
                )
            except Exception as e:
                print(f"Belge kayıt hatası: {e}")
    
    def go_next(self):
        if self.current_step < 3:
            # Step 3'e geçerken form verilerini step 4'e aktar
            if self.current_step == 2:
                kayit = self.step3.get_belge_kayit()
                self.step4.set_belge_kayit(kayit)
            
            self.current_step += 1
            self.steps_stack.setCurrentIndex(self.current_step)
            self.update_step_label()
            
            self.back_btn.setEnabled(True)
            
            if self.current_step == 3:
                self.next_btn.setEnabled(False)
            elif self.current_step == 2:
                self.next_btn.setEnabled(True)  # Düzenleme adımında her zaman ileri gidebilir
    
    def go_back(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.steps_stack.setCurrentIndex(self.current_step)
            self.update_step_label()
            
            self.next_btn.setEnabled(True)
            
            if self.current_step == 0:
                self.back_btn.setEnabled(False)
    
    def reset_wizard(self):
        """Sihirbazı sıfırla"""
        self.current_step = 0
        self.steps_stack.setCurrentIndex(0)
        self.update_step_label()
        
        self.back_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        
        self.step1.clear_selection()
        self.preview_label.setText("Belge önizlemesi\nburada görünecek")
        self.preview_label.setPixmap(QPixmap())
