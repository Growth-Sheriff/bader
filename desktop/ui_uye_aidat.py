"""
BADER Derneği - Üye Bazlı Aidat Takip Sayfası (Full Page)
Tek üyenin tüm yıllarına ait aidat durumunu gösteren tam sayfa
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QScrollArea, QLineEdit,
                             QCompleter, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QStringListModel, QDate
from qfluentwidgets import MessageBox
from PyQt5.QtGui import QColor
from database import Database
from models import UyeYoneticisi, AidatYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import create_double_spin_box, create_date_edit, create_combo_box, create_line_edit
from datetime import datetime
from typing import Optional


class YilAidatCard(QFrame):
    """Bir yılın aidat kartı"""
    
    odeme_ekle = pyqtSignal(int)  # aidat_id
    
    def __init__(self, aidat_data: dict, odemeler: list, parent=None):
        super().__init__(parent)
        self.aidat_data = aidat_data
        self.odemeler = odemeler
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.1);
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Yıl
        yil_label = QLabel(str(self.aidat_data['yil']))
        yil_label.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 22px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(yil_label)
        
        header_layout.addStretch()
        
        # Durum badge
        durum = self.aidat_data['durum']
        if durum == 'Tamamlandı':
            badge_color = "#4CAF50"
            badge_bg = "rgba(76, 175, 80, 0.12)"
        elif durum == 'Kısmi':
            badge_color = "#FF9800"
            badge_bg = "rgba(255, 152, 0, 0.12)"
        else:
            badge_color = "#f44336"
            badge_bg = "rgba(244, 67, 54, 0.12)"
            
        durum_badge = QLabel(f"● {durum}")
        durum_badge.setStyleSheet(f"""
            QLabel {{
                color: {badge_color};
                background-color: {badge_bg};
                padding: 6px 14px;
                border-radius: 15px;
                font-size: 13px;
                font-weight: 600;
                border: none;
            }}
        """)
        header_layout.addWidget(durum_badge)
        
        layout.addLayout(header_layout)
        
        # Özet satırı
        ozet_layout = QHBoxLayout()
        ozet_layout.setSpacing(30)
        
        yillik = self.aidat_data['yillik_aidat_tutari']
        odenen = self.aidat_data.get('toplam_odenen', 0) or 0
        kalan = self.aidat_data['odenecek_tutar']
        
        # Yıllık Aidat
        ozet_layout.addWidget(self._create_stat("Yıllık Aidat", f"{yillik:,.2f} ₺", "#64B5F6"))
        # Ödenen
        ozet_layout.addWidget(self._create_stat("Ödenen", f"{odenen:,.2f} ₺", "#4CAF50"))
        # Kalan
        kalan_color = "#f44336" if kalan > 0 else "#4CAF50"
        ozet_layout.addWidget(self._create_stat("Kalan", f"{kalan:,.2f} ₺", kalan_color))
        
        ozet_layout.addStretch()
        
        layout.addLayout(ozet_layout)
        
        # Ödemeler tablosu
        if self.odemeler:
            odeme_label = QLabel("Ödemeler")
            odeme_label.setStyleSheet("""
                QLabel {
                    color: #6d6b77;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-top: 10px;
                    background: transparent;
                    border: none;
                }
            """)
            layout.addWidget(odeme_label)
            
            for odeme in self.odemeler:
                odeme_row = QHBoxLayout()
                
                tarih = QLabel(odeme['tarih'])
                tarih.setStyleSheet("color: #6d6b77; font-size: 13px; background: transparent; border: none;")
                odeme_row.addWidget(tarih)
                
                tutar = QLabel(f"{odeme['tutar']:,.2f} ₺")
                tutar.setStyleSheet("color: #444050; font-size: 13px; font-weight: 600; background: transparent; border: none;")
                odeme_row.addWidget(tutar)
                
                tahsilat = QLabel(odeme.get('tahsilat_turu', 'Nakit'))
                tahsilat.setStyleSheet("color: #97959e; font-size: 12px; background: transparent; border: none;")
                odeme_row.addWidget(tahsilat)
                
                dekont = odeme.get('dekont_no', '')
                if dekont:
                    dekont_label = QLabel(f"#{dekont}")
                    dekont_label.setStyleSheet("color: #64B5F6; font-size: 12px; background: transparent; border: none;")
                    odeme_row.addWidget(dekont_label)
                
                odeme_row.addStretch()
                layout.addLayout(odeme_row)
        
        # Ödeme ekle butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        odeme_btn = QPushButton("+ Ödeme Ekle")
        odeme_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64B5F6;
                border: 1px solid #64B5F6;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(100, 181, 246, 0.1);
            }
        """)
        odeme_btn.clicked.connect(lambda: self.odeme_ekle.emit(self.aidat_data['aidat_id']))
        btn_layout.addWidget(odeme_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def _create_stat(self, label: str, value: str, color: str) -> QWidget:
        """İstatistik widget oluştur"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #97959e; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(value_widget)
        
        widget.setLayout(layout)
        return widget


class UyeAidatWidget(QWidget):
    """Üye bazlı aidat takip sayfası - Full Page"""
    
    geri_don = pyqtSignal()  # Listeye dön sinyali
    
    def __init__(self, db: Database, uye_id: int = None):
        super().__init__()
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.aidat_yoneticisi = AidatYoneticisi(db)
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
        self.title_label = QLabel("Aidat Takip")
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
        
        # Çok yıllık ödeme butonu
        self.coklu_yil_btn = QPushButton("📅 Çok Yıllık Ödeme")
        self.coklu_yil_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.coklu_yil_btn.clicked.connect(self.coklu_yil_odeme_ac)
        self.coklu_yil_btn.setEnabled(False)
        header_layout.addWidget(self.coklu_yil_btn)
        
        # Üye arama
        self.arama_edit = QLineEdit()
        self.arama_edit.setPlaceholderText("🔍 Üye ara (isim yazın)...")
        self.arama_edit.setMinimumWidth(300)
        self.arama_edit.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #64B5F6;
                background-color: white;
            }
        """)
        self.arama_edit.returnPressed.connect(self.uye_ara)
        header_layout.addWidget(self.arama_edit)
        
        # Completer için üye listesi
        self._setup_completer()
        
        header.setLayout(header_layout)
        main_layout.addWidget(header)
        
        # Content Area
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #f8f7fa;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)
        
        # Özet Kartı
        self.ozet_frame = QFrame()
        self.ozet_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.08);
                border-radius: 10px;
            }
        """)
        ozet_layout = QHBoxLayout()
        ozet_layout.setContentsMargins(25, 20, 25, 20)
        ozet_layout.setSpacing(40)
        
        self.ozet_odenen = self._create_ozet_stat("Toplam Ödenen", "0.00 ₺", "#4CAF50")
        ozet_layout.addWidget(self.ozet_odenen)
        
        self.ozet_borc = self._create_ozet_stat("Toplam Borç", "0.00 ₺", "#f44336")
        ozet_layout.addWidget(self.ozet_borc)
        
        self.ozet_fazla = self._create_ozet_stat("Fazla Ödeme", "0.00 ₺", "#64B5F6")
        ozet_layout.addWidget(self.ozet_fazla)
        
        ozet_layout.addStretch()
        self.ozet_frame.setLayout(ozet_layout)
        content_layout.addWidget(self.ozet_frame)
        
        # Yıllar Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.yillar_widget = QWidget()
        self.yillar_widget.setStyleSheet("background: transparent;")
        self.yillar_layout = QVBoxLayout()
        self.yillar_layout.setContentsMargins(0, 0, 0, 0)
        self.yillar_layout.setSpacing(15)
        self.yillar_widget.setLayout(self.yillar_layout)
        
        scroll.setWidget(self.yillar_widget)
        content_layout.addWidget(scroll)
        
        content_frame.setLayout(content_layout)
        main_layout.addWidget(content_frame)
        
        self.setLayout(main_layout)
        
    def _setup_completer(self):
        """Üye arama için autocomplete"""
        uyeler = self.uye_yoneticisi.uye_listesi()
        uye_isimleri = [u['ad_soyad'] for u in uyeler]
        
        completer = QCompleter(uye_isimleri)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.arama_edit.setCompleter(completer)
        
        # Seçildiğinde yükle
        completer.activated.connect(self._on_uye_selected)
        
    def _on_uye_selected(self, text: str):
        """Üye seçildiğinde"""
        uyeler = self.uye_yoneticisi.uye_listesi()
        for uye in uyeler:
            if uye['ad_soyad'] == text:
                self.load_uye(uye['uye_id'])
                break
        
    def _create_ozet_stat(self, label: str, value: str, color: str) -> QWidget:
        """Özet istatistik widget"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #6d6b77; font-size: 13px; background: transparent; border: none;")
        label_widget.setObjectName("label")
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 700; background: transparent; border: none;")
        value_widget.setObjectName("value")
        layout.addWidget(value_widget)
        
        widget.setLayout(layout)
        return widget
        
    def load_uye(self, uye_id: int):
        """Üye verilerini yükle"""
        self.uye_id = uye_id
        self.uye_data = self.uye_yoneticisi.uye_getir(uye_id)
        
        if not self.uye_data:
            MessageBox("Hata", "Üye bulunamadı!", self).show()
            return
        
        # Başlık güncelle
        self.title_label.setText(f"Aidat Takip: {self.uye_data['ad_soyad']}")
        self.arama_edit.setText(self.uye_data['ad_soyad'])
        
        # Çok yıllık ödeme butonunu aktif et
        self.coklu_yil_btn.setEnabled(True)
        
        # Yılları temizle
        while self.yillar_layout.count():
            item = self.yillar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Aidat verilerini al
        yillar = self.uye_yoneticisi.uye_aidat_yillari(uye_id)
        
        # Özet hesapla
        toplam_odenen = 0
        toplam_borc = 0
        
        for aidat in yillar:
            odenen = aidat.get('toplam_odenen', 0) or 0
            kalan = aidat.get('odenecek_tutar', 0) or 0
            toplam_odenen += odenen
            if kalan > 0:
                toplam_borc += kalan
        
        # Fazla ödeme hesapla (negatif kalan toplamı)
        fazla_odeme = 0
        for aidat in yillar:
            kalan = aidat.get('odenecek_tutar', 0) or 0
            if kalan < 0:
                fazla_odeme += abs(kalan)
        
        # Özet güncelle
        self.ozet_odenen.findChild(QLabel, "value").setText(f"{toplam_odenen:,.2f} ₺")
        self.ozet_borc.findChild(QLabel, "value").setText(f"{toplam_borc:,.2f} ₺")
        self.ozet_fazla.findChild(QLabel, "value").setText(f"{fazla_odeme:,.2f} ₺")
        
        # Her yıl için kart oluştur
        for aidat in yillar:
            odemeler = self.aidat_yoneticisi.uye_aidat_odemeleri(aidat['aidat_id'])
            card = YilAidatCard(aidat, odemeler)
            card.odeme_ekle.connect(self.odeme_ekle)
            self.yillar_layout.addWidget(card)
        
        # Kayıt yoksa mesaj göster
        if not yillar:
            no_data = QLabel("Bu üye için aidat kaydı bulunamadı.")
            no_data.setStyleSheet("""
                QLabel {
                    color: #97959e;
                    font-size: 15px;
                    padding: 40px;
                    background: white;
                    border-radius: 10px;
                }
            """)
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.yillar_layout.addWidget(no_data)
        
        self.yillar_layout.addStretch()
        
    def uye_ara(self):
        """Üye ara"""
        text = self.arama_edit.text().strip()
        if not text:
            return
            
        uyeler = self.uye_yoneticisi.uye_ara(text)
        if uyeler:
            self.load_uye(uyeler[0]['uye_id'])
        else:
            MessageBox("Bilgi", "Üye bulunamadı.", self).show()
    
    def coklu_yil_odeme_ac(self):
        """Çok yıllık ödeme drawer'ını aç"""
        if not self.uye_id:
            MessageBox("Uyarı", "Lütfen önce bir üye seçiniz!", self).exec()
            return
        
        from ui_coklu_yil_odeme import CokluYilOdemeFormWidget
        from ui_drawer import DrawerPanel
        from models import GelirYoneticisi
        
        form = CokluYilOdemeFormWidget(self.db, self.uye_id)
        drawer = DrawerPanel(self, "💰 Çok Yıllık Aidat Ödemesi", form, width=550)
        
        def on_submit():
            if not form.validate():
                return
            
            data = form.get_data()
            
            # Onay
            yil_sayisi = data['bitis'] - data['baslangic'] + 1
            toplam = data['yillik_aidat'] * yil_sayisi
            
            onay = MessageBox(
                "Çok Yıllık Ödeme Onayı",
                f"{data['uye_adi']}\n\n"
                f"Yıllar: {data['baslangic']} - {data['bitis']} ({yil_sayisi} yıl)\n"
                f"Yıllık Tutar: {data['yillik_aidat']:,.2f} ₺\n"
                f"Toplam: {toplam:,.2f} ₺\n\n"
                f"Onaylıyor musunuz?",
                self
            )
            
            if onay.exec() != MessageBox.StandardButton.Yes:
                return
            
            try:
                gelir_yoneticisi = GelirYoneticisi(self.db)
                
                # Çok yıllık gelir ekle
                odeme_grup_id = gelir_yoneticisi.coklu_yil_gelir_ekle(
                    gelir_turu='AİDAT',
                    kasa_id=data['kasa_id'],
                    baslangic_yil=data['baslangic'],
                    bitis_yil=data['bitis'],
                    yillik_tutar=data['yillik_aidat'],
                    tahsil_tarihi=data['tarih'],
                    uye_id=data['uye_id'],
                    aciklama=f"{data['uye_adi']} - Çok Yıllık Aidat",
                    tahsil_eden="Sistem"
                )
                
                self.load_uye(self.uye_id)
                MessageBox("Başarılı", f"{yil_sayisi} yıllık ödeme kaydedildi!", self).exec()
                drawer.close()
                
            except Exception as e:
                MessageBox("Hata", f"Ödeme kaydedilemedi:\n{str(e)}", self).exec()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
            
    def odeme_ekle(self, aidat_id: int):
        """Ödeme ekle drawer"""
        # Kalan tutarı hesapla
        self.db.cursor.execute("""
            SELECT odenecek_tutar FROM aidat_takip WHERE aidat_id = ?
        """, (aidat_id,))
        result = self.db.cursor.fetchone()
        kalan = result['odenecek_tutar'] if result else 0
        
        # Form oluştur
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(20)
        
        # Kalan borç bilgisi
        if kalan > 0:
            info_label = QLabel(f"Kalan Borç: {kalan:.2f} ₺")
            info_label.setStyleSheet("""
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
            form_layout.addWidget(info_label)
        
        # Tarih
        tarih_field = create_date_edit("Tarih")
        tarih_field[1].setDate(QDate.currentDate())
        form_layout.addWidget(tarih_field[0])
        
        # Tutar
        tutar_field = create_double_spin_box("Tutar *")
        tutar_field[1].setMinimum(0.01)
        tutar_field[1].setMaximum(1000000)
        tutar_field[1].setValue(kalan if kalan > 0 else 100)
        tutar_field[1].setSuffix(" ₺")
        form_layout.addWidget(tutar_field[0])
        
        # Tahsilat Türü
        tahsilat_field = create_combo_box("Tahsilat Türü")
        tahsilat_field[1].addItems(["Nakit", "Banka Transferi", "Kredi Kartı", "Havale"])
        form_layout.addWidget(tahsilat_field[0])
        
        # Dekont No
        dekont_field = create_line_edit("Dekont No", "Dekont numarası...")
        form_layout.addWidget(dekont_field[0])
        
        # Açıklama
        aciklama_field = create_line_edit("Açıklama", "Ödeme açıklaması...")
        form_layout.addWidget(aciklama_field[0])
        
        form_layout.addStretch()
        form_widget.setLayout(form_layout)
        
        # Drawer aç
        drawer = DrawerPanel(self, "Ödeme Ekle", form_widget)
        
        def on_submit():
            try:
                self.aidat_yoneticisi.aidat_odeme_ekle(
                    aidat_id,
                    tarih_field[1].date().toString("yyyy-MM-dd"),
                    tutar_field[1].value(),
                    aciklama_field[1].text().strip(),
                    tahsilat_field[1].currentText(),
                    dekont_field[1].text().strip()
                )
                self.load_uye(self.uye_id)  # Yenile
                MessageBox("Başarılı", "Ödeme kaydedildi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Hata oluştu:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()


