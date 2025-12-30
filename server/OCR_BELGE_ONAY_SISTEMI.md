# BADER - OCR Belge Onay Sistemi
## Ultra Detaylı Mimari ve Entegrasyon Dokümanı

**Versiyon:** 2.0  
**Tarih:** 29 Aralık 2025

---

# 1. SİSTEM MİMARİSİ

## 1.1 Genel Akış

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│   ÜYE/PERSONEL                  SUNUCU                         YÖNETİCİ              │
│   (Mobil/Web)                   (API)                          (Web Panel)           │
│                                                                                      │
│   ┌─────────┐                 ┌─────────┐                    ┌─────────┐            │
│   │ 1.Giriş │────────────────▶│  Auth   │◀───────────────────│ 1.Giriş │            │
│   └────┬────┘                 └─────────┘                    └────┬────┘            │
│        │                                                          │                  │
│        ▼                                                          │                  │
│   ┌─────────┐                 ┌─────────┐                         │                  │
│   │ 2.Belge │────────────────▶│   OCR   │                         │                  │
│   │   Çek   │                 │  İşleme │                         │                  │
│   └────┬────┘                 └────┬────┘                         │                  │
│        │                           │                              │                  │
│        ▼                           ▼                              ▼                  │
│   ┌─────────┐                 ┌─────────┐                    ┌─────────┐            │
│   │ 3.Öniz- │◀────────────────│ Bekley- │───────────────────▶│ 2.Liste │            │
│   │   leme  │                 │   en    │                    │   Gör   │            │
│   └────┬────┘                 │ Belgeler│                    └────┬────┘            │
│        │                      └─────────┘                         │                  │
│        ▼                                                          ▼                  │
│   ┌─────────┐                                                ┌─────────┐            │
│   │ 4.Gönder│                                                │ 3.Detay │            │
│   │   +Not  │                                                │+Düzenle │            │
│   └─────────┘                                                └────┬────┘            │
│                                                                   │                  │
│        ┌──────────────────────────────────────────────────────────┘                  │
│        │                                                                             │
│        ▼                                                                             │
│   ┌─────────┐                 ┌─────────┐                    ┌─────────┐            │
│   │ 5.Bildi-│◀────────────────│  Onay/  │───────────────────▶│  Gelir/ │            │
│   │   rim   │                 │  Red    │                    │  Gider  │            │
│   └─────────┘                 └─────────┘                    │  Kayıt  │            │
│                                                              └─────────┘            │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. VERİTABANI ŞEMASI

## 2.1 Yeni Tablolar

### 2.1.1 `web_kullanicilar` - Web/Mobil Kullanıcıları

```sql
CREATE TABLE web_kullanicilar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    
    -- Kimlik
    kullanici_adi TEXT NOT NULL,
    sifre_hash TEXT NOT NULL,
    ad_soyad TEXT NOT NULL,
    email TEXT,
    telefon TEXT,
    
    -- Bağlantı
    uye_id INTEGER,                    -- Üye ise referans
    
    -- Yetki
    rol TEXT DEFAULT 'uye' CHECK(rol IN ('uye', 'personel', 'muhasebeci', 'yonetici', 'admin')),
    
    -- Durum
    aktif INTEGER DEFAULT 1,
    son_giris TIMESTAMP,
    
    -- Token
    auth_token TEXT,
    token_son_kullanim TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(customer_id, kullanici_adi),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (uye_id) REFERENCES uyeler(uye_id)
);
```

### 2.1.2 `bekleyen_belgeler` - Onay Bekleyen Belgeler

```sql
CREATE TABLE bekleyen_belgeler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    
    -- Gönderen
    gonderen_id INTEGER NOT NULL,
    gonderen_ad_soyad TEXT NOT NULL,
    gonderen_rol TEXT,
    
    -- Belge
    belge_turu TEXT DEFAULT 'FATURA' CHECK(belge_turu IN 
        ('FATURA', 'FİŞ', 'DEKONT', 'MAKBUZ', 'DİĞER')),
    dosya_yolu TEXT NOT NULL,
    dosya_boyutu INTEGER,
    
    -- OCR Ham Veriler
    ocr_raw_text TEXT,
    ocr_satirlar TEXT,                 -- JSON: ["satır1", "satır2", ...]
    ocr_bulunan_tutarlar TEXT,         -- JSON: [{"raw": "₺1.234", "value": 1234.00}, ...]
    ocr_bulunan_tarihler TEXT,         -- JSON: ["15/03/2025", "01.03.2025", ...]
    ocr_pikseller TEXT,                -- JSON: Satır koordinatları (opsiyonel)
    ocr_sure REAL,
    
    -- OCR Önerileri
    onerilen_tur TEXT CHECK(onerilen_tur IN ('GELİR', 'GİDER')),
    onerilen_kategori TEXT,
    onerilen_tutar REAL,
    onerilen_tarih DATE,
    onerilen_aciklama TEXT,
    
    -- Kullanıcı Notu
    gonderen_notu TEXT,
    
    -- Durum
    durum TEXT DEFAULT 'beklemede' CHECK(durum IN 
        ('beklemede', 'inceleniyor', 'onaylandi', 'reddedildi')),
    
    -- Onay/Red Bilgileri
    islem_yapan_id INTEGER,
    islem_yapan_ad_soyad TEXT,
    islem_tarihi TIMESTAMP,
    islem_notu TEXT,
    
    -- Onaylanan Değerler (Düzenlenmiş)
    onaylanan_tur TEXT,
    onaylanan_kategori TEXT,
    onaylanan_tutar REAL,
    onaylanan_tarih DATE,
    onaylanan_aciklama TEXT,
    onaylanan_kasa TEXT,
    
    -- Oluşturulan Kayıt
    olusturulan_kayit_tipi TEXT,       -- 'gelir' veya 'gider'
    olusturulan_kayit_id INTEGER,
    
    -- Tarihler
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (gonderen_id) REFERENCES web_kullanicilar(id),
    FOREIGN KEY (islem_yapan_id) REFERENCES web_kullanicilar(id)
);

-- İndeksler
CREATE INDEX idx_bekleyen_durum ON bekleyen_belgeler(durum);
CREATE INDEX idx_bekleyen_customer ON bekleyen_belgeler(customer_id);
CREATE INDEX idx_bekleyen_gonderen ON bekleyen_belgeler(gonderen_id);
```

---

# 3. API ENDPOINTLERİ

## 3.1 Kimlik Doğrulama

### POST `/auth/login`

**İstek:**
```json
{
    "customer_id": "BADER-2024-DEMO-0001",
    "kullanici_adi": "ahmet.yilmaz",
    "sifre": "********"
}
```

**Başarılı Yanıt:**
```json
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2025-03-21T14:30:00",
    "user": {
        "id": 5,
        "ad_soyad": "Ahmet Yılmaz",
        "rol": "uye",
        "yetkiler": ["belge_gonder", "kendi_belgelerini_gor"]
    }
}
```

### POST `/auth/logout`

**Header:** `Authorization: Bearer <token>`

---

## 3.2 Belge İşlemleri

### POST `/belge/gonder`

Üye/personel belge gönderir. OCR otomatik çalışır.

**Header:** `Authorization: Bearer <token>`

**İstek:**
```json
{
    "image_base64": "/9j/4AAQSkZJRgABAQEA...",
    "belge_turu": "FATURA",
    "gonderen_notu": "Mart ayı elektrik faturası"
}
```

**Başarılı Yanıt:**
```json
{
    "success": true,
    "belge_id": 42,
    "message": "Belge gönderildi, onay bekliyor.",
    "ocr": {
        "sure": 1.23,
        "satirlar": [
            "TEDAŞ ELEKTRİK DAĞITIM A.Ş.",
            "Fatura No: 2025-123456",
            "Tarih: 15.03.2025",
            "Müşteri No: 12345678",
            "Tüketim: 450 kWh",
            "Tutar: 1.234,56 TL",
            "KDV: 222,22 TL",
            "TOPLAM: 1.456,78 TL"
        ],
        "bulunan_tutarlar": [
            {"raw": "1.234,56 TL", "value": 1234.56, "tip": "ara_toplam"},
            {"raw": "222,22 TL", "value": 222.22, "tip": "kdv"},
            {"raw": "1.456,78 TL", "value": 1456.78, "tip": "genel_toplam"}
        ],
        "bulunan_tarihler": [
            {"raw": "15.03.2025", "value": "2025-03-15"}
        ],
        "oneri": {
            "tur": "GİDER",
            "kategori": "ELEKTRİK",
            "tutar": 1456.78,
            "tarih": "2025-03-15",
            "aciklama": "TEDAŞ ELEKTRİK DAĞITIM A.Ş."
        }
    }
}
```

### GET `/belge/bekleyenler`

Yönetici için bekleyen belgeleri listeler.

**Header:** `Authorization: Bearer <token>` (rol: muhasebeci, yonetici, admin)

**Yanıt:**
```json
{
    "success": true,
    "toplam": 3,
    "belgeler": [
        {
            "id": 42,
            "gonderen_ad_soyad": "Ahmet Yılmaz",
            "gonderen_rol": "uye",
            "belge_turu": "FATURA",
            "onerilen_tur": "GİDER",
            "onerilen_kategori": "ELEKTRİK",
            "onerilen_tutar": 1456.78,
            "onerilen_tarih": "2025-03-15",
            "gonderen_notu": "Mart ayı elektrik faturası",
            "durum": "beklemede",
            "created_at": "2025-03-20T14:30:00"
        },
        {
            "id": 41,
            "gonderen_ad_soyad": "Mehmet Demir",
            "belge_turu": "FİŞ",
            "onerilen_tur": "GİDER",
            "onerilen_kategori": "KIRTASIYE",
            "onerilen_tutar": 89.50,
            "durum": "beklemede",
            "created_at": "2025-03-20T10:15:00"
        }
    ]
}
```

### GET `/belge/{id}`

Belge detayı (OCR sonuçları dahil).

**Yanıt:**
```json
{
    "success": true,
    "belge": {
        "id": 42,
        "gonderen": {
            "id": 5,
            "ad_soyad": "Ahmet Yılmaz",
            "rol": "uye"
        },
        "belge_turu": "FATURA",
        "dosya_url": "/uploads/belge_42.jpg",
        "gonderen_notu": "Mart ayı elektrik faturası",
        "durum": "beklemede",
        "created_at": "2025-03-20T14:30:00",
        
        "ocr": {
            "raw_text": "TEDAŞ ELEKTRİK DAĞITIM A.Ş.\nFatura No: 2025-123456\n...",
            "satirlar": [
                {"no": 1, "text": "TEDAŞ ELEKTRİK DAĞITIM A.Ş.", "secili": false},
                {"no": 2, "text": "Fatura No: 2025-123456", "secili": false},
                {"no": 3, "text": "Tarih: 15.03.2025", "secili": true, "tip": "tarih"},
                {"no": 4, "text": "Müşteri No: 12345678", "secili": false},
                {"no": 5, "text": "Tüketim: 450 kWh", "secili": false},
                {"no": 6, "text": "Tutar: 1.234,56 TL", "secili": false, "tip": "tutar"},
                {"no": 7, "text": "KDV: 222,22 TL", "secili": false, "tip": "tutar"},
                {"no": 8, "text": "TOPLAM: 1.456,78 TL", "secili": true, "tip": "tutar"}
            ],
            "bulunan_tutarlar": [
                {"raw": "1.234,56 TL", "value": 1234.56},
                {"raw": "222,22 TL", "value": 222.22},
                {"raw": "1.456,78 TL", "value": 1456.78}
            ],
            "bulunan_tarihler": [
                {"raw": "15.03.2025", "value": "2025-03-15"}
            ]
        },
        
        "oneri": {
            "tur": "GİDER",
            "kategori": "ELEKTRİK",
            "tutar": 1456.78,
            "tarih": "2025-03-15",
            "aciklama": "TEDAŞ ELEKTRİK DAĞITIM A.Ş."
        }
    },
    
    "secenekler": {
        "gelir_kategorileri": ["AİDAT", "KİRA", "BAĞIŞ", "DÜĞÜN", "KINA", "TOPLANTI", "DAVET", "DİĞER"],
        "gider_kategorileri": ["ELEKTRİK", "SU", "DOĞALGAZ", "İNTERNET", "TELEFON", "KİRA", "TEMİZLİK", "BAKIM-ONARIM", "KIRTASIYE", "ORGANİZASYON", "YEMEK", "ULAŞIM", "PERSONEL", "VERGİ-HARÇ", "SİGORTA", "DİĞER"],
        "kasalar": [
            {"id": 1, "ad": "BANKA TL", "para_birimi": "TL"},
            {"id": 2, "ad": "DERNEK KASA TL", "para_birimi": "TL"}
        ]
    }
}
```

### POST `/belge/{id}/onayla`

Belgeyi onaylar ve gelir/gider kaydı oluşturur.

**Header:** `Authorization: Bearer <token>` (rol: muhasebeci, yonetici, admin)

**İstek:**
```json
{
    "tur": "GİDER",
    "kategori": "ELEKTRİK",
    "tutar": 1456.78,
    "tarih": "2025-03-15",
    "aciklama": "Mart 2025 elektrik faturası - TEDAŞ",
    "kasa": "BANKA TL",
    "onay_notu": "Fatura kontrol edildi, uygun."
}
```

**Yanıt:**
```json
{
    "success": true,
    "message": "Belge onaylandı ve gider kaydı oluşturuldu.",
    "kayit": {
        "tip": "gider",
        "id": 156,
        "tutar": 1456.78
    }
}
```

### POST `/belge/{id}/reddet`

Belgeyi reddeder.

**İstek:**
```json
{
    "red_notu": "Belge bulanık, lütfen tekrar çekin."
}
```

### GET `/belge/gonderilerim`

Üyenin kendi gönderdiği belgeleri listeler.

**Header:** `Authorization: Bearer <token>`

---

# 4. OCR MOTOR DETAYLARI

## 4.1 Tutar Algılama

```python
TUTAR_PATTERNS = [
    # Etiketli tutarlar (öncelikli)
    (r'(?:TOPLAM|GENEL\s*TOPLAM|NET|G\.TOPLAM)[:\s]*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})', 'genel_toplam'),
    (r'(?:KDV\s*DAHİL|KDV\s*HARİÇ)[:\s]*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})', 'kdv_dahil'),
    (r'(?:TUTAR|BEDEL|FİYAT)[:\s]*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})', 'tutar'),
    
    # Para birimi ile
    (r'([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})\s*(?:TL|₺|TRY)', 'tl_tutar'),
    (r'(?:TL|₺|TRY)\s*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})', 'tl_tutar'),
    
    # Ondalık tutarlar
    (r'([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})', 'tr_format'),    # 1.234,56
    (r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})', 'en_format'),    # 1,234.56
]
```

## 4.2 Tarih Algılama

```python
TARIH_PATTERNS = [
    (r'(\d{2})[./](\d{2})[./](\d{4})', 'DMY'),      # 15.03.2025
    (r'(\d{4})[-/](\d{2})[-/](\d{2})', 'YMD'),      # 2025-03-15
    (r'(\d{2})[-/](\d{2})[-/](\d{2})', 'DMY_SHORT'), # 15/03/25
]
```

## 4.3 Kategori Tahmini

```python
KATEGORI_KEYWORDS = {
    'ELEKTRİK': ['elektrik', 'tedaş', 'enerjisa', 'enerji', 'kwh', 'sayaç', 'tüketim'],
    'SU': ['su', 'iski', 'aski', 'su idaresi', 'metreküp', 'm³', 'sayaç'],
    'DOĞALGAZ': ['doğalgaz', 'igdaş', 'başkentgaz', 'dogalgaz', 'naturelgaz', 'sm³'],
    'İNTERNET': ['internet', 'fiber', 'adsl', 'mbps', 'gbps'],
    'TELEFON': ['telefon', 'gsm', 'turk telekom', 'vodafone', 'turkcell'],
    'KİRA': ['kira', 'kiralama', 'gayrimenkul', 'kontrat'],
    'TEMİZLİK': ['temizlik', 'hijyen', 'deterjan'],
    'BAKIM-ONARIM': ['bakım', 'onarım', 'tamir', 'servis', 'tadilat'],
    'KIRTASIYE': ['kırtasiye', 'kalem', 'kağıt', 'toner', 'kartuş'],
    'YEMEK': ['restaurant', 'restoran', 'cafe', 'lokanta', 'yemek', 'kebap'],
    'ULAŞIM': ['taksi', 'uber', 'benzin', 'akaryakıt', 'otopark'],
    'PERSONEL': ['maaş', 'ücret', 'personel', 'işçilik'],
    'VERGİ-HARÇ': ['vergi', 'harç', 'belediye', 'resmi'],
    'SİGORTA': ['sigorta', 'poliçe', 'prim'],
}

def tahmin_kategori(text: str) -> tuple[str, float]:
    """Metinden kategori tahmin et, güven skoru ile döndür"""
    text_lower = text.lower()
    scores = {}
    
    for kategori, keywords in KATEGORI_KEYWORDS.items():
        score = sum(2 if kw in text_lower else 0 for kw in keywords)
        if score > 0:
            scores[kategori] = score
    
    if not scores:
        return ('DİĞER', 0.3)
    
    best = max(scores, key=scores.get)
    confidence = min(scores[best] / 10, 1.0)
    return (best, confidence)
```

---

# 5. WEB ARAYÜZÜ

## 5.1 Üye/Personel Ekranı (Mobil)

```
┌──────────────────────────────────────┐
│  🏛️ BADER              Ahmet Y. 👤  │
├──────────────────────────────────────┤
│                                      │
│  ╔══════════════════════════════╗   │
│  ║                              ║   │
│  ║       📸 BELGE GÖNDER        ║   │
│  ║                              ║   │
│  ║   ┌────────┐  ┌────────┐    ║   │
│  ║   │ 📷     │  │ 📁     │    ║   │
│  ║   │ Kamera │  │ Galeri │    ║   │
│  ║   └────────┘  └────────┘    ║   │
│  ║                              ║   │
│  ╚══════════════════════════════╝   │
│                                      │
│  📋 Gönderdiğim Belgeler             │
│  ┌──────────────────────────────┐   │
│  │ ✅ Elektrik Faturası         │   │
│  │    15.03.2025 • ₺1.456,78    │   │
│  │    Onaylandı                 │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │ ⏳ Su Faturası                │   │
│  │    18.03.2025 • ₺256,80      │   │
│  │    Onay bekliyor             │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │ ❌ Market Fişi               │   │
│  │    10.03.2025 • ₺89,50       │   │
│  │    Reddedildi: Bulanık       │   │
│  └──────────────────────────────┘   │
│                                      │
└──────────────────────────────────────┘
```

## 5.2 Yönetici Onay Paneli

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│  🏛️ BADER Yönetim Paneli                                           Admin 👤 Çıkış │
├────────────────────────────────────────────────────────────────────────────────────┤
│  📊 Dashboard  │  📄 Bekleyen Belgeler (3)  │  💰 Gelirler  │  💸 Giderler         │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌─────────────────────────────┐   ┌──────────────────────────────────────────┐  │
│  │ 📄 Bekleyen Belgeler        │   │ 📋 Belge Detayı                #42       │  │
│  ├─────────────────────────────┤   ├──────────────────────────────────────────┤  │
│  │                             │   │                                          │  │
│  │ ⏳ Elektrik Faturası        │   │  ┌────────────────────────────────────┐ │  │
│  │    Ahmet Yılmaz • 2s önce   │   │  │                                    │ │  │
│  │    💰 ₺1.456,78   ◀ SEÇİLİ  │   │  │     [BELGE GÖRÜNTÜSÜ]             │ │  │
│  │                             │   │  │                                    │ │  │
│  │ ⏳ Su Faturası              │   │  └────────────────────────────────────┘ │  │
│  │    Mehmet D. • 5s önce      │   │                                          │  │
│  │    💰 ₺256,80               │   │  📝 OCR Çıktısı (satır seçilebilir):    │  │
│  │                             │   │  ┌────────────────────────────────────┐ │  │
│  │ ⏳ Kırtasiye Fişi           │   │  │ No │ Satır                    │ 🎯 │ │  │
│  │    Ali K. • 1g önce         │   │  ├────────────────────────────────────┤ │  │
│  │    💰 ₺89,50                │   │  │ 1  │ TEDAŞ ELEKTRİK A.Ş.     │ ☐  │ │  │
│  │                             │   │  │ 2  │ Fatura No: 2025-123     │ ☐  │ │  │
│  └─────────────────────────────┘   │  │ 3  │ Tarih: 15.03.2025       │ 📅 │ │  │
│                                    │  │ 4  │ Müşteri: 12345678       │ ☐  │ │  │
│                                    │  │ 5  │ Tüketim: 450 kWh        │ ☐  │ │  │
│                                    │  │ 6  │ TOPLAM: 1.456,78 TL     │ 💰 │ │  │
│                                    │  └────────────────────────────────────┘ │  │
│                                    │                                          │  │
│                                    │  💰 Bulunan Tutarlar:                    │  │
│                                    │  ◉ ₺1.456,78 (TOPLAM)                    │  │
│                                    │  ○ ₺1.234,56 (Tutar)                     │  │
│                                    │  ○ ₺222,22 (KDV)                         │  │
│                                    │                                          │  │
│                                    │  ──────────────────────────────────────  │  │
│                                    │                                          │  │
│                                    │  Kayıt Türü:  ◉ GİDER   ○ GELİR          │  │
│                                    │                                          │  │
│                                    │  Kategori:    [⚡ ELEKTRİK          ▼]   │  │
│                                    │                                          │  │
│                                    │  Tutar:       [₺ 1.456,78            ]   │  │
│                                    │                                          │  │
│                                    │  Tarih:       [2025-03-15            ]   │  │
│                                    │                                          │  │
│                                    │  Açıklama:    [Mart 2025 elektrik    ]   │  │
│                                    │                                          │  │
│                                    │  Kasa:        [BANKA TL              ▼]   │  │
│                                    │                                          │  │
│                                    │  Not:         [Fatura kontrol edildi ]   │  │
│                                    │                                          │  │
│                                    │  ┌─────────────┐  ┌─────────────────┐   │  │
│                                    │  │ ❌ REDDET   │  │ ✅ ONAYLA       │   │  │
│                                    │  └─────────────┘  └─────────────────┘   │  │
│                                    └──────────────────────────────────────────┘  │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 6. YETKİLENDİRME

## 6.1 Rol Matrisi

| İşlem | Üye | Personel | Muhasebeci | Yönetici | Admin |
|-------|-----|----------|------------|----------|-------|
| Giriş yapma | ✅ | ✅ | ✅ | ✅ | ✅ |
| Belge gönderme | ✅ | ✅ | ✅ | ✅ | ✅ |
| Kendi belgelerini görme | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tüm bekleyen belgeleri görme | ❌ | ❌ | ✅ | ✅ | ✅ |
| Belge onaylama/reddetme | ❌ | ❌ | ✅ | ✅ | ✅ |
| Onaylanan kaydı düzenleme | ❌ | ❌ | ✅ | ✅ | ✅ |
| Kullanıcı yönetimi | ❌ | ❌ | ❌ | ✅ | ✅ |
| Sistem ayarları | ❌ | ❌ | ❌ | ❌ | ✅ |

---

# 7. ENTEGRASYON

## 7.1 Masaüstü Uygulaması ile Senkronizasyon

Masaüstü uygulama (`server_client.py`) mevcut API'yi kullanıyor. Yeni endpointler eklendikten sonra:

1. **Bekleyen belgeler widget'ı** masaüstüne eklenebilir
2. **Push notification** ile yeni belge bildirimi
3. **Onaylanan kayıtlar** otomatik olarak lokal DB'ye senkronize

## 7.2 Mevcut Sistemle Uyum

### Gelir Kaydı Oluşturma
```python
# Onay sonrası gelir oluşturma
def onayla_ve_kaydet(belge_id, onay_verileri):
    # 1. Bekleyen belgeyi güncelle
    # 2. Gelir/gider kaydı oluştur (mevcut API kullanılır)
    # 3. Belgeye referans ekle
    
    if onay_verileri['tur'] == 'GELİR':
        kayit_id = gelir_ekle(
            tarih=onay_verileri['tarih'],
            gelir_turu=onay_verileri['kategori'],
            aciklama=onay_verileri['aciklama'],
            tutar=onay_verileri['tutar'],
            kasa=onay_verileri['kasa']
        )
    else:
        kayit_id = gider_ekle(...)
    
    return kayit_id
```

---

# 8. UYGULAMA DURUMU

## ✅ Tamamlanan Fazlar

### Faz 1: Veritabanı ✅
- [x] `web_kullanicilar` tablosu - Oluşturuldu
- [x] `bekleyen_belgeler` tablosu - Oluşturuldu
- [x] Demo kullanıcılar - admin, muhasebe, ahmet, mehmet

### Faz 2: API Endpointleri ✅ (v3.0.0)
- [x] `/auth/login`, `/auth/logout`, `/auth/me`
- [x] `/belge/gonder` - OCR entegre, tutar/tarih/kategori tahmini
- [x] `/belge/bekleyenler` - Admin için liste
- [x] `/belge/{id}` - Detay + OCR sonuçları
- [x] `/belge/{id}/onayla` - Gelir/Gider kaydı oluşturur
- [x] `/belge/{id}/reddet` - Not ile reddet
- [x] `/belge/gonderilerim` - Üyenin belgeleri

### Faz 3: Web Arayüzü ✅
- [x] Üye giriş sayfası - Modern dark tema
- [x] Belge gönderme - Drag & drop + kamera
- [x] OCR sonuç önizleme - Tutar/tarih/kategori
- [x] Bekleyen belgeler listesi - Admin paneli
- [x] Belge detay & onay formu - Düzenlenebilir alanlar

## 🔗 Erişim Bilgileri

| Sayfa | URL |
|-------|-----|
| Web Panel | http://157.90.154.48:8080/belge.html |
| API | http://157.90.154.48:8080/api/health |

## 👤 Demo Hesaplar

| Kullanıcı | Şifre | Rol | Yetkiler |
|-----------|-------|-----|----------|
| ahmet | uye123 | Üye | Belge gönder, kendi belgelerini gör |
| mehmet | uye123 | Üye | Belge gönder, kendi belgelerini gör |
| muhasebe | muhasebe123 | Muhasebeci | + Onay/Red yapabilir |
| admin | admin123 | Admin | Tüm yetkiler |

## 📋 Kalan İşler

- [ ] Mobil uygulama (PWA)
- [ ] Push bildirimler
- [ ] E-posta bildirimleri
- [ ] Masaüstü uygulamaya entegrasyon

---

# 9. TEKNİK NOTLAR

## 9.1 Güvenlik
- JWT token, 24 saat geçerli
- HTTPS zorunlu (production)
- Rate limiting: 10 belge/saat/kullanıcı
- Dosya boyutu: max 10MB
- Desteklenen formatlar: JPEG, PNG

## 9.2 Performans
- Görsel sıkıştırma (upload öncesi)
- OCR timeout: 30 saniye
- Thumbnail oluşturma (liste için)

## 9.3 Saklama
- Onaylanan belgeler: `/opt/bader-server/uploads/approved/`
- Reddedilen belgeler: 30 gün sonra otomatik sil
- Bekleyen belgeler: 7 gün sonra uyarı

---

*Son Güncelleme: 29 Aralık 2025*
