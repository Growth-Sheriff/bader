# 🏛️ DERNEK MUHASEBESİ - TAM MİMARİ

## 📋 SİSTEM GEREKSİNİMLERİ

### 🔴 KRİTİK EKSİKLİKLER (Acil Geliştirme)

#### 1. HESAP PLANI SİSTEMİ
```sql
CREATE TABLE hesap_plani (
    hesap_kodu TEXT PRIMARY KEY,  -- 100.01.001
    hesap_adi TEXT NOT NULL,
    ust_hesap TEXT,               -- Hiyerarşi
    hesap_tipi TEXT CHECK(hesap_tipi IN ('VARLIK', 'KAYNAK', 'GELİR', 'GİDER')),
    borc_alacak TEXT CHECK(borc_alacak IN ('BORÇ', 'ALACAK', 'HER İKİSİ')),
    ana_grup TEXT,                -- 1:Dönen Varlıklar, 6:Gelirler
    aktif INTEGER DEFAULT 1,
    detay_hesap INTEGER DEFAULT 0 -- 1: Alt hesaba bölünmez
);

-- ÖRNEK HESAPLAR:
-- 100 DÖNEN VARLIKLAR
-- 100.01 Kasa
-- 100.01.001 TL Kasası
-- 100.01.002 Döviz Kasası
-- 100.02 Bankalar
-- 100.02.001 Ziraat Bankası TL
-- 102 ALACAKLAR
-- 102.01 Üye Aidat Alacakları
-- 102.02 Diğer Alacaklar

-- 120 STOKLAR (Dernek için)
-- 120.01 Satılabilir Ürünler
-- 120.02 Yardım Malzemeleri

-- 200 DURAN VARLIKLAR
-- 220 Maddi Duran Varlıklar
-- 220.01 Arazi ve Arsalar
-- 220.02 Binalar
-- 220.03 Demirbaşlar
-- 220.04 Taşıtlar
-- 257 Birikmiş Amortismanlar

-- 300 KISA VADELİ BORÇLAR
-- 320 Satıcılar (Tedarikçiler)
-- 360 Ödenecek Vergiler
-- 361 Ödenecek SGK Primleri

-- 500 ÖZ KAYNAKLAR
-- 500.01 Dernek Sermayesi
-- 590 Dönem Net Karı/Zararı

-- 600 GELİRLER
-- 602 Aidat Gelirleri
-- 602.01 Asil Üye Aidatı
-- 602.02 Onursal Üye Aidatı
-- 603 Bağış ve Yardımlar
-- 603.01 Nakdi Bağışlar
-- 603.02 Ayni Bağışlar
-- 604 Faaliyet Gelirleri
-- 604.01 Düğün/Kına Gelirleri
-- 604.02 Etkinlik Gelirleri
-- 605 Kira Gelirleri
-- 649 Diğer Olağan Gelirler

-- 700 GİDERLER
-- 710 Personel Giderleri
-- 710.01 Ücretler
-- 710.02 SGK İşveren Payı
-- 720 Genel Yönetim Giderleri
-- 720.01 Kira Gideri
-- 720.02 Elektrik-Su-Doğalgaz
-- 720.03 Telefon-İnternet
-- 720.04 Kırtasiye
-- 730 Faaliyet Giderleri
-- 730.01 Etkinlik Giderleri
-- 730.02 Yardım Giderleri
-- 770 Amortisman Giderleri
```

#### 2. MUHASEBE FİŞİ (YEVMİYE DEFTERİ)
```sql
CREATE TABLE muhasebe_fisi (
    fis_id INTEGER PRIMARY KEY,
    fis_no TEXT UNIQUE,           -- MB-2025-001
    fis_tipi TEXT,                -- MAHSUP, AÇILIŞ, KAPANIŞ
    tarih DATE NOT NULL,
    aciklama TEXT,
    referans_tablo TEXT,          -- gelirler, giderler, virmanlar
    referans_id INTEGER,
    evrak_no TEXT,                -- Dekont, fatura no
    durum TEXT DEFAULT 'TASLAK',  -- TASLAK, ONAYLI, İPTAL
    onaylayan_kullanici TEXT,
    onay_tarihi TIMESTAMP,
    olusturan_kullanici TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fis_satirlari (
    satir_id INTEGER PRIMARY KEY,
    fis_id INTEGER NOT NULL,
    hesap_kodu TEXT NOT NULL,
    borc REAL DEFAULT 0,
    alacak REAL DEFAULT 0,
    aciklama TEXT,
    FOREIGN KEY (fis_id) REFERENCES muhasebe_fisi(fis_id) ON DELETE CASCADE,
    FOREIGN KEY (hesap_kodu) REFERENCES hesap_plani(hesap_kodu),
    CHECK (borc >= 0 AND alacak >= 0),
    CHECK (NOT (borc > 0 AND alacak > 0))  -- Aynı satırda hem borç hem alacak olmaz
);

-- TRIGGER: Fiş dengesini kontrol et
CREATE TRIGGER fis_denge_kontrolu
AFTER INSERT ON fis_satirlari
BEGIN
    SELECT CASE
        WHEN (SELECT ABS(SUM(borc) - SUM(alacak)) FROM fis_satirlari WHERE fis_id = NEW.fis_id) > 0.01
        THEN RAISE(ABORT, 'Fiş dengeli değil! Borç = Alacak olmalı')
    END;
END;
```

#### 3. BÜYÜK DEFTER
```sql
CREATE TABLE buyuk_defter (
    kayit_id INTEGER PRIMARY KEY,
    hesap_kodu TEXT NOT NULL,
    tarih DATE NOT NULL,
    fis_id INTEGER NOT NULL,
    fis_no TEXT,
    aciklama TEXT,
    borc REAL DEFAULT 0,
    alacak REAL DEFAULT 0,
    bakiye REAL DEFAULT 0,
    bakiye_yonu TEXT CHECK(bakiye_yonu IN ('BORÇ', 'ALACAK')),
    FOREIGN KEY (hesap_kodu) REFERENCES hesap_plani(hesap_kodu),
    FOREIGN KEY (fis_id) REFERENCES muhasebe_fisi(fis_id)
);

-- INDEX: Hızlı sorgu için
CREATE INDEX idx_buyuk_defter_hesap_tarih ON buyuk_defter(hesap_kodu, tarih);
```

#### 4. DEMİRBAŞ/ENVANTER YÖNETİMİ
```sql
CREATE TABLE demirbas (
    demirbas_id INTEGER PRIMARY KEY,
    demirbas_no TEXT UNIQUE,
    demirbas_adi TEXT NOT NULL,
    kategori TEXT,                -- Mobilya, Elektronik, Taşıt
    marka_model TEXT,
    seri_no TEXT,
    hesap_kodu TEXT,              -- 220.03
    alis_tarihi DATE,
    alis_tutari REAL,
    tedarikci TEXT,
    fatura_no TEXT,
    -- Amortisman
    amortisman_suresi_yil INTEGER,  -- 5 yıl
    amortisman_orani REAL,          -- %20
    birikmi_amortisman REAL DEFAULT 0,
    net_deger REAL,                  -- Alis tutarı - Birikmiş amortisman
    -- Durum
    durum TEXT DEFAULT 'KULANIMDA',  -- KULANIMDA, ARIZALI, HURDALANMİŞ
    lokasyon TEXT,
    sorumlu_kisi TEXT,
    notlar TEXT,
    FOREIGN KEY (hesap_kodu) REFERENCES hesap_plani(hesap_kodu)
);

CREATE TABLE amortisman_kayitlari (
    kayit_id INTEGER PRIMARY KEY,
    demirbas_id INTEGER NOT NULL,
    donem TEXT,                    -- 2025-01 (Aylık)
    tutar REAL,
    fis_id INTEGER,
    FOREIGN KEY (demirbas_id) REFERENCES demirbas(demirbas_id),
    FOREIGN KEY (fis_id) REFERENCES muhasebe_fisi(fis_id)
);
```

#### 5. BANKA HAREKETLERİ & MUTABAKAT
```sql
CREATE TABLE banka_hesaplari (
    hesap_id INTEGER PRIMARY KEY,
    banka_adi TEXT NOT NULL,
    sube_kodu TEXT,
    hesap_no TEXT NOT NULL,
    iban TEXT,
    para_birimi TEXT DEFAULT 'TL',
    hesap_kodu TEXT,              -- 100.02.001
    aktif INTEGER DEFAULT 1,
    FOREIGN KEY (hesap_kodu) REFERENCES hesap_plani(hesap_kodu)
);

CREATE TABLE banka_hareketleri (
    hareket_id INTEGER PRIMARY KEY,
    hesap_id INTEGER NOT NULL,
    tarih DATE NOT NULL,
    valor_tarihi DATE,
    islem_tipi TEXT,              -- HAVALE, EFT, ÇEK, OTOMATIK ÖDEME
    aciklama TEXT,
    tutar REAL NOT NULL,
    borc_alacak TEXT,             -- GİRİŞ, ÇIKIŞ
    dekont_no TEXT,
    karsi_hesap TEXT,
    fis_id INTEGER,
    mutabakat_durumu TEXT DEFAULT 'BEKLİYOR', -- BEKLİYOR, EŞLEŞTİ
    FOREIGN KEY (hesap_id) REFERENCES banka_hesaplari(hesap_id),
    FOREIGN KEY (fis_id) REFERENCES muhasebe_fisi(fis_id)
);

CREATE TABLE banka_mutabakat (
    mutabakat_id INTEGER PRIMARY KEY,
    hesap_id INTEGER NOT NULL,
    donem DATE NOT NULL,          -- Ay sonu: 2025-01-31
    ekstre_bakiye REAL,           -- Banka ekstresindeki bakiye
    defter_bakiye REAL,           -- Muhasebe defterindeki bakiye
    fark REAL,
    aciklama TEXT,
    mutabik INTEGER DEFAULT 0,    -- 1: Mutabık
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hesap_id) REFERENCES banka_hesaplari(hesap_id)
);
```

#### 6. ÇEK/SENET TAKİBİ
```sql
CREATE TABLE cekler (
    cek_id INTEGER PRIMARY KEY,
    cek_tipi TEXT CHECK(cek_tipi IN ('ALACAK', 'BORÇ')),  -- Aldığımız / Verdiğimiz
    cek_no TEXT NOT NULL,
    banka TEXT,
    sube TEXT,
    hesap_no TEXT,
    tutar REAL NOT NULL,
    para_birimi TEXT DEFAULT 'TL',
    duzenlenme_tarihi DATE,
    vade_tarihi DATE NOT NULL,
    duzenleyen TEXT,              -- Çeki kesen kişi/firma
    ciro_eden TEXT,
    lehtar TEXT,                  -- Çeki alan kişi/firma
    -- Durum takibi
    durum TEXT DEFAULT 'PORTFÖYDE',  -- PORTFÖYDE, BANKAYA VERİLDİ, TAHSİL EDİLDİ, İADE, KARŞILIKSIZ
    tahsil_tarihi DATE,
    iade_nedeni TEXT,
    -- Muhasebe bağlantısı
    fis_id INTEGER,
    hesap_kodu TEXT,              -- 101.01 Alınan Çekler
    notlar TEXT,
    FOREIGN KEY (fis_id) REFERENCES muhasebe_fisi(fis_id),
    FOREIGN KEY (hesap_kodu) REFERENCES hesap_plani(hesap_kodu)
);

CREATE TABLE senetler (
    senet_id INTEGER PRIMARY KEY,
    senet_tipi TEXT CHECK(senet_tipi IN ('ALACAK', 'BORÇ')),
    senet_no TEXT NOT NULL,
    tutar REAL NOT NULL,
    para_birimi TEXT DEFAULT 'TL',
    duzenlenme_tarihi DATE,
    vade_tarihi DATE NOT NULL,
    duzenleyen TEXT,
    lehtar TEXT,
    aval TEXT,                    -- Kefil
    durum TEXT DEFAULT 'PORTFÖYDE',
    tahsil_tarihi DATE,
    fis_id INTEGER,
    hesap_kodu TEXT,              -- 101.02 Alınan Senetler
    notlar TEXT,
    FOREIGN KEY (fis_id) REFERENCES muhasebe_fisi(fis_id),
    FOREIGN KEY (hesap_kodu) REFERENCES hesap_plani(hesap_kodu)
);
```

#### 7. VERGİ & STOPAJ TAKİBİ
```sql
CREATE TABLE vergi_beyan (
    beyan_id INTEGER PRIMARY KEY,
    beyan_tipi TEXT,              -- KDV, MUHTASAR, DAMGA VERGİSİ
    donem TEXT NOT NULL,          -- 2025-01
    beyan_tarihi DATE,
    odeme_tarihi DATE,
    matrah REAL,
    vergi_tutari REAL,
    durum TEXT DEFAULT 'HAZIRLANIYOR',  -- HAZIRLANIYOR, BEYANEDİLDİ, ÖDENDİ
    fis_id INTEGER,
    FOREIGN KEY (fis_id) REFERENCES muhasebe_fisi(fis_id)
);

CREATE TABLE stopaj_kayitlari (
    stopaj_id INTEGER PRIMARY KEY,
    donem TEXT NOT NULL,
    belge_no TEXT,
    belge_tarihi DATE,
    odeyen TEXT,                  -- Dernek
    alan TEXT,                    -- Hizmet veren
    tc_no TEXT,
    matrah REAL,
    stopaj_orani REAL,
    stopaj_tutari REAL,
    stopaj_kodu TEXT,             -- 061: Serbest meslek
    beyan_durumu TEXT DEFAULT 'BEKLİYOR',
    fis_id INTEGER,
    FOREIGN KEY (fis_id) REFERENCES muhasebe_fisi(fis_id)
);
```

#### 8. DÖNEM KAPAMA & DEVİR
```sql
CREATE TABLE donem_kapama (
    kapama_id INTEGER PRIMARY KEY,
    donem_tipi TEXT CHECK(donem_tipi IN ('AYLIK', 'YILLIK')),
    donem TEXT NOT NULL,          -- 2025-01 veya 2025
    baslangic_tarihi DATE,
    bitis_tarihi DATE,
    kapama_tarihi DATE,
    toplam_borc REAL,
    toplam_alacak REAL,
    donem_kari REAL,
    donem_zarari REAL,
    durum TEXT DEFAULT 'AÇIK',    -- AÇIK, KAPANDI
    kapatan_kullanici TEXT,
    notlar TEXT
);

CREATE TABLE devir_kayitlari (
    devir_id INTEGER PRIMARY KEY,
    donem TEXT NOT NULL,
    hesap_kodu TEXT NOT NULL,
    borc REAL DEFAULT 0,
    alacak REAL DEFAULT 0,
    bakiye REAL,
    bakiye_yonu TEXT CHECK(bakiye_yonu IN ('BORÇ', 'ALACAK')),
    sonraki_donem_fis_id INTEGER,  -- Açılış fişi
    FOREIGN KEY (hesap_kodu) REFERENCES hesap_plani(hesap_kodu),
    FOREIGN KEY (sonraki_donem_fis_id) REFERENCES muhasebe_fisi(fis_id)
);
```

#### 9. MALİ TABLOLAR (Views)
```sql
-- MİZAN (Deneme Bilançosu)
CREATE VIEW mizan_view AS
SELECT 
    hp.hesap_kodu,
    hp.hesap_adi,
    hp.ana_grup,
    SUM(bd.borc) as toplam_borc,
    SUM(bd.alacak) as toplam_alacak,
    ABS(SUM(bd.borc) - SUM(bd.alacak)) as bakiye,
    CASE 
        WHEN SUM(bd.borc) > SUM(bd.alacak) THEN 'BORÇ'
        ELSE 'ALACAK'
    END as bakiye_yonu
FROM hesap_plani hp
LEFT JOIN buyuk_defter bd ON hp.hesap_kodu = bd.hesap_kodu
WHERE bd.tarih BETWEEN ? AND ?
GROUP BY hp.hesap_kodu, hp.hesap_adi, hp.ana_grup;

-- BİLANÇO (Aktif-Pasif)
CREATE VIEW bilanco_view AS
SELECT 
    CASE 
        WHEN ana_grup IN ('1', '2') THEN 'AKTİF'
        ELSE 'PASİF'
    END as bilanco_tarafi,
    ana_grup,
    hesap_kodu,
    hesap_adi,
    bakiye
FROM mizan_view
WHERE bakiye > 0
ORDER BY hesap_kodu;

-- GELİR TABLOSU
CREATE VIEW gelir_tablosu_view AS
SELECT 
    CASE 
        WHEN ana_grup = '6' THEN 'GELİRLER'
        WHEN ana_grup = '7' THEN 'GİDERLER'
    END as grup,
    hesap_kodu,
    hesap_adi,
    bakiye
FROM mizan_view
WHERE ana_grup IN ('6', '7')
ORDER BY hesap_kodu;
```

---

## 🔧 YENİ MİMARİ KATMANLAR

### 1. **İş Kuralları Katmanı (Business Rules)**
```python
# models_muhasebe.py

class MuhasebeYoneticisi:
    """Muhasebe fiş işlemleri"""
    
    def fis_olustur(self, tarih: str, aciklama: str, 
                    satirlar: List[Dict]) -> int:
        """
        Muhasebe fişi oluştur
        satirlar: [
            {'hesap_kodu': '100.01.001', 'borc': 1000, 'alacak': 0},
            {'hesap_kodu': '602.01', 'borc': 0, 'alacak': 1000}
        ]
        """
        # 1. Denge kontrolü
        toplam_borc = sum(s['borc'] for s in satirlar)
        toplam_alacak = sum(s['alacak'] for s in satirlar)
        
        if abs(toplam_borc - toplam_alacak) > 0.01:
            raise ValueError("Fiş dengeli değil!")
        
        # 2. Fiş oluştur
        fis_no = self.get_next_fis_no()
        self.db.cursor.execute("""
            INSERT INTO muhasebe_fisi 
            (fis_no, tarih, aciklama, durum)
            VALUES (?, ?, ?, 'TASLAK')
        """, (fis_no, tarih, aciklama))
        fis_id = self.db.cursor.lastrowid
        
        # 3. Satırları ekle
        for satir in satirlar:
            self.db.cursor.execute("""
                INSERT INTO fis_satirlari 
                (fis_id, hesap_kodu, borc, alacak, aciklama)
                VALUES (?, ?, ?, ?, ?)
            """, (fis_id, satir['hesap_kodu'], 
                  satir['borc'], satir['alacak'], 
                  satir.get('aciklama', '')))
        
        # 4. Büyük defter kaydet
        self.buyuk_deftere_kaydet(fis_id, satirlar, tarih)
        
        self.db.commit()
        return fis_id
    
    def aidat_tahsilati_fis(self, aidat_id: int, tutar: float, 
                            tarih: str, kasa_hesap_kodu: str):
        """Aidat tahsilatı için otomatik fiş"""
        satirlar = [
            {
                'hesap_kodu': kasa_hesap_kodu,  # 100.01.001
                'borc': tutar,
                'alacak': 0,
                'aciklama': 'Aidat tahsilatı'
            },
            {
                'hesap_kodu': '602.01',  # Aidat Gelirleri
                'borc': 0,
                'alacak': tutar,
                'aciklama': 'Aidat tahsilatı'
            }
        ]
        return self.fis_olustur(tarih, f'Aidat No: {aidat_id}', satirlar)
    
    def gider_fisi(self, gider_id: int, tutar: float, 
                   tarih: str, kasa_hesap_kodu: str, 
                   gider_hesap_kodu: str):
        """Gider için otomatik fiş"""
        satirlar = [
            {
                'hesap_kodu': gider_hesap_kodu,  # 720.01
                'borc': tutar,
                'alacak': 0
            },
            {
                'hesap_kodu': kasa_hesap_kodu,  # 100.01.001
                'borc': 0,
                'alacak': tutar
            }
        ]
        return self.fis_olustur(tarih, f'Gider No: {gider_id}', satirlar)

class DonemKapamaYoneticisi:
    """Dönem kapama işlemleri"""
    
    def aylik_kapama(self, donem: str):
        """Aylık kapama"""
        # 1. Amortisman hesapla
        self.amortisman_hesapla(donem)
        
        # 2. Gelir-gider hesaplarını kapat (690'a)
        self.gelir_gider_kapat(donem)
        
        # 3. Mizan oluştur
        self.mizan_olustur(donem)
        
        # 4. Mali tabloları hazırla
        self.mali_tablolar_hazirla(donem)
    
    def yillik_kapama(self, yil: int):
        """Yıllık kapama"""
        # 1. Geçici hesapları kapat
        # 2. Net kar/zararı hesapla
        # 3. Bilançoyu hazırla
        # 4. Devir işlemleri
        pass

class DemirbasYoneticisi:
    """Demirbaş yönetimi"""
    
    def amortisman_hesapla(self, donem: str):
        """Aylık amortisman hesapla"""
        # Tüm demirbaşlar için
        # Aylık amortisman = (Alış tutarı / Süre(yıl)) / 12
        pass
    
    def demirbas_hurda(self, demirbas_id: int):
        """Demirbaşı hurdaya çıkar"""
        # Muhasebe kaydı: Birikmiş amortismanı düş
        pass
```

### 2. **Rapor Katmanı (Reporting)**
```python
# models_raporlama.py

class MaliRaporYoneticisi:
    """Mali raporlama"""
    
    def mizan_raporu(self, baslangic: str, bitis: str) -> pd.DataFrame:
        """Mizan raporu"""
        pass
    
    def bilanco_raporu(self, tarih: str) -> Dict:
        """Bilanço raporu"""
        return {
            'aktif': {
                'donen_varliklar': {},
                'duran_varliklar': {},
                'toplam_aktif': 0
            },
            'pasif': {
                'kisa_vadeli_borclar': {},
                'uzun_vadeli_borclar': {},
                'oz_kaynaklar': {},
                'toplam_pasif': 0
            }
        }
    
    def gelir_tablosu(self, baslangic: str, bitis: str) -> Dict:
        """Gelir tablosu"""
        return {
            'gelirler': {},
            'giderler': {},
            'faaliyet_kari': 0,
            'net_kar_zarar': 0
        }
    
    def nakit_akis_tablosu(self, baslangic: str, bitis: str):
        """Nakit akış tablosu"""
        pass
    
    def yonetim_kurulu_raporu(self, donem: str):
        """YK için özet rapor"""
        pass
```

---

## 📱 YENİ UI MODÜLLER

### 1. Muhasebe Fişi Sayfası
- Fiş listesi
- Yeni fiş oluşturma (çift kayıt mantığıyla)
- Fiş onaylama sistemi
- Fiş yazdırma (resmi format)

### 2. Büyük Defter Sayfası
- Hesap bazlı işlem geçmişi
- Hesap ekstre raporu
- Bakiye takibi

### 3. Mali Tablolar Sayfası
- Mizan raporu
- Bilanço
- Gelir tablosu
- Nakit akış tablosu
- Grafiklerle görselleştirme

### 4. Demirbaş Yönetimi
- Demirbaş listesi
- Amortisman takibi
- Zimmet kayıtları
- QR kod ile demirbaş takibi

### 5. Banka İşlemleri
- Hesap hareketleri
- Otomatik OFX/Excel import
- Mutabakat ekranı

### 6. Dönem Kapama
- Aylık kapama sihirbazı
- Yıllık kapama
- Devir işlemleri

---

## 🎯 UYGULAMA PLANI (Öncelik Sırasıyla)

### FAZA 1: Hesap Planı (1 hafta)
1. hesap_plani tablosu oluştur
2. Dernek standart hesap planını yükle
3. Hesap seçici UI komponenti

### FAZA 2: Muhasebe Fişi (2 hafta)
1. muhasebe_fisi + fis_satirlari tabloları
2. buyuk_defter tablosu
3. Fiş oluşturma UI
4. Otomatik fiş yaratma (gelir/gider/virman için)

### FAZA 3: Mali Tablolar (1 hafta)
1. Mizan hesaplama
2. Bilanço
3. Gelir tablosu
4. Raporlama UI

### FAZA 4: Dönem Kapama (1 hafta)
1. Aylık kapama mantığı
2. Yıllık kapama
3. Devir işlemleri

### FAZA 5: Demirbaş & Amortisman (1 hafta)
1. Demirbaş takibi
2. Otomatik amortisman hesaplama
3. QR kod entegrasyonu (opsiyonel)

### FAZA 6: Banka İşlemleri (1 hafta)
1. Banka hesap hareketleri
2. OFX import
3. Mutabakat

### FAZA 7: Vergi & Stopaj (1 hafta)
1. KDV hesaplama
2. Stopaj kayıtları
3. Beyanname hazırlığı

---

## 🚀 HIZLI BAŞLANGIÇ

Hangisini önce yapalım? Önerim:

**FAZA 1 + FAZA 2** birlikte - Hesap Planı ve Muhasebe Fişi sistemi.

Bu temeli kurduktan sonra diğer modüller kolayca eklenebilir.

Başlayayım mı? 🚀
