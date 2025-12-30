#!/usr/bin/env python3
"""
BADER - Minimal Test Uygulaması
"""
import sys
import os

# Matplotlib backend'ini önce ayarla
import matplotlib
matplotlib.use('Agg')  # GUI gerektirmeyen backend

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QPushButton, QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import Database


class TestWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("BADER - Test")
        self.resize(1000, 700)
        
        # Ana widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # Başlık
        title = QLabel("🏛️ BADER Dernek Yönetim Sistemi")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Bilgi
        info = QLabel("Uygulama başarıyla çalışıyor!")
        info.setFont(QFont("Arial", 14))
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        # Veritabanı durumu
        try:
            stats = f"Üye sayısı: {len(self.db.get_all_uyeler())}"
        except:
            stats = "Veritabanı bağlantısı..."
        
        db_label = QLabel(stats)
        db_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(db_label)


def main():
    app = QApplication(sys.argv)
    
    # Veritabanı
    db_path = os.path.expanduser("~/Documents/BADER/bader.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = Database(db_path)
    
    window = TestWindow(db)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
