"""
⚙️ BADER - Ayarlar Sayfası
FluentWidgets ile modern ayarlar arayüzü
Server, Takım Yönetimi ve Genel Ayarlar
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QStackedWidget
from PyQt5.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, CardWidget,
    LineEdit, DoubleSpinBox, PushButton, InfoBar, InfoBarPosition,
    Pivot, ScrollArea, qrouter
)
from database import Database


class GeneralSettingsWidget(QWidget):
    """Genel ayarlar"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_ayarlar()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # === DERNEK BİLGİLERİ ===
        dernek_card = CardWidget()
        dernek_layout = QVBoxLayout(dernek_card)
        dernek_layout.setContentsMargins(20, 20, 20, 20)
        dernek_layout.setSpacing(15)
        
        dernek_title = SubtitleLabel("🏢 Dernek Bilgileri")
        dernek_layout.addWidget(dernek_title)
        
        form1 = QFormLayout()
        form1.setSpacing(10)
        
        self.dernek_adi_edit = LineEdit()
        self.dernek_adi_edit.setPlaceholderText("Dernek adını girin")
        form1.addRow(BodyLabel("Dernek Adı:"), self.dernek_adi_edit)
        
        self.dernek_adres_edit = LineEdit()
        self.dernek_adres_edit.setPlaceholderText("Dernek adresini girin")
        form1.addRow(BodyLabel("Adres:"), self.dernek_adres_edit)
        
        self.dernek_telefon_edit = LineEdit()
        self.dernek_telefon_edit.setPlaceholderText("Telefon numarası")
        form1.addRow(BodyLabel("Telefon:"), self.dernek_telefon_edit)
        
        self.dernek_email_edit = LineEdit()
        self.dernek_email_edit.setPlaceholderText("E-posta adresi")
        form1.addRow(BodyLabel("E-posta:"), self.dernek_email_edit)
        
        dernek_layout.addLayout(form1)
        layout.addWidget(dernek_card)
        
        # === MALİ AYARLAR ===
        mali_card = CardWidget()
        mali_layout = QVBoxLayout(mali_card)
        mali_layout.setContentsMargins(20, 20, 20, 20)
        mali_layout.setSpacing(15)
        
        mali_title = SubtitleLabel("💰 Mali Ayarlar")
        mali_layout.addWidget(mali_title)
        
        form2 = QFormLayout()
        form2.setSpacing(10)
        
        self.varsayilan_aidat_spin = DoubleSpinBox()
        self.varsayilan_aidat_spin.setRange(0, 1000000)
        self.varsayilan_aidat_spin.setSuffix(" ₺")
        form2.addRow(BodyLabel("Varsayılan Aidat:"), self.varsayilan_aidat_spin)
        
        self.usd_kur_spin = DoubleSpinBox()
        self.usd_kur_spin.setRange(0, 1000)
        self.usd_kur_spin.setDecimals(4)
        form2.addRow(BodyLabel("USD Kuru (TL):"), self.usd_kur_spin)
        
        self.eur_kur_spin = DoubleSpinBox()
        self.eur_kur_spin.setRange(0, 1000)
        self.eur_kur_spin.setDecimals(4)
        form2.addRow(BodyLabel("EUR Kuru (TL):"), self.eur_kur_spin)
        
        mali_layout.addLayout(form2)
        layout.addWidget(mali_card)
        
        # Kaydet butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.kaydet_btn = PushButton("💾 Ayarları Kaydet")
        self.kaydet_btn.clicked.connect(self.kaydet)
        btn_layout.addWidget(self.kaydet_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
    
    def load_ayarlar(self):
        """Ayarları veritabanından yükle"""
        ayarlar = {
            'dernek_adi': 'BADER Derneği',
            'dernek_adres': '',
            'dernek_telefon': '',
            'dernek_email': '',
            'varsayilan_aidat_tutari': '1000',
            'usd_kuru': '30.0',
            'eur_kuru': '33.0'
        }
        
        try:
            for ayar_adi in ayarlar.keys():
                self.db.cursor.execute(
                    "SELECT ayar_degeri FROM ayarlar WHERE ayar_adi = ?",
                    (ayar_adi,)
                )
                result = self.db.cursor.fetchone()
                if result:
                    ayarlar[ayar_adi] = result[0]
        except Exception as e:
            print(f"Ayarlar yüklenirken hata: {e}")
        
        self.dernek_adi_edit.setText(ayarlar['dernek_adi'])
        self.dernek_adres_edit.setText(ayarlar['dernek_adres'])
        self.dernek_telefon_edit.setText(ayarlar['dernek_telefon'])
        self.dernek_email_edit.setText(ayarlar['dernek_email'])
        self.varsayilan_aidat_spin.setValue(float(ayarlar['varsayilan_aidat_tutari']))
        self.usd_kur_spin.setValue(float(ayarlar['usd_kuru']))
        self.eur_kur_spin.setValue(float(ayarlar['eur_kuru']))
        
    def kaydet(self):
        """Ayarları veritabanına kaydet"""
        ayarlar = {
            'dernek_adi': self.dernek_adi_edit.text(),
            'dernek_adres': self.dernek_adres_edit.text(),
            'dernek_telefon': self.dernek_telefon_edit.text(),
            'dernek_email': self.dernek_email_edit.text(),
            'varsayilan_aidat_tutari': str(self.varsayilan_aidat_spin.value()),
            'usd_kuru': str(self.usd_kur_spin.value()),
            'eur_kuru': str(self.eur_kur_spin.value())
        }
        
        try:
            for ayar_adi, ayar_degeri in ayarlar.items():
                self.db.cursor.execute("""
                    INSERT OR REPLACE INTO ayarlar (ayar_adi, ayar_degeri)
                    VALUES (?, ?)
                """, (ayar_adi, ayar_degeri))
            
            self.db.commit()
            
            InfoBar.success(
                title="Başarılı",
                content="Ayarlar kaydedildi",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
        except Exception as e:
            InfoBar.error(
                title="Hata",
                content=f"Ayarlar kaydedilemedi: {e}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000
            )


class AyarlarWidget(QWidget):
    """Ayarlar sayfası - Sekmeli"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Başlık
        title = TitleLabel("⚙️ Ayarlar")
        layout.addWidget(title)
        
        # Pivot (Tab) navigasyonu
        self.pivot = Pivot()
        layout.addWidget(self.pivot)
        
        # Stacked widget for content
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Genel Ayarlar
        self.general_widget = GeneralSettingsWidget(self.db)
        self.stack.addWidget(self.general_widget)
        self.pivot.addItem(
            routeKey='general',
            text='Genel',
            onClick=lambda: self.stack.setCurrentWidget(self.general_widget)
        )
        
        # Takım Yönetimi
        from ui_team import TeamManagementWidget
        self.team_widget = TeamManagementWidget(self.db)
        self.stack.addWidget(self.team_widget)
        self.pivot.addItem(
            routeKey='team',
            text='Takım Yönetimi',
            onClick=lambda: self.stack.setCurrentWidget(self.team_widget)
        )
        
        # Server Ayarları
        from ui_server import ServerSettingsWidget
        self.server_widget = ServerSettingsWidget(self.db)
        self.stack.addWidget(self.server_widget)
        self.pivot.addItem(
            routeKey='server',
            text='Server',
            onClick=lambda: self.stack.setCurrentWidget(self.server_widget)
        )
        
        # İlk sekmeyi seç
        self.pivot.setCurrentItem('general')
        self.stack.setCurrentWidget(self.general_widget)
