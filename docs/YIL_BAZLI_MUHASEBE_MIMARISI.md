# 📊 YILLAR ARASI MALİ HAREKET MİMARİSİ
## Çok Yıllık Ödeme ve Tahakkuk Sistemi

---

## 🎯 PROBLEM TANIMI

### Senaryo
```
Üye: Ahmet Yılmaz
Tarih: 15 Ocak 2025
Ödeme: 1000 TL (10 yıllık aidat: 2025-2034)
Yıllık Aidat: 100 TL

SORU:
- Para fiziksel olarak 2025 kasasına girer ✅
- Ama 2026, 2027... 2034 için de ödeme yapılmış
- 2026'nın mali tablosunda bu para nasıl görünmeli?
- 2025 kasası eksi ise → Gelecek yılın parasını mı yemiş oluyor?
```

### Kritik Noktalar
1. **Fiziksel Para ≠ Muhasebe Yılı**
2. **Tahsil Yılı ≠ Ait Olduğu Yıl**
3. **Cari Açık Riski**: 2025 kasası eksiyse, 2026'nın parasını kullanmış olabilir
4. **Devir İşlemi**: Hangi yıl ne kadar devredecek?
5. **Virman**: Yıllar arası virman nasıl olacak?

---

## 🏗️ MEVCUT SİSTEM ANALİZİ

### 1. GELİRLER TABLOSU (Mevcut)
```sql
CREATE TABLE gelirler (
    gelir_id INTEGER PRIMARY KEY,
    tarih DATE NOT NULL,              -- Tahsil tarihi
    gelir_turu TEXT,                  -- AİDAT, KİRA, vs.
    tutar REAL NOT NULL,
    kasa_id INTEGER,
    aidat_id INTEGER                  -- Aidat bağlantısı
)
```

**SORUN:**
- ✅ `tarih` var → Paranın geldiği gün
- ❌ `ait_oldugu_yil` yok → Bu gelir hangi yıla ait?

### 2. AİDAT TAKİP (Mevcut)
```sql
CREATE TABLE aidat_takip (
    aidat_id INTEGER PRIMARY KEY,
    uye_id INTEGER,
    yil INTEGER,                      -- 2025, 2026, vs.
    yillik_aidat_tutari REAL,
    odenecek_tutar REAL,
    durum TEXT                        -- Tamamlandı/Eksik/Kısmi
)

CREATE TABLE aidat_odemeleri (
    odeme_id INTEGER PRIMARY KEY,
    aidat_id INTEGER,                 -- Tek yıl bağlantısı
    tarih DATE,
    tutar REAL
)
```

**SORUN:**
- ✅ Yıl bazlı takip var
- ❌ Tek ödemede birden fazla yıl ödenemez
- ❌ 2025'te 2026 için ödeme yaparsan → Sistem karışır

### 3. KASA SİSTEMİ (Mevcut)
```python
def kasa_bakiye_hesapla(kasa_id, tarih=None):
    bakiye = devir_bakiye
    bakiye += gelirler_toplam(kasa_id, tarih)
    bakiye -= giderler_toplam(kasa_id, tarih)
    bakiye -= virman_giden(kasa_id, tarih)
    bakiye += virman_gelen(kasa_id, tarih)
    return bakiye
```

**SORUN:**
- ✅ Fiziksel para hesabı doğru
- ❌ Hangi gelir hangi yıla ait bilmiyor
- ❌ 2025 kasasında 2026'nın parası da var ama ayrım yok

### 4. DEVİR SİSTEMİ (Mevcut)
```python
def yil_sonu_devir(yil):
    # Her kasa için net bakiye hesapla
    # Yeni yıl için devir_bakiye olarak kaydet
```

**SORUN:**
- ❌ Gelecek yıl tahakkukları hesaba katmıyor
- ❌ "Gerçek sermaye" vs "Kağıt sermaye" ayrımı yok

---

## ✨ YENİ MİMARİ ÖNERİSİ

### KAVRAMLAR

#### 1. TAHSİL YILI vs AİT OLDUĞU YIL
```
Tahsil Yılı: Paranın fiziksel olarak kasaya girdiği yıl
Ait Olduğu Yıl: Bu gelirin hangi yılın hasılatı olduğu

Örnek:
- 2025'te tahsil edildi → Tahsil Yılı = 2025
- Ama 2026 aidatı → Ait Olduğu Yıl = 2026
```

#### 2. TAHAKKUK MUHASEBESİ
```
Tahakkuk: Henüz gerçekleşmemiş ama garantilenmiş gelir/gider

Gelir Tahakkuku (Pasif - Kaynak):
- 2025'te alınan 2026 parası = Borç gibiydir
- "Bu para gelecek yıla aittir" demektir

Gider Tahakkuku (Aktif - Varlık):
- 2026 için 2025'te yapılan ödeme = Peşin ödeme
- "Bu parayı gelecek yıl için verdik" demektir
```

#### 3. GERİ İADE/ERKEN ÖDEME
```
Erken Ödeme: Üye 2025'te 2026-2034 için ödedi
- Para 2025 kasasında ✅
- Ama 2026-2034'ün "Ödenmiş Aidatı" ✅
- 2025 mali tablosunda "Gelir Tahakkuku" olarak görünür

Geri İade Riski: Üye 2026'da ayrılırsa
- 2027-2034 parasını iade etmemiz gerekir
- Ama para 2025 kasasında kullanılmış olabilir
- = ZARAR riski
```

---

## 🗄️ YENİ VERİTABANI YAPISI

### 1. GELİRLER TABLOSU (GÜNCELLENMİŞ)

```sql
CREATE TABLE gelirler (
    gelir_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Tarih Bilgileri
    tahsil_tarihi DATE NOT NULL,           -- Paranın geldiği tarih
    ait_oldugu_yil INTEGER NOT NULL,       -- Bu gelir hangi yıla ait (2025, 2026)
    
    -- Mali Bilgiler
    gelir_turu TEXT NOT NULL,
    tutar REAL NOT NULL,
    kasa_id INTEGER NOT NULL,
    
    -- Tahakkuk Durumu
    tahakkuk_durumu TEXT DEFAULT 'NORMAL', -- 'NORMAL', 'PEŞİN', 'GERİYE_DÖNÜK'
    
    -- İlişkiler
    aidat_id INTEGER,
    coklu_odeme_grup_id TEXT,              -- Aynı ödemeden gelen kayıtlar
    
    -- Açıklama
    aciklama TEXT,
    notlar TEXT,
    
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Örnekler:**

**Normal Ödeme:**
```sql
INSERT INTO gelirler (tahsil_tarihi, ait_oldugu_yil, gelir_turu, tutar, tahakkuk_durumu)
VALUES ('2025-01-15', 2025, 'AİDAT', 100, 'NORMAL')
-- 2025'te tahsil → 2025'e ait → Normal
```

**Peşin Ödeme (Çok Yıllık):**
```sql
-- Tek ödemede 10 yıl
grup_id = 'GRUP_2025_001'

-- Her yıl için ayrı kayıt
INSERT INTO gelirler (tahsil_tarihi, ait_oldugu_yil, tutar, tahakkuk_durumu, coklu_odeme_grup_id)
VALUES 
  ('2025-01-15', 2025, 100, 'NORMAL', grup_id),    -- 2025 için
  ('2025-01-15', 2026, 100, 'PEŞİN', grup_id),      -- 2026 için peşin
  ('2025-01-15', 2027, 100, 'PEŞİN', grup_id),      -- 2027 için peşin
  ...
  ('2025-01-15', 2034, 100, 'PEŞİN', grup_id);      -- 2034 için peşin

-- Kasaya tek seferde girer: 1000 TL
-- Ama 10 ayrı gelir kaydı
```

**Geriye Dönük Ödeme:**
```sql
-- 2025'te 2024 borcunu ödüyor
INSERT INTO gelirler (tahsil_tarihi, ait_oldugu_yil, tutar, tahakkuk_durumu)
VALUES ('2025-01-15', 2024, 100, 'GERİYE_DÖNÜK')
-- Para 2025 kasasına giriyor ama 2024'ün geliri
```

### 2. GİDERLER TABLOSU (GÜNCELLENMİŞ)

```sql
CREATE TABLE giderler (
    gider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Tarih Bilgileri
    odeme_tarihi DATE NOT NULL,            -- Paranın çıktığı tarih
    ait_oldugu_yil INTEGER NOT NULL,       -- Bu gider hangi yıla ait
    
    -- Mali Bilgiler
    gider_turu TEXT NOT NULL,
    tutar REAL NOT NULL,
    kasa_id INTEGER NOT NULL,
    
    -- Tahakkuk Durumu
    tahakkuk_durumu TEXT DEFAULT 'NORMAL', -- 'NORMAL', 'PEŞİN', 'GERİYE_DÖNÜK'
    
    aciklama TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 3. AİDAT SİSTEMİ (GÜNCELLENMİŞ)

```sql
-- aidat_takip tablosu aynı kalıyor (yıl bazlı)

-- aidat_odemeleri tablosu güncelleniyor
CREATE TABLE aidat_odemeleri (
    odeme_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- ÇOK ÖNEMLİ: Birden fazla yıla bağlanabilir
    odeme_grup_id TEXT UNIQUE,             -- Tek ödemede birden fazla yıl
    
    tarih DATE NOT NULL,
    toplam_tutar REAL NOT NULL,            -- Toplam ödenen
    kasa_id INTEGER NOT NULL,
    
    aciklama TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Hangi ödeme hangi yıla ait
CREATE TABLE aidat_odeme_detay (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    odeme_grup_id TEXT NOT NULL,
    aidat_id INTEGER NOT NULL,             -- Hangi yıl
    tutar REAL NOT NULL,                   -- O yıl için ne kadar
    FOREIGN KEY (aidat_id) REFERENCES aidat_takip(aidat_id)
)
```

**Örnek Kullanım:**
```python
# 10 yıllık ödeme
odeme_grup_id = "ODEME_2025_001"

# Ana ödeme kaydı
INSERT INTO aidat_odemeleri (odeme_grup_id, tarih, toplam_tutar, kasa_id)
VALUES (odeme_grup_id, '2025-01-15', 1000, 1)

# Her yıl için detay
for yil in range(2025, 2035):
    aidat_id = get_or_create_aidat(uye_id, yil)
    
    INSERT INTO aidat_odeme_detay (odeme_grup_id, aidat_id, tutar)
    VALUES (odeme_grup_id, aidat_id, 100)
    
    # Gelir kaydı (yıl bazlı)
    tahakkuk = 'NORMAL' if yil == 2025 else 'PEŞİN'
    INSERT INTO gelirler (tahsil_tarihi, ait_oldugu_yil, tutar, tahakkuk_durumu)
    VALUES ('2025-01-15', yil, 100, tahakkuk)

# Kasa hareketi: Tek seferde +1000 TL
```

### 4. TAHAKKUK TABLOSU (YENİ)

```sql
CREATE TABLE tahakkuklar (
    tahakkuk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    tahakkuk_turu TEXT NOT NULL,           -- 'GELİR' veya 'GİDER'
    kaynak_tablo TEXT NOT NULL,            -- 'gelirler', 'giderler'
    kaynak_id INTEGER NOT NULL,
    
    tahsil_yili INTEGER NOT NULL,          -- Para hangi yılda alındı/verildi
    ait_oldugu_yil INTEGER NOT NULL,       -- Hangi yılın geliri/gideri
    
    tutar REAL NOT NULL,
    durum TEXT DEFAULT 'AKTİF',            -- 'AKTİF', 'KULLANILDI', 'İADE_EDİLDİ'
    
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Kullanım:**
```sql
-- 2025'te alınan 2026 parası
INSERT INTO tahakkuklar (tahakkuk_turu, kaynak_tablo, kaynak_id, tahsil_yili, ait_oldugu_yil, tutar)
VALUES ('GELİR', 'gelirler', 123, 2025, 2026, 100)

-- 2026 başında bu tahakkuk "kullanılır"
UPDATE tahakkuklar SET durum='KULLANILDI' WHERE tahakkuk_id=...
```

---

## 📊 MALİ TABLO HESAPLAMALARI

### 1. BİLANÇO (2025 Sonu)

#### VARLIKLAR
```
DÖNEN VARLIKLAR:
  Kasalar:                         10,000 TL  ← Fiziksel para
  Aidat Alacakları (2025):          2,000 TL  ← 2025 borçları
  Alacaklar:                        5,000 TL
  ----------------------------------------
  Toplam Dönen:                    17,000 TL

TOPLAM VARLIK:                     17,000 TL
```

#### KAYNAKLAR
```
KISA VADELİ YÜKÜMLÜLÜKLER:
  Verecekler (Borçlar):             3,000 TL
  Gelir Tahakkuku (2026-2034):      9,000 TL  ← Peşin alınan gelecek yıl paraları
  ----------------------------------------
  Toplam Kısa Vadeli:              12,000 TL

ÖZ KAYNAKLAR:
  Dernek Sermayesi:                 3,000 TL
  Dönem Karı:                       2,000 TL
  ----------------------------------------
  Toplam Öz Kaynak:                 5,000 TL

TOPLAM KAYNAK:                     17,000 TL
```

**Açıklama:**
- Kasada 10K var ama 9K'sı gelecek yıllara ait → "Borç" gibi
- Gerçek serbest para = 10K - 9K = 1K

### 2. GELİR TABLOSU (2025)

```sql
-- 2025'e ait gelirler (tahsil tarihi değil!)
SELECT SUM(tutar) FROM gelirler 
WHERE ait_oldugu_yil = 2025

-- Örnek:
2025 Aidat Gelirleri:              10,000 TL  ← Sadece 2025'e ait olanlar
2025 Kira Gelirleri:                5,000 TL
2025 Bağışlar:                      2,000 TL
----------------------------------------
TOPLAM GELİR (2025):               17,000 TL

2025 Giderler:                     15,000 TL
----------------------------------------
NET KAR:                            2,000 TL
```

**ÖNEMLI:** 2025'te tahsil edilen ama 2026'ya ait paralar → Gelir tablosuna GİRMEZ!

### 3. NAKİT AKIŞ (2025)

```
DÖNEM BAŞI NAKİT:                   3,000 TL

NAKİT GİRİŞLERİ:
  Tahsil Edilen Tüm Gelirler:      20,000 TL  ← Hangi yıla ait olursa olsun
  (2025: 10K + 2026-2034: 10K)
  
NAKİT ÇIKIŞLARI:
  Ödenen Tüm Giderler:             13,000 TL
  ----------------------------------------
NET NAKİT AKIŞI:                    7,000 TL

DÖNEM SONU NAKİT:                  10,000 TL  ✅ Kasayla eşleşir
```

### 4. TAHAKKUK RAPORU (Ek Rapor - YENİ)

```
2025 SONU İTİBARİYLE TAHAKKUK DURUMU

GELİR TAHAKKUKLARI (Peşin Alınan Gelecek Yıl Paraları):
┌─────┬────────┬────────────┐
│ Yıl │ Tutar  │ Durum      │
├─────┼────────┼────────────┤
│2026 │ 1,000  │ Aktif      │
│2027 │ 1,000  │ Aktif      │
│2028 │ 1,000  │ Aktif      │
│2029 │ 1,000  │ Aktif      │
│2030 │ 1,000  │ Aktif      │
│2031 │ 1,000  │ Aktif      │
│2032 │ 1,000  │ Aktif      │
│2033 │ 1,000  │ Aktif      │
│2034 │ 1,000  │ Aktif      │
└─────┴────────┴────────────┘
TOPLAM: 9,000 TL

UYARI: 
- Bu paralar kasada var ama 2025'in değil!
- 2025 sonu devir: 10,000 TL (fiziksel)
- Ama gerçek serbest: 1,000 TL (10K - 9K)
```

---

## 🔄 DEVİR SİSTEMİ (YENİ)

### Mevcut Devir (YANLIŞ)
```python
def yil_sonu_devir_ESKİ(yil):
    # Her kasa için
    net_bakiye = kasa_bakiye_hesapla(kasa_id, f"{yil}-12-31")
    
    # Yeni yıl kasasına devret
    UPDATE kasalar SET devir_bakiye = net_bakiye WHERE kasa_id=...
```

**SORUN:** Gelecek yıl tahakkuklarını hesaba katmıyor!

### Yeni Devir (DOĞRU)
```python
def yil_sonu_devir_YENİ(yil):
    """
    İki tip devir:
    1. Fiziksel Devir: Kasadaki gerçek para
    2. Serbest Devir: Gelecek yıllara ait tahakkuklar çıkarılmış
    """
    
    # 1. Fiziksel Devir (Kasadaki gerçek para)
    fiziksel_bakiye = kasa_bakiye_hesapla(kasa_id, f"{yil}-12-31")
    
    # 2. Gelecek yıl tahakkukları (2025'te alınan 2026+ paraları)
    gelir_tahakkuku = db.execute("""
        SELECT COALESCE(SUM(tutar), 0) FROM gelirler
        WHERE tahsil_tarihi <= ?
        AND ait_oldugu_yil > ?
        AND tahakkuk_durumu = 'PEŞİN'
    """, (f"{yil}-12-31", yil)).fetchone()[0]
    
    # 3. Geçmiş yıl tahakkukları (2026'da kullanılacak 2025 tahakkukları)
    gecmis_tahakkuk = db.execute("""
        SELECT COALESCE(SUM(tutar), 0) FROM gelirler
        WHERE tahsil_tarihi <= ?
        AND ait_oldugu_yil = ?
        AND tahakkuk_durumu = 'GERİYE_DÖNÜK'
    """, (f"{yil}-12-31", yil+1)).fetchone()[0]
    
    # 4. Serbest Bakiye
    serbest_bakiye = fiziksel_bakiye - gelir_tahakkuku + gecmis_tahakkuk
    
    # 5. Devir kayıtları
    db.execute("""
        UPDATE kasalar SET 
            devir_bakiye = ?,
            serbest_devir_bakiye = ?,
            tahakkuk_toplami = ?
        WHERE kasa_id = ?
    """, (fiziksel_bakiye, serbest_bakiye, gelir_tahakkuku, kasa_id))
    
    # 6. Uyarı: Serbest bakiye negatifse
    if serbest_bakiye < 0:
        uyari_olustur(
            baslik="CARİ AÇIK UYARISI",
            mesaj=f"{yil} yılı sonu kasası negatif! "
                  f"Gelecek yılların parasını kullanmış durumdasınız. "
                  f"Fiziksel: {fiziksel_bakiye:,.2f} TL "
                  f"Serbest: {serbest_bakiye:,.2f} TL"
        )
```

**Örnek Hesaplama:**
```
2025 Sonu:
- Fiziksel Kasa:           10,000 TL
- Gelir Tahakkuku (2026+): -9,000 TL  (gelecek yıllara ait)
- Serbest Bakiye:           1,000 TL  ← Gerçek sermaye

2026'ya Devir:
- Fiziksel Devir:          10,000 TL  (kasada ne varsa)
- Tahakkuk Kullanım:        1,000 TL  (2026'ya ait olan)
- 2026 Başlangıç:          10,000 TL (fiziksel) + 1,000 TL (tahakkuk)
```

---

## 🔀 VİRMAN SİSTEMİ (GÜNCELLENMİŞ)

### Mevcut Virman (YANLIŞ)
```python
def virman_yap(gonderen_kasa, alan_kasa, tutar):
    # Sadece para transferi
    gonderen -= tutar
    alan += tutar
```

**SORUN:** Tahakkukları transfer etmiyor!

### Yeni Virman (DOĞRU)
```python
def virman_yap(gonderen_kasa, alan_kasa, tutar, tahakkuk_ile=False):
    """
    tahakkuk_ile = True: Gelecek yıl tahakkuklarını da transfer et
    tahakkuk_ile = False: Sadece serbest parayı transfer et (default)
    """
    
    if not tahakkuk_ile:
        # Normal virman: Sadece serbest para
        serbest = kasa_serbest_bakiye(gonderen_kasa)
        
        if tutar > serbest:
            raise Exception(
                f"Yetersiz serbest bakiye! "
                f"İstenen: {tutar:,.2f} TL "
                f"Serbest: {serbest:,.2f} TL "
                f"(Fiziksel: {kasa_bakiye(gonderen_kasa):,.2f} TL ama "
                f"{kasa_bakiye(gonderen_kasa) - serbest:,.2f} TL gelecek yıllara ait)"
            )
        
        # Para transferi
        virman_kaydi_olustur(gonderen_kasa, alan_kasa, tutar)
    
    else:
        # Tahakkuklu virman: Gelecek yıl tahakkuklarını da taşı
        
        # 1. Para transferi
        virman_kaydi_olustur(gonderen_kasa, alan_kasa, tutar)
        
        # 2. Tahakkuk transferi
        tahakkuklar = db.execute("""
            SELECT * FROM tahakkuklar
            WHERE kaynak_tablo = 'gelirler'
            AND tahsil_yili <= CURRENT_YEAR
            AND ait_oldugu_yil > CURRENT_YEAR
            AND durum = 'AKTİF'
        """).fetchall()
        
        for tahakkuk in tahakkuklar:
            # Gelir kaydını güncelle (kasa değiştir)
            db.execute("""
                UPDATE gelirler
                SET kasa_id = ?
                WHERE gelir_id = ?
            """, (alan_kasa, tahakkuk['kaynak_id']))
```

---

## 📱 KULLANICI ARAYÜZÜ ÖNERİLERİ

### 1. ÇOK YILLIK ÖDEME DİALOĞU

```
┌────────────────────────────────────────────┐
│ ÇOK YILLIK AİDAT ÖDEMESİ                   │
├────────────────────────────────────────────┤
│ Üye: Ahmet Yılmaz (#1234)                  │
│ Yıllık Aidat: 100 TL                       │
│                                            │
│ Başlangıç Yılı: [2025 ▼]                  │
│ Bitiş Yılı:     [2034 ▼]                  │
│                                            │
│ Ödeme Özeti:                               │
│ ┌────────────────────────────────────────┐ │
│ │ 2025: 100 TL ✓                         │ │
│ │ 2026: 100 TL (Peşin)                   │ │
│ │ 2027: 100 TL (Peşin)                   │ │
│ │ ...                                    │ │
│ │ 2034: 100 TL (Peşin)                   │ │
│ │                                        │ │
│ │ TOPLAM: 1,000 TL                       │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ Kasa: [Ana Kasa ▼]                        │
│ Tarih: [15/01/2025]                       │
│                                            │
│ ⚠️  UYARI: Bu ödeme 2025 kasasına         │
│     girecektir ama 2026-2034 için de      │
│     aidat ödenmiş sayılacaktır.           │
│                                            │
│ [💾 Kaydet] [❌ İptal]                    │
└────────────────────────────────────────────┘
```

### 2. KASA DETAY EKRANI (YENİ)

```
┌────────────────────────────────────────────┐
│ ANA KASA - 2025 YILI                       │
├────────────────────────────────────────────┤
│                                            │
│ FİZİKSEL BAKİYE:      10,000 TL           │
│                                            │
│ TAHAKKUK DURUMU:                           │
│ ├─ Gelecek Yıl Gelirleri: -9,000 TL      │
│ ├─ Geçmiş Yıl Alacakları: +500 TL        │
│ └─ Net Tahakkuk:          -8,500 TL      │
│                                            │
│ SERBEST BAKİYE:        1,500 TL ✅        │
│                                            │
│ ┌──────────────────────────────────────┐  │
│ │ GELECEK YIL TAHAKKUKLARİ:            │  │
│ │ 2026: 1,000 TL (10 üye)              │  │
│ │ 2027: 800 TL (8 üye)                 │  │
│ │ 2028: 600 TL (6 üye)                 │  │
│ │ ...                                  │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ [📊 Detay Rapor] [⚠️ Tahakkuk Listesi]   │
└────────────────────────────────────────────┘
```

### 3. DEVİR ONAY EKRANI (GÜNCELLENMİŞ)

```
┌────────────────────────────────────────────┐
│ 2025 YILI KAPANIŞ ONAY                     │
├────────────────────────────────────────────┤
│                                            │
│ ANA KASA:                                  │
│ ├─ Fiziksel Bakiye:    10,000 TL          │
│ ├─ Tahakkuk:           -9,000 TL          │
│ └─ Serbest Bakiye:      1,000 TL          │
│                                            │
│ 2026'YA DEVREDİLECEK:                      │
│ ├─ Fiziksel:           10,000 TL          │
│ ├─ 2026 Tahakkuku:      1,000 TL          │
│ └─ Toplam Kullanılabilir: 11,000 TL       │
│                                            │
│ ⚠️  UYARILAR:                              │
│ • Serbest bakiye düşük!                   │
│ • 9,000 TL gelecek yıllara ait            │
│ • Üyelerin ayrılma riski var              │
│                                            │
│ [✅ Onayla ve Devret] [❌ İptal]          │
└────────────────────────────────────────────┘
```

### 4. TAHAKKUK RAPORU (YENİ)

```
┌────────────────────────────────────────────┐
│ GELİR TAHAKKUK RAPORU (2025)               │
├────────────────────────────────────────────┤
│                                            │
│ Filtre: [Tüm Yıllar ▼] [Kasa: Tümü ▼]    │
│                                            │
│ ┌──────────────────────────────────────┐  │
│ │Yıl │Üye       │Tutar│Tahsil │Durum  │  │
│ ├────┼──────────┼─────┼────────┼───────┤  │
│ │2026│Ahmet Y.  │100  │2025-01 │Aktif  │  │
│ │2026│Mehmet K. │100  │2025-02 │Aktif  │  │
│ │2027│Ahmet Y.  │100  │2025-01 │Aktif  │  │
│ │2027│Ayşe T.   │100  │2025-03 │İade   │  │
│ │...                                    │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ TOPLAM TAHAKKUK:        9,000 TL          │
│ AKTİF:                  8,500 TL          │
│ İADE EDİLENLER:          -500 TL          │
│                                            │
│ [📥 Excel] [🔄 Yenile]                    │
└────────────────────────────────────────────┘
```

---

## 🧮 PYTHON SINIF YAPISI

### 1. YeniGelirYoneticisi

```python
class GelirYoneticisi:
    
    def gelir_ekle(self, gelir_turu: str, tutar: float, kasa_id: int,
                   tahsil_tarihi: str = None, ait_oldugu_yil: int = None,
                   tahakkuk_durumu: str = 'NORMAL', **kwargs) -> int:
        """
        ait_oldugu_yil: Belirtilmezse tahsil_tarihi'nin yılı alınır
        tahakkuk_durumu: 'NORMAL', 'PEŞİN', 'GERİYE_DÖNÜK'
        """
        if tahsil_tarihi is None:
            tahsil_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        if ait_oldugu_yil is None:
            ait_oldugu_yil = int(tahsil_tarihi[:4])
        
        self.db.cursor.execute("""
            INSERT INTO gelirler 
            (tahsil_tarihi, ait_oldugu_yil, gelir_turu, tutar, 
             kasa_id, tahakkuk_durumu, ...)
            VALUES (?, ?, ?, ?, ?, ?, ...)
        """, (tahsil_tarihi, ait_oldugu_yil, gelir_turu, tutar,
              kasa_id, tahakkuk_durumu, ...))
        
        gelir_id = self.db.cursor.lastrowid
        
        # Tahakkuk kaydı (eğer peşin ödeme ise)
        if tahakkuk_durumu == 'PEŞİN':
            self._tahakkuk_kaydet('GELİR', gelir_id, 
                                 int(tahsil_tarihi[:4]), ait_oldugu_yil, tutar)
        
        self.db.commit()
        return gelir_id
    
    def coklu_yil_gelir_ekle(self, gelir_turu: str, kasa_id: int,
                             baslangic_yil: int, bitis_yil: int,
                             yillik_tutar: float, tahsil_tarihi: str = None,
                             uye_id: int = None) -> str:
        """
        Çok yıllık ödeme (örn: 10 yıllık aidat)
        
        Returns: odeme_grup_id
        """
        if tahsil_tarihi is None:
            tahsil_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        tahsil_yili = int(tahsil_tarihi[:4])
        odeme_grup_id = f"GRUP_{tahsil_yili}_{self._get_next_grup_no()}"
        
        toplam_tutar = 0
        gelir_idler = []
        
        for yil in range(baslangic_yil, bitis_yil + 1):
            # Tahakkuk durumu
            if yil == tahsil_yili:
                tahakkuk = 'NORMAL'
            elif yil < tahsil_yili:
                tahakkuk = 'GERİYE_DÖNÜK'
            else:
                tahakkuk = 'PEŞİN'
            
            # Gelir kaydı
            gelir_id = self.gelir_ekle(
                gelir_turu=gelir_turu,
                tutar=yillik_tutar,
                kasa_id=kasa_id,
                tahsil_tarihi=tahsil_tarihi,
                ait_oldugu_yil=yil,
                tahakkuk_durumu=tahakkuk,
                coklu_odeme_grup_id=odeme_grup_id
            )
            
            gelir_idler.append(gelir_id)
            toplam_tutar += yillik_tutar
        
        # Aidat bağlantısı (eğer üye varsa)
        if uye_id and gelir_turu == 'AİDAT':
            self._aidat_odemesi_bagla(uye_id, baslangic_yil, bitis_yil,
                                     yillik_tutar, odeme_grup_id, gelir_idler)
        
        return odeme_grup_id
    
    def _aidat_odemesi_bagla(self, uye_id, baslangic_yil, bitis_yil,
                            yillik_tutar, odeme_grup_id, gelir_idler):
        """Aidat sistemine bağla"""
        aidat_yoneticisi = AidatYoneticisi(self.db)
        
        # Ana ödeme kaydı
        self.db.cursor.execute("""
            INSERT INTO aidat_odemeleri
            (odeme_grup_id, tarih, toplam_tutar, kasa_id)
            VALUES (?, ?, ?, ?)
        """, (odeme_grup_id, datetime.now().strftime("%Y-%m-%d"),
              yillik_tutar * (bitis_yil - baslangic_yil + 1), ...))
        
        # Her yıl için detay
        for i, yil in enumerate(range(baslangic_yil, bitis_yil + 1)):
            # Aidat kaydı oluştur/bul
            aidat_id = aidat_yoneticisi.aidat_olustur_veya_getir(uye_id, yil)
            
            # Detay kaydı
            self.db.cursor.execute("""
                INSERT INTO aidat_odeme_detay
                (odeme_grup_id, aidat_id, tutar, gelir_id)
                VALUES (?, ?, ?, ?)
            """, (odeme_grup_id, aidat_id, yillik_tutar, gelir_idler[i]))
            
            # Aidat durumunu güncelle
            aidat_yoneticisi._aidat_durumunu_guncelle(aidat_id)
```

### 2. KasaYoneticisi (Güncellenmiş)

```python
class KasaYoneticisi:
    
    def kasa_bakiye_hesapla(self, kasa_id: int, tarih: str = None,
                            tip: str = 'fiziksel') -> float:
        """
        tip: 'fiziksel' (kasadaki gerçek para) veya 'serbest' (tahakkuksuz)
        """
        if tarih is None:
            tarih = datetime.now().strftime("%Y-%m-%d")
        
        # Fiziksel bakiye (mevcut hesaplama)
        fiziksel = self._fiziksel_bakiye(kasa_id, tarih)
        
        if tip == 'fiziksel':
            return fiziksel
        
        elif tip == 'serbest':
            # Gelir tahakkukları (gelecek yıllara ait)
            yil = int(tarih[:4])
            self.db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) FROM gelirler
                WHERE kasa_id = ?
                AND tahsil_tarihi <= ?
                AND ait_oldugu_yil > ?
                AND tahakkuk_durumu = 'PEŞİN'
            """, (kasa_id, tarih, yil))
            gelir_tahakkuk = self.db.cursor.fetchone()[0]
            
            # Gider tahakkukları (gelecek için peşin ödemeler)
            self.db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) FROM giderler
                WHERE kasa_id = ?
                AND odeme_tarihi <= ?
                AND ait_oldugu_yil > ?
                AND tahakkuk_durumu = 'PEŞİN'
            """, (kasa_id, tarih, yil))
            gider_tahakkuk = self.db.cursor.fetchone()[0]
            
            serbest = fiziksel - gelir_tahakkuk + gider_tahakkuk
            return serbest
    
    def kasa_tahakkuk_detay(self, kasa_id: int, tarih: str = None) -> Dict:
        """Kasanın tahakkuk detayı"""
        if tarih is None:
            tarih = datetime.now().strftime("%Y-%m-%d")
        
        yil = int(tarih[:4])
        
        # Gelecek yıl tahakkukları (yıl bazlı)
        self.db.cursor.execute("""
            SELECT 
                ait_oldugu_yil as yil,
                COUNT(*) as adet,
                SUM(tutar) as tutar
            FROM gelirler
            WHERE kasa_id = ?
            AND tahsil_tarihi <= ?
            AND ait_oldugu_yil > ?
            AND tahakkuk_durumu = 'PEŞİN'
            GROUP BY ait_oldugu_yil
            ORDER BY ait_oldugu_yil
        """, (kasa_id, tarih, yil))
        
        gelecek_yil_tahakkuklari = [dict(row) for row in self.db.cursor.fetchall()]
        
        toplam_tahakkuk = sum([t['tutar'] for t in gelecek_yil_tahakkuklari])
        
        return {
            'fiziksel_bakiye': self.kasa_bakiye_hesapla(kasa_id, tarih, 'fiziksel'),
            'tahakkuk_toplami': toplam_tahakkuk,
            'serbest_bakiye': self.kasa_bakiye_hesapla(kasa_id, tarih, 'serbest'),
            'gelecek_yil_detay': gelecek_yil_tahakkuklari
        }
```

### 3. DevirYoneticisi (Tamamen Yeni)

```python
class DevirYoneticisi:
    
    def yil_sonu_devir(self, yil: int, onay: bool = False) -> Dict:
        """
        Yıl sonu kapanış ve devir işlemi
        
        onay=False: Sadece rapor (simülasyon)
        onay=True: Gerçek devir
        """
        kasa_yoneticisi = KasaYoneticisi(self.db)
        
        tarih = f"{yil}-12-31"
        kasalar = kasa_yoneticisi.liste_getir()
        
        devir_raporu = {
            'yil': yil,
            'tarih': tarih,
            'kasalar': [],
            'uyarilar': [],
            'toplam': {
                'fiziksel': 0,
                'tahakkuk': 0,
                'serbest': 0
            }
        }
        
        for kasa in kasalar:
            kasa_id = kasa['kasa_id']
            
            # Tahakkuk detayı
            detay = kasa_yoneticisi.kasa_tahakkuk_detay(kasa_id, tarih)
            
            kasa_devir = {
                'kasa_id': kasa_id,
                'kasa_adi': kasa['kasa_adi'],
                'fiziksel_bakiye': detay['fiziksel_bakiye'],
                'tahakkuk_toplami': detay['tahakkuk_toplami'],
                'serbest_bakiye': detay['serbest_bakiye'],
                'gelecek_yil_tahakkuklari': detay['gelecek_yil_detay']
            }
            
            # Uyarı kontrolleri
            if detay['serbest_bakiye'] < 0:
                devir_raporu['uyarilar'].append({
                    'tip': 'CARİ_AÇIK',
                    'kasa': kasa['kasa_adi'],
                    'mesaj': f"Serbest bakiye negatif: {detay['serbest_bakiye']:,.2f} TL. "
                            f"Gelecek yılların parasını kullanmış durumdasınız!"
                })
            
            if detay['tahakkuk_toplami'] > detay['fiziksel_bakiye'] * 0.8:
                devir_raporu['uyarilar'].append({
                    'tip': 'YÜKSEK_TAHAKKUK',
                    'kasa': kasa['kasa_adi'],
                    'mesaj': f"Tahakkuk oranı çok yüksek (%{detay['tahakkuk_toplami']/detay['fiziksel_bakiye']*100:.0f}). "
                            f"Üye ayrılma riski!"
                })
            
            devir_raporu['kasalar'].append(kasa_devir)
            
            # Toplamlar
            devir_raporu['toplam']['fiziksel'] += detay['fiziksel_bakiye']
            devir_raporu['toplam']['tahakkuk'] += detay['tahakkuk_toplami']
            devir_raporu['toplam']['serbest'] += detay['serbest_bakiye']
        
        # Gerçek devir
        if onay:
            self._devri_uygula(yil, devir_raporu)
        
        return devir_raporu
    
    def _devri_uygula(self, yil: int, rapor: Dict):
        """Devir işlemini uygula"""
        for kasa_devir in rapor['kasalar']:
            self.db.cursor.execute("""
                UPDATE kasalar
                SET devir_bakiye = ?,
                    serbest_devir_bakiye = ?,
                    tahakkuk_toplami = ?,
                    son_devir_tarihi = CURRENT_TIMESTAMP
                WHERE kasa_id = ?
            """, (
                kasa_devir['fiziksel_bakiye'],
                kasa_devir['serbest_bakiye'],
                kasa_devir['tahakkuk_toplami'],
                kasa_devir['kasa_id']
            ))
        
        # Devir log kaydı
        self.db.cursor.execute("""
            INSERT INTO devir_islemleri
            (yil, devir_tarihi, toplam_fiziksel, toplam_tahakkuk, 
             toplam_serbest, rapor_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            yil,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            rapor['toplam']['fiziksel'],
            rapor['toplam']['tahakkuk'],
            rapor['toplam']['serbest'],
            json.dumps(rapor, ensure_ascii=False)
        ))
        
        self.db.commit()
```

### 4. TahakkukYoneticisi (Yeni)

```python
class TahakkukYoneticisi:
    
    def tahakkuk_listesi(self, yil: int = None, durum: str = 'AKTİF') -> List[Dict]:
        """Tahakkuk listesi"""
        query = """
            SELECT 
                t.*,
                g.gelir_turu,
                g.aciklama,
                k.kasa_adi,
                u.ad_soyad as uye_adi
            FROM tahakkuklar t
            LEFT JOIN gelirler g ON t.kaynak_id = g.gelir_id
            LEFT JOIN kasalar k ON g.kasa_id = k.kasa_id
            LEFT JOIN aidat_takip a ON g.aidat_id = a.aidat_id
            LEFT JOIN uyeler u ON a.uye_id = u.uye_id
            WHERE t.tahakkuk_turu = 'GELİR'
        """
        params = []
        
        if yil:
            query += " AND t.ait_oldugu_yil = ?"
            params.append(yil)
        
        if durum:
            query += " AND t.durum = ?"
            params.append(durum)
        
        query += " ORDER BY t.ait_oldugu_yil, t.tutar DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def tahakkuk_ozet(self) -> Dict:
        """Yıl bazlı tahakkuk özeti"""
        self.db.cursor.execute("""
            SELECT 
                ait_oldugu_yil as yil,
                COUNT(*) as adet,
                SUM(tutar) as tutar,
                durum
            FROM tahakkuklar
            WHERE tahakkuk_turu = 'GELİR'
            AND ait_oldugu_yil > strftime('%Y', 'now')
            GROUP BY ait_oldugu_yil, durum
            ORDER BY ait_oldugu_yil
        """)
        
        return [dict(row) for row in self.db.cursor.fetchall()]
```

---

## ✅ ENTEGRASYON KONTROLLERİ

### 1. Alacak-Verecek Entegrasyonu
```python
# Alacak tahsilatı → Gelir (yıl bazlı)
def alacak_tahsilat_ekle(alacak_id, tutar, kasa_id, tahsilat_tarihi, ait_oldugu_yil):
    # Gelir kaydı (yıl bilgisiyle)
    gelir_id = gelir_yoneticisi.gelir_ekle(
        gelir_turu='DİĞER',
        tutar=tutar,
        kasa_id=kasa_id,
        tahsil_tarihi=tahsilat_tarihi,
        ait_oldugu_yil=ait_oldugu_yil  ← YENİ
    )
```

### 2. Mali Tablolar Entegrasyonu
```python
# Bilanço - Gelir Tahakkukları (Pasif)
def bilanco_raporu(tarih):
    ...
    # Kısa Vadeli Yükümlülükler
    gelir_tahakkuku = db.execute("""
        SELECT SUM(tutar) FROM gelirler
        WHERE tahsil_tarihi <= ?
        AND ait_oldugu_yil > ?
        AND tahakkuk_durumu = 'PEŞİN'
    """, (tarih, int(tarih[:4]))).fetchone()[0]
    
    kaynaklar['kisa_vadeli_yukumlulukler'] += gelir_tahakkuku
```

### 3. Virman Entegrasyonu
```python
# Virman serbest bakiye kontrolü
def virman_yap(gonderen, alan, tutar):
    serbest = kasa_yoneticisi.kasa_bakiye_hesapla(gonderen, tip='serbest')
    
    if tutar > serbest:
        raise Exception(f"Yetersiz serbest bakiye!")
    
    # Normal virman işlemi
    ...
```

---

## 🚀 UYGULAMA ÖNCELİĞİ

### FAZ 1: Veritabanı (1 gün)
1. ✅ `gelirler` tablosu → `ait_oldugu_yil`, `tahakkuk_durumu` ekle
2. ✅ `giderler` tablosu → `ait_oldugu_yil`, `tahakkuk_durumu` ekle
3. ✅ `aidat_odemeleri` → `odeme_grup_id` ekle
4. ✅ `aidat_odeme_detay` tablosu oluştur
5. ✅ `tahakkuklar` tablosu oluştur
6. ✅ `kasalar` → `serbest_devir_bakiye`, `tahakkuk_toplami` ekle

### FAZ 2: Backend (2-3 gün)
1. ✅ `GelirYoneticisi.coklu_yil_gelir_ekle()`
2. ✅ `KasaYoneticisi.kasa_tahakkuk_detay()`
3. ✅ `DevirYoneticisi` sınıfı
4. ✅ `TahakkukYoneticisi` sınıfı
5. ✅ Mevcut fonksiyonları güncelle

### FAZ 3: UI (2-3 gün)
1. ✅ Çok yıllık ödeme dialogu
2. ✅ Kasa detay ekranı (tahakkuk gösterimi)
3. ✅ Devir onay ekranı (güncellenmiş)
4. ✅ Tahakkuk raporu
5. ✅ Uyarı sistemleri

### FAZ 4: Test (1-2 gün)
1. ✅ Senaryo testleri
2. ✅ Mali tablo doğrulamaları
3. ✅ Devir simülasyonları

---

## 📋 ÖZET

### Temel Prensipler
1. **Tahsil Yılı ≠ Ait Olduğu Yıl**
2. **Fiziksel Para ≠ Serbest Para**
3. **Gelir Tahakkuku = Borç (Pasif)**
4. **Her İşlem Yıl Bazlı Takip**

### Kritik Noktalar
- ✅ Çok yıllık ödeme desteği
- ✅ Yıl bazlı gelir/gider takibi
- ✅ Tahakkuk muhasebesi
- ✅ Serbest bakiye hesaplama
- ✅ Cari açık uyarıları
- ✅ Gelecek yıl sermaye hesabı
- ✅ Virman tahakkuk kontrolü

### Avantajlar
- ✅ Doğru mali raporlama
- ✅ Gelecek yıl planlama
- ✅ Risk yönetimi
- ✅ Şeffaflık
- ✅ Denetim uyumluluğu

---

**Onayınızı bekliyorum! 🎯**
