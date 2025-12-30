# 📋 BADER DERNEĞİ - DETAYLI ÖZELLİKLER

## 🎯 Temel Özellikler

### 1. ÜYE YÖNETİMİ 👥
- ✅ Üye ekleme, düzenleme, silme (CRUD)
- ✅ Aktif/Pasif durum yönetimi
- ✅ Gelişmiş arama (ad, telefon, email)
- ✅ Durum bazlı filtreleme
- ✅ İletişim bilgileri (telefon, email)
- ✅ Üye notları
- ✅ Otomatik üye numarası
- ✅ Kayıt tarihi takibi
- ✅ İstatistikler (toplam, aktif, pasif)
- ✅ Çift tıklama ile düzenleme

### 2. AİDAT TAKİP SİSTEMİ 💳
- ✅ Yıllık aidat kayıt oluşturma
- ✅ Toplu aidat kaydı (tüm aktif üyeler)
- ✅ Bireysel aidat kaydı
- ✅ Taksitli ödeme desteği
- ✅ **Otomatik gelir senkronizasyonu** ⭐
- ✅ Ödeme durumu takibi (Tamamlandı/Kısmi/Eksik)
- ✅ Aktarım durumu izleme
- ✅ Kalan borç hesaplama
- ✅ Ödeme geçmişi
- ✅ Ödeme silme (otomatik gelir güncellemesi)
- ✅ Yıl ve durum filtreleme
- ✅ Renk kodlu durum gösterimi
- ✅ Split panel (aidat listesi + ödemeler)

### 3. GELİR YÖNETİMİ 💰
- ✅ Manuel gelir girişi
- ✅ Otomatik aidat geliri entegrasyonu
- ✅ Gelir türleri:
  - AİDAT (otomatik)
  - KİRA
  - BAĞIŞ
  - DÜĞÜN
  - KINA
  - TOPLANTI
  - DAVET
  - DİĞER
- ✅ Otomatik belge numarası (GEL000001...)
- ✅ Kasa bazlı gelir kaydı
- ✅ Tahsil eden kişi bilgisi
- ✅ Tarih aralığı filtreleme
- ✅ Gelir türü filtreleme
- ✅ Kasa filtreleme
- ✅ Toplam gelir hesaplama
- ✅ Aidat gelirlerinin korunması (silinemez/düzenlenemez)

### 4. GİDER YÖNETİMİ 💸
- ✅ Gider ekleme, düzenleme, silme
- ✅ Otomatik işlem numarası (GID000001...)
- ✅ Dinamik gider kategorileri
- ✅ Varsayılan gider türleri:
  - ELEKTRİK
  - SU
  - DOĞALGAZ
  - İNTERNET
  - TELEFON
  - KİRA
  - TEMİZLİK
  - BAKIM-ONARIM
  - KIRTASIYE
  - ORGANİZASYON
  - YEMEK
  - ULAŞIM
  - PERSONEL
  - VERGİ-HARÇ
  - SİGORTA
  - DİĞER
- ✅ Yeni gider türü ekleme
- ✅ Kasa entegrasyonu
- ✅ Ödeyen kişi bilgisi
- ✅ Tarih ve tür filtreleme
- ✅ Toplam gider hesaplama

### 5. VİRMAN (KASA TRANSFER) 🔄
- ✅ Kasalar arası para transferi
- ✅ Otomatik çift taraflı bakiye güncelleme
- ✅ Gönderen kasa bakiyesi azalır
- ✅ Alan kasa bakiyesi artar
- ✅ Toplam para sabit kalır
- ✅ Transfer geçmişi
- ✅ Tarih filtreleme
- ✅ Açıklama alanı
- ✅ Transfer silme

### 6. KASA YÖNETİMİ 🏦
- ✅ Çoklu kasa desteği
- ✅ Para birimi desteği (TL, USD, EUR)
- ✅ Varsayılan kasalar:
  - BANKA TL
  - BANKA USD
  - DERNEK KASA TL
  - SAYMAN TL
  - ŞEREF USD
  - ŞEREF TL
  - EURO KASA
- ✅ Yeni kasa ekleme
- ✅ Kasa düzenleme
- ✅ Devir bakiye yönetimi
- ✅ Gerçek zamanlı bakiye hesaplama
- ✅ Kasa bazlı hareket özeti:
  - Devir
  - Toplam gelir
  - Toplam gider
  - Virman net (giren-çıkan)
  - Net bakiye
- ✅ Para birimi bazlı toplam
- ✅ Negatif bakiye uyarısı (kırmızı)
- ✅ Kasa detay görünümü

### 7. DASHBOARD & RAPORLAMA 📊
- ✅ Genel mali durum özeti
- ✅ İstatistik kartları:
  - Toplam Gelir
  - Toplam Gider
  - Net Sonuç
  - Toplam Kasa Bakiye
  - Aidat Ödeyen/Toplam Üye
- ✅ İnteraktif grafikler (Matplotlib):
  - Aylık Gelir-Gider Karşılaştırması (Bar)
  - Gelir Türleri Dağılımı (Pasta)
  - Gider Türleri Dağılımı (Pasta)
  - Kasa Bakiyeleri (Yatay Bar)
- ✅ Yıl seçimi ve filtreleme
- ✅ Renk kodlu görselleştirme
- ✅ Gerçek zamanlı güncelleme
- ✅ Scroll destekli görünüm

### 8. EXPORT & YEDEKLEME 💾
- ✅ Excel Export:
  - Tüm veriler tek dosyada
  - Sayfalar: Üyeler, Aidat, Gelirler, Giderler, Kasa Özeti, Genel Rapor
  - Formatlı başlıklar
  - Renk kodlu tasarım
- ✅ Veritabanı yedekleme
- ✅ Veritabanı geri yükleme
- ✅ Progress bar ile işlem takibi
- ✅ Async işlem (thread-based)
- ✅ İşlem geçmişi logu
- ✅ Otomatik dosya adlandırma (timestamp)

## 🎨 Kullanıcı Arayüzü

### Tasarım Özellikleri
- ✅ Modern Material Design benzeri tema
- ✅ Koyu mavi renk paleti (#1976D2)
- ✅ Responsive tasarım
- ✅ Yuvarlatılmış köşeler
- ✅ Hover efektleri
- ✅ Renk kodlu durum gösterimi
- ✅ İkonlu butonlar
- ✅ Alternatif satır renkleri (tablo)
- ✅ Smooth scrolling
- ✅ Modern progress bar
- ✅ Tool tip'ler

### Navigasyon
- ✅ Üst menü bar
- ✅ Hızlı erişim toolbar
- ✅ Alt durum çubuğu
- ✅ Klavye kısayolları
- ✅ Çift tıklama ile düzenleme
- ✅ Bağlamsal buton aktivasyonu

### Formlar ve Dialoglar
- ✅ Modal dialoglar
- ✅ Form validasyonu
- ✅ Placeholder metinler
- ✅ Tarih seçici (calendar popup)
- ✅ Otomatik tamamlama
- ✅ Dinamik combobox'lar
- ✅ Scroll destekli uzun formlar

## 🔐 Güvenlik ve Kontroller

### Veri Güvenliği
- ✅ SQLite injection koruması (parameterized queries)
- ✅ Transaction yönetimi
- ✅ Foreign key constraints
- ✅ Unique constraints
- ✅ Check constraints
- ✅ Cascade delete

### İş Kuralları
- ✅ Aidat tamamlandığında otomatik gelir
- ✅ Aidat ödemesi silinince gelir de silinir
- ✅ Aidat geliri manuel silinemez/düzenlenemez
- ✅ Virman'da gönderen ≠ alan kontrolü
- ✅ Negatif tutar kontrolü
- ✅ Zorunlu alan kontrolü

### Denetim İzi
- ✅ Tüm işlemler log kaydına alınır
- ✅ İşlem tipi: EKLE, SİL, GÜNCELLE, OTOMATIK
- ✅ Kullanıcı bilgisi
- ✅ Tarih/saat damgası
- ✅ Eski ve yeni değerler
- ✅ İşlem açıklaması

### Yedekleme
- ✅ Tek tıkla yedekleme
- ✅ Otomatik dosya adlandırma
- ✅ Geri yükleme onayı
- ✅ Yedek dosya doğrulama

## 📊 Veritabanı Özellikleri

### Tablo Yapısı
- ✅ 10 ana tablo
- ✅ İndekslenmiş sorgular (hızlı arama)
- ✅ Foreign key ilişkileri
- ✅ Otomatik timestamp'ler
- ✅ Varsayılan değerler
- ✅ Check constraint'ler

### Performans
- ✅ Optimize edilmiş sorgular
- ✅ Index kullanımı
- ✅ Verimli JOIN işlemleri
- ✅ Lazy loading destekli
- ✅ Connection pooling

## 🌐 Ek Özellikler

### Sistem Ayarları
- ✅ Dernek bilgileri
- ✅ Varsayılan aidat tutarı
- ✅ Döviz kurları (USD, EUR)
- ✅ Dinamik ayar yönetimi

### Çoklu Dil Desteği
- ✅ Türkçe arayüz
- ✅ Türk Lirası formatı
- ✅ Tarih formatı (YYYY-MM-DD)

### Platform Desteği
- ✅ Windows
- ✅ macOS
- ✅ Linux
- ✅ Platform bağımsız SQLite

### Dokümantasyon
- ✅ Detaylı README
- ✅ Hızlı başlangıç rehberi
- ✅ Özellikler dokümanı
- ✅ Kurulum scriptleri
- ✅ Kod yorumları

## 🚀 Performans

### Hız
- ✅ Anında açılış
- ✅ Hızlı veri yükleme
- ✅ Gerçek zamanlı hesaplamalar
- ✅ Smooth UI geçişleri
- ✅ Async export işlemleri

### Kaynak Kullanımı
- ✅ Düşük RAM kullanımı
- ✅ Minimal CPU kullanımı
- ✅ Küçük dosya boyutu
- ✅ Verimli veritabanı

## 📈 İstatistikler

### Kod Metrikleri
- **Toplam Dosya:** 19
- **Python Dosyası:** 13
- **Kod Satırı:** ~6000+
- **Fonksiyon Sayısı:** 150+
- **Sınıf Sayısı:** 30+
- **Tablo Sayısı:** 10

### Kapsanan İşlevler
- **Üye Yönetimi:** 100%
- **Aidat Takibi:** 100%
- **Gelir/Gider:** 100%
- **Kasa Yönetimi:** 100%
- **Raporlama:** 100%
- **Export:** 100%

## 🎯 Hedef Kitle

Bu yazılım özellikle şu kullanıcılar için tasarlanmıştır:
- ✅ Dernek yöneticileri
- ✅ Sayman/Muhasebeciler
- ✅ Yönetim kurulu üyeleri
- ✅ Mali işler sorumluları
- ✅ Bilgisayar kullanabilen herkes (kullanıcı dostu)

## 💡 Benzersiz Özellikler

### ⭐ Otomatik Aidat-Gelir Senkronizasyonu
En kritik özellik! Aidat ödemesi tamamlandığında otomatik olarak gelir kaydı oluşturur.

### ⭐ İki Yönlü Güncelleme
Aidat ödemesi silinirse gelir kaydı da otomatik silinir. Tutarlılık her zaman korunur.

### ⭐ Çoklu Kasa Desteği
TL, USD, EUR kasaları aynı anda yönetin. Her biri bağımsız takip edilir.

### ⭐ Gerçek Zamanlı Raporlama
Dashboard tüm verileri gerçek zamanlı hesaplar ve gösterir.

### ⭐ Thread-based Export
Excel export ve yedekleme işlemleri arka planda çalışır, program donmaz.

---

**🎉 BADER Derneği - Modern Dernek Yönetimi**


