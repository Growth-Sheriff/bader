#!/usr/bin/env python3
"""
BADER - Minimal Fluent Test
"""
import sys
import os

# Matplotlib backend'ini en başta ayarla
import matplotlib
matplotlib.use('Agg')  # Güvenli backend

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon as FIF
from qfluentwidgets import TitleLabel, BodyLabel, CardWidget, PushButton

from database import Database


class SimpleWidget(CardWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        from PyQt5.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(self)
        layout.addWidget(TitleLabel(title))
        layout.addWidget(BodyLabel("Widget yüklendi"))


class MinimalFluentWindow(FluentWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("BADER - Dernek Yönetim Sistemi")
        self.resize(1200, 800)
        
        # Dashboard
        self.dashboard = SimpleWidget("📊 Dashboard", self)
        self.dashboard.setObjectName("dashboard")
        self.addSubInterface(self.dashboard, FIF.HOME, "Dashboard")
        
        # Üyeler  
        self.uyeler = SimpleWidget("👥 Üyeler", self)
        self.uyeler.setObjectName("uyeler")
        self.addSubInterface(self.uyeler, FIF.PEOPLE, "Üyeler")
        
        # Gelir
        self.gelir = SimpleWidget("💰 Gelir", self)
        self.gelir.setObjectName("gelir")
        self.addSubInterface(self.gelir, FIF.UP, "Gelir")
        
        # Gider
        self.gider = SimpleWidget("💸 Gider", self)
        self.gider.setObjectName("gider")
        self.addSubInterface(self.gider, FIF.DOWN, "Gider")
        
        # Ayarlar
        self.ayarlar = SimpleWidget("⚙️ Ayarlar", self)
        self.ayarlar.setObjectName("ayarlar")
        self.addSubInterface(self.ayarlar, FIF.SETTING, "Ayarlar", NavigationItemPosition.BOTTOM)


def main():
    app = QApplication(sys.argv)
    
    # Veritabanı
    db_path = os.path.expanduser("~/Documents/BADER/bader.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = Database(db_path)
    
    window = MinimalFluentWindow(db)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
