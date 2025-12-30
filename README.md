# 🏢 BADER Derneği - Aidat & Kasa Yönetim Sistemi

Modern, güçlü ve kullanıcı dostu masaüstü dernek yönetim yazılımı.

## 📋 Özellikler

### 🎯 Temel Modüller

1. **Üye Yönetimi**
   - Üye ekleme, düzenleme, silme
   - Aktif/Pasif üye takibi
   - Üye arama ve filtreleme
   - İletişim bilgileri yönetimi

2. **Aidat Takip Sistemi** ⭐
   - Yıllık aidat kayıtları
   - Taksitli ödeme takibi
   - **Otomatik gelir senkronizasyonu**
   - Toplu aidat kaydı oluşturma
   - Ödeme geçmişi

3. **Gelir Yönetimi**
   - Manuel gelir girişi
   - Otomatik aidat geliri entegrasyonu
   - Gelir türü kategorileri (Kira, Bağış, Düğün, Kına, vb.)
   - Belge numarası otomatik üretimi
   - Kasa bazlı gelir takibi

4. **Gider Yönetimi**
   - Gider kategorileri (Elektrik, Su, Kira, vb.)
   - İşlem numarası otomatik üretimi
   - Dinamik gider türü ekleme
   - Kasa entegrasyonu

5. **Virman (Kasa Transfer)**
   - Kasalar arası para transferi
   - Otomatik bakiye güncelleme
   - Transfer geçmişi

6. **Kasa Yönetimi**
   - Çoklu kasa desteği (TL, USD, EUR)
   - Gerçek zamanlı bakiye hesaplama
   - Devir bakiye yönetimi
   - Kasa bazlı raporlama

7. **Dashboard & Raporlama** 📊
   - Genel mali durum özeti
   - İnteraktif grafikler
   - Aylık gelir-gider karşılaştırması
   - Gelir/Gider türü dağılım grafikleri
   - Kasa bakiye grafikleri
   - Aidat istatistikleri

8. **Export & Yedekleme** 💾
   - Excel export (tüm veriler)
   - Veritabanı yedekleme
   - Veritabanı geri yükleme
   - İşlem geçmişi logu

## 🚀 Kurulum

### Gereksinimler
- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)

### Adım 1: Depoyu İndirin
```bash
git clone <repo-url>
cd bader
```

### Adım 2: Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### Adım 3: Programı Çalıştırın
```bash
python main.py
```

## 💻 Kullanım

### İlk Kurulum
Program ilk çalıştırıldığında otomatik olarak:
- Veritabanı oluşturulur (`bader_dernegi.db`)
- Varsayılan kasalar eklenir
- Varsayılan gider türleri yüklenir
- Sistem ayarları hazırlanır

### Temel İşlemler

#### 1. Üye Ekleme
1. "Üyeler" modülüne gidin
2. "Yeni Üye" butonuna tıklayın
3. Bilgileri doldurun ve kaydedin

#### 2. Aidat Kaydı Oluşturma
1. "Aidat" modülüne gidin
2. **Toplu:** "Toplu Aidat Oluştur" ile tüm aktif üyeler için
3. **Tekil:** "Tek Kayıt Oluştur" ile belirli bir üye için

#### 3. Aidat Ödemesi Alma
1. Aidat listesinden ilgili kaydı seçin
2. "Ödeme Ekle" butonuna tıklayın
3. Ödeme bilgilerini girin
4. ✅ Toplam ödeme yıllık aidatı geçtiğinde **otomatik olarak Gelirler'e aktarılır**

#### 4. Gelir/Gider Ekleme
- Gelir/Gider modüllerine gidin
- Yeni kayıt ekleyin
- Kasa seçimini doğru yapın

#### 5. Virman (Transfer)
- Virman modülüne gidin
- Gönderen ve alan kasayı seçin
- Transfer tutarını girin

#### 6. Raporlama
- Dashboard'da tüm özetleri görün
- Yıl seçerek filtreleme yapın
- Grafikleri inceleyin

#### 7. Export
- Export modülüne gidin
- Excel'e export veya yedekleme yapın

## 🔐 Güvenlik

- Tüm işlemler log kaydına alınır
- Veritabanı düzenli olarak yedeklenmelidir
- Kritik işlemler onay gerektirir
- Aidat gelirleri manuel olarak silinemez/düzenlenemez

## 🎨 Arayüz Özellikleri

- **Vuexy-Inspired Modern UI** - Premium admin template tasarımı
- **Profesyonel Renk Paleti:**
  - Primary: #7367f0 (Mor/Purple)
  - Success: #28c76f (Yeşil)
  - Danger: #ff4c51 (Kırmızı)
  - Warning: #ff9f43 (Turuncu)
  - Info: #00bad1 (Cyan)
- **Tipografi:** Segoe UI / Public Sans
- **Yüksek Kontrast:** Tüm elementler okunabilirlik için optimize edilmiş
- **Card-based Layout:** Modern kart tasarımları
- **Soft Shadows & Rounded Corners**
- **İnteraktif Grafikler:** Matplotlib ile Vuexy renk paletinde
- **Responsive & Clean:** Minimal ve profesyonel görünüm

## 📊 Veritabanı Yapısı

- **SQLite** tabanlı (taşınabilir)
- 10 ana tablo:
  - `uyeler` - Üye bilgileri
  - `aidat_takip` - Aidat kayıtları
  - `aidat_odemeleri` - Ödeme detayları
  - `kasalar` - Kasa tanımları
  - `gelirler` - Gelir kayıtları
  - `giderler` - Gider kayıtları
  - `virmanlar` - Transfer kayıtları
  - `gider_turleri` - Gider kategorileri
  - `ayarlar` - Sistem ayarları
  - `islem_loglari` - Denetim izi

## 🔧 Teknik Detaylar

### Teknoloji Stack
- **UI Framework:** PyQt6
- **Veritabanı:** SQLite3
- **Grafikler:** Matplotlib
- **Export:** OpenPyXL

### Mimari
- **MVC Benzeri Yapı:**
  - `database.py` - Veri erişim katmanı
  - `models.py` - İş mantığı katmanı
  - `ui_*.py` - Görünüm katmanı
  - `main_window.py` - Ana koordinatör

### Kritik İş Kuralları
1. Aidat "Tamamlandı" → Otomatik Gelir kaydı
2. Aidat ödemesi silinirse → Gelir kaydı da silinir
3. Aidat gelirleri manuel değiştirilemez
4. Virman'da toplam para değişmez
5. Kasa bakiyeleri gerçek zamanlı hesaplanır

## 🐛 Sorun Giderme

### PyQt6 Kurulum Hatası
```bash
pip install --upgrade pip
pip install PyQt6
```

### Matplotlib Görüntüleme Sorunu
Program başında backend otomatik ayarlanır. Sorun devam ederse:
```bash
pip install --upgrade matplotlib
```

### Veritabanı Hatası
Eğer veritabanı bozulursa:
1. Yedeklemeden geri yükleyin
2. Veya `bader_dernegi.db` dosyasını silin (yeni başlangıç)

## 📞 Destek

Sorularınız için:
- 📧 E-posta: support@bader.org
- 📱 Telefon: (XXX) XXX XX XX

## 📝 Lisans

Bu yazılım BADER Derneği için özel olarak geliştirilmiştir.

## 🎯 Yol Haritası

### Gelecek Özellikler
- [ ] PDF rapor oluşturma
- [ ] E-posta bildirimleri
- [ ] SMS entegrasyonu
- [ ] Web tabanlı üye paneli
- [ ] Mobil uygulama
- [ ] Otomatik yedekleme
- [ ] Çoklu kullanıcı yetkilendirmesi

## 👨‍💻 Geliştirici Notları

### Yeni Modül Ekleme
1. `models.py`'de yönetici sınıfı oluşturun
2. `ui_*.py` dosyası ile UI oluşturun
3. `main_window.py`'ye entegre edin

### Veritabanı Değişikliği
1. `database.py`'de tablo yapısını değiştirin
2. Migration scripti yazın (manuel)
3. Mevcut verileri migrate edin

### Stil Değişikliği
`ui_styles.py` dosyasını düzenleyin.

---

**© 2025 BADER Derneği - Tüm hakları saklıdır.**

