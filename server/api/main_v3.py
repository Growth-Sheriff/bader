"""BADER API Server - v3.1.0
OCR Belge Onay Sistemi - Validasyonlar ve Düzeltmeler
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, timedelta, date
import sqlite3
import re
import time
import base64
import hashlib
import secrets
import json
from pathlib import Path

# Config
BASE_DIR = Path("/opt/bader-server")
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = DATA_DIR / "database"
UPLOADS_DIR = BASE_DIR / "uploads"
DATABASE_FILE = DATABASE_DIR / "bader_server.db"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="BADER API", version="3.1.0")

# ==================== SABIT LİSTELER ====================

GELIR_KATEGORILERI = ["AİDAT", "KİRA", "BAĞIŞ", "DÜĞÜN", "KINA", "TOPLANTI", "DAVET", "DİĞER"]
GIDER_KATEGORILERI = ["ELEKTRİK", "SU", "DOĞALGAZ", "İNTERNET", "TELEFON", "KİRA", "TEMİZLİK", "BAKIM-ONARIM", "KIRTASIYE", "ORGANİZASYON", "YEMEK", "ULAŞIM", "PERSONEL", "VERGİ-HARÇ", "SİGORTA", "DİĞER"]
KASALAR = ["BANKA TL", "DERNEK KASA TL", "Ana Kasa"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploads klasörünü statik olarak serve et
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

def get_db():
    conn = sqlite3.connect(str(DATABASE_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_hex(32)

# ==================== VERITABANI SETUP ====================

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Web kullanıcıları tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS web_kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            kullanici_adi TEXT NOT NULL,
            sifre_hash TEXT NOT NULL,
            ad_soyad TEXT NOT NULL,
            email TEXT,
            telefon TEXT,
            uye_id INTEGER,
            rol TEXT DEFAULT 'uye' CHECK(rol IN ('uye', 'personel', 'muhasebeci', 'yonetici', 'admin')),
            aktif INTEGER DEFAULT 1,
            son_giris TIMESTAMP,
            auth_token TEXT,
            token_son_kullanim TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(customer_id, kullanici_adi)
        )
    """)
    
    # Bekleyen belgeler tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bekleyen_belgeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            gonderen_id INTEGER NOT NULL,
            gonderen_ad_soyad TEXT NOT NULL,
            gonderen_rol TEXT,
            belge_turu TEXT DEFAULT 'FATURA',
            dosya_yolu TEXT NOT NULL,
            dosya_boyutu INTEGER,
            ocr_raw_text TEXT,
            ocr_satirlar TEXT,
            ocr_bulunan_tutarlar TEXT,
            ocr_bulunan_tarihler TEXT,
            ocr_sure REAL,
            onerilen_tur TEXT,
            onerilen_kategori TEXT,
            onerilen_tutar REAL,
            onerilen_tarih TEXT,
            onerilen_aciklama TEXT,
            gonderen_notu TEXT,
            durum TEXT DEFAULT 'beklemede' CHECK(durum IN ('beklemede', 'inceleniyor', 'onaylandi', 'reddedildi', 'silindi')),
            islem_yapan_id INTEGER,
            islem_yapan_ad_soyad TEXT,
            islem_tarihi TIMESTAMP,
            islem_notu TEXT,
            onaylanan_tur TEXT,
            onaylanan_kategori TEXT,
            onaylanan_tutar REAL,
            onaylanan_tarih TEXT,
            onaylanan_aciklama TEXT,
            onaylanan_kasa TEXT,
            olusturulan_kayit_tipi TEXT,
            olusturulan_kayit_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # İndeksler
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bekleyen_durum ON bekleyen_belgeler(durum)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bekleyen_customer ON bekleyen_belgeler(customer_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bekleyen_gonderen ON bekleyen_belgeler(gonderen_id)")
    
    # Demo kullanıcılar oluştur
    demo_users = [
        ("BADER-2024-DEMO-0001", "admin", "Sistem Yöneticisi", "admin", "admin123"),
        ("BADER-2024-DEMO-0001", "muhasebe", "Muhasebe Sorumlusu", "muhasebeci", "muhasebe123"),
        ("BADER-2024-DEMO-0001", "ahmet", "Ahmet Yılmaz", "uye", "uye123"),
        ("BADER-2024-DEMO-0001", "mehmet", "Mehmet Demir", "uye", "uye123"),
    ]
    
    for customer_id, kullanici_adi, ad_soyad, rol, sifre in demo_users:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO web_kullanicilar 
                (customer_id, kullanici_adi, ad_soyad, rol, sifre_hash) 
                VALUES (?, ?, ?, ?, ?)
            """, (customer_id, kullanici_adi, ad_soyad, rol, hash_password(sifre)))
        except:
            pass
    
    conn.commit()
    conn.close()

# Uygulama başlatıldığında DB'yi hazırla
init_db()

# ==================== MODELS ====================

class LoginRequest(BaseModel):
    customer_id: str
    kullanici_adi: str
    sifre: str

class BelgeGonderRequest(BaseModel):
    image_base64: str
    belge_turu: Optional[str] = "FATURA"
    gonderen_notu: Optional[str] = None

class BelgeOnayRequest(BaseModel):
    tur: str  # GELİR veya GİDER
    kategori: str
    tutar: float
    tarih: str
    aciklama: Optional[str] = ""
    kasa: Optional[str] = "Ana Kasa"
    onay_notu: Optional[str] = ""
    
    @field_validator('tutar')
    @classmethod
    def tutar_pozitif_olmali(cls, v):
        if v <= 0:
            raise ValueError('Tutar 0\'dan büyük olmalıdır')
        return v
    
    @field_validator('tur')
    @classmethod
    def tur_gecerli_olmali(cls, v):
        if v not in ["GELİR", "GİDER"]:
            raise ValueError('Tür GELİR veya GİDER olmalıdır')
        return v
    
    @field_validator('tarih')
    @classmethod
    def tarih_gecerli_olmali(cls, v):
        try:
            tarih_obj = datetime.strptime(v, "%Y-%m-%d").date()
            if tarih_obj > date.today():
                raise ValueError('Tarih bugünden ileri olamaz')
        except ValueError as e:
            if 'bugünden ileri' in str(e):
                raise e
            raise ValueError('Geçersiz tarih formatı (YYYY-MM-DD olmalı)')
        return v

class BelgeRedRequest(BaseModel):
    red_notu: str

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

# ==================== AUTH HELPERS ====================

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token gerekli")
    
    token = authorization.replace("Bearer ", "")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM web_kullanicilar 
        WHERE auth_token = ? AND token_son_kullanim > ? AND aktif = 1
    """, (token, datetime.now().isoformat()))
    user = cur.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token")
    
    return dict(user)

async def get_admin_user(user: dict = Depends(get_current_user)):
    if user["rol"] not in ["muhasebeci", "yonetici", "admin"]:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    return user

# ==================== OCR HELPERS ====================

KATEGORI_KEYWORDS = {
    "ELEKTRİK": ["elektrik", "tedaş", "enerjisa", "enerji", "kwh", "sayaç", "tüketim", "akedas", "toroslar"],
    "SU": ["su", "iski", "aski", "su idaresi", "metreküp", "m³", "sayaç"],
    "DOĞALGAZ": ["doğalgaz", "igdaş", "başkentgaz", "dogalgaz", "naturelgaz", "sm³", "gazdas"],
    "İNTERNET": ["internet", "fiber", "adsl", "mbps", "gbps", "turk telekom", "superonline"],
    "TELEFON": ["telefon", "gsm", "vodafone", "turkcell", "avea"],
    "KİRA": ["kira", "kiralama", "gayrimenkul", "kontrat"],
    "TEMİZLİK": ["temizlik", "hijyen", "deterjan"],
    "BAKIM-ONARIM": ["bakım", "onarım", "tamir", "servis", "tadilat"],
    "KIRTASIYE": ["kırtasiye", "kalem", "kağıt", "toner", "kartuş", "ofis"],
    "YEMEK": ["restaurant", "restoran", "cafe", "lokanta", "yemek", "kebap", "pizza", "burger"],
    "ULAŞIM": ["taksi", "uber", "benzin", "akaryakıt", "otopark", "petrol", "opet", "shell"],
    "PERSONEL": ["maaş", "ücret", "personel", "işçilik"],
    "VERGİ-HARÇ": ["vergi", "harç", "belediye", "resmi", "damga"],
    "SİGORTA": ["sigorta", "poliçe", "prim"],
}

GELIR_KEYWORDS = ["bağış", "aidat", "kira gelir", "yardım", "hibe", "tahsilat", "gelir"]
GIDER_KEYWORDS = ["fatura", "ödeme", "satın", "alım", "harcama", "gider", "borç"]

def tahmin_kategori(text: str) -> tuple:
    text_lower = text.lower()
    scores = {}
    
    for kategori, keywords in KATEGORI_KEYWORDS.items():
        score = sum(2 if kw in text_lower else 0 for kw in keywords)
        if score > 0:
            scores[kategori] = score
    
    if not scores:
        return ("DİĞER", 0.3)
    
    best = max(scores, key=scores.get)
    confidence = min(scores[best] / 10, 1.0)
    return (best, confidence)

def tahmin_tur(text: str) -> str:
    text_lower = text.lower()
    gelir_score = sum(1 for kw in GELIR_KEYWORDS if kw in text_lower)
    gider_score = sum(1 for kw in GIDER_KEYWORDS if kw in text_lower)
    
    # Fatura, fiş genellikle gider
    if "fatura" in text_lower or "fiş" in text_lower:
        gider_score += 3
    
    return "GELİR" if gelir_score > gider_score else "GİDER"

def extract_tutarlar(text: str) -> list:
    tutarlar = []
    patterns = [
        (r"(?:TOPLAM|GENEL\s*TOPLAM|NET|G\.TOPLAM)[:\s]*([\d.,]+)", "genel_toplam"),
        (r"(?:KDV\s*DAHİL|ÖDENEN)[:\s]*([\d.,]+)", "kdv_dahil"),
        (r"(?:TUTAR|BEDEL|FİYAT)[:\s]*([\d.,]+)", "tutar"),
        (r"([\d]{1,3}(?:[.,][\d]{3})*[.,][\d]{2})\s*(?:TL|₺|TRY)", "tl"),
        (r"(?:TL|₺|TRY)\s*([\d]{1,3}(?:[.,][\d]{3})*[.,][\d]{2})", "tl"),
    ]
    
    for pattern, tip in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                tutar_str = match.group(1).replace(".", "").replace(",", ".")
                tutar = float(tutar_str)
                if tutar > 0:
                    tutarlar.append({"raw": match.group(0), "value": tutar, "tip": tip})
            except:
                pass
    
    # Tekrarları kaldır
    seen = set()
    unique = []
    for t in tutarlar:
        if t["value"] not in seen:
            seen.add(t["value"])
            unique.append(t)
    
    return sorted(unique, key=lambda x: x["value"], reverse=True)

def extract_tarihler(text: str) -> list:
    tarihler = []
    patterns = [
        (r"(\d{2})[./](\d{2})[./](\d{4})", "DMY"),
        (r"(\d{4})[-/](\d{2})[-/](\d{2})", "YMD"),
    ]
    
    for pattern, fmt in patterns:
        for match in re.finditer(pattern, text):
            try:
                if fmt == "DMY":
                    d, m, y = match.groups()
                    date_str = f"{y}-{m}-{d}"
                else:
                    y, m, d = match.groups()
                    date_str = f"{y}-{m}-{d}"
                tarihler.append({"raw": match.group(0), "value": date_str})
            except:
                pass
    
    return tarihler

# ==================== HEALTH ====================

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "3.1.0"}

# ==================== ACTIVATE (Masaüstü Uygulama için) ====================

class ActivateRequest(BaseModel):
    license_key: str
    device_info: Optional[dict] = None

@app.post("/activate")
def activate_license(request: ActivateRequest):
    """Masaüstü uygulama lisans aktivasyonu"""
    
    # Demo lisans kontrolü
    if request.license_key == "BADER-2024-DEMO-0001":
        return {
            "success": True,
            "customer_id": "BADER-2024-DEMO-0001",
            "api_key": "bader_api_key_2024_secure_demo",
            "name": "BADER Demo Derneği",
            "plan": "demo",
            "expires": "2025-12-31",
            "features": ["belge_ocr", "sync", "backup"]
        }
    
    # Gerçek lisans kontrolü (veritabanından)
    conn = get_db()
    cur = conn.cursor()
    
    # Müşteri tablosu varsa kontrol et
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='musteriler'")
    if cur.fetchone():
        cur.execute("""
            SELECT * FROM musteriler 
            WHERE customer_id = ? OR api_key = ?
        """, (request.license_key, request.license_key))
        
        customer = cur.fetchone()
        if customer:
            conn.close()
            return {
                "success": True,
                "customer_id": customer["customer_id"],
                "api_key": customer["api_key"],
                "name": customer.get("name", ""),
                "plan": customer.get("plan", "basic"),
                "expires": customer.get("expires", ""),
                "features": ["belge_ocr", "sync", "backup"]
            }
    
    conn.close()
    raise HTTPException(status_code=401, detail="Geçersiz lisans anahtarı")

# ==================== OCR (Masaüstü Uygulama için) ====================

@app.post("/ocr")
async def ocr_endpoint(image: UploadFile = File(...)):
    """Masaüstü uygulaması için OCR endpoint'i"""
    import tempfile
    from PIL import Image
    
    start_time = time.time()
    
    # Dosyayı geçici olarak kaydet
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # OCR işle
        try:
            import pytesseract
            img = Image.open(tmp_path)
            raw_text = pytesseract.image_to_string(img, lang="tur")
        except Exception as e:
            raw_text = f"OCR hatası: {str(e)}"
        
        ocr_sure = round(time.time() - start_time, 2)
        
        # Satırları ayıkla
        satirlar = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # Tutarları bul
        tutarlar = extract_tutarlar(raw_text)
        
        # Tarihleri bul
        tarihler = extract_tarihler(raw_text)
        
        # Öneri oluştur
        kategori_result = tahmin_kategori(raw_text)
        oneri = {
            "tutar": tutarlar[0]["value"] if tutarlar else None,
            "tarih": tarihler[0]["value"] if tarihler else None,
            "kategori": kategori_result[0] if isinstance(kategori_result, tuple) else kategori_result,
            "tur": tahmin_tur(raw_text),
            "aciklama": satirlar[0] if satirlar else ""
        }
        
        return {
            "success": True,
            "text": raw_text,  # Client 'text' bekliyor
            "raw_text": raw_text,
            "lines": satirlar,  # Client 'lines' bekliyor
            "satirlar": satirlar,
            "confidence": 0.85,  # Client 'confidence' bekliyor
            "bulunan_tutarlar": tutarlar,
            "bulunan_tarihler": tarihler,
            "oneri": oneri,
            "ocr_sure": ocr_sure
        }
    finally:
        # Geçici dosyayı sil
        import os
        os.unlink(tmp_path)

# ==================== AUTH ====================

@app.post("/auth/login")
def login(request: LoginRequest):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM web_kullanicilar 
        WHERE customer_id = ? AND kullanici_adi = ? AND sifre_hash = ? AND aktif = 1
    """, (request.customer_id, request.kullanici_adi, hash_password(request.sifre)))
    
    user = cur.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    
    # Token oluştur
    token = generate_token()
    expires = datetime.now() + timedelta(hours=24)
    
    cur.execute("""
        UPDATE web_kullanicilar 
        SET auth_token = ?, token_son_kullanim = ?, son_giris = ?
        WHERE id = ?
    """, (token, expires.isoformat(), datetime.now().isoformat(), user["id"]))
    
    conn.commit()
    conn.close()
    
    # Yetkileri belirle
    yetkiler = ["belge_gonder", "kendi_belgelerini_gor"]
    if user["rol"] in ["muhasebeci", "yonetici", "admin"]:
        yetkiler.extend(["bekleyen_belgeleri_gor", "belge_onayla", "belge_reddet"])
    if user["rol"] in ["yonetici", "admin"]:
        yetkiler.append("kullanici_yonet")
    if user["rol"] == "admin":
        yetkiler.append("sistem_ayarlari")
    
    return {
        "success": True,
        "token": token,
        "expires_at": expires.isoformat(),
        "user": {
            "id": user["id"],
            "ad_soyad": user["ad_soyad"],
            "rol": user["rol"],
            "yetkiler": yetkiler
        }
    }

@app.post("/auth/logout")
def logout(user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE web_kullanicilar SET auth_token = NULL WHERE id = ?", (user["id"],))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Çıkış yapıldı"}

@app.get("/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "ad_soyad": user["ad_soyad"],
        "rol": user["rol"],
        "customer_id": user["customer_id"]
    }

# ==================== BELGE İŞLEMLERİ ====================

@app.post("/belge/gonder")
def belge_gonder(request: BelgeGonderRequest, user: dict = Depends(get_current_user)):
    start_time = time.time()
    
    # Resmi kaydet
    try:
        image_data = base64.b64decode(request.image_base64)
    except:
        raise HTTPException(status_code=400, detail="Geçersiz resim verisi")
    
    dosya_adi = f"belge_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user['id']}.jpg"
    dosya_yolu = UPLOADS_DIR / dosya_adi
    
    with open(dosya_yolu, "wb") as f:
        f.write(image_data)
    
    # OCR işle
    try:
        import pytesseract
        from PIL import Image
        
        img = Image.open(str(dosya_yolu))
        raw_text = pytesseract.image_to_string(img, lang="tur")
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    except Exception as e:
        raw_text = ""
        lines = []
    
    ocr_sure = round(time.time() - start_time, 2)
    
    # Tutarları ve tarihleri çıkar
    tutarlar = extract_tutarlar(raw_text)
    tarihler = extract_tarihler(raw_text)
    
    # Öneri oluştur
    onerilen_tur = tahmin_tur(raw_text)
    onerilen_kategori, _ = tahmin_kategori(raw_text)
    onerilen_tutar = tutarlar[0]["value"] if tutarlar else None
    onerilen_tarih = tarihler[0]["value"] if tarihler else datetime.now().strftime("%Y-%m-%d")
    onerilen_aciklama = lines[0] if lines else ""
    
    # Veritabanına kaydet
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bekleyen_belgeler (
            customer_id, gonderen_id, gonderen_ad_soyad, gonderen_rol,
            belge_turu, dosya_yolu, dosya_boyutu,
            ocr_raw_text, ocr_satirlar, ocr_bulunan_tutarlar, ocr_bulunan_tarihler, ocr_sure,
            onerilen_tur, onerilen_kategori, onerilen_tutar, onerilen_tarih, onerilen_aciklama,
            gonderen_notu
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user["customer_id"], user["id"], user["ad_soyad"], user["rol"],
        request.belge_turu, dosya_adi, len(image_data),
        raw_text, json.dumps(lines, ensure_ascii=False), 
        json.dumps(tutarlar, ensure_ascii=False), 
        json.dumps(tarihler, ensure_ascii=False), ocr_sure,
        onerilen_tur, onerilen_kategori, onerilen_tutar, onerilen_tarih, onerilen_aciklama,
        request.gonderen_notu
    ))
    belge_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "belge_id": belge_id,
        "message": "Belge gönderildi, onay bekliyor.",
        "ocr": {
            "sure": ocr_sure,
            "satirlar": lines,
            "bulunan_tutarlar": tutarlar,
            "bulunan_tarihler": tarihler,
            "oneri": {
                "tur": onerilen_tur,
                "kategori": onerilen_kategori,
                "tutar": onerilen_tutar,
                "tarih": onerilen_tarih,
                "aciklama": onerilen_aciklama
            }
        }
    }

# ÖNEMLİ: /belge/gonderilerim ve /belge/bekleyenler, /belge/{belge_id}'den ÖNCE tanımlanmalı!

@app.get("/belge/gonderilerim")
def belge_gonderilerim(
    user: dict = Depends(get_current_user),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    limit: int = Query(20, ge=1, le=100, description="Sayfa başına kayıt")
):
    """Kullanıcının kendi gönderdiği belgeleri listeler"""
    offset = (sayfa - 1) * limit
    
    conn = get_db()
    cur = conn.cursor()
    
    # Toplam sayı
    cur.execute("""
        SELECT COUNT(*) FROM bekleyen_belgeler 
        WHERE gonderen_id = ? AND durum != 'silindi'
    """, (user["id"],))
    toplam = cur.fetchone()[0]
    
    # Sayfalı veri
    cur.execute("""
        SELECT * FROM bekleyen_belgeler 
        WHERE gonderen_id = ? AND durum != 'silindi'
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (user["id"], limit, offset))
    rows = cur.fetchall()
    conn.close()
    
    return {
        "success": True,
        "toplam": toplam,
        "sayfa": sayfa,
        "limit": limit,
        "toplam_sayfa": (toplam + limit - 1) // limit if toplam > 0 else 1,
        "belgeler": [{
            "id": r["id"],
            "belge_turu": r["belge_turu"],
            "onerilen_tutar": r["onerilen_tutar"],
            "onerilen_tarih": r["onerilen_tarih"],
            "gonderen_notu": r["gonderen_notu"],
            "durum": r["durum"],
            "islem_notu": r["islem_notu"],
            "created_at": r["created_at"]
        } for r in rows]
    }

@app.get("/belge/bekleyenler")
def belge_bekleyenler(
    user: dict = Depends(get_admin_user),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    limit: int = Query(20, ge=1, le=100, description="Sayfa başına kayıt"),
    durum: str = Query("beklemede", description="Filtre: beklemede, onaylandi, reddedildi, hepsi")
):
    """Admin/muhasebeci için bekleyen belgeler - sayfalı"""
    offset = (sayfa - 1) * limit
    
    conn = get_db()
    cur = conn.cursor()
    
    # Durum filtresi
    if durum == "hepsi":
        durum_filter = "durum != 'silindi'"
        params_count = (user["customer_id"],)
        params_data = (user["customer_id"], limit, offset)
    else:
        durum_filter = "durum = ?"
        params_count = (user["customer_id"], durum)
        params_data = (user["customer_id"], durum, limit, offset)
    
    # Toplam sayı
    cur.execute(f"""
        SELECT COUNT(*) FROM bekleyen_belgeler 
        WHERE customer_id = ? AND {durum_filter}
    """, params_count)
    toplam = cur.fetchone()[0]
    
    # Sayfalı veri
    cur.execute(f"""
        SELECT * FROM bekleyen_belgeler 
        WHERE customer_id = ? AND {durum_filter}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, params_data)
    rows = cur.fetchall()
    conn.close()
    
    return {
        "success": True,
        "toplam": toplam,
        "sayfa": sayfa,
        "limit": limit,
        "toplam_sayfa": (toplam + limit - 1) // limit if toplam > 0 else 1,
        "belgeler": [{
            "id": r["id"],
            "gonderen_ad_soyad": r["gonderen_ad_soyad"],
            "gonderen_rol": r["gonderen_rol"],
            "belge_turu": r["belge_turu"],
            "onerilen_tur": r["onerilen_tur"],
            "onerilen_kategori": r["onerilen_kategori"],
            "onerilen_tutar": r["onerilen_tutar"],
            "onerilen_tarih": r["onerilen_tarih"],
            "gonderen_notu": r["gonderen_notu"],
            "durum": r["durum"],
            "created_at": r["created_at"]
        } for r in rows]
    }

# Şimdi /belge/{belge_id} ve alt endpointleri
@app.get("/belge/{belge_id}")
def belge_detay(belge_id: int, user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bekleyen_belgeler WHERE id = ? AND customer_id = ?", 
                (belge_id, user["customer_id"]))
    r = cur.fetchone()
    conn.close()
    
    if not r:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")
    
    # Üye sadece kendi belgesini görebilir
    if user["rol"] not in ["muhasebeci", "yonetici", "admin"] and r["gonderen_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Bu belgeyi görme yetkiniz yok")
    
    return {
        "success": True,
        "belge": {
            "id": r["id"],
            "gonderen": {
                "id": r["gonderen_id"],
                "ad_soyad": r["gonderen_ad_soyad"],
                "rol": r["gonderen_rol"]
            },
            "belge_turu": r["belge_turu"],
            "dosya_url": f"/uploads/{r['dosya_yolu']}",
            "gonderen_notu": r["gonderen_notu"],
            "durum": r["durum"],
            "created_at": r["created_at"],
            
            "ocr": {
                "raw_text": r["ocr_raw_text"],
                "satirlar": json.loads(r["ocr_satirlar"]) if r["ocr_satirlar"] else [],
                "bulunan_tutarlar": json.loads(r["ocr_bulunan_tutarlar"]) if r["ocr_bulunan_tutarlar"] else [],
                "bulunan_tarihler": json.loads(r["ocr_bulunan_tarihler"]) if r["ocr_bulunan_tarihler"] else [],
                "sure": r["ocr_sure"]
            },
            
            "oneri": {
                "tur": r["onerilen_tur"],
                "kategori": r["onerilen_kategori"],
                "tutar": r["onerilen_tutar"],
                "tarih": r["onerilen_tarih"],
                "aciklama": r["onerilen_aciklama"]
            },
            
            "islem": {
                "islem_yapan": r["islem_yapan_ad_soyad"],
                "islem_tarihi": r["islem_tarihi"],
                "islem_notu": r["islem_notu"]
            } if r["islem_tarihi"] else None
        },
        
        "secenekler": {
            "gelir_kategorileri": ["AİDAT", "KİRA", "BAĞIŞ", "DÜĞÜN", "KINA", "TOPLANTI", "DAVET", "DİĞER"],
            "gider_kategorileri": ["ELEKTRİK", "SU", "DOĞALGAZ", "İNTERNET", "TELEFON", "KİRA", "TEMİZLİK", "BAKIM-ONARIM", "KIRTASIYE", "ORGANİZASYON", "YEMEK", "ULAŞIM", "PERSONEL", "VERGİ-HARÇ", "SİGORTA", "DİĞER"],
            "kasalar": ["BANKA TL", "DERNEK KASA TL", "Ana Kasa"]
        }
    }

@app.post("/belge/{belge_id}/onayla")
def belge_onayla(belge_id: int, request: BelgeOnayRequest, user: dict = Depends(get_admin_user)):
    # Kategori validasyonu
    if request.tur == "GELİR":
        if request.kategori not in GELIR_KATEGORILERI:
            raise HTTPException(
                status_code=400, 
                detail=f"Geçersiz gelir kategorisi. Geçerli kategoriler: {', '.join(GELIR_KATEGORILERI)}"
            )
    else:
        if request.kategori not in GIDER_KATEGORILERI:
            raise HTTPException(
                status_code=400, 
                detail=f"Geçersiz gider kategorisi. Geçerli kategoriler: {', '.join(GIDER_KATEGORILERI)}"
            )
    
    conn = get_db()
    cur = conn.cursor()
    
    # Belgeyi kontrol et
    cur.execute("SELECT * FROM bekleyen_belgeler WHERE id = ? AND customer_id = ? AND durum = 'beklemede'", 
                (belge_id, user["customer_id"]))
    belge = cur.fetchone()
    
    if not belge:
        conn.close()
        raise HTTPException(status_code=404, detail="Onaylanacak belge bulunamadı")
    
    # Gelir/Gider kaydı oluştur
    tarih = request.tarih or datetime.now().strftime("%Y-%m-%d")
    
    if request.tur == "GELİR":
        cur.execute("""
            INSERT INTO gelirler (customer_id, tarih, gelir_turu, aciklama, tutar, kasa, kaynak)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user["customer_id"], tarih, request.kategori, request.aciklama, request.tutar, request.kasa, "ocr"))
        kayit_id = cur.lastrowid
        kayit_tipi = "gelir"
    else:
        cur.execute("""
            INSERT INTO giderler (customer_id, tarih, gider_turu, aciklama, tutar, kasa, kaynak)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user["customer_id"], tarih, request.kategori, request.aciklama, request.tutar, request.kasa, "ocr"))
        kayit_id = cur.lastrowid
        kayit_tipi = "gider"
    
    # Belgeyi güncelle
    cur.execute("""
        UPDATE bekleyen_belgeler SET
            durum = 'onaylandi',
            islem_yapan_id = ?,
            islem_yapan_ad_soyad = ?,
            islem_tarihi = ?,
            islem_notu = ?,
            onaylanan_tur = ?,
            onaylanan_kategori = ?,
            onaylanan_tutar = ?,
            onaylanan_tarih = ?,
            onaylanan_aciklama = ?,
            onaylanan_kasa = ?,
            olusturulan_kayit_tipi = ?,
            olusturulan_kayit_id = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        user["id"], user["ad_soyad"], datetime.now().isoformat(), request.onay_notu,
        request.tur, request.kategori, request.tutar, tarih, request.aciklama, request.kasa,
        kayit_tipi, kayit_id, datetime.now().isoformat(), belge_id
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Belge onaylandı ve {kayit_tipi} kaydı oluşturuldu.",
        "kayit": {
            "tip": kayit_tipi,
            "id": kayit_id,
            "tutar": request.tutar
        }
    }

@app.post("/belge/{belge_id}/reddet")
def belge_reddet(belge_id: int, request: BelgeRedRequest, user: dict = Depends(get_admin_user)):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM bekleyen_belgeler WHERE id = ? AND customer_id = ? AND durum = 'beklemede'", 
                (belge_id, user["customer_id"]))
    belge = cur.fetchone()
    
    if not belge:
        conn.close()
        raise HTTPException(status_code=404, detail="Reddedilecek belge bulunamadı")
    
    cur.execute("""
        UPDATE bekleyen_belgeler SET
            durum = 'reddedildi',
            islem_yapan_id = ?,
            islem_yapan_ad_soyad = ?,
            islem_tarihi = ?,
            islem_notu = ?,
            updated_at = ?
        WHERE id = ?
    """, (user["id"], user["ad_soyad"], datetime.now().isoformat(), request.red_notu,
          datetime.now().isoformat(), belge_id))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Belge reddedildi."}

@app.delete("/belge/{belge_id}")
def belge_sil(belge_id: int, user: dict = Depends(get_current_user)):
    """Kullanıcı kendi bekleyen belgesini silebilir, admin herhangi birini silebilir"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM bekleyen_belgeler WHERE id = ? AND customer_id = ?", 
                (belge_id, user["customer_id"]))
    belge = cur.fetchone()
    
    if not belge:
        conn.close()
        raise HTTPException(status_code=404, detail="Belge bulunamadı")
    
    # Yetki kontrolü
    is_owner = belge["gonderen_id"] == user["id"]
    is_admin = user["rol"] in ["yonetici", "admin"]
    
    if not is_owner and not is_admin:
        conn.close()
        raise HTTPException(status_code=403, detail="Bu belgeyi silme yetkiniz yok")
    
    # Sadece beklemede olan silinebilir (owner için)
    if is_owner and not is_admin and belge["durum"] != "beklemede":
        conn.close()
        raise HTTPException(status_code=400, detail="Sadece beklemede olan belgeler silinebilir")
    
    # Soft delete
    cur.execute("""
        UPDATE bekleyen_belgeler SET
            durum = 'silindi',
            updated_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), belge_id))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Belge silindi."}

# ==================== OCR DEMO ====================

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
        raw_text = pytesseract.image_to_string(img, lang="tur")
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        
        tutarlar = extract_tutarlar(raw_text)
        tarihler = extract_tarihler(raw_text)
        
        tutar = tutarlar[0]["value"] if tutarlar else None
        tarih = tarihler[0]["value"] if tarihler else None
        
        processing_time = round(time.time() - start_time, 2)
        upload_path.unlink(missing_ok=True)
        
        return {
            "success": True,
            "raw_text": raw_text,
            "lines": lines,
            "tutar": tutar,
            "tarih": tarih,
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
    tarih = request.tarih or datetime.now().strftime("%Y-%m-%d")
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
    tarih = request.tarih or datetime.now().strftime("%Y-%m-%d")
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
    
    # Bekleyen belge sayısı
    cur.execute("SELECT COUNT(*) FROM bekleyen_belgeler WHERE customer_id = ? AND durum = 'beklemede'", (customer_id,))
    bekleyen_belge = cur.fetchone()[0]
    
    conn.close()
    
    net_bakiye = toplam_gelir - toplam_gider
    
    return {
        "aktif_uye": aktif_uye,
        "uye_sayisi": aktif_uye,
        "toplam_gelir": toplam_gelir,
        "toplam_gider": toplam_gider,
        "net_bakiye": net_bakiye,
        "bakiye": net_bakiye,
        "bekleyen_belge": bekleyen_belge
    }


# ==================== ADMIN PANEL - LİSANS YÖNETİMİ ====================

ADMIN_SECRET = "BADER_ADMIN_2024_SUPER_SECRET"  # Gerçek ortamda env variable olmalı

def verify_admin(x_admin_key: str = Header(...)):
    """Admin yetkisi kontrolü"""
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    return True

# Müşteri/Lisans tablosu oluştur
def init_admin_tables():
    conn = get_db()
    cur = conn.cursor()
    
    # Müşteriler (Lisans sahipleri)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            telefon TEXT,
            adres TEXT,
            plan TEXT DEFAULT 'basic' CHECK(plan IN ('demo', 'basic', 'pro', 'enterprise')),
            max_kullanici INTEGER DEFAULT 5,
            max_uye INTEGER DEFAULT 500,
            aktif INTEGER DEFAULT 1,
            expires TEXT,
            features TEXT DEFAULT '["belge_ocr", "sync", "backup"]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            device_info TEXT,
            notes TEXT
        )
    """)
    
    # Uygulama versiyonları
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            platform TEXT DEFAULT 'all' CHECK(platform IN ('all', 'macos', 'windows', 'linux')),
            download_url TEXT,
            file_path TEXT,
            file_size INTEGER,
            changelog TEXT,
            min_required_version TEXT,
            is_critical INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Aktivasyon logları
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            device_info TEXT,
            ip_address TEXT,
            success INTEGER,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Backup'lar
    cur.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Admin tabloları oluştur
init_admin_tables()


# ========== MÜŞTERİ/LİSANS YÖNETİMİ ==========

class MusteriCreate(BaseModel):
    name: str
    email: Optional[str] = None
    telefon: Optional[str] = None
    adres: Optional[str] = None
    plan: str = "basic"
    max_kullanici: int = 5
    max_uye: int = 500
    expires: Optional[str] = None
    notes: Optional[str] = None

@app.get("/admin/musteriler")
def admin_list_musteriler(admin: bool = Depends(verify_admin)):
    """Tüm müşterileri listele"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, customer_id, api_key, name, email, telefon, plan, 
               max_kullanici, max_uye, aktif, expires, last_seen, created_at
        FROM musteriler ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    
    return {"musteriler": [dict(row) for row in rows]}

@app.post("/admin/musteriler")
def admin_create_musteri(data: MusteriCreate, admin: bool = Depends(verify_admin)):
    """Yeni müşteri/lisans oluştur"""
    import uuid
    
    customer_id = f"BADER-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
    api_key = f"bader_api_{secrets.token_hex(16)}"
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO musteriler (customer_id, api_key, name, email, telefon, adres, plan, max_kullanici, max_uye, expires, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_id, api_key, data.name, data.email, data.telefon, data.adres, 
              data.plan, data.max_kullanici, data.max_uye, data.expires, data.notes))
        conn.commit()
        
        return {
            "success": True,
            "customer_id": customer_id,
            "api_key": api_key,
            "message": f"Müşteri oluşturuldu: {data.name}"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/admin/musteriler/{customer_id}")
def admin_get_musteri(customer_id: str, admin: bool = Depends(verify_admin)):
    """Müşteri detayı"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM musteriler WHERE customer_id = ?", (customer_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    return dict(row)

@app.put("/admin/musteriler/{customer_id}")
def admin_update_musteri(customer_id: str, data: MusteriCreate, admin: bool = Depends(verify_admin)):
    """Müşteri güncelle"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE musteriler SET 
            name = ?, email = ?, telefon = ?, adres = ?, plan = ?, 
            max_kullanici = ?, max_uye = ?, expires = ?, notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE customer_id = ?
    """, (data.name, data.email, data.telefon, data.adres, data.plan,
          data.max_kullanici, data.max_uye, data.expires, data.notes, customer_id))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Müşteri güncellendi"}

@app.delete("/admin/musteriler/{customer_id}")
def admin_delete_musteri(customer_id: str, admin: bool = Depends(verify_admin)):
    """Müşteri sil (soft delete)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE musteriler SET aktif = 0 WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Müşteri devre dışı bırakıldı"}

@app.post("/admin/musteriler/{customer_id}/yenile-api-key")
def admin_regenerate_api_key(customer_id: str, admin: bool = Depends(verify_admin)):
    """API key yenile"""
    new_api_key = f"bader_api_{secrets.token_hex(16)}"
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE musteriler SET api_key = ? WHERE customer_id = ?", (new_api_key, customer_id))
    conn.commit()
    conn.close()
    
    return {"success": True, "api_key": new_api_key}


# ========== GÜNCELLEME SİSTEMİ ==========

class VersionCreate(BaseModel):
    version: str
    platform: str = "all"
    changelog: str = ""
    min_required_version: Optional[str] = None
    is_critical: bool = False

@app.get("/admin/versions")
def admin_list_versions(admin: bool = Depends(verify_admin)):
    """Tüm versiyonları listele"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM app_versions ORDER BY released_at DESC")
    rows = cur.fetchall()
    conn.close()
    
    return {"versions": [dict(row) for row in rows]}

@app.post("/admin/versions")
def admin_create_version(data: VersionCreate, admin: bool = Depends(verify_admin)):
    """Yeni versiyon kaydı oluştur"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO app_versions (version, platform, changelog, min_required_version, is_critical)
            VALUES (?, ?, ?, ?, ?)
        """, (data.version, data.platform, data.changelog, data.min_required_version, 1 if data.is_critical else 0))
        version_id = cur.lastrowid
        conn.commit()
        
        return {"success": True, "id": version_id, "version": data.version}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.put("/admin/versions/{version}")
async def admin_update_version(version: str, admin: bool = Depends(verify_admin), 
                               download_url: str = None, changelog: str = None, 
                               is_active: bool = None, is_critical: bool = None):
    """Versiyon bilgilerini güncelle"""
    conn = get_db()
    cur = conn.cursor()
    
    updates = []
    params = []
    
    if download_url is not None:
        updates.append("download_url = ?")
        params.append(download_url)
    if changelog is not None:
        updates.append("changelog = ?")
        params.append(changelog)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if is_active else 0)
    if is_critical is not None:
        updates.append("is_critical = ?")
        params.append(1 if is_critical else 0)
    
    if not updates:
        return {"success": False, "message": "Güncellenecek alan yok"}
    
    params.append(version)
    cur.execute(f"UPDATE app_versions SET {', '.join(updates)} WHERE version = ?", params)
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"Versiyon {version} güncellendi"}

@app.post("/admin/versions/{version}/upload")
async def admin_upload_version(version: str, file: UploadFile = File(...), admin: bool = Depends(verify_admin)):
    """Güncelleme dosyası yükle"""
    updates_dir = BASE_DIR / "updates"
    updates_dir.mkdir(exist_ok=True)
    
    # Platform'a göre dosya adı
    ext = Path(file.filename).suffix
    file_path = updates_dir / f"BADER-{version}{ext}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Veritabanını güncelle
    conn = get_db()
    cur = conn.cursor()
    download_url = f"/updates/BADER-{version}{ext}"
    cur.execute("""
        UPDATE app_versions SET 
            file_path = ?, file_size = ?, download_url = ?, is_active = 1
        WHERE version = ?
    """, (str(file_path), len(content), download_url, version))
    conn.commit()
    conn.close()
    
    return {
        "success": True, 
        "message": f"Dosya yüklendi: {file.filename}",
        "size": len(content),
        "download_url": download_url
    }

# Güncelleme dosyalarını serve et
updates_dir = BASE_DIR / "updates"
updates_dir.mkdir(exist_ok=True)
app.mount("/updates", StaticFiles(directory=str(updates_dir)), name="updates")


# ========== KULLANICI GÜNCELLEME KONTROLÜ (Public) ==========

@app.get("/version/check")
def check_version(current_version: str, platform: str = "all"):
    """Kullanıcı için güncelleme kontrolü (Public endpoint)"""
    conn = get_db()
    cur = conn.cursor()
    
    # En son aktif versiyonu bul
    cur.execute("""
        SELECT version, download_url, changelog, is_critical, min_required_version, file_size
        FROM app_versions 
        WHERE is_active = 1 AND (platform = ? OR platform = 'all')
        ORDER BY released_at DESC LIMIT 1
    """, (platform,))
    
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return {
            "has_update": False,
            "current_version": current_version,
            "latest_version": current_version,
            "message": "Güncel sürümdesiniz"
        }
    
    latest = dict(row)
    latest_version = latest["version"]
    
    # Versiyon karşılaştır (basit string comparison)
    def version_tuple(v):
        return tuple(map(int, (v.replace("v", "").split("."))))
    
    try:
        has_update = version_tuple(latest_version) > version_tuple(current_version)
    except:
        has_update = latest_version != current_version
    
    # Kritik güncelleme veya minimum versiyon kontrolü
    force_update = False
    if latest.get("min_required_version"):
        try:
            force_update = version_tuple(current_version) < version_tuple(latest["min_required_version"])
        except:
            pass
    
    return {
        "has_update": has_update,
        "current_version": current_version,
        "latest_version": latest_version,
        "download_url": latest.get("download_url"),
        "changelog": latest.get("changelog", ""),
        "is_critical": bool(latest.get("is_critical")),
        "force_update": force_update or bool(latest.get("is_critical")),
        "file_size": latest.get("file_size", 0),
        "message": f"Yeni sürüm mevcut: {latest_version}" if has_update else "Güncel sürümdesiniz"
    }


# ========== AKTİVASYON LOGLARI ==========

@app.get("/admin/aktivasyon-loglari")
def admin_activation_logs(admin: bool = Depends(verify_admin), limit: int = 100):
    """Aktivasyon logları"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM activation_logs ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    
    return {"logs": [dict(row) for row in rows]}


# ========== DASHBOARD İSTATİSTİKLERİ ==========

@app.get("/admin/dashboard")
def admin_dashboard(admin: bool = Depends(verify_admin)):
    """Admin dashboard istatistikleri"""
    conn = get_db()
    cur = conn.cursor()
    
    # Toplam müşteri
    cur.execute("SELECT COUNT(*) FROM musteriler WHERE aktif = 1")
    toplam_musteri = cur.fetchone()[0]
    
    # Plan dağılımı
    cur.execute("SELECT plan, COUNT(*) as count FROM musteriler WHERE aktif = 1 GROUP BY plan")
    plan_dagilim = {row["plan"]: row["count"] for row in cur.fetchall()}
    
    # Son 24 saat aktivasyon
    cur.execute("""
        SELECT COUNT(*) FROM activation_logs 
        WHERE created_at > datetime('now', '-24 hours')
    """)
    aktivasyon_24h = cur.fetchone()[0]
    
    # Son 7 gün aktivasyon
    cur.execute("""
        SELECT COUNT(*) FROM activation_logs 
        WHERE created_at > datetime('now', '-7 days')
    """)
    aktivasyon_7d = cur.fetchone()[0]
    
    # Aktif versiyon
    cur.execute("SELECT version FROM app_versions WHERE is_active = 1 ORDER BY released_at DESC LIMIT 1")
    row = cur.fetchone()
    aktif_versiyon = row["version"] if row else "1.0.0"
    
    # Bekleyen belgeler
    cur.execute("SELECT COUNT(*) FROM bekleyen_belgeler WHERE durum = 'beklemede'")
    bekleyen_belge = cur.fetchone()[0]
    
    conn.close()
    
    return {
        "toplam_musteri": toplam_musteri,
        "plan_dagilim": plan_dagilim,
        "aktivasyon_24h": aktivasyon_24h,
        "aktivasyon_7d": aktivasyon_7d,
        "aktif_versiyon": aktif_versiyon,
        "bekleyen_belge": bekleyen_belge
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
