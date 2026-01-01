"""
BADER Derneği - Kasa Yönetimi UI
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QDialog, QFormLayout,
                             QDoubleSpinBox, QHeaderView, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from qfluentwidgets import MessageBox
from database import Database
from models import KasaYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import create_line_edit, create_combo_box, create_text_edit, create_double_spin_box
from ui_helpers import export_table_to_excel, setup_resizable_table
from ui_login import session


class KasaFormWidget(QWidget):
    """Kasa ekleme/düzenleme formu"""
    
    def __init__(self, kasa_data: dict = None):
        super().__init__()
        self.kasa_data = kasa_data
        self.setup_ui()
        
        if kasa_data:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Kasa Adı
        self.kasa_adi_edit = create_line_edit("Kasa Adı *", "Örn: BANKA TL, Sayman Kasası vb.")
        layout.addWidget(self.kasa_adi_edit[0])
        
        # Para Birimi
        self.para_birimi_combo = create_combo_box("Para Birimi *")
        self.para_birimi_combo[1].addItems(["TL", "USD", "EUR"])
        layout.addWidget(self.para_birimi_combo[0])
        
        # Devir Bakiye
        self.devir_spin = create_double_spin_box("Devir Bakiye")
        self.devir_spin[1].setMinimum(-10000000)
        self.devir_spin[1].setMaximum(10000000)
        layout.addWidget(self.devir_spin[0])
        
        # Açıklama
        self.aciklama_edit = create_text_edit("Açıklama", "Kasa açıklaması...")
        layout.addWidget(self.aciklama_edit[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_data(self):
        if self.kasa_data:
            self.kasa_adi_edit[1].setText(self.kasa_data['kasa_adi'])
            self.para_birimi_combo[1].setCurrentText(self.kasa_data['para_birimi'])
            self.devir_spin[1].setValue(self.kasa_data['devir_bakiye'])
            self.aciklama_edit[1].setPlainText(self.kasa_data.get('aciklama', ''))
            
    def get_data(self):
        return {
            'kasa_adi': self.kasa_adi_edit[1].text().strip(),
            'para_birimi': self.para_birimi_combo[1].currentText(),
            'devir_bakiye': self.devir_spin[1].value(),
            'aciklama': self.aciklama_edit[1].toPlainText().strip()
        }


class KasaDetayWidget(QWidget):
    """Kasa işlem geçmişi detay widget'ı"""
    
    def __init__(self, db: Database, kasa_id: int, kasa_adi: str, para_birimi: str):
        super().__init__()
        self.db = db
        self.kasa_id = kasa_id
        self.kasa_adi = kasa_adi
        self.para_birimi = para_birimi
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        self.load_islemler()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Özet bilgiler
        ozet = self.kasa_yoneticisi.tum_kasalar_ozet()
        kasa_ozet = next((k for k in ozet if k['kasa_id'] == self.kasa_id), None)
        
        if kasa_ozet:
            ozet_group = QGroupBox("📊 Kasa Özeti")
            ozet_layout = QVBoxLayout()
            
            devir_label = QLabel(f"Devir Bakiye: {kasa_ozet['devir_bakiye']:,.2f} {self.para_birimi}")
            ozet_layout.addWidget(devir_label)
            
            gelir_label = QLabel(f"Toplam Gelir: +{kasa_ozet['toplam_gelir']:,.2f} {self.para_birimi}")
            gelir_label.setStyleSheet("color: #2E7D32;")
            ozet_layout.addWidget(gelir_label)
            
            gider_label = QLabel(f"Toplam Gider: -{kasa_ozet['toplam_gider']:,.2f} {self.para_birimi}")
            gider_label.setStyleSheet("color: #C62828;")
            ozet_layout.addWidget(gider_label)
            
            virman_net = kasa_ozet['virman_gelen'] - kasa_ozet['virman_giden']
            virman_label = QLabel(f"Virman Net: {virman_net:+,.2f} {self.para_birimi}")
            virman_label.setStyleSheet("color: #1565C0;")
            ozet_layout.addWidget(virman_label)
            
            bakiye_label = QLabel(f"Net Bakiye: {kasa_ozet['net_bakiye']:,.2f} {self.para_birimi}")
            bakiye_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            ozet_layout.addWidget(bakiye_label)
            
            ozet_group.setLayout(ozet_layout)
            layout.addWidget(ozet_group)
        
        # İşlem listesi
        islem_label = QLabel("📋 Son İşlemler")
        islem_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(islem_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Tarih", "Tür", "Açıklama", "Tutar", "Yön"])
        setup_resizable_table(self.table, table_id="kasa_detay_tablosu", stretch_column=2)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(300)
        layout.addWidget(self.table)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_islemler(self):
        """Kasanın tüm işlemlerini yükle"""
        self.table.setRowCount(0)
        
        # Gelirler
        self.db.cursor.execute("""
            SELECT tarih, 'GELİR' as tip, gelir_turu as tur, aciklama, tutar
            FROM gelirler WHERE kasa_id = ?
        """, (self.kasa_id,))
        gelirler = self.db.cursor.fetchall()
        
        # Giderler
        self.db.cursor.execute("""
            SELECT tarih, 'GİDER' as tip, gider_turu as tur, aciklama, tutar
            FROM giderler WHERE kasa_id = ?
        """, (self.kasa_id,))
        giderler = self.db.cursor.fetchall()
        
        # Virmanlar (gelen)
        self.db.cursor.execute("""
            SELECT tarih, 'VİRMAN GELEN' as tip, 'Transfer' as tur, aciklama, tutar
            FROM virmanlar WHERE alan_kasa_id = ?
        """, (self.kasa_id,))
        virman_gelen = self.db.cursor.fetchall()
        
        # Virmanlar (giden)
        self.db.cursor.execute("""
            SELECT tarih, 'VİRMAN GİDEN' as tip, 'Transfer' as tur, aciklama, tutar
            FROM virmanlar WHERE gonderen_kasa_id = ?
        """, (self.kasa_id,))
        virman_giden = self.db.cursor.fetchall()
        
        # Tüm işlemleri birleştir ve tarihe göre sırala
        tum_islemler = []
        for g in gelirler:
            tum_islemler.append({'tarih': g['tarih'], 'tip': 'GELİR', 'tur': g['tur'], 
                                'aciklama': g['aciklama'], 'tutar': g['tutar'], 'yon': '+'})
        for g in giderler:
            tum_islemler.append({'tarih': g['tarih'], 'tip': 'GİDER', 'tur': g['tur'], 
                                'aciklama': g['aciklama'], 'tutar': g['tutar'], 'yon': '-'})
        for v in virman_gelen:
            tum_islemler.append({'tarih': v['tarih'], 'tip': 'VİRMAN', 'tur': 'Gelen', 
                                'aciklama': v['aciklama'] or 'Transfer', 'tutar': v['tutar'], 'yon': '+'})
        for v in virman_giden:
            tum_islemler.append({'tarih': v['tarih'], 'tip': 'VİRMAN', 'tur': 'Giden', 
                                'aciklama': v['aciklama'] or 'Transfer', 'tutar': v['tutar'], 'yon': '-'})
        
        # Tarihe göre sırala (en yeni en üstte)
        tum_islemler.sort(key=lambda x: x['tarih'], reverse=True)
        
        for islem in tum_islemler:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(islem['tarih']))
            self.table.setItem(row, 1, QTableWidgetItem(f"{islem['tip']} - {islem['tur']}"))
            self.table.setItem(row, 2, QTableWidgetItem(islem['aciklama'] or ''))
            
            tutar_item = QTableWidgetItem(f"{islem['tutar']:,.2f}")
            if islem['yon'] == '+':
                tutar_item.setForeground(QColor("#2E7D32"))
            else:
                tutar_item.setForeground(QColor("#C62828"))
            self.table.setItem(row, 3, tutar_item)
            
            yon_item = QTableWidgetItem(islem['yon'])
            if islem['yon'] == '+':
                yon_item.setForeground(QColor("#2E7D32"))
            else:
                yon_item.setForeground(QColor("#C62828"))
            self.table.setItem(row, 4, yon_item)


class KasaWidget(QWidget):
    """Kasa yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        self.load_kasalar()
        self.apply_permissions()
    
    def apply_permissions(self):
        """Kullanıcı izinlerine göre butonları ayarla"""
        self.ekle_btn.setVisible(session.has_permission('kasa_islem'))
        self.duzenle_btn.setVisible(session.has_permission('kasa_islem'))
        self.sil_btn.setVisible(session.has_permission('kasa_islem'))
        self.export_btn.setVisible(session.has_permission('rapor_export'))
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("KASA YÖNETİMİ")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        subtitle = QLabel("Tüm kasaların bakiye ve hareket özeti")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()
        
        self.yenile_btn = QPushButton("🔄 Yenile")
        self.yenile_btn.clicked.connect(self.load_kasalar)
        toolbar_layout.addWidget(self.yenile_btn)
        
        self.ekle_btn = QPushButton("➕ Yeni Kasa")
        self.ekle_btn.clicked.connect(self.kasa_ekle)
        toolbar_layout.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.kasa_duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar_layout.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.clicked.connect(self.kasa_sil)
        self.sil_btn.setEnabled(False)
        toolbar_layout.addWidget(self.sil_btn)
        
        self.detay_btn = QPushButton("👁️ Kasa Detay")
        self.detay_btn.setToolTip("Seçili kasanın işlem geçmişini göster")
        self.detay_btn.clicked.connect(self.kasa_detay_goster)
        self.detay_btn.setEnabled(False)
        toolbar_layout.addWidget(self.detay_btn)
        
        self.tahakkuk_btn = QPushButton("📊 Tahakkuk Detayı")
        self.tahakkuk_btn.setToolTip("Seçili kasanın tahakkuk detayını göster")
        self.tahakkuk_btn.clicked.connect(self.tahakkuk_detay_goster)
        self.tahakkuk_btn.setEnabled(False)
        toolbar_layout.addWidget(self.tahakkuk_btn)
        
        # Excel export
        self.export_btn = QPushButton("📄 Excel")
        self.export_btn.setToolTip("Listeyi Excel'e Aktar")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "kasalar", self))
        toolbar_layout.addWidget(self.export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Kasa Özet Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kasa Adı", "Para Birimi", "Devir", 
            "Toplam Gelir", "Toplam Gider", "Virman Net", "Fiziksel Bakiye", "Tahakkuk", "Serbest Bakiye"
        ])
        
        # Responsive sütunlar - hareket ettirilebilir, sağ tık ile gizle/göster
        setup_resizable_table(self.table, table_id="kasalar_tablosu", stretch_column=1)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Inline editing KAPALI
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.kasa_duzenle)  # Çift tıkla → Drawer aç
        
        layout.addWidget(self.table)
        
        # Genel Toplam
        toplam_group = QGroupBox("GENEL TOPLAM")
        toplam_layout = QVBoxLayout()
        
        self.toplam_tl_label = QLabel("TL Kasalar Toplamı: 0.00 ₺")
        self.toplam_tl_label.setProperty("class", "success")
        toplam_layout.addWidget(self.toplam_tl_label)
        
        self.toplam_usd_label = QLabel("USD Kasalar Toplamı: 0.00 $")
        toplam_layout.addWidget(self.toplam_usd_label)
        
        self.toplam_eur_label = QLabel("EUR Kasalar Toplamı: 0.00 €")
        toplam_layout.addWidget(self.toplam_eur_label)
        
        toplam_group.setLayout(toplam_layout)
        layout.addWidget(toplam_group)
        
        self.setLayout(layout)
        
    def load_kasalar(self):
        """Kasaları ve bakiyelerini yükle"""
        ozet = self.kasa_yoneticisi.tum_kasalar_ozet()
        
        self.table.setRowCount(0)
        
        toplam_tl = 0.0
        toplam_usd = 0.0
        toplam_eur = 0.0
        
        for kasa in ozet:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(kasa['kasa_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(kasa['kasa_adi']))
            self.table.setItem(row, 2, QTableWidgetItem(kasa['para_birimi']))
            self.table.setItem(row, 3, QTableWidgetItem(f"{kasa['devir_bakiye']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{kasa['toplam_gelir']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{kasa['toplam_gider']:.2f}"))
            
            virman_net = kasa['virman_gelen'] - kasa['virman_giden']
            virman_item = QTableWidgetItem(f"{virman_net:.2f}")
            if virman_net > 0:
                virman_item.setForeground(Qt.GlobalColor.darkGreen)
            elif virman_net < 0:
                virman_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, 6, virman_item)
            
            # Fiziksel Bakiye (eskiden Net Bakiye)
            bakiye_item = QTableWidgetItem(f"{kasa['net_bakiye']:.2f}")
            if kasa['net_bakiye'] < 0:
                bakiye_item.setForeground(Qt.GlobalColor.darkRed)
                bakiye_item.setBackground(QColor(255, 230, 230))
            else:
                bakiye_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 7, bakiye_item)
            
            # Tahakkuk ve Serbest Bakiye hesapla
            try:
                tahakkuk_detay = self.kasa_yoneticisi.kasa_tahakkuk_detay(kasa['kasa_id'])
                tahakkuk_tutari = tahakkuk_detay.get('tahakkuk_toplami', 0)
                serbest_bakiye = tahakkuk_detay.get('serbest_bakiye', kasa['net_bakiye'])
            except:
                tahakkuk_tutari = 0
                serbest_bakiye = kasa['net_bakiye']
            
            # Tahakkuk kolonu
            tahakkuk_item = QTableWidgetItem(f"{tahakkuk_tutari:.2f}")
            if tahakkuk_tutari > 0:
                tahakkuk_item.setForeground(QColor("#FF9800"))
            self.table.setItem(row, 8, tahakkuk_item)
            
            # Serbest Bakiye kolonu
            serbest_item = QTableWidgetItem(f"{serbest_bakiye:.2f}")
            if serbest_bakiye < 0:
                serbest_item.setForeground(Qt.GlobalColor.darkRed)
                serbest_item.setBackground(QColor(255, 230, 230))
            else:
                serbest_item.setForeground(QColor("#2196F3"))
            self.table.setItem(row, 9, serbest_item)
            
            # Para birimi toplamları
            if kasa['para_birimi'] == 'TL':
                toplam_tl += kasa['net_bakiye']
            elif kasa['para_birimi'] == 'USD':
                toplam_usd += kasa['net_bakiye']
            elif kasa['para_birimi'] == 'EUR':
                toplam_eur += kasa['net_bakiye']
        
        # Toplam etiketlerini güncelle
        self.toplam_tl_label.setText(f"TL Kasalar Toplamı: {toplam_tl:,.2f} ₺")
        self.toplam_usd_label.setText(f"USD Kasalar Toplamı: {toplam_usd:,.2f} $")
        self.toplam_eur_label.setText(f"EUR Kasalar Toplamı: {toplam_eur:,.2f} €")
        
    def on_selection_changed(self):
        has_selection = self.table.selectionModel().hasSelection()
        self.duzenle_btn.setEnabled(has_selection)
        self.sil_btn.setEnabled(has_selection)
        self.detay_btn.setEnabled(has_selection)
        self.tahakkuk_btn.setEnabled(has_selection)
    
    def kasa_ekle(self):
        """Yeni kasa ekle"""
        form_widget = KasaFormWidget()
        drawer = DrawerPanel(self, "Yeni Kasa Ekle", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            if not data['kasa_adi']:
                MessageBox("Uyarı", "Kasa adı boş bırakılamaz!", self).show()
                return
                
            try:
                self.kasa_yoneticisi.kasa_ekle(**data)
                self.load_kasalar()
                MessageBox("Başarılı", "Kasa eklendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Kasa eklenirken hata:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
                
    def kasa_duzenle(self):
        """Kasa düzenle"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        kasa_id = int(self.table.item(row, 0).text())
        
        # Kasa bilgilerini al
        self.db.cursor.execute("SELECT * FROM kasalar WHERE kasa_id = ?", (kasa_id,))
        kasa_data = dict(self.db.cursor.fetchone())
        
        form_widget = KasaFormWidget(kasa_data)
        drawer = DrawerPanel(self, "Kasa Düzenle", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            if not data['kasa_adi']:
                MessageBox("Uyarı", "Kasa adı boş bırakılamaz!", self).show()
                return
                
            try:
                self.kasa_yoneticisi.kasa_guncelle(kasa_id, **data)
                self.load_kasalar()
                MessageBox("Başarılı", "Kasa güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Güncelleme hatası:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def kasa_sil(self):
        """Kasa sil"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        kasa_id = int(self.table.item(row, 0).text())
        kasa_adi = self.table.item(row, 1).text()
        bakiye = float(self.table.item(row, 7).text())
        
        # Bakiye kontrolü
        if bakiye != 0:
            MessageBox(
                "Uyarı", 
                f"'{kasa_adi}' kasasının bakiyesi sıfır değil ({bakiye:,.2f}).\n\n"
                "Bakiyesi olan kasa silinemez. Önce bakiyeyi sıfırlayın.", 
                self
            ).show()
            return
        
        # İşlem kontrolü
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM gelirler WHERE kasa_id = ?
            UNION ALL
            SELECT COUNT(*) FROM giderler WHERE kasa_id = ?
            UNION ALL
            SELECT COUNT(*) FROM virmanlar WHERE gonderen_kasa_id = ? OR alan_kasa_id = ?
        """, (kasa_id, kasa_id, kasa_id, kasa_id))
        
        islem_sayisi = sum(row[0] for row in self.db.cursor.fetchall())
        
        if islem_sayisi > 0:
            w = MessageBox(
                "Dikkat!", 
                f"'{kasa_adi}' kasasına bağlı {islem_sayisi} işlem bulunuyor.\n\n"
                "Bu kasayı silmek yerine pasif yapmak ister misiniz?",
                self
            )
            if w.exec():
                try:
                    self.db.cursor.execute("UPDATE kasalar SET aktif = 0 WHERE kasa_id = ?", (kasa_id,))
                    self.db.commit()
                    self.load_kasalar()
                    MessageBox("Başarılı", "Kasa pasif yapıldı!", self).show()
                except Exception as e:
                    MessageBox("Hata", f"İşlem hatası:\n{e}", self).show()
            return
        
        # Silme onayı
        w = MessageBox("Kasa Sil", f"'{kasa_adi}' kasasını silmek istediğinize emin misiniz?", self)
        if w.exec():
            try:
                self.db.cursor.execute("DELETE FROM kasalar WHERE kasa_id = ?", (kasa_id,))
                self.db.commit()
                self.load_kasalar()
                MessageBox("Başarılı", "Kasa silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Silme hatası:\n{e}", self).show()
    
    def kasa_detay_goster(self):
        """Seçili kasanın işlem geçmişini göster"""
        if not self.table.selectionModel().hasSelection():
            return
        
        row = self.table.currentRow()
        kasa_id = int(self.table.item(row, 0).text())
        kasa_adi = self.table.item(row, 1).text()
        para_birimi = self.table.item(row, 2).text()
        
        form = KasaDetayWidget(self.db, kasa_id, kasa_adi, para_birimi)
        drawer = DrawerPanel(self, f"💰 {kasa_adi} - İşlem Geçmişi", form, width=700)
        drawer.show()
    
    def tahakkuk_detay_goster(self):
        """Seçili kasanın tahakkuk detayını göster"""
        if not self.table.selectionModel().hasSelection():
            return
        
        row = self.table.currentRow()
        kasa_id = int(self.table.item(row, 0).text())
        kasa_adi = self.table.item(row, 1).text()
        
        from ui_coklu_yil_odeme import KasaTahakkukFormWidget
        
        form = KasaTahakkukFormWidget(self.db, kasa_id)
        drawer = DrawerPanel(self, f"📊 {kasa_adi} - Tahakkuk Detayı", form, width=600)
        drawer.show()
