"""
BADER - Aktivasyon ve Lisans Yönetimi UI
Desktop uygulaması için lisans aktivasyonu ve güncelleme kontrolü
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox, QProgressBar, QGroupBox,
    QStackedWidget, QDialog, QTextEdit, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

try:
    from qfluentwidgets import (
        PrimaryPushButton, PushButton, LineEdit, InfoBar, InfoBarPosition,
        ProgressBar, CardWidget, TitleLabel, BodyLabel, CaptionLabel,
        FluentIcon, SubtitleLabel, TextEdit, MessageBox
    )
    FLUENT = True
except ImportError:
    FLUENT = False

from server_client import ServerClient
import platform
import os


class ActivationWorker(QThread):
    """Aktivasyon işlemi için arka plan thread'i"""
    finished = pyqtSignal(bool, str, dict)
    
    def __init__(self, client: ServerClient, license_key: str):
        super().__init__()
        self.client = client
        self.license_key = license_key
    
    def run(self):
        success, message, data = self.client.activate_license(self.license_key)
        self.finished.emit(success, message, data or {})


class UpdateCheckWorker(QThread):
    """Güncelleme kontrolü için arka plan thread'i"""
    finished = pyqtSignal(bool, str, dict)
    
    def __init__(self, client: ServerClient, current_version: str):
        super().__init__()
        self.client = client
        self.current_version = current_version
    
    def run(self):
        success, message, data = self.client.check_update(self.current_version)
        self.finished.emit(success, message, data or {})


class ActivationDialog(QDialog):
    """Lisans aktivasyon dialog'u"""
    
    activated = pyqtSignal(dict)  # Aktivasyon başarılı olduğunda
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = ServerClient()
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("BADER - Lisans Aktivasyonu")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo/Başlık
        title = QLabel("🏛️ BADER")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Dernek & Köy Yönetim Sistemi")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #6b7280;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Açıklama
        desc = QLabel(
            "Uygulamayı kullanmak için lisans anahtarınızı girin.\n"
            "Lisans anahtarı admin panelinizden alabilirsiniz."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #4b5563;")
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        # Lisans anahtarı girişi
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Lisans Anahtarı (örn: BADER-2024-XXXX-XXXX)")
        self.license_input.setFont(QFont("Consolas", 12))
        self.license_input.setMinimumHeight(45)
        self.license_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)
        layout.addWidget(self.license_input)
        
        # Durum mesajı
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Belirsiz progress
        self.progress.hide()
        layout.addWidget(self.progress)
        
        layout.addStretch()
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.activate_btn = QPushButton("Aktive Et")
        self.activate_btn.setMinimumHeight(40)
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.activate_btn.clicked.connect(self.do_activate)
        button_layout.addWidget(self.activate_btn)
        
        layout.addLayout(button_layout)
        
        # Demo bilgisi
        demo_label = QLabel(
            "<small>Demo için: <code>BADER-2024-DEMO-0001</code></small>"
        )
        demo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        demo_label.setStyleSheet("color: #9ca3af;")
        layout.addWidget(demo_label)
    
    def do_activate(self):
        license_key = self.license_input.text().strip()
        
        if not license_key:
            self.show_status("Lütfen lisans anahtarı girin", "error")
            return
        
        self.activate_btn.setEnabled(False)
        self.license_input.setEnabled(False)
        self.progress.show()
        self.show_status("Aktivasyon kontrol ediliyor...", "info")
        
        self.worker = ActivationWorker(self.client, license_key)
        self.worker.finished.connect(self.on_activation_result)
        self.worker.start()
    
    def on_activation_result(self, success: bool, message: str, data: dict):
        self.progress.hide()
        self.activate_btn.setEnabled(True)
        self.license_input.setEnabled(True)
        
        if success:
            self.show_status(f"✅ {message}", "success")
            self.activated.emit(data)
            QTimer.singleShot(1500, self.accept)
        else:
            self.show_status(f"❌ {message}", "error")
    
    def show_status(self, message: str, status: str = "info"):
        colors = {
            "info": "#3b82f6",
            "success": "#10b981",
            "error": "#ef4444",
            "warning": "#f59e0b"
        }
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {colors.get(status, '#3b82f6')};")


class UpdateDialog(QDialog):
    """Güncelleme dialog'u"""
    
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("BADER - Güncelleme Mevcut")
        self.setFixedSize(450, 350)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Başlık
        title = QLabel("🎉 Yeni Güncelleme Mevcut!")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Versiyon bilgisi
        version_text = f"v{self.update_info.get('current_version', '?')} → v{self.update_info.get('latest_version', '?')}"
        version_label = QLabel(version_text)
        version_label.setFont(QFont("Segoe UI", 14))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #6366f1; font-weight: bold;")
        layout.addWidget(version_label)
        
        # Değişiklik notları
        changelog = self.update_info.get('changelog', 'Değişiklik notları mevcut değil.')
        changelog_box = QTextEdit()
        changelog_box.setPlainText(changelog)
        changelog_box.setReadOnly(True)
        changelog_box.setMaximumHeight(120)
        changelog_box.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px;
                background-color: #f9fafb;
            }
        """)
        layout.addWidget(changelog_box)
        
        # Dosya boyutu
        file_size = self.update_info.get('file_size', 0)
        if file_size:
            size_mb = file_size / (1024 * 1024)
            size_label = QLabel(f"📦 Dosya boyutu: {size_mb:.1f} MB")
            size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            size_label.setStyleSheet("color: #6b7280;")
            layout.addWidget(size_label)
        
        # Kritik güncelleme uyarısı
        if self.update_info.get('is_critical') or self.update_info.get('force_update'):
            warning = QLabel("⚠️ Bu kritik bir güncelleme. Lütfen en kısa sürede güncelleyin.")
            warning.setStyleSheet("color: #ef4444; font-weight: bold;")
            warning.setWordWrap(True)
            warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(warning)
        
        layout.addStretch()
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        if not self.update_info.get('force_update'):
            later_btn = QPushButton("Daha Sonra")
            later_btn.setMinimumHeight(40)
            later_btn.clicked.connect(self.reject)
            button_layout.addWidget(later_btn)
        
        download_btn = QPushButton("Şimdi İndir")
        download_btn.setMinimumHeight(40)
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        download_btn.clicked.connect(self.download_update)
        button_layout.addWidget(download_btn)
        
        layout.addLayout(button_layout)
    
    def download_update(self):
        download_url = self.update_info.get('download_url')
        if download_url:
            import webbrowser
            # Tam URL oluştur
            if download_url.startswith('/'):
                base_url = "http://157.90.154.48:8080"
                download_url = base_url + download_url
            webbrowser.open(download_url)
        self.accept()


class ActivationWidget(QWidget):
    """Ana pencere için aktivasyon widget'ı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = ServerClient()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("Lisans Bilgileri")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Lisans durumu kartı
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        
        if self.client.is_configured():
            # Aktif lisans
            status_icon = QLabel("✅")
            status_icon.setFont(QFont("Segoe UI", 32))
            status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(status_icon)
            
            status_text = QLabel("Lisans Aktif")
            status_text.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            status_text.setStyleSheet("color: #10b981;")
            status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(status_text)
            
            card_layout.addSpacing(15)
            
            # Lisans detayları
            customer_id = self.client.config.customer_id or "-"
            details = QLabel(f"<b>Customer ID:</b> {customer_id}")
            details.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(details)
            
        else:
            # Lisans yok
            status_icon = QLabel("🔒")
            status_icon.setFont(QFont("Segoe UI", 32))
            status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(status_icon)
            
            status_text = QLabel("Lisans Gerekli")
            status_text.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            status_text.setStyleSheet("color: #f59e0b;")
            status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(status_text)
            
            card_layout.addSpacing(15)
            
            desc = QLabel("Uygulamayı kullanmak için lisans aktivasyonu gerekli.")
            desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc.setStyleSheet("color: #6b7280;")
            card_layout.addWidget(desc)
        
        layout.addWidget(card)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        if self.client.is_configured():
            # Lisans kaldır butonu
            remove_btn = QPushButton("Lisansı Kaldır")
            remove_btn.clicked.connect(self.remove_license)
            btn_layout.addWidget(remove_btn)
            
            # Güncelleme kontrolü
            update_btn = QPushButton("Güncelleme Kontrol Et")
            update_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6366f1;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #4f46e5;
                }
            """)
            update_btn.clicked.connect(self.check_update)
            btn_layout.addWidget(update_btn)
        else:
            # Aktivasyon butonu
            activate_btn = QPushButton("Lisans Aktive Et")
            activate_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6366f1;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 30px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4f46e5;
                }
            """)
            activate_btn.clicked.connect(self.show_activation_dialog)
            btn_layout.addWidget(activate_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
    
    def show_activation_dialog(self):
        dialog = ActivationDialog(self)
        dialog.activated.connect(self.on_activated)
        dialog.exec()
    
    def on_activated(self, data: dict):
        # UI'ı yenile
        self.setup_ui()
        QMessageBox.information(
            self, "Başarılı",
            f"Lisans aktive edildi!\n\nHoş geldiniz: {data.get('name', 'Kullanıcı')}"
        )
    
    def remove_license(self):
        reply = QMessageBox.question(
            self, "Onay",
            "Lisansı kaldırmak istediğinize emin misiniz?\n\nBu işlem tüm yerel yapılandırmayı siler.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.client.config.customer_id = None
            self.client.config.api_key = None
            self.client._save_config()
            self.setup_ui()
    
    def check_update(self):
        from server_client import APP_VERSION
        success, message, data = self.client.check_update(APP_VERSION)
        
        if success and data and data.get('has_update'):
            dialog = UpdateDialog(data, self)
            dialog.exec()
        elif success:
            QMessageBox.information(
                self, "Güncel",
                "Uygulamanız güncel! 🎉"
            )
        else:
            QMessageBox.warning(
                self, "Hata",
                f"Güncelleme kontrolü: {message}"
            )


def check_activation_on_startup(parent=None) -> bool:
    """
    Uygulama başlangıcında aktivasyon kontrolü
    Returns: True eğer aktivasyon geçerliyse
    """
    client = ServerClient()
    
    if not client.is_configured():
        # Aktivasyon dialog'u göster
        dialog = ActivationDialog(parent)
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted
    
    return True


def check_update_on_startup(parent=None, current_version: str = "1.0.0"):
    """
    Uygulama başlangıcında güncelleme kontrolü
    """
    client = ServerClient()
    
    if not client.is_configured():
        return
    
    try:
        success, message, data = client.check_update(current_version)
        
        if success and data and data.get('has_update'):
            dialog = UpdateDialog(data, parent)
            dialog.exec()
    except Exception as e:
        print(f"Güncelleme kontrolü hatası: {e}")
