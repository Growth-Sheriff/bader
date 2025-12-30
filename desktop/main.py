#!/usr/bin/env python3
"""
BADER Derneği - Aidat & Kasa Yönetim Sistemi
Ana Program - Minimal & Clean Design
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from main_window import MainWindow


def get_resource_path(relative_path):
    """PyInstaller için doğru dosya yolunu al"""
    try:
        # PyInstaller bundle içinde
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal Python ortamında
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def main():
    """Ana fonksiyon"""
    # High DPI desteği
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Uygulama oluştur
    app = QApplication(sys.argv)
    
    # Uygulama bilgileri
    app.setApplicationName("BADER Derneği")
    app.setOrganizationName("BADER")
    app.setApplicationVersion("1.0.0")
    
    # Modern, temiz font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    
    # Temiz, minimal color palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#FAFAFA"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#212121"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F5F5F5"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#212121"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#212121"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1976D2"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow()
    window.showMaximized()
    
    # Uygulama döngüsü
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

