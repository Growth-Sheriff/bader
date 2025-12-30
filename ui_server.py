"""
BADER - Server Aktivasyon ve Ayarlar Widget'ları
Desktop uygulaması için server bağlantı yönetimi.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QDialog,
                             QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from qfluentwidgets import (CardWidget, LineEdit, PushButton, PrimaryPushButton,
                            SwitchButton, MessageBox, TitleLabel, SubtitleLabel,
                            BodyLabel, CaptionLabel, InfoBar, InfoBarPosition,
                            ProgressRing, FluentIcon as FIF, IconWidget)
from server_client import get_server_client, ServerClient
from typing import Optional
import os


class BackgroundWorker(QThread):
    """Arka plan işlemleri için thread"""
    finished = pyqtSignal(bool, str, object)
    progress = pyqtSignal(int)
    
    def __init__(self, task_func, *args):
        super().__init__()
        self.task_func = task_func
        self.args = args
    
    def run(self):
        try:
            result = self.task_func(*self.args)
            if isinstance(result, tuple):
                if len(result) == 3:
                    self.finished.emit(result[0], result[1], result[2])
                else:
                    self.finished.emit(result[0], result[1], None)
            else:
                self.finished.emit(True, str(result), None)
        except Exception as e:
            self.finished.emit(False, str(e), None)


class ActivationDialog(QDialog):
    """Lisans aktivasyon dialogu"""
    
    activation_successful = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = get_server_client()
        self.worker = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("BADER - Aktivasyon")
        self.setFixedSize(450, 380)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Başlık
        title = TitleLabel("Ürün Aktivasyonu")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = BodyLabel("BADER'i aktifleştirmek için lisans anahtarınızı girin")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Lisans Anahtarı Kartı
        card = CardWidget()
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)
        
        # Server URL (opsiyonel)
        url_label = CaptionLabel("Server URL (Opsiyonel)")
        card_layout.addWidget(url_label)
        
        self.server_url_edit = LineEdit()
        self.server_url_edit.setPlaceholderText("http://157.90.154.48:8080/api")
        self.server_url_edit.setText(self.client.config.server_url)
        card_layout.addWidget(self.server_url_edit)
        
        # Lisans Anahtarı
        key_label = BodyLabel("Lisans Anahtarı")
        card_layout.addWidget(key_label)
        
        self.license_key_edit = LineEdit()
        self.license_key_edit.setPlaceholderText("BADER-XXXX-XXXX-XXXX")
        self.license_key_edit.returnPressed.connect(self.activate)
        card_layout.addWidget(self.license_key_edit)
        
        # Bağlantı durumu
        self.status_label = CaptionLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.status_label)
        
        card.setLayout(card_layout)
        layout.addWidget(card)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.test_btn = PushButton("Bağlantı Test")
        self.test_btn.setIcon(FIF.SYNC)
        self.test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(self.test_btn)
        
        self.activate_btn = PrimaryPushButton("Aktifleştir")
        self.activate_btn.clicked.connect(self.activate)
        btn_layout.addWidget(self.activate_btn)
        
        layout.addLayout(btn_layout)
        
        # Progress
        self.progress_ring = ProgressRing()
        self.progress_ring.setFixedSize(30, 30)
        self.progress_ring.hide()
        layout.addWidget(self.progress_ring, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # İlk açılışta bağlantı test et
        QTimer.singleShot(500, self.test_connection)
    
    def test_connection(self):
        """Bağlantı testi"""
        url = self.server_url_edit.text().strip()
        if url:
            self.client.set_server_url(url)
        
        self.status_label.setText("Bağlantı test ediliyor...")
        self.test_btn.setEnabled(False)
        self.progress_ring.show()
        
        self.worker = BackgroundWorker(self.client.test_connection)
        self.worker.finished.connect(self._on_test_complete)
        self.worker.start()
    
    def _on_test_complete(self, success, message, _):
        self.test_btn.setEnabled(True)
        self.progress_ring.hide()
        
        if success:
            self.status_label.setText("✅ " + message)
            self.status_label.setStyleSheet("color: #2ECC71;")
        else:
            self.status_label.setText("❌ " + message)
            self.status_label.setStyleSheet("color: #E74C3C;")
    
    def activate(self):
        """Lisans aktivasyonu"""
        license_key = self.license_key_edit.text().strip()
        
        if not license_key:
            MessageBox("Uyarı", "Lisans anahtarı boş bırakılamaz!", self).exec()
            return
        
        url = self.server_url_edit.text().strip()
        if url:
            self.client.set_server_url(url)
        
        self.activate_btn.setEnabled(False)
        self.progress_ring.show()
        self.status_label.setText("Aktifleştiriliyor...")
        
        self.worker = BackgroundWorker(self.client.activate_license, license_key)
        self.worker.finished.connect(self._on_activation_complete)
        self.worker.start()
    
    def _on_activation_complete(self, success, message, data):
        self.activate_btn.setEnabled(True)
        self.progress_ring.hide()
        
        if success:
            self.status_label.setText("✅ Aktivasyon başarılı!")
            self.status_label.setStyleSheet("color: #2ECC71;")
            self.activation_successful.emit(data or {})
            
            # 1 saniye sonra kapat
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setText("❌ " + message)
            self.status_label.setStyleSheet("color: #E74C3C;")
            MessageBox("Aktivasyon Hatası", message, self).exec()


class ServerSettingsWidget(QWidget):
    """Server ayarları widget'ı"""
    
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.client = get_server_client()
        self.worker = None
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        title = SubtitleLabel("Server Bağlantısı")
        layout.addWidget(title)
        
        # Bağlantı Durumu Kartı
        status_card = CardWidget()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(16, 16, 16, 16)
        
        self.status_icon = IconWidget(FIF.CANCEL)
        self.status_icon.setFixedSize(24, 24)
        status_layout.addWidget(self.status_icon)
        
        status_info = QVBoxLayout()
        self.status_title = BodyLabel("Bağlantı Durumu")
        self.status_detail = CaptionLabel("Yapılandırılmamış")
        status_info.addWidget(self.status_title)
        status_info.addWidget(self.status_detail)
        status_layout.addLayout(status_info)
        
        status_layout.addStretch()
        
        self.connect_btn = PrimaryPushButton("Bağlan")
        self.connect_btn.clicked.connect(self.show_activation)
        status_layout.addWidget(self.connect_btn)
        
        status_card.setLayout(status_layout)
        layout.addWidget(status_card)
        
        # Müşteri Bilgileri Kartı
        self.customer_card = CardWidget()
        customer_layout = QVBoxLayout()
        customer_layout.setContentsMargins(16, 16, 16, 16)
        customer_layout.setSpacing(8)
        
        customer_title = BodyLabel("Müşteri Bilgileri")
        customer_layout.addWidget(customer_title)
        
        self.customer_id_label = CaptionLabel("ID: -")
        customer_layout.addWidget(self.customer_id_label)
        
        self.last_backup_label = CaptionLabel("Son Yedek: -")
        customer_layout.addWidget(self.last_backup_label)
        
        self.last_update_label = CaptionLabel("Son Güncelleme Kontrolü: -")
        customer_layout.addWidget(self.last_update_label)
        
        self.customer_card.setLayout(customer_layout)
        self.customer_card.hide()
        layout.addWidget(self.customer_card)
        
        # Ayarlar Kartı
        settings_card = CardWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(16, 16, 16, 16)
        settings_layout.setSpacing(12)
        
        settings_title = BodyLabel("Ayarlar")
        settings_layout.addWidget(settings_title)
        
        # Otomatik Yedekleme
        backup_row = QHBoxLayout()
        backup_label = CaptionLabel("Otomatik Yedekleme")
        backup_row.addWidget(backup_label)
        backup_row.addStretch()
        self.auto_backup_switch = SwitchButton()
        self.auto_backup_switch.checkedChanged.connect(self.on_auto_backup_changed)
        backup_row.addWidget(self.auto_backup_switch)
        settings_layout.addLayout(backup_row)
        
        # Otomatik Güncelleme
        update_row = QHBoxLayout()
        update_label = CaptionLabel("Otomatik Güncelleme")
        update_row.addWidget(update_label)
        update_row.addStretch()
        self.auto_update_switch = SwitchButton()
        self.auto_update_switch.checkedChanged.connect(self.on_auto_update_changed)
        update_row.addWidget(self.auto_update_switch)
        settings_layout.addLayout(update_row)
        
        settings_card.setLayout(settings_layout)
        layout.addWidget(settings_card)
        
        # İşlemler Kartı
        actions_card = CardWidget()
        actions_layout = QVBoxLayout()
        actions_layout.setContentsMargins(16, 16, 16, 16)
        actions_layout.setSpacing(12)
        
        actions_title = BodyLabel("İşlemler")
        actions_layout.addWidget(actions_title)
        
        btn_row1 = QHBoxLayout()
        
        self.backup_now_btn = PushButton("Şimdi Yedekle")
        self.backup_now_btn.setIcon(FIF.SAVE)
        self.backup_now_btn.clicked.connect(self.backup_now)
        btn_row1.addWidget(self.backup_now_btn)
        
        self.check_update_btn = PushButton("Güncelleme Kontrol")
        self.check_update_btn.setIcon(FIF.UPDATE)
        self.check_update_btn.clicked.connect(self.check_update)
        btn_row1.addWidget(self.check_update_btn)
        
        actions_layout.addLayout(btn_row1)
        
        btn_row2 = QHBoxLayout()
        
        self.restore_btn = PushButton("Yedekten Geri Yükle")
        self.restore_btn.setIcon(FIF.HISTORY)
        self.restore_btn.clicked.connect(self.restore_backup)
        btn_row2.addWidget(self.restore_btn)
        
        self.disconnect_btn = PushButton("Bağlantıyı Kes")
        self.disconnect_btn.setIcon(FIF.POWER_BUTTON)
        self.disconnect_btn.clicked.connect(self.disconnect)
        btn_row2.addWidget(self.disconnect_btn)
        
        actions_layout.addLayout(btn_row2)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        actions_layout.addWidget(self.progress_bar)
        
        self.action_status = CaptionLabel("")
        self.action_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_layout.addWidget(self.action_status)
        
        actions_card.setLayout(actions_layout)
        layout.addWidget(actions_card)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_settings(self):
        """Ayarları yükle"""
        info = self.client.get_customer_info()
        
        if info['is_configured']:
            self.status_icon.setIcon(FIF.ACCEPT)
            self.status_title.setText("Bağlı")
            self.status_detail.setText(f"Server: {info['server_url']}")
            self.connect_btn.setText("Yeniden Bağlan")
            
            self.customer_card.show()
            self.customer_id_label.setText(f"ID: {info['customer_id']}")
            
            if info['last_backup']:
                self.last_backup_label.setText(f"Son Yedek: {info['last_backup'][:19]}")
            
            if info['last_update_check']:
                self.last_update_label.setText(f"Son Kontrol: {info['last_update_check'][:19]}")
            
            self.auto_backup_switch.setChecked(info['auto_backup'])
            self.auto_update_switch.setChecked(info['auto_update'])
            
            # Butonları aktif et
            self.backup_now_btn.setEnabled(True)
            self.check_update_btn.setEnabled(True)
            self.restore_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
        else:
            self.status_icon.setIcon(FIF.CANCEL)
            self.status_title.setText("Bağlı Değil")
            self.status_detail.setText("Aktivasyon gerekli")
            self.connect_btn.setText("Bağlan")
            
            self.customer_card.hide()
            
            # Butonları pasif et
            self.backup_now_btn.setEnabled(False)
            self.check_update_btn.setEnabled(False)
            self.restore_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
    
    def show_activation(self):
        """Aktivasyon dialogunu göster"""
        dialog = ActivationDialog(self)
        dialog.activation_successful.connect(self._on_activation_success)
        dialog.exec()
    
    def _on_activation_success(self, data):
        """Aktivasyon başarılı"""
        self.load_settings()
        InfoBar.success(
            title="Başarılı",
            content="Server'a bağlandı!",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000
        )
    
    def on_auto_backup_changed(self, checked):
        """Otomatik yedekleme değişti"""
        self.client.set_auto_backup(checked)
    
    def on_auto_update_changed(self, checked):
        """Otomatik güncelleme değişti"""
        self.client.set_auto_update(checked)
    
    def backup_now(self):
        """Şimdi yedekle"""
        if not self.db:
            MessageBox("Hata", "Veritabanı bağlantısı yok!", self).exec()
            return
        
        db_path = self.db.db_path if hasattr(self.db, 'db_path') else "bader.db"
        
        self.backup_now_btn.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.action_status.setText("Yedekleniyor...")
        
        self.worker = BackgroundWorker(self.client.upload_backup, db_path)
        self.worker.finished.connect(self._on_backup_complete)
        self.worker.start()
    
    def _on_backup_complete(self, success, message, _):
        self.backup_now_btn.setEnabled(True)
        self.progress_bar.hide()
        
        if success:
            self.action_status.setText("✅ " + message)
            self.load_settings()  # Son yedek tarihini güncelle
            InfoBar.success(
                title="Başarılı",
                content=message,
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
        else:
            self.action_status.setText("❌ " + message)
            InfoBar.error(
                title="Hata",
                content=message,
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000
            )
    
    def check_update(self):
        """Güncelleme kontrol"""
        from main_fluent_full import APP_VERSION  # Versiyon
        current_version = getattr(self, 'app_version', '1.0.0')
        
        self.check_update_btn.setEnabled(False)
        self.action_status.setText("Güncelleme kontrol ediliyor...")
        
        self.worker = BackgroundWorker(self.client.check_update, current_version)
        self.worker.finished.connect(self._on_update_check_complete)
        self.worker.start()
    
    def _on_update_check_complete(self, has_update, message, data):
        self.check_update_btn.setEnabled(True)
        self.load_settings()  # Son kontrol tarihini güncelle
        
        if has_update and data:
            self.action_status.setText(f"🆕 Yeni sürüm: {data.get('latest_version')}")
            w = MessageBox(
                "Güncelleme Mevcut",
                f"Yeni sürüm: {data.get('latest_version')}\n\n"
                f"Değişiklikler:\n{data.get('changelog', 'Bilgi yok')}\n\n"
                "Şimdi indirmek ister misiniz?",
                self
            )
            if w.exec():
                # Güncelleme indir
                self._download_update(data)
        else:
            self.action_status.setText("✅ " + message)
            InfoBar.info(
                title="Güncel",
                content=message,
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def _download_update(self, data):
        """Güncelleme indir"""
        download_url = data.get('download_url')
        if not download_url:
            MessageBox("Hata", "İndirme linki bulunamadı!", self).exec()
            return
        
        # Kaydetme konumu seç
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Güncellemeyi Kaydet", 
            f"BADER_{data.get('latest_version')}.zip",
            "ZIP Files (*.zip)"
        )
        
        if not save_path:
            return
        
        self.progress_bar.show()
        self.progress_bar.setRange(0, 100)
        self.action_status.setText("İndiriliyor...")
        
        self.worker = BackgroundWorker(
            self.client.download_update, 
            download_url, 
            save_path
        )
        self.worker.progress.connect(lambda p: self.progress_bar.setValue(p))
        self.worker.finished.connect(self._on_download_complete)
        self.worker.start()
    
    def _on_download_complete(self, success, message, _):
        self.progress_bar.hide()
        
        if success:
            self.action_status.setText("✅ Güncelleme indirildi!")
            InfoBar.success(
                title="İndirildi",
                content="Güncelleme dosyası indirildi. Kurulum için çift tıklayın.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000
            )
        else:
            self.action_status.setText("❌ " + message)
    
    def restore_backup(self):
        """Yedekten geri yükle"""
        # Yedek geçmişini al
        self.action_status.setText("Yedekler alınıyor...")
        
        self.worker = BackgroundWorker(self.client.get_backup_history)
        self.worker.finished.connect(self._on_backup_history)
        self.worker.start()
    
    def _on_backup_history(self, success, message, backups):
        if not success or not backups:
            self.action_status.setText("")
            MessageBox("Bilgi", "Henüz yedek bulunmuyor.", self).exec()
            return
        
        # Basit seçim için son yedeği göster
        last_backup = backups[0] if backups else None
        if last_backup:
            w = MessageBox(
                "Yedekten Geri Yükle",
                f"Son yedek: {last_backup.get('created_at', 'Tarih yok')}\n\n"
                "Bu yedeği geri yüklemek istiyor musunuz?\n"
                "⚠️ Mevcut verileriniz silinecek!",
                self
            )
            if w.exec():
                # Kaydetme konumu seç
                save_path, _ = QFileDialog.getSaveFileName(
                    self, "Yedeği Kaydet", "bader_backup.db",
                    "SQLite Database (*.db)"
                )
                if save_path:
                    self._do_restore(last_backup.get('id'), save_path)
        
        self.action_status.setText("")
    
    def _do_restore(self, backup_id, target_path):
        """Yedeği indir"""
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        self.action_status.setText("Yedek indiriliyor...")
        
        self.worker = BackgroundWorker(
            self.client.restore_backup, backup_id, target_path
        )
        self.worker.finished.connect(self._on_restore_complete)
        self.worker.start()
    
    def _on_restore_complete(self, success, message, _):
        self.progress_bar.hide()
        
        if success:
            self.action_status.setText("✅ Yedek indirildi!")
            MessageBox(
                "Başarılı",
                "Yedek dosyası indirildi.\n"
                "Geri yüklemek için uygulamayı kapatın ve "
                "indirilen dosyayı mevcut veritabanı ile değiştirin.",
                self
            ).exec()
        else:
            self.action_status.setText("❌ " + message)
    
    def disconnect(self):
        """Bağlantıyı kes"""
        w = MessageBox(
            "Bağlantıyı Kes",
            "Server bağlantısını kesmek istediğinize emin misiniz?\n"
            "Tekrar bağlanmak için aktivasyon gerekecek.",
            self
        )
        if w.exec():
            self.client.clear_credentials()
            self.load_settings()
            InfoBar.info(
                title="Bağlantı Kesildi",
                content="Server bağlantısı kesildi.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
