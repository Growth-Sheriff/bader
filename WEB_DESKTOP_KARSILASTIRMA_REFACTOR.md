# 🔄 BADER Web vs Desktop Karşılaştırma ve Kapsamlı Refactor Planı

**Oluşturulma Tarihi:** 30 Aralık 2025  
**Versiyon:** 1.0  
**Amaç:** Masaüstü uygulamasındaki tüm özelliklerin web uygulamasına eksiksiz taşınması

---

## 📊 GENEL DURUM ÖZETİ

| Modül | Masaüstü | Web API | Web Frontend | Eksik % |
|-------|----------|---------|--------------|---------|
| **Üye Yönetimi** | ✅ 26 alan | ⚠️ 8 alan | ⚠️ 6 alan | **70%** |
| **Aidat Sistemi** | ✅ Tam | ⚠️ Kısmi | ⚠️ Kısmi | **60%** |
| **Gelir Yönetimi** | ✅ 12 alan | ⚠️ 8 alan | ⚠️ 6 alan | **40%** |
| **Gider Yönetimi** | ✅ 10 alan | ⚠️ 7 alan | ⚠️ 5 alan | **40%** |
| **Kasa Yönetimi** | ✅ Tam | ⚠️ Basit | ❌ Yok | **80%** |
| **Virman İşlemleri** | ✅ Tam | ⚠️ Basit | ⚠️ Basit | **50%** |
| **Etkinlikler** | ✅ Tam | ⚠️ Basit | ⚠️ Basit | **60%** |
| **Toplantılar** | ✅ Tam | ❌ Yok | ❌ Yok | **100%** |
| **Bütçe Planlama** | ✅ Tam | ⚠️ Basit | ⚠️ Basit | **70%** |
| **Belgeler/OCR** | ✅ Tam | ⚠️ Kısmi | ❌ Yok | **80%** |
| **Alacak-Verecek** | ✅ Tam | ❌ Yok | ❌ Yok | **100%** |
| **Köy İşlemleri** | ✅ Tam | ⚠️ Basit | ⚠️ Basit | **60%** |
| **Raporlar** | ✅ 10+ rapor | ⚠️ 2 rapor | ⚠️ 2 rapor | **80%** |
| **Mali Tablolar** | ✅ Tam | ❌ Yok | ❌ Yok | **100%** |
| **Kullanıcı/Yetki** | ✅ Tam | ⚠️ Basit | ❌ Yok | **70%** |
| **Devir İşlemleri** | ✅ Tam | ⚠️ Basit | ⚠️ Basit | **60%** |
| **Tahakkuk Sistemi** | ✅ Tam | ❌ Yok | ⚠️ Rapor var | **90%** |

---

## 1️⃣ ÜYE YÖNETİMİ - KRİTİK FARKLAR

### Masaüstü (database.py - `uyeler` tablosu) - 26+ Alan:

```
TEMEL:
- uye_id, uye_no, tc_kimlik, ad_soyad, durum, uyelik_tipi

İLETİŞİM:
- telefon, telefon2, email

KİŞİSEL:
- cinsiyet, dogum_tarihi, dogum_yeri, kan_grubu
- aile_durumu, cocuk_sayisi

MESLEK:
- egitim_durumu, meslek, is_yeri

ADRES:
- il, ilce, mahalle, adres, posta_kodu

AİDAT:
- ozel_aidat_tutari, aidat_indirimi_yuzde

DİĞER:
- referans_uye_id, notlar, kayit_tarihi
- ayrilma_tarihi, ayrilma_nedeni
```

### Web API (main_api.py - `members` tablosu) - 8 Alan:

```
id, customer_id, member_no, full_name, tc_no, phone, 
email, address, birth_date, join_date, leave_date, 
status, membership_fee, notes, extra_data
```

### 🔴 EKSİK ALANLAR (Web'e eklenmeli):

| # | Alan | Açıklama | Öncelik |
|---|------|----------|---------|
| 1 | `phone2` | 2. telefon | Yüksek |
| 2 | `gender` | Cinsiyet | Yüksek |
| 3 | `birth_place` | Doğum yeri | Orta |
| 4 | `blood_type` | Kan grubu | Orta |
| 5 | `marital_status` | Medeni durum | Orta |
| 6 | `child_count` | Çocuk sayısı | Düşük |
| 7 | `education` | Eğitim durumu | Orta |
| 8 | `occupation` | Meslek | Orta |
| 9 | `workplace` | İş yeri | Düşük |
| 10 | `city` | İl | Yüksek |
| 11 | `district` | İlçe | Yüksek |
| 12 | `neighborhood` | Mahalle | Orta |
| 13 | `postal_code` | Posta kodu | Düşük |
| 14 | `membership_type` | Üyelik tipi (Asil/Onursal/Fahri/Kurumsal) | Yüksek |
| 15 | `special_fee` | Özel aidat tutarı | Yüksek |
| 16 | `fee_discount` | Aidat indirimi % | Orta |
| 17 | `referrer_id` | Referans üye | Düşük |
| 18 | `leave_reason` | Ayrılma nedeni | Orta |

---

## 2️⃣ AİDAT SİSTEMİ - KRİTİK FARKLAR

### Masaüstü Özellikleri:

1. **Aidat Takip Tablosu (`aidat_takip`):**
   - Üye bazlı yıllık aidat kaydı
   - Yıllık tutar, kalan borç
   - Durum (Tamamlandı/Kısmi/Eksik)
   - Otomatik gelir kaydı oluşturma
   - Gelir ID bağlantısı

2. **Aidat Ödemeleri (`aidat_odemeleri`):**
   - Birden fazla ödeme kaydı
   - Tahsilat türü (Nakit/Havale/Kart)
   - Dekont numarası
   - Otomatik durum güncelleme

3. **Çok Yıllık Ödeme:**
   - `coklu_odeme_grup_id`
   - Peşin tahsilat desteği
   - Tahakkuk durumu (Normal/Peşin/Geriye Dönük)

### Web API Durumu:

```python
class Due(Base):
    id, customer_id, member_id, year, 
    yearly_amount, paid_amount, status
```

### 🔴 EKSİK ÖZELLİKLER:

| # | Özellik | Açıklama | Öncelik |
|---|---------|----------|---------|
| 1 | `DuePayment` tablosu | Aidat ödemeleri detay | **Kritik** |
| 2 | Otomatik Gelir Kaydı | Aidat tamamlandığında | **Kritik** |
| 3 | Tahsilat Türü | Nakit/Havale/Kart | Yüksek |
| 4 | Dekont Numarası | Her ödeme için | Orta |
| 5 | Çok Yıllık Ödeme | 10 yıllık aidat desteği | Orta |
| 6 | Toplu Aidat Oluşturma | Tüm üyeler için | Yüksek |
| 7 | Üye Özel Aidat | Varsayılandan farklı tutar | Orta |

---

## 3️⃣ GELİR YÖNETİMİ - FARKLAR

### Masaüstü:

```python
gelirler:
- gelir_id, tarih, belge_no, gelir_turu
- aciklama, tutar, kasa_id
- tahsil_eden, notlar, dekont_no
- aidat_id (aidat bağlantısı)
- ait_oldugu_yil (yıl bazlı muhasebe)
- tahakkuk_durumu (NORMAL/PEŞİN/GERİYE_DÖNÜK)
- coklu_odeme_grup_id
```

### Web API:

```python
incomes:
- id, customer_id, member_id, category
- amount, currency, date, description
- receipt_no, cash_account, document_path
- fiscal_year
```

### 🔴 EKSİK ALANLAR:

| # | Alan | Açıklama |
|---|------|----------|
| 1 | `due_id` | Aidat bağlantısı |
| 2 | `collected_by` | Tahsil eden kişi |
| 3 | `receipt_type` | Tahsilat türü |
| 4 | `belongs_to_year` | Ait olduğu yıl |
| 5 | `accrual_status` | Tahakkuk durumu |
| 6 | `multi_payment_group` | Grup ID |

---

## 4️⃣ GİDER YÖNETİMİ - FARKLAR

### Masaüstü:

```python
giderler:
- gider_id, tarih, islem_no, gider_turu
- aciklama, tutar, kasa_id, odeyen
- notlar, ait_oldugu_yil, tahakkuk_durumu
```

### Web API:

```python
expenses:
- id, customer_id, category, amount
- currency, date, description
- invoice_no, vendor, cash_account
- document_path, fiscal_year
```

### 🔴 EKSİK:

| # | Alan | Açıklama |
|---|------|----------|
| 1 | `paid_by` | Ödeyen kişi |
| 2 | `belongs_to_year` | Ait olduğu yıl |
| 3 | `accrual_status` | Tahakkuk durumu |
| 4 | Dinamik gider türleri | Tablo bazlı |

---

## 5️⃣ KASA YÖNETİMİ - FARKLAR

### Masaüstü:

```python
kasalar:
- kasa_id, kasa_adi, para_birimi
- devir_bakiye, aktif, aciklama
- serbest_devir_bakiye
- tahakkuk_toplami
- son_devir_tarihi

Fonksiyonlar:
- kasa_bakiye_hesapla()
- kasa_bakiye_tip(fiziksel/serbest)
- kasa_tahakkuk_detay()
- tum_kasalar_ozet()
```

### Web API:

```python
cash_accounts:
- id, customer_id, name, account_type, balance
```

### 🔴 EKSİK:

| # | Özellik |
|---|---------|
| 1 | Para birimi desteği |
| 2 | Devir bakiye |
| 3 | Aktif/Pasif durumu |
| 4 | Bakiye hesaplama fonksiyonları |
| 5 | Tahakkuk takibi |
| 6 | Serbest bakiye ayrımı |

---

## 6️⃣ VİRMAN İŞLEMLERİ

### Masaüstü:

```python
virmanlar:
- virman_id, tarih, gonderen_kasa_id
- alan_kasa_id, tutar, aciklama
```

### Web API: ✅ Mevcut (basit)

---

## 7️⃣ ETKİNLİK YÖNETİMİ

### Masaüstü:

```python
etkinlikler:
- etkinlik_turu (DÜĞÜN, NİŞAN, KINA, SÜNNET, CENAZE, vb.)
- baslik, aciklama, tarih, saat, bitis_tarihi
- mekan, durum, katilimci_sayisi
- tahmini_gelir, tahmini_gider
- gerceklesen_gelir, gerceklesen_gider
- notlar, sorumlu_uye_id

etkinlik_katilimcilari:
- uye_id, katilimci_adi, katilim_durumu
- kisi_sayisi, notlar
```

### Web API: ✅ Basit hali mevcut

### 🔴 EKSİK:

| # | Özellik |
|---|---------|
| 1 | Katılımcı yönetimi tablosu |
| 2 | Tahmini/Gerçekleşen gelir-gider |
| 3 | Etkinlik türleri detayı |
| 4 | Sorumlu üye bağlantısı |

---

## 8️⃣ TOPLANTI YÖNETİMİ - ❌ WEB'DE YOK

### Masaüstü:

```python
toplantilar:
- toplanti_turu (Yönetim Kurulu, Genel Kurul, vb.)
- baslik, tarih, saat, mekan
- gundem, kararlar, katilimcilar
- tutanak, sonuc, bir_sonraki_toplanti
- dosya_yolu
```

### Web API: ❌ Hiç yok

---

## 9️⃣ BÜTÇE PLANLAMA

### Masaüstü:

```python
butce_planlari:
- yil, ay, kategori, tur (GELİR/GİDER)
- planlanan_tutar, gerceklesen_tutar
- aciklama
```

### Web API: ✅ Basit hali var

---

## 🔟 BELGELER VE OCR

### Masaüstü:

```python
belgeler:
- belge_turu (DEKONT, FATURA, MAKBUZ, vb.)
- baslik, dosya_adi, dosya_yolu
- dosya_boyutu, ilgili_tablo
- ilgili_kayit_id, aciklama

OCR Servisi:
- Otomatik belge tanıma
- Fatura/makbuz okuma
- Onay workflow'u
```

### Web API: ⚠️ Kısmi

---

## 1️⃣1️⃣ ALACAK-VERECEK SİSTEMİ - ❌ WEB'DE YOK

### Masaüstü:

```python
alacaklar:
- alacak_turu, aciklama, kisi_kurum
- kisi_telefon, kisi_adres, uye_id
- toplam_tutar, tahsil_edilen, kalan_tutar
- para_birimi, alacak_tarihi, vade_tarihi
- durum, gelir_id, senet_no, notlar

alacak_tahsilatlari:
- alacak_id, tutar, tahsilat_tarihi
- kasa_id, gelir_id, odeme_sekli
- aciklama

verecekler:
- (benzer yapı)

verecek_odemeleri:
- (benzer yapı)
```

### Web API: ❌ Hiç yok

---

## 1️⃣2️⃣ KÖY İŞLEMLERİ

### Masaüstü:

- Ayrı kasa sistemi (`koy_kasalar`)
- Ayrı gelir/gider (`koy_gelirleri`, `koy_giderleri`)
- Ayrı virman (`koy_virmanlar`)
- Ayrı gelir/gider türleri

### Web API: ✅ Basit hali var

---

## 1️⃣3️⃣ RAPORLAR

### Masaüstü (10+ rapor):

1. Genel Mali Özet
2. Gelir Türü Dağılımı
3. Gider Türü Dağılımı
4. Aylık Gelir-Gider Karşılaştırması
5. Aidat Tahakkuk Raporu
6. Kasa Hareketleri
7. Üye İstatistikleri
8. Tahakkuk Listesi
9. Bilanço Benzeri Rapor
10. Yıl Sonu Devir Raporu

### Web API: ⚠️ 2-3 basit rapor

---

## 1️⃣4️⃣ MALİ TABLOLAR - ❌ WEB'DE YOK

### Masaüstü:

```python
class MaliTabloYoneticisi:
    - bilanco_raporu()
    - gelir_tablosu()
    - nakit_akim_tablosu()
```

---

## 1️⃣5️⃣ KULLANICI/YETKİ SİSTEMİ

### Masaüstü:

```python
kullanicilar:
- kullanici_adi, sifre_hash, ad_soyad
- email, rol (admin/muhasebeci/görüntüleyici)
- izinler (JSON), aktif, son_giris

İzin Sistemi:
- uye_ekle, uye_duzenle, uye_sil
- gelir_ekle, gelir_duzenle, gelir_sil
- gider_ekle, gider_duzenle, gider_sil
- rapor_export, ayarlar_degistir
- kasa_gorme, kasa_yonetme
- vb...
```

### Web API: ⚠️ Basit rol sistemi var, detaylı izinler yok

---

## 1️⃣6️⃣ DEVİR İŞLEMLERİ

### Masaüstü:

```python
class DevirYoneticisi:
    - yil_sonu_devir(yil, onay)
    - Tahakkuk ayrımı (serbest/bağlı)
    - Devir log kaydı
    - Uyarı sistemi (negatif serbest bakiye vb.)

devir_islemleri:
- yil, devir_tarihi, kasa_id
- onceki_bakiye, devir_bakiye
- serbest_bakiye, tahakkuk_bakiye
- aciklama, islem_yapan
```

### Web API: ⚠️ Çok basit

---

## 1️⃣7️⃣ TAHAKKUK SİSTEMİ

### Masaüstü:

```python
tahakkuklar:
- yil, ay, tahakkuk_tipi
- aciklama, tutar, kasa_id
- durum (BEKLIYOR/GERCEKLESTI/IPTAL)
- gerceklesme_tarihi, ilgili_kayit_id

class TahakkukYoneticisi:
    - tahakkuk_listesi()
    - tahakkuk_ozet()
```

### Web API: ❌ Yok (sadece basit rapor)

---

# 🛠️ REFACTOR PLANI

## FAZ 1: VERİTABANI GÜNCELLEMESİ (1 hafta)

### 1.1 members tablosu genişletme:

```sql
ALTER TABLE members ADD COLUMN phone2 VARCHAR(50);
ALTER TABLE members ADD COLUMN gender VARCHAR(10);
ALTER TABLE members ADD COLUMN birth_place VARCHAR(100);
ALTER TABLE members ADD COLUMN blood_type VARCHAR(5);
ALTER TABLE members ADD COLUMN marital_status VARCHAR(20);
ALTER TABLE members ADD COLUMN child_count INTEGER DEFAULT 0;
ALTER TABLE members ADD COLUMN education VARCHAR(50);
ALTER TABLE members ADD COLUMN occupation VARCHAR(100);
ALTER TABLE members ADD COLUMN workplace VARCHAR(200);
ALTER TABLE members ADD COLUMN city VARCHAR(100);
ALTER TABLE members ADD COLUMN district VARCHAR(100);
ALTER TABLE members ADD COLUMN neighborhood VARCHAR(100);
ALTER TABLE members ADD COLUMN postal_code VARCHAR(20);
ALTER TABLE members ADD COLUMN membership_type VARCHAR(20) DEFAULT 'Asil';
ALTER TABLE members ADD COLUMN special_fee DECIMAL(10,2);
ALTER TABLE members ADD COLUMN fee_discount DECIMAL(5,2) DEFAULT 0;
ALTER TABLE members ADD COLUMN referrer_id UUID;
ALTER TABLE members ADD COLUMN leave_reason TEXT;
```

### 1.2 Yeni tablolar:

```sql
-- Aidat Ödemeleri
CREATE TABLE due_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(50) NOT NULL,
    due_id UUID NOT NULL REFERENCES dues(id),
    payment_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_type VARCHAR(50) DEFAULT 'Nakit',
    receipt_no VARCHAR(50),
    description TEXT,
    income_id UUID REFERENCES incomes(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Toplantılar
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(50) NOT NULL,
    meeting_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    date DATE NOT NULL,
    time TIME,
    venue VARCHAR(200),
    agenda TEXT,
    decisions TEXT,
    attendees TEXT,
    minutes TEXT,
    outcome TEXT,
    next_meeting DATE,
    document_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alacaklar
CREATE TABLE receivables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    person_org VARCHAR(200) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    member_id UUID,
    total_amount DECIMAL(12,2) NOT NULL,
    collected DECIMAL(12,2) DEFAULT 0,
    remaining DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'TRY',
    date DATE NOT NULL,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'Bekliyor',
    income_id UUID,
    bond_no VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alacak Tahsilatları
CREATE TABLE receivable_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(50) NOT NULL,
    receivable_id UUID NOT NULL REFERENCES receivables(id),
    amount DECIMAL(12,2) NOT NULL,
    collection_date DATE NOT NULL,
    cash_account_id UUID,
    income_id UUID,
    payment_method VARCHAR(50) DEFAULT 'Nakit',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verecekler (benzer yapı)
CREATE TABLE payables (...);
CREATE TABLE payable_payments (...);

-- Tahakkuklar
CREATE TABLE accruals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER,
    type VARCHAR(20) NOT NULL, -- GELIR/GIDER
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    cash_account_id UUID,
    status VARCHAR(20) DEFAULT 'BEKLIYOR',
    realized_date DATE,
    source_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Devir İşlemleri
CREATE TABLE carryover_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    date DATE NOT NULL,
    cash_account_id UUID,
    previous_balance DECIMAL(12,2) DEFAULT 0,
    carryover_balance DECIMAL(12,2) DEFAULT 0,
    free_balance DECIMAL(12,2) DEFAULT 0,
    accrual_balance DECIMAL(12,2) DEFAULT 0,
    description TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3 incomes ve expenses güncelleme:

```sql
ALTER TABLE incomes ADD COLUMN due_id UUID REFERENCES dues(id);
ALTER TABLE incomes ADD COLUMN collected_by VARCHAR(100);
ALTER TABLE incomes ADD COLUMN belongs_to_year INTEGER;
ALTER TABLE incomes ADD COLUMN accrual_status VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE incomes ADD COLUMN multi_payment_group VARCHAR(50);

ALTER TABLE expenses ADD COLUMN paid_by VARCHAR(100);
ALTER TABLE expenses ADD COLUMN belongs_to_year INTEGER;
ALTER TABLE expenses ADD COLUMN accrual_status VARCHAR(20) DEFAULT 'NORMAL';
```

### 1.4 cash_accounts güncelleme:

```sql
ALTER TABLE cash_accounts ADD COLUMN currency VARCHAR(10) DEFAULT 'TRY';
ALTER TABLE cash_accounts ADD COLUMN opening_balance DECIMAL(12,2) DEFAULT 0;
ALTER TABLE cash_accounts ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE cash_accounts ADD COLUMN description TEXT;
ALTER TABLE cash_accounts ADD COLUMN free_balance DECIMAL(12,2) DEFAULT 0;
ALTER TABLE cash_accounts ADD COLUMN accrual_total DECIMAL(12,2) DEFAULT 0;
ALTER TABLE cash_accounts ADD COLUMN last_carryover_date DATE;
```

---

## FAZ 2: API ENDPOİNTLERİ (1 hafta)

### 2.1 Üye Endpoints Güncelleme:

```python
# GET /web/members - Tüm alanlarla
# POST /web/members - 26 alan destekli
# PUT /web/members/{id} - Tam güncelleme
# GET /web/members/{id}/details - Detaylı bilgi + aidat geçmişi
# POST /web/members/bulk-create-dues - Toplu aidat oluşturma
```

### 2.2 Aidat Endpoints:

```python
# GET /web/dues - Liste
# POST /web/dues - Yeni aidat kaydı
# POST /web/dues/{id}/payment - Ödeme ekle
# DELETE /web/dues/payments/{id} - Ödeme sil
# POST /web/dues/bulk-create - Toplu oluşturma
# GET /web/dues/multi-year - Çok yıllık görünüm
```

### 2.3 Yeni Modül Endpoints:

```python
# Toplantılar
GET/POST /web/meetings
PUT/DELETE /web/meetings/{id}

# Alacak-Verecek
GET/POST /web/receivables
POST /web/receivables/{id}/collect
GET/POST /web/payables
POST /web/payables/{id}/pay

# Raporlar (10+ endpoint)
GET /web/reports/summary
GET /web/reports/income-breakdown
GET /web/reports/expense-breakdown
GET /web/reports/monthly-comparison
GET /web/reports/dues-status
GET /web/reports/cash-movements
GET /web/reports/member-stats
GET /web/reports/accruals
GET /web/reports/balance-sheet
GET /web/reports/carryover
```

### 2.4 Mali Tablolar:

```python
GET /web/financial/balance-sheet
GET /web/financial/income-statement
GET /web/financial/cash-flow
```

---

## FAZ 3: WEB FRONTEND (2 hafta)

### 3.1 Üye Formu Genişletme:

Mevcut 6 alandan 26+ alana çıkarılacak. Tab yapısı ile organize:
- Tab 1: Temel Bilgiler
- Tab 2: İletişim
- Tab 3: Kişisel
- Tab 4: Meslek
- Tab 5: Adres
- Tab 6: Aidat

### 3.2 Yeni Sayfalar:

1. **Toplantı Yönetimi** - Yeni menü
2. **Alacak-Verecek** - Yeni menü
3. **Detaylı Raporlar** - Yeni menü
4. **Mali Tablolar** - Yeni menü
5. **Kasa Detayları** - Mevcut genişletilecek
6. **Kullanıcı Yetkileri** - Yeni menü

### 3.3 Mevcut Sayfalar İyileştirme:

1. **Üye Detay Modal** - Tam bilgi gösterimi
2. **Aidat Sayfası** - Ödeme geçmişi, toplu işlemler
3. **Gelir Sayfası** - Aidat bağlantısı, tahakkuk
4. **Gider Sayfası** - Yıl bazlı görünüm

---

## FAZ 4: İŞ MANTIĞI (1 hafta)

### 4.1 Otomatik İşlemler:

- Aidat tamamlandığında otomatik gelir kaydı
- Aidat ödemesi silindiğinde gelir kaydı geri alma
- Yıl sonu otomatik devir hatırlatması
- Vade geçmiş alacak/borç uyarıları

### 4.2 Tahakkuk Sistemi:

- Peşin tahsilat takibi
- Yıl bazlı ayrıştırma
- Serbest/bağlı bakiye ayrımı

### 4.3 Raporlama:

- Tüm masaüstü raporların web'e eklenmesi
- PDF export
- Excel export

---

## FAZ 5: TEST VE DEPLOY (3 gün)

1. Birim testleri
2. Entegrasyon testleri
3. Masaüstü ile karşılaştırmalı test
4. Production deployment
5. Migration script'leri

---

## 📅 ZAMAN ÇİZELGESİ

| Faz | Süre | Başlangıç | Bitiş |
|-----|------|-----------|-------|
| Faz 1: Veritabanı | 5 gün | Gün 1 | Gün 5 |
| Faz 2: API | 5 gün | Gün 6 | Gün 10 |
| Faz 3: Frontend | 10 gün | Gün 11 | Gün 20 |
| Faz 4: İş Mantığı | 5 gün | Gün 21 | Gün 25 |
| Faz 5: Test/Deploy | 3 gün | Gün 26 | Gün 28 |

**Toplam: ~4 hafta**

---

## 🎯 ÖNCELİK SIRASI

### P0 - KRİTİK (Hemen):
1. Üye tablosu genişletme
2. Aidat ödeme sistemi
3. Gelir-Aidat bağlantısı

### P1 - YÜKSEK (1. hafta):
4. Kasa sistemi geliştirme
5. Raporlar
6. Toplantı modülü

### P2 - ORTA (2. hafta):
7. Alacak-Verecek sistemi
8. Mali tablolar
9. Devir işlemleri

### P3 - DÜŞÜK (3. hafta):
10. OCR entegrasyonu
11. Belgeler modülü
12. Kullanıcı yetkileri detayı

---

## 📝 NOTLAR

1. **Veri Uyumluluğu:** Web ve Desktop farklı veritabanı kullandığından, ONLINE/HYBRID lisanslarda senkronizasyon gerekecek.

2. **Migration:** Mevcut web verisinin kaybolmaması için dikkatli migration gerekli.

3. **Backward Compatibility:** Mevcut API endpoint'leri bozulmamalı.

4. **Performance:** Rapor endpoint'lerinde cache kullanılmalı.

5. **Security:** Tüm yeni endpoint'lere yetki kontrolü eklenmeli.
