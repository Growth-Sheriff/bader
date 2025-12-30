"""
BADER Derneği - PDF Oluşturma Modülü
Tahsilat makbuzu, rapor çıktıları
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from database import Database


class PDFStyle:
    """PDF stil sabitleri"""
    FONT_TITLE = ('Helvetica-Bold', 16)
    FONT_HEADER = ('Helvetica-Bold', 12)
    FONT_NORMAL = ('Helvetica', 10)
    FONT_SMALL = ('Helvetica', 8)
    
    COLOR_PRIMARY = (0.39, 0.71, 0.96)  # #64B5F6
    COLOR_BLACK = (0, 0, 0)
    COLOR_GRAY = (0.4, 0.4, 0.4)
    COLOR_LIGHT_GRAY = (0.9, 0.9, 0.9)


def sayi_yaziya(sayi: float) -> str:
    """Sayıyı yazıya çevir (Türkçe)"""
    birler = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
    onlar = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
    
    if sayi == 0:
        return "sıfır"
    
    tam = int(sayi)
    kusur = int(round((sayi - tam) * 100))
    
    def yuz_basamak(n):
        if n == 0:
            return ""
        result = []
        yuz = n // 100
        on = (n % 100) // 10
        bir = n % 10
        
        if yuz > 0:
            if yuz == 1:
                result.append("yüz")
            else:
                result.append(birler[yuz] + " yüz")
        if on > 0:
            result.append(onlar[on])
        if bir > 0:
            result.append(birler[bir])
        return " ".join(result)
    
    def tam_yazi(n):
        if n == 0:
            return ""
        
        parts = []
        
        # Milyar
        milyar = n // 1000000000
        if milyar > 0:
            parts.append(yuz_basamak(milyar) + " milyar")
            n %= 1000000000
        
        # Milyon
        milyon = n // 1000000
        if milyon > 0:
            parts.append(yuz_basamak(milyon) + " milyon")
            n %= 1000000
        
        # Bin
        bin_ = n // 1000
        if bin_ > 0:
            if bin_ == 1:
                parts.append("bin")
            else:
                parts.append(yuz_basamak(bin_) + " bin")
            n %= 1000
        
        # Yüzler
        if n > 0:
            parts.append(yuz_basamak(n))
        
        return " ".join(parts).strip()
    
    result = tam_yazi(tam)
    
    if kusur > 0:
        result += " TL " + tam_yazi(kusur) + " kuruş"
    else:
        result += " TL"
    
    return result.upper()


def generate_makbuz_html(data: Dict) -> str:
    """Tahsilat makbuzu HTML oluştur"""
    
    # Dernek bilgileri
    dernek_adi = data.get('dernek_adi', 'BADER DERNEĞİ')
    dernek_adres = data.get('dernek_adres', '')
    dernek_tel = data.get('dernek_tel', '')
    
    # Makbuz bilgileri
    makbuz_no = data.get('makbuz_no', '')
    tarih = data.get('tarih', datetime.now().strftime('%d.%m.%Y'))
    
    # Ödeme bilgileri
    ad_soyad = data.get('ad_soyad', '')
    tutar = data.get('tutar', 0)
    tutar_yazi = sayi_yaziya(tutar)
    aciklama = data.get('aciklama', 'Aidat ödemesi')
    odeme_sekli = data.get('odeme_sekli', 'Nakit')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A5 landscape;
                margin: 1cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 11px;
                line-height: 1.4;
            }}
            .container {{
                border: 2px solid #64B5F6;
                padding: 15px;
                max-width: 550px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #64B5F6;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }}
            .header h1 {{
                color: #64B5F6;
                margin: 0;
                font-size: 18px;
            }}
            .header p {{
                margin: 5px 0 0 0;
                color: #666;
                font-size: 10px;
            }}
            .makbuz-no {{
                text-align: right;
                color: #f44336;
                font-weight: bold;
                font-size: 12px;
            }}
            .title {{
                text-align: center;
                background-color: #64B5F6;
                color: white;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                margin: 10px 0;
            }}
            .info-row {{
                display: flex;
                margin: 8px 0;
            }}
            .label {{
                font-weight: bold;
                width: 120px;
            }}
            .value {{
                flex: 1;
                border-bottom: 1px dotted #999;
            }}
            .tutar-box {{
                text-align: center;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 10px;
                margin: 15px 0;
            }}
            .tutar {{
                font-size: 22px;
                font-weight: bold;
                color: #64B5F6;
            }}
            .tutar-yazi {{
                font-size: 10px;
                color: #666;
                font-style: italic;
            }}
            .footer {{
                display: flex;
                justify-content: space-between;
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #ddd;
            }}
            .imza {{
                text-align: center;
                width: 45%;
            }}
            .imza-line {{
                border-top: 1px solid #333;
                margin-top: 40px;
                padding-top: 5px;
                font-size: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="makbuz-no">Makbuz No: {makbuz_no}</div>
            
            <div class="header">
                <h1>{dernek_adi}</h1>
                <p>{dernek_adres}</p>
                <p>Tel: {dernek_tel}</p>
            </div>
            
            <div class="title">TAHSİLAT MAKBUZU</div>
            
            <div class="info-row">
                <span class="label">Tarih:</span>
                <span class="value">{tarih}</span>
            </div>
            
            <div class="info-row">
                <span class="label">Ad Soyad:</span>
                <span class="value">{ad_soyad}</span>
            </div>
            
            <div class="info-row">
                <span class="label">Açıklama:</span>
                <span class="value">{aciklama}</span>
            </div>
            
            <div class="info-row">
                <span class="label">Ödeme Şekli:</span>
                <span class="value">{odeme_sekli}</span>
            </div>
            
            <div class="tutar-box">
                <div class="tutar">{tutar:,.2f} ₺</div>
                <div class="tutar-yazi">{tutar_yazi}</div>
            </div>
            
            <div class="footer">
                <div class="imza">
                    <div class="imza-line">Teslim Eden</div>
                </div>
                <div class="imza">
                    <div class="imza-line">Teslim Alan</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_rapor_html(title: str, data: List[Dict], columns: List[Dict], 
                        summary: Dict = None, dernek_adi: str = "BADER DERNEĞİ") -> str:
    """Genel rapor HTML oluştur"""
    
    tarih = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    # Tablo başlıkları
    headers_html = "".join([f"<th>{col['label']}</th>" for col in columns])
    
    # Tablo satırları
    rows_html = ""
    for row in data:
        cells = ""
        for col in columns:
            value = row.get(col['key'], '')
            if col.get('format') == 'currency':
                value = f"{float(value or 0):,.2f} ₺"
            elif col.get('format') == 'date' and value:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d').strftime('%d.%m.%Y')
                except:
                    pass
            cells += f"<td style='text-align: {col.get('align', 'left')}'>{value}</td>"
        rows_html += f"<tr>{cells}</tr>"
    
    # Özet
    summary_html = ""
    if summary:
        summary_rows = ""
        for key, value in summary.items():
            summary_rows += f"<tr><td><strong>{key}:</strong></td><td>{value}</td></tr>"
        summary_html = f"""
        <div class="summary">
            <h3>ÖZET</h3>
            <table>{summary_rows}</table>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 1.5cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 10px;
                line-height: 1.4;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #64B5F6;
                padding-bottom: 15px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                color: #64B5F6;
                margin: 0;
                font-size: 16px;
            }}
            .header h2 {{
                color: #444;
                margin: 10px 0 0 0;
                font-size: 14px;
            }}
            .header .date {{
                color: #888;
                font-size: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th {{
                background-color: #64B5F6;
                color: white;
                padding: 8px 5px;
                text-align: left;
                font-size: 10px;
            }}
            td {{
                padding: 6px 5px;
                border-bottom: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            tr:hover {{
                background-color: #f0f0f0;
            }}
            .summary {{
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
            }}
            .summary h3 {{
                color: #64B5F6;
                margin: 0 0 10px 0;
            }}
            .summary table {{
                width: auto;
            }}
            .summary td {{
                padding: 3px 10px;
                border: none;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 15px;
                border-top: 1px solid #ddd;
                color: #888;
                font-size: 9px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{dernek_adi}</h1>
            <h2>{title}</h2>
            <p class="date">Oluşturulma: {tarih}</p>
        </div>
        
        <table>
            <thead>
                <tr>{headers_html}</tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        
        {summary_html}
        
        <div class="footer">
            Bu rapor BADER Dernek Yönetim Sistemi tarafından oluşturulmuştur.
        </div>
    </body>
    </html>
    """
    
    return html


def save_html_as_pdf(html: str, filename: str, folder: str = None) -> str:
    """HTML'i PDF olarak kaydet (temel)"""
    import webbrowser
    import tempfile
    
    if folder is None:
        folder = os.path.expanduser("~/Documents/BADER_Raporlar")
    
    os.makedirs(folder, exist_ok=True)
    
    # HTML dosyası olarak kaydet
    html_path = os.path.join(folder, filename.replace('.pdf', '.html'))
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Tarayıcıda aç (kullanıcı PDF olarak yazdırabilir)
    webbrowser.open('file://' + html_path)
    
    return html_path


class MakbuzGenerator:
    """Makbuz oluşturucu"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def get_dernek_bilgileri(self) -> Dict:
        """Dernek bilgilerini al"""
        bilgiler = {
            'dernek_adi': 'BADER DERNEĞİ',
            'dernek_adres': '',
            'dernek_tel': ''
        }
        
        try:
            self.db.cursor.execute("SELECT ayar_adi, ayar_degeri FROM ayarlar")
            for row in self.db.cursor.fetchall():
                if row['ayar_adi'] == 'dernek_adi':
                    bilgiler['dernek_adi'] = row['ayar_degeri']
                elif row['ayar_adi'] == 'dernek_adres':
                    bilgiler['dernek_adres'] = row['ayar_degeri']
                elif row['ayar_adi'] == 'dernek_tel':
                    bilgiler['dernek_tel'] = row['ayar_degeri']
        except:
            pass
        
        return bilgiler
    
    def generate_makbuz(self, odeme_id: int, odeme_data: Dict) -> str:
        """Ödeme için makbuz oluştur"""
        
        dernek = self.get_dernek_bilgileri()
        
        data = {
            **dernek,
            'makbuz_no': f"M-{datetime.now().year}-{odeme_id:06d}",
            'tarih': odeme_data.get('tarih', datetime.now().strftime('%d.%m.%Y')),
            'ad_soyad': odeme_data.get('ad_soyad', ''),
            'tutar': odeme_data.get('tutar', 0),
            'aciklama': odeme_data.get('aciklama', 'Aidat ödemesi'),
            'odeme_sekli': odeme_data.get('odeme_sekli', 'Nakit')
        }
        
        html = generate_makbuz_html(data)
        filename = f"makbuz_{odeme_id}_{datetime.now().strftime('%Y%m%d')}.html"
        
        return save_html_as_pdf(html, filename)


