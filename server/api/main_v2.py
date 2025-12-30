"""
BADER API Server - v2.2.0 Enhanced OCR
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3
import re
import time
import base64
from pathlib import Path

# Config
BASE_DIR = Path("/opt/bader-server")
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = DATA_DIR / "database"
UPLOADS_DIR = BASE_DIR / "uploads"
DATABASE_FILE = DATABASE_DIR / "bader_server.db"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="BADER API", version="2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(str(DATABASE_FILE))
    conn.row_factory = sqlite3.Row
    return conn

# ==================== MODELS ====================

class OCRRequest(BaseModel):
    image_base64: str
    filename: Optional[str] = "document.png"

class KayitRequest(BaseModel):
    tutar: float
    aciklama: Optional[str] = ""
    tarih: Optional[str] = None
    tur: Optional[str] = None
    kasa: Optional[str] = "Ana Kasa"
    kaynak: Optional[str] = "web"
    customer_id: Optional[str] = "BADER-2024-DEMO-0001"

class UyeRequest(BaseModel):
    uye_no: Optional[str] = None
    ad_soyad: str
    tc_kimlik: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    adres: Optional[str] = None
    customer_id: Optional[str] = "BADER-2024-DEMO-0001"

# ==================== HEALTH ====================

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "2.2.0"}

# ==================== OCR ====================

def extract_amounts(text: str) -> List[dict]:
    """Metinden tüm para tutarlarını çıkar"""
    amounts = []
    
    # Türk formatı: 1.234,56 veya 1234,56
    pattern1 = r'(\d{1,3}(?:\.\d{3})*,\d{2})'
    for match in re.finditer(pattern1, text):
        try:
            val = match.group(1).replace('.', '').replace(',', '.')
            amounts.append({
                'raw': match.group(1),
                'value': float(val),
                'position': match.start()
            })
        except:
            pass
    
    # Basit format: 123.45 veya 123,45
    pattern2 = r'(?<![.,\d])(\d+)[.,](\d{2})(?![.,\d])'
    for match in re.finditer(pattern2, text):
        try:
            val = float(match.group(1) + '.' + match.group(2))
            raw = match.group(0)
            # Zaten bulunmuş mu kontrol et
            if not any(a['raw'] == raw for a in amounts):
                amounts.append({
                    'raw': raw,
                    'value': val,
                    'position': match.start()
                })
        except:
            pass
    
    # Tam sayılar (TL veya ₺ ile)
    pattern3 = r'(\d+)\s*(?:TL|tl|₺)'
    for match in re.finditer(pattern3, text):
        try:
            val = float(match.group(1))
            if val > 0:
                amounts.append({
                    'raw': match.group(0),
                    'value': val,
                    'position': match.start()
                })
        except:
            pass
    
    # Pozisyona göre sırala ve tekrarları kaldır
    seen = set()
    unique = []
    for a in sorted(amounts, key=lambda x: x['position']):
        if a['value'] not in seen:
            seen.add(a['value'])
            unique.append(a)
    
    return unique

def extract_dates(text: str) -> List[str]:
    """Metinden tüm tarihleri çıkar"""
    dates = []
    patterns = [
        r'(\d{2}[./]\d{2}[./]\d{4})',
        r'(\d{2}[./]\d{2}[./]\d{2})',
        r'(\d{4}[./]\d{2}[./]\d{2})',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            dates.append(match.group(1))
    return list(set(dates))

def find_best_amount(text: str, amounts: List[dict]) -> Optional[float]:
    """En olası toplam tutarı bul"""
    if not amounts:
        return None
    
    # Önce TOPLAM, GENEL TOPLAM, NET, ÖDENECEK gibi kelimelerin yanındaki tutarı ara
    keywords = ['TOPLAM', 'GENEL', 'NET', 'ODENECEK', 'ODENEN', 'TUTAR', 'BEDEL', 'TOTAL']
    
    text_upper = text.upper()
    for kw in keywords:
        # Anahtar kelimeden sonraki satırda veya aynı satırda tutar ara
        pattern = kw + r'[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+[.,]\d{2}|\d+)'
        match = re.search(pattern, text_upper)
        if match:
            try:
                val_str = match.group(1).replace('.', '').replace(',', '.')
                val = float(val_str)
                if val > 0:
                    return val
            except:
                pass
    
    # En büyük tutarı döndür (genellikle toplam budur)
    if amounts:
        return max(a['value'] for a in amounts)
    
    return None

@app.post("/ocr/demo")
def ocr_demo(request: OCRRequest):
    start_time = time.time()
    
    try:
        image_data = base64.b64decode(request.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geçersiz base64: {str(e)}")
    
    upload_path = UPLOADS_DIR / f"demo_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    with open(upload_path, "wb") as f:
        f.write(image_data)
    
    try:
        import pytesseract
        from PIL import Image
        
        img = Image.open(str(upload_path))
        raw_text = pytesseract.image_to_string(img, lang='tur')
        
        # Satırları ayır ve temizle
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # Tüm tutarları çıkar
        all_amounts = extract_amounts(raw_text)
        
        # Tüm tarihleri çıkar
        all_dates = extract_dates(raw_text)
        
        # En iyi tutarı bul
        best_amount = find_best_amount(raw_text, all_amounts)
        
        # Her satır için analiz
        analyzed_lines = []
        for i, line in enumerate(lines):
            line_amounts = extract_amounts(line)
            line_dates = extract_dates(line)
            analyzed_lines.append({
                'index': i,
                'text': line,
                'amounts': [a['value'] for a in line_amounts],
                'dates': line_dates,
                'has_amount': len(line_amounts) > 0,
                'has_date': len(line_dates) > 0
            })
        
        processing_time = round(time.time() - start_time, 2)
        upload_path.unlink(missing_ok=True)
        
        return {
            "success": True,
            "raw_text": raw_text,
            "lines": lines,
            "analyzed_lines": analyzed_lines,
            "all_amounts": [{'raw': a['raw'], 'value': a['value']} for a in all_amounts],
            "all_dates": all_dates,
            "tutar": best_amount,
            "tarih": all_dates[0] if all_dates else None,
            "aciklama": lines[0] if lines else None,
            "processing_time": processing_time
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="Tesseract OCR yüklü değil")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DERNEK - ÜYELER ====================

@app.get("/dernek/uyeler")
def get_uyeler(customer_id: str = "BADER-2024-DEMO-0001"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM uyeler WHERE customer_id = ?", (customer_id,))
    rows = cur.fetchall()
    conn.close()
    return [{
        "id": r["uye_id"],
        "uye_no": r["uye_no"],
        "ad_soyad": r["ad_soyad"],
        "telefon": r["telefon"],
        "email": r["email"],
        "durum": r["durum"]
    } for r in rows]

@app.post("/dernek/uyeler")
def add_uye(request: UyeRequest):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO uyeler (customer_id, uye_no, ad_soyad, tc_kimlik, telefon, email, adres) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (request.customer_id, request.uye_no, request.ad_soyad, request.tc_kimlik, request.telefon, request.email, request.adres)
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Üye kaydedildi"}

# ==================== DERNEK - GELİRLER ====================

@app.get("/dernek/gelirler")
def get_gelirler(customer_id: str = "BADER-2024-DEMO-0001"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gelirler WHERE customer_id = ? ORDER BY tarih DESC LIMIT 50", (customer_id,))
    rows = cur.fetchall()
    conn.close()
    return [{
        "id": r["gelir_id"],
        "tarih": r["tarih"],
        "gelir_turu": r["gelir_turu"],
        "aciklama": r["aciklama"],
        "tutar": r["tutar"],
        "kasa": r["kasa"],
        "kaynak": r["kaynak"]
    } for r in rows]

@app.post("/dernek/gelirler")
def add_gelir(request: KayitRequest):
    conn = get_db()
    cur = conn.cursor()
    tarih = request.tarih or datetime.now().strftime('%Y-%m-%d')
    cur.execute(
        "INSERT INTO gelirler (customer_id, tarih, gelir_turu, aciklama, tutar, kasa, kaynak) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (request.customer_id, tarih, request.tur, request.aciklama, request.tutar, request.kasa, request.kaynak)
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Gelir kaydedildi"}

# ==================== DERNEK - GİDERLER ====================

@app.get("/dernek/giderler")
def get_giderler(customer_id: str = "BADER-2024-DEMO-0001"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM giderler WHERE customer_id = ? ORDER BY tarih DESC LIMIT 50", (customer_id,))
    rows = cur.fetchall()
    conn.close()
    return [{
        "id": r["gider_id"],
        "tarih": r["tarih"],
        "gider_turu": r["gider_turu"],
        "aciklama": r["aciklama"],
        "tutar": r["tutar"],
        "kasa": r["kasa"],
        "kaynak": r["kaynak"]
    } for r in rows]

@app.post("/dernek/giderler")
def add_gider(request: KayitRequest):
    conn = get_db()
    cur = conn.cursor()
    tarih = request.tarih or datetime.now().strftime('%Y-%m-%d')
    cur.execute(
        "INSERT INTO giderler (customer_id, tarih, gider_turu, aciklama, tutar, kasa, kaynak) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (request.customer_id, tarih, request.tur, request.aciklama, request.tutar, request.kasa, request.kaynak)
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Gider kaydedildi"}

# ==================== DERNEK - ÖZET ====================

@app.get("/dernek/ozet")
def get_ozet(customer_id: str = "BADER-2024-DEMO-0001"):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM uyeler WHERE customer_id = ? AND durum = 'Aktif'", (customer_id,))
    aktif_uye = cur.fetchone()[0]
    
    cur.execute("SELECT COALESCE(SUM(tutar), 0) FROM gelirler WHERE customer_id = ?", (customer_id,))
    toplam_gelir = cur.fetchone()[0]
    
    cur.execute("SELECT COALESCE(SUM(tutar), 0) FROM giderler WHERE customer_id = ?", (customer_id,))
    toplam_gider = cur.fetchone()[0]
    
    conn.close()
    
    net_bakiye = toplam_gelir - toplam_gider
    
    return {
        "aktif_uye": aktif_uye,
        "uye_sayisi": aktif_uye,
        "toplam_gelir": toplam_gelir,
        "toplam_gider": toplam_gider,
        "net_bakiye": net_bakiye,
        "bakiye": net_bakiye
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
