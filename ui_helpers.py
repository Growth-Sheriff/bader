"""
BADER Derneği - UI Helper Fonksiyonları
Ortak kullanılan UI yardımcı fonksiyonları
"""

from PyQt5.QtWidgets import QComboBox, QCompleter
from PyQt5.QtCore import Qt


def make_searchable_combobox(combobox: QComboBox):
    """
    ComboBox'ı aranabilir hale getirir
    
    Args:
        combobox: Aranabilir yapılacak QComboBox
    """
    # Düzenlenebilir yap
    combobox.setEditable(True)
    
    # Insert policy: kullanıcı yazarsa eklenmesin
    combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    
    # Completer ekle
    completer = QCompleter(combobox.model())
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    
    combobox.setCompleter(completer)
    
    # Stil düzeltmeleri
    combobox.lineEdit().setPlaceholderText("Arama veya seçim yapın...")
    
    return combobox


def create_searchable_combobox(items: list = None) -> QComboBox:
    """
    Yeni aranabilir ComboBox oluşturur
    
    Args:
        items: ComboBox'a eklenecek öğeler listesi
        
    Returns:
        Aranabilir QComboBox
    """
    combobox = QComboBox()
    
    if items:
        combobox.addItems(items)
    
    return make_searchable_combobox(combobox)


def add_separator_to_layout(layout, height: int = 1):
    """Layout'a ayırıcı çizgi ekler"""
    from PyQt5.QtWidgets import QFrame
    
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setMaximumHeight(height)
    line.setStyleSheet("background-color: #E0E0E0;")
    
    layout.addWidget(line)
    
    return line


def format_currency(amount: float, currency: str = "₺") -> str:
    """
    Para birimini formatlar
    
    Args:
        amount: Tutar
        currency: Para birimi sembolü
        
    Returns:
        Formatlanmış string
    """
    return f"{amount:,.2f} {currency}".replace(",", ".")


def format_date(date_str: str) -> str:
    """
    Tarih formatını düzenler
    
    Args:
        date_str: ISO format tarih (YYYY-MM-DD)
        
    Returns:
        Formatlanmış tarih (DD.MM.YYYY)
    """
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except:
        return date_str


def export_table_to_excel(table, default_filename: str, parent_widget=None):
    """
    QTableWidget içeriğini Excel dosyasına export eder
    
    Args:
        table: QTableWidget nesnesi
        default_filename: Varsayılan dosya adı (uzantısız)
        parent_widget: Dialog için parent widget
        
    Returns:
        bool: Başarılı ise True
    """
    import csv
    from PyQt5.QtWidgets import QFileDialog, QMessageBox
    from datetime import datetime
    
    # Dosya kaydet dialogu
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suggested_name = f"{default_filename}_{timestamp}.csv"
    
    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Excel'e Aktar",
        suggested_name,
        "CSV Dosyası (*.csv);;Tüm Dosyalar (*)"
    )
    
    if not file_path:
        return False
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Başlık satırı
            headers = []
            for col in range(table.columnCount()):
                header = table.horizontalHeaderItem(col)
                headers.append(header.text() if header else f"Sütun {col+1}")
            writer.writerow(headers)
            
            # Veri satırları
            for row in range(table.rowCount()):
                if table.isRowHidden(row):
                    continue
                    
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)
        
        MessageBox("Başarılı", f"Veriler başarıyla export edildi:\n{file_path}", parent_widget).show()
        return True
        
    except Exception as e:
        MessageBox("Hata", f"Export sırasında hata oluştu:\n{str(e)}", parent_widget).show()
        return False
