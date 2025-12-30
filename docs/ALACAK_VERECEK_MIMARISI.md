# 💰 ALACAK-VERECEK TAKİP SİSTEMİ MİMARİSİ

## 📋 GENEL BAKIŞ

### Amaç
Dernek için gelecek olan paraları (alacaklar) ve ödenmesi gereken paraları (verecekler) sistematik bir şekilde takip etmek.

### İş Senaryoları

#### ALACAKLAR (Receivables)
1. **Kira Kaporu**: Derneği kiraya veriyoruz, kapora alıyoruz
2. **Verilen Borç**: Bir üyeye/dışarı borç veriyoruz
3. **Taksitli Satış**: Bir varlık satıyoruz, taksitle gelecek
4. **Hizmet Bedelleri**: Verilen hizmetlerin ödemesi bekleniyorsa
5. **Rehinli İşlemler**: Emanet alınan paralar

#### VERECEKLER (Payables)
1. **Tedarikçi Borcu**: Mal/hizmet aldık, henüz ödeme yapmadık
2. **Alınan Borç**: Dışarıdan borç aldık
3. **Taksitli Alım**: Bir şey satın aldık, taksitle ödeyeceğiz
4. **Ödenecek Faturalar**: Elektrik, su, vs.

---

## 🗄️ VERİTABANI YAPISI

### 1. ALACAKLAR Tablosu

```sql
CREATE TABLE alacaklar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Temel Bilgiler
    alacak_turu TEXT NOT NULL,          -- 'Kira Kaporu', 'Borç', 'Taksitli Satış', 'Emanet', 'Diğer'
    aciklama TEXT NOT NULL,             -- Detaylı açıklama
    
    -- Taraflar
    kisi_kurum TEXT NOT NULL,           -- Kimden alacağız
    kisi_telefon TEXT,                  -- İletişim
    kisi_adres TEXT,                    -- Adres
    uye_id INTEGER,                     -- Eğer üye ise bağlantı (NULL olabilir)
    
    -- Mali Bilgiler
    toplam_tutar REAL NOT NULL,         -- Toplam alacak tutarı
    tahsil_edilen REAL DEFAULT 0,       -- Şu ana kadar tahsil edilen
    kalan_tutar REAL NOT NULL,          -- Kalan alacak
    para_birimi TEXT DEFAULT 'TRY',     -- TRY, USD, EUR
    
    -- Tarihler
    alacak_tarihi TEXT NOT NULL,        -- Alacağın doğduğu tarih
    vade_tarihi TEXT,                   -- Son ödeme tarihi (NULL olabilir)
    
    -- Durum
    durum TEXT DEFAULT 'Bekliyor',      -- 'Bekliyor', 'Kısmi', 'Tahsil Edildi', 'İptal', 'Gecikmiş'
    
    -- İlişkili İşlemler
    gelir_id INTEGER,                   -- İlk kapora geliri (NULL olabilir)
    senet_no TEXT,                      -- Senet varsa numarası
    
    -- Notlar
    notlar TEXT,
    
    -- Sistem
    olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
    kullanici_id INTEGER,
    
    FOREIGN KEY (uye_id) REFERENCES uyeler(id),
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id),
    FOREIGN KEY (gelir_id) REFERENCES gelirler(id)
);
```

### 2. ALACAK_TAHSILATLARI Tablosu

```sql
CREATE TABLE alacak_tahsilatlari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    alacak_id INTEGER NOT NULL,         -- Hangi alacağa ait
    
    -- Tahsilat Bilgileri
    tutar REAL NOT NULL,                -- Tahsil edilen tutar
    para_birimi TEXT DEFAULT 'TRY',
    tahsilat_tarihi TEXT NOT NULL,      -- Tahsilat tarihi
    
    -- Kasa İşlemi
    kasa_id INTEGER NOT NULL,           -- Hangi kasaya girdi
    gelir_id INTEGER NOT NULL,          -- Otomatik oluşturulan gelir kaydı
    
    -- Ödeme Şekli
    odeme_sekli TEXT DEFAULT 'Nakit',   -- 'Nakit', 'Banka', 'Kredi Kartı', 'Senet'
    
    -- Notlar
    aciklama TEXT,
    
    -- Sistem
    olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
    kullanici_id INTEGER,
    
    FOREIGN KEY (alacak_id) REFERENCES alacaklar(id),
    FOREIGN KEY (kasa_id) REFERENCES kasalar(id),
    FOREIGN KEY (gelir_id) REFERENCES gelirler(id),
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
);
```

### 3. VERECEKLER Tablosu

```sql
CREATE TABLE verecekler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Temel Bilgiler
    verecek_turu TEXT NOT NULL,         -- 'Tedarikçi', 'Alınan Borç', 'Taksitli Alım', 'Fatura', 'Diğer'
    aciklama TEXT NOT NULL,
    
    -- Taraflar
    kisi_kurum TEXT NOT NULL,           -- Kime borçluyuz
    kisi_telefon TEXT,
    kisi_adres TEXT,
    
    -- Mali Bilgiler
    toplam_tutar REAL NOT NULL,         -- Toplam borç tutarı
    odenen REAL DEFAULT 0,              -- Şu ana kadar ödenen
    kalan_tutar REAL NOT NULL,          -- Kalan borç
    para_birimi TEXT DEFAULT 'TRY',
    
    -- Tarihler
    verecek_tarihi TEXT NOT NULL,       -- Borcun doğduğu tarih
    vade_tarihi TEXT,                   -- Son ödeme tarihi
    
    -- Durum
    durum TEXT DEFAULT 'Bekliyor',      -- 'Bekliyor', 'Kısmi', 'Ödendi', 'İptal', 'Gecikmiş'
    
    -- İlişkili İşlemler
    gider_id INTEGER,                   -- İlgili gider (NULL olabilir)
    fatura_no TEXT,
    
    -- Notlar
    notlar TEXT,
    
    -- Sistem
    olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
    kullanici_id INTEGER,
    
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id),
    FOREIGN KEY (gider_id) REFERENCES giderler(id)
);
```

### 4. VERECEK_ODEMELERI Tablosu

```sql
CREATE TABLE verecek_odemeleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    verecek_id INTEGER NOT NULL,        -- Hangi verece ait
    
    -- Ödeme Bilgileri
    tutar REAL NOT NULL,                -- Ödenen tutar
    para_birimi TEXT DEFAULT 'TRY',
    odeme_tarihi TEXT NOT NULL,         -- Ödeme tarihi
    
    -- Kasa İşlemi
    kasa_id INTEGER NOT NULL,           -- Hangi kasadan çıktı
    gider_id INTEGER NOT NULL,          -- Otomatik oluşturulan gider kaydı
    
    -- Ödeme Şekli
    odeme_sekli TEXT DEFAULT 'Nakit',
    
    -- Notlar
    aciklama TEXT,
    
    -- Sistem
    olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
    kullanici_id INTEGER,
    
    FOREIGN KEY (verecek_id) REFERENCES verecekler(id),
    FOREIGN KEY (kasa_id) REFERENCES kasalar(id),
    FOREIGN KEY (gider_id) REFERENCES giderler(id),
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
);
```

---

## 🔄 İŞ AKIŞLARI

### SENARYO 1: Kira Kaporu İşlemi

#### Adım 1: Kira Sözleşmesi ve Kapora
```python
# 1. Alacak Kaydı Oluştur
alacak = {
    'alacak_turu': 'Kira Kaporu',
    'aciklama': '2025 Yıllık Dernek Binası Kirası',
    'kisi_kurum': 'ABC Şirketi',
    'toplam_tutar': 50000.00,  # Yıllık kira
    'tahsil_edilen': 5000.00,  # Kapora
    'kalan_tutar': 45000.00,   # Kalan
    'alacak_tarihi': '2025-01-01',
    'vade_tarihi': '2025-12-31',
    'durum': 'Kısmi'
}

# 2. Kapora Gelir Kaydı (Otomatik)
gelir = {
    'gelir_turu': 'Kira Geliri',
    'tutar': 5000.00,
    'kasa_id': 1,  # Ana kasa
    'aciklama': 'ABC Şirketi kira kaporu',
    'gelir_tarihi': '2025-01-01'
}
# → Kasaya 5000 TL ekle

# 3. Tahsilat Kaydı
tahsilat = {
    'alacak_id': alacak_id,
    'tutar': 5000.00,
    'kasa_id': 1,
    'gelir_id': gelir_id,
    'tahsilat_tarihi': '2025-01-01'
}
```

#### Adım 2: Aylık Kira Ödemeleri
```python
# Her ay kira geldiğinde
for ay in range(12):
    tahsilat = {
        'alacak_id': alacak_id,
        'tutar': 3750.00,  # Aylık (45000/12)
        'tahsilat_tarihi': f'2025-{ay+1:02d}-05',
        'kasa_id': 1
    }
    # Otomatik gelir kaydı oluştur
    # Alacağın kalan_tutar değerini güncelle
    # Durum: 'Kısmi' → Son ödeme 'Tahsil Edildi'
```

#### Adım 3: İptal Durumu
```python
# Kiracı iptal etmek isterse
# 1. Kapora iade edilmeyebilir (sözleşmeye göre)
# 2. Alacak durumu 'İptal' olur
# 3. Eğer iade varsa:
gider = {
    'gider_turu': 'İade',
    'tutar': 5000.00,  # Kapora iadesi
    'kasa_id': 1,
    'aciklama': 'Kira kaporu iadesi - ABC Şirketi'
}
# Kasadan 5000 TL düş
```

---

### SENARYO 2: Borç Verme İşlemi

#### Adım 1: Borç Ver
```python
# 1. Gider Kaydı (Borç veriyoruz, kasadan çıkıyor)
gider = {
    'gider_turu': 'Verilen Borç',
    'tutar': 10000.00,
    'kasa_id': 1,
    'aciklama': 'Mehmet Bey\'e borç',
    'gider_tarihi': '2025-01-15'
}
# → Kasadan 10000 TL çıkar

# 2. Alacak Kaydı Oluştur
alacak = {
    'alacak_turu': 'Borç',
    'aciklama': 'Mehmet Bey - 10 taksit',
    'kisi_kurum': 'Mehmet Yılmaz',
    'kisi_telefon': '0555 111 22 33',
    'uye_id': 42,  # Eğer üye ise
    'toplam_tutar': 10000.00,
    'tahsil_edilen': 0,
    'kalan_tutar': 10000.00,
    'alacak_tarihi': '2025-01-15',
    'vade_tarihi': '2025-11-15',  # 10 ay sonra
    'durum': 'Bekliyor'
}
```

#### Adım 2: Parça Parça Geri Gelme
```python
# Mehmet her ay 1000 TL ödüyor
for ay in range(10):
    tahsilat = {
        'alacak_id': alacak_id,
        'tutar': 1000.00,
        'tahsilat_tarihi': f'2025-{ay+2:02d}-15',
        'kasa_id': 1,
        'odeme_sekli': 'Banka',
        'aciklama': f'{ay+1}. taksit'
    }
    
    # Otomatik işlemler:
    # 1. Gelir kaydı oluştur (Gelir Türü: 'Borç Tahsilatı')
    # 2. Kasaya para ekle
    # 3. Alacak.tahsil_edilen += 1000
    # 4. Alacak.kalan_tutar -= 1000
    # 5. Son taksitte: Alacak.durum = 'Tahsil Edildi'
```

---

## 💻 PYTHON SINIF YAPISI

### AlacakYoneticisi

```python
class AlacakYoneticisi:
    """Alacak takip yöneticisi"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def alacak_ekle(self, alacak_turu: str, aciklama: str, kisi_kurum: str,
                    toplam_tutar: float, para_birimi: str = 'TRY',
                    vade_tarihi: str = None, ilk_tahsilat: float = 0,
                    kasa_id: int = None, **kwargs) -> int:
        """
        Yeni alacak ekle
        
        Parametreler:
        - ilk_tahsilat: İlk ödeme varsa (kapora gibi)
        - kasa_id: İlk ödeme hangi kasaya
        
        Returns:
        - alacak_id
        """
        cursor = self.db.conn.cursor()
        
        kalan = toplam_tutar - ilk_tahsilat
        durum = 'Kısmi' if ilk_tahsilat > 0 else 'Bekliyor'
        
        cursor.execute("""
            INSERT INTO alacaklar 
            (alacak_turu, aciklama, kisi_kurum, toplam_tutar, 
             tahsil_edilen, kalan_tutar, para_birimi, 
             alacak_tarihi, vade_tarihi, durum, ...)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ...)
        """, (alacak_turu, aciklama, kisi_kurum, toplam_tutar,
              ilk_tahsilat, kalan, para_birimi, 
              datetime.now().date(), vade_tarihi, durum, ...))
        
        alacak_id = cursor.lastrowid
        
        # İlk tahsilat varsa kaydet
        if ilk_tahsilat > 0 and kasa_id:
            self.tahsilat_ekle(alacak_id, ilk_tahsilat, kasa_id,
                              datetime.now().date())
        
        self.db.conn.commit()
        return alacak_id
    
    def tahsilat_ekle(self, alacak_id: int, tutar: float, 
                      kasa_id: int, tahsilat_tarihi: str,
                      odeme_sekli: str = 'Nakit',
                      aciklama: str = "") -> int:
        """
        Alacak tahsilatı ekle
        
        İşlemler:
        1. Gelir kaydı oluştur
        2. Kasaya para ekle
        3. Alacak bilgilerini güncelle
        4. Tahsilat kaydı oluştur
        """
        cursor = self.db.conn.cursor()
        
        # 1. Alacak bilgisini al
        cursor.execute("SELECT * FROM alacaklar WHERE id=?", (alacak_id,))
        alacak = dict(cursor.fetchone())
        
        # 2. Gelir kaydı oluştur
        gelir_yoneticisi = GelirYoneticisi(self.db)
        gelir_id = gelir_yoneticisi.gelir_ekle(
            gelir_turu='Alacak Tahsilatı',
            tutar=tutar,
            kasa_id=kasa_id,
            para_birimi=alacak['para_birimi'],
            aciklama=f"{alacak['kisi_kurum']} - {alacak['aciklama']} tahsilatı",
            gelir_tarihi=tahsilat_tarihi
        )
        
        # 3. Tahsilat kaydı
        cursor.execute("""
            INSERT INTO alacak_tahsilatlari
            (alacak_id, tutar, para_birimi, tahsilat_tarihi,
             kasa_id, gelir_id, odeme_sekli, aciklama)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (alacak_id, tutar, alacak['para_birimi'], 
              tahsilat_tarihi, kasa_id, gelir_id, 
              odeme_sekli, aciklama))
        
        tahsilat_id = cursor.lastrowid
        
        # 4. Alacak bilgisini güncelle
        yeni_tahsil = alacak['tahsil_edilen'] + tutar
        yeni_kalan = alacak['toplam_tutar'] - yeni_tahsil
        
        if yeni_kalan <= 0:
            durum = 'Tahsil Edildi'
        elif yeni_tahsil > 0:
            durum = 'Kısmi'
        else:
            durum = 'Bekliyor'
        
        cursor.execute("""
            UPDATE alacaklar
            SET tahsil_edilen = ?,
                kalan_tutar = ?,
                durum = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (yeni_tahsil, yeni_kalan, durum, alacak_id))
        
        self.db.conn.commit()
        return tahsilat_id
    
    def alacak_iptal(self, alacak_id: int, iade_tutari: float = 0,
                     kasa_id: int = None, aciklama: str = "") -> bool:
        """
        Alacağı iptal et
        
        - İade varsa gider kaydı oluştur
        - Durumu 'İptal' yap
        """
        cursor = self.db.conn.cursor()
        
        if iade_tutari > 0 and kasa_id:
            # İade gideri
            gider_yoneticisi = GiderYoneticisi(self.db)
            gider_yoneticisi.gider_ekle(
                gider_turu='İade',
                tutar=iade_tutari,
                kasa_id=kasa_id,
                aciklama=f"Alacak iadesi - {aciklama}",
                gider_tarihi=datetime.now().date()
            )
        
        cursor.execute("""
            UPDATE alacaklar
            SET durum = 'İptal',
                notlar = notlar || ' | İPTAL: ' || ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (aciklama, alacak_id))
        
        self.db.conn.commit()
        return True
    
    def liste_getir(self, durum: str = None, vade_gecmis: bool = False) -> List[Dict]:
        """Alacak listesi"""
        cursor = self.db.conn.cursor()
        
        sql = "SELECT * FROM alacaklar WHERE 1=1"
        params = []
        
        if durum:
            sql += " AND durum = ?"
            params.append(durum)
        
        if vade_gecmis:
            sql += " AND vade_tarihi < date('now') AND durum != 'Tahsil Edildi'"
        
        sql += " ORDER BY alacak_tarihi DESC"
        
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def ozet(self) -> Dict:
        """Alacak özeti"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as toplam_alacak,
                SUM(CASE WHEN durum='Bekliyor' THEN 1 ELSE 0 END) as bekleyen,
                SUM(CASE WHEN durum='Kısmi' THEN 1 ELSE 0 END) as kismi,
                SUM(CASE WHEN durum='Tahsil Edildi' THEN 1 ELSE 0 END) as tahsil_edildi,
                SUM(kalan_tutar) as toplam_kalan_tutar,
                SUM(CASE WHEN vade_tarihi < date('now') AND durum != 'Tahsil Edildi' 
                    THEN kalan_tutar ELSE 0 END) as vade_gecmis_tutar
            FROM alacaklar
            WHERE durum != 'İptal'
        """)
        
        return dict(cursor.fetchone())
    
    def tahsilat_gecmisi(self, alacak_id: int) -> List[Dict]:
        """Bir alacağın tahsilat geçmişi"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT t.*, k.kasa_adi
            FROM alacak_tahsilatlari t
            LEFT JOIN kasalar k ON t.kasa_id = k.id
            WHERE t.alacak_id = ?
            ORDER BY t.tahsilat_tarihi DESC
        """, (alacak_id,))
        
        return [dict(row) for row in cursor.fetchall()]
```

### VerecekYoneticisi

```python
class VerecekYoneticisi:
    """Verecek (borç) takip yöneticisi"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def verecek_ekle(self, verecek_turu: str, aciklama: str, 
                     kisi_kurum: str, toplam_tutar: float,
                     para_birimi: str = 'TRY',
                     vade_tarihi: str = None, **kwargs) -> int:
        """Yeni borç ekle"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            INSERT INTO verecekler
            (verecek_turu, aciklama, kisi_kurum, toplam_tutar,
             odenen, kalan_tutar, para_birimi, verecek_tarihi,
             vade_tarihi, durum, ...)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, 'Bekliyor', ...)
        """, (verecek_turu, aciklama, kisi_kurum, toplam_tutar,
              toplam_tutar, para_birimi, datetime.now().date(),
              vade_tarihi, ...))
        
        verecek_id = cursor.lastrowid
        self.db.conn.commit()
        return verecek_id
    
    def odeme_yap(self, verecek_id: int, tutar: float,
                  kasa_id: int, odeme_tarihi: str,
                  odeme_sekli: str = 'Nakit',
                  aciklama: str = "") -> int:
        """
        Borç ödemesi yap
        
        İşlemler:
        1. Gider kaydı oluştur
        2. Kasadan para çıkar
        3. Verecek bilgilerini güncelle
        4. Ödeme kaydı oluştur
        """
        cursor = self.db.conn.cursor()
        
        # 1. Verecek bilgisini al
        cursor.execute("SELECT * FROM verecekler WHERE id=?", (verecek_id,))
        verecek = dict(cursor.fetchone())
        
        # 2. Gider kaydı oluştur
        gider_yoneticisi = GiderYoneticisi(self.db)
        gider_id = gider_yoneticisi.gider_ekle(
            gider_turu='Borç Ödemesi',
            tutar=tutar,
            kasa_id=kasa_id,
            para_birimi=verecek['para_birimi'],
            aciklama=f"{verecek['kisi_kurum']} - {verecek['aciklama']} ödemesi",
            gider_tarihi=odeme_tarihi
        )
        
        # 3. Ödeme kaydı
        cursor.execute("""
            INSERT INTO verecek_odemeleri
            (verecek_id, tutar, para_birimi, odeme_tarihi,
             kasa_id, gider_id, odeme_sekli, aciklama)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (verecek_id, tutar, verecek['para_birimi'],
              odeme_tarihi, kasa_id, gider_id,
              odeme_sekli, aciklama))
        
        odeme_id = cursor.lastrowid
        
        # 4. Verecek bilgisini güncelle
        yeni_odenen = verecek['odenen'] + tutar
        yeni_kalan = verecek['toplam_tutar'] - yeni_odenen
        
        if yeni_kalan <= 0:
            durum = 'Ödendi'
        elif yeni_odenen > 0:
            durum = 'Kısmi'
        else:
            durum = 'Bekliyor'
        
        cursor.execute("""
            UPDATE verecekler
            SET odenen = ?,
                kalan_tutar = ?,
                durum = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (yeni_odenen, yeni_kalan, durum, verecek_id))
        
        self.db.conn.commit()
        return odeme_id
    
    # ... liste_getir, ozet, odeme_gecmisi metodları (benzer)
```

---

## 🎨 KULLANICI ARAYÜZÜ

### 1. Ana Alacak-Verecek Dashboard

```
┌─────────────────────────────────────────────────────┐
│ 💰 ALACAK-VERECEK YÖNETİMİ                          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  📊 ALACAKLAR                 📉 VERECEKLER         │
│  ┌──────────────────┐        ┌──────────────────┐  │
│  │ Toplam Alacak    │        │ Toplam Borç      │  │
│  │ 125,000 ₺        │        │ 85,000 ₺         │  │
│  ├──────────────────┤        ├──────────────────┤  │
│  │ Bekleyen: 75,000 │        │ Bekleyen: 50,000 │  │
│  │ Kısmi: 45,000    │        │ Kısmi: 30,000    │  │
│  │ Vade Geçmiş: ⚠️  │        │ Vade Geçmiş: ⚠️  │  │
│  │ 15,000 ₺         │        │ 5,000 ₺          │  │
│  └──────────────────┘        └──────────────────┘  │
│                                                      │
│  [➕ Yeni Alacak]   [💰 Tahsilat]                   │
│  [➕ Yeni Verecek]  [💸 Ödeme]                      │
│                                                      │
├─────────────────────────────────────────────────────┤
│ ALACAK LİSTESİ                                      │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Kişi/Kurum    │Tür      │Tutar    │Kalan │Vade │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ ABC Şirketi   │Kira     │50,000 ₺ │45K   │⚠️   │ │
│ │ Mehmet Yılmaz │Borç     │10,000 ₺ │8K    │✅   │ │
│ │ XYZ Ltd.      │Emanet   │5,000 ₺  │5K    │✅   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ VERECEK LİSTESİ                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Kişi/Kurum    │Tür      │Tutar    │Kalan │Vade │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ Enerji AŞ     │Fatura   │3,000 ₺  │3K    │⚠️   │ │
│ │ Tedarikçi A   │Malzeme  │15,000 ₺ │10K   │✅   │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 2. Yeni Alacak Formu

```
┌──────────────────────────────────────────┐
│ ➕ YENİ ALACAK EKLE                      │
├──────────────────────────────────────────┤
│                                           │
│ Alacak Türü: [▼ Kira Kaporu]            │
│              - Kira Kaporu                │
│              - Borç                       │
│              - Taksitli Satış             │
│              - Emanet                     │
│              - Diğer                      │
│                                           │
│ Kişi/Kurum: [________________]           │
│ Telefon:    [________________]           │
│                                           │
│ Toplam Tutar: [_______] [TRY ▼]         │
│                                           │
│ Vade Tarihi: [📅 __/__/____]            │
│                                           │
│ Açıklama:                                │
│ [_________________________________]      │
│ [_________________________________]      │
│                                           │
│ ✅ İlk Ödeme (Kapora) Var               │
│    Tutar: [_______] ₺                    │
│    Kasa:  [▼ Ana Kasa]                  │
│                                           │
│ [💾 Kaydet] [❌ İptal]                  │
└──────────────────────────────────────────┘
```

### 3. Tahsilat/Ödeme Formu

```
┌──────────────────────────────────────────┐
│ 💰 TAHSİLAT YAP                          │
├──────────────────────────────────────────┤
│                                           │
│ Alacak: ABC Şirketi - Kira               │
│ Toplam: 50,000 ₺                         │
│ Tahsil: 5,000 ₺                          │
│ Kalan:  45,000 ₺                         │
│                                           │
│ Tahsilat Tutarı: [_______] ₺            │
│ Tarih: [📅 __/__/____]                  │
│ Kasa:  [▼ Ana Kasa]                     │
│ Ödeme Şekli: [▼ Nakit]                  │
│                                           │
│ Açıklama: [___________________]          │
│                                           │
│ [💾 Tahsil Et] [❌ İptal]               │
└──────────────────────────────────────────┘
```

---

## 📈 RAPORLAR

### 1. Alacak-Verecek Özet Raporu

```python
def alacak_verecek_ozet() -> Dict:
    """Genel özet"""
    return {
        'alacaklar': {
            'toplam': 125000,
            'tahsil_edilen': 35000,
            'kalan': 90000,
            'vade_gecmis': 15000,
            'adet': {
                'bekleyen': 5,
                'kismi': 3,
                'tahsil_edildi': 12
            }
        },
        'verecekler': {
            'toplam': 85000,
            'odenen': 25000,
            'kalan': 60000,
            'vade_gecmis': 5000,
            'adet': {
                'bekleyen': 4,
                'kismi': 2,
                'odendi': 8
            }
        },
        'net_durum': {
            'alacak_fazlasi': 30000,  # alacak_kalan - verecek_kalan
            'durum': 'Pozitif'  # veya 'Negatif'
        }
    }
```

### 2. Vade Takip Raporu

```python
def vade_takip() -> Dict:
    """Vadesi yaklaşan/geçen işlemler"""
    return {
        'vade_gecmis_alacaklar': [
            {
                'kisi': 'ABC Şirketi',
                'tutar': 15000,
                'vade': '2025-11-30',
                'gecikme_gun': 12
            }
        ],
        'yaklaşan_alacaklar': [
            # Önümüzdeki 7 gün
        ],
        'vade_gecmis_verecekler': [...],
        'yaklaşan_verecekler': [...]
    }
```

### 3. Mali Tablolara Entegrasyon

Bilanço'ya eklenecek:

```
VARLIKLAR
├─ Dönen Varlıklar
│  ├─ Kasalar: 50,000 ₺
│  ├─ Aidat Alacaklar��: 25,000 ₺
│  └─ Diğer Alacaklar: 90,000 ₺  ← YENİ
└─ TOPLAM VARLIK: 165,000 ₺

KAYNAKLAR
├─ Kısa Vadeli Yükümlülükler
│  └─ Borçlar: 60,000 ₺  ← YENİ
├─ Öz Kaynaklar
│  ├─ Sermaye: 80,000 ₺
│  └─ Dönem Karı: 25,000 ₺
└─ TOPLAM KAYNAK: 165,000 ₺
```

---

## ⚙️ UYGULAMA ÖNERİLERİ

### 1. Otomatik Hatırlatmalar
```python
def vade_hatirlat():
    """Günlük kontrol - vade yaklaşanlar için bildirim"""
    # 7 gün öncesinden uyarı ver
    # Email/SMS gönder
```

### 2. Toplu İşlemler
```python
def toplu_tahsilat(alacak_id_list: List[int], tutar_list: List[float]):
    """Birden fazla alacak için tek seferde tahsilat"""
```

### 3. Excel/PDF Export
```python
def alacak_verecek_rapor_export(format: str = 'excel'):
    """Alacak-verecek raporunu dışa aktar"""
```

### 4. Dashboard Widget'ı
```python
class AlacakVerecekDashboard(CardWidget):
    """Ana dashboard'a eklenecek özet widget"""
    # Toplam alacak/verecek
    # Vade geçmiş uyarıları
    # Hızlı işlem butonları
```

---

## 🔗 MEVCUT SİSTEMLE ENTEGRASYON

### 1. Gelir Sistemi
- Alacak tahsilatı → Otomatik gelir kaydı
- Gelir türü: "Alacak Tahsilatı"
- Kasa bakiyesi otomatik güncellenir

### 2. Gider Sistemi
- Borç ödemesi → Otomatik gider kaydı
- Gider türü: "Borç Ödemesi"
- Verilen borç → Gider kaydı

### 3. Mali Tablolar
- Bilanço'ya alacaklar/borçlar eklenir
- Nakit akış tablosuna tahsilat/ödeme akışları

### 4. Üye Sistemi
- Üyelere verilen/alınan borçlar bağlanabilir
- Üye detay sayfasında alacak/verecek sekmesi

---

## 🚀 UYGULAMA AŞAMALARI

### Faz 1: Veritabanı (1 gün)
- [x] 4 tablo oluştur
- [x] Migration script

### Faz 2: Backend (2 gün)
- [ ] AlacakYoneticisi sınıfı
- [ ] VerecekYoneticisi sınıfı
- [ ] Test case'ler

### Faz 3: UI (2-3 gün)
- [ ] ui_alacak_verecek.py
- [ ] Dashboard widget
- [ ] Form sayfaları
- [ ] Raporlar entegrasyonu

### Faz 4: Mali Tablolar Entegrasyonu (1 gün)
- [ ] Bilanço'ya alacak/verecek ekle
- [ ] Nakit akışı güncelle

### Faz 5: Test & Debug (1 gün)
- [ ] Gerçek senaryolarla test
- [ ] Vade takibi test
- [ ] Çoklu tahsilat/ödeme test

---

## 📝 NOTLAR

### Avantajlar
✅ Profesyonel alacak-verecek takibi
✅ Otomatik gelir-gider kayıtları
✅ Vade takibi ve uyarılar
✅ Mali tablolara tam entegrasyon
✅ Taksitli işlem desteği
✅ İptal/iade senaryoları
✅ Detaylı raporlama

### Dikkat Edilmesi Gerekenler
⚠️ Para birimi dönüşümleri
⚠️ Vade geçmiş hesaplamaları
⚠️ Kısmi tahsilat/ödeme durumları
⚠️ Alacak-Gelir ilişkisi (double entry önleme)
⚠️ Verecek-Gider ilişkisi

### Gelecek Geliştirmeler
🔮 Faiz hesaplama (gecikme vs.)
🔮 Senet takibi
🔮 Çek takibi
🔮 Teminat/rehin yönetimi
🔮 Mahsup işlemleri (alacak-verecek)
🔮 Döviz kuru entegrasyonu
🔮 SMS/Email otomatik hatırlatma

---

**HAZIR MIYIZ? İŞE BAŞLAYALIM! 🚀**
