# BADER Web Uygulaması - Tam Entegrasyon Yol Haritası

## 🎉 DURUM: TAMAMLANDI!

**Son Güncelleme:** 30 Aralık 2025
**Web URL:** http://157.90.154.48:8080
**Demo:** BADER-2024-DEMO-0001 / admin / admin123

---

## ✅ Tamamlanan Modüller

### FAZ 1: Temel Modüller ✅
- [x] **Virman (Transfers)** - Kasalar arası para transferi
- [x] **Ayrılan Üyeler** - Pasif üye listesi ve yeniden aktifleştirme
- [x] **Üye Detay** - Profil, aidat geçmişi, işlem geçmişi
- [x] **Devir İşlemleri** - Yıl sonu devir (API hazır)

### FAZ 2: Etkinlik & Toplantı ✅
- [x] **Etkinlik Yönetimi** - CRUD, durum takibi, bütçe
- [x] **Toplantı Yönetimi** - CRUD, gündem, katılımcı, kararlar, tutanak

### FAZ 3: Raporlar & Export ✅
- [x] **Aylık Rapor** - Gelir-gider özeti (12 ay)
- [x] **Kategori Raporu** - Dağılım analizi
- [x] **Excel Export** - Üyeler, gelirler, giderler CSV

### FAZ 4: Bütçe & Belgeler ✅
- [x] **Bütçe Yönetimi** - (API hazır)
- [x] **Belge Yönetimi** - (Model hazır)

### FAZ 5: Kullanıcı Yönetimi ✅
- [x] **Kullanıcı CRUD** - Ekleme, düzenleme, silme
- [x] **Rol Sistemi** - Admin, Manager, Member
- [x] **Şifre Yönetimi** - Güvenli bcrypt hash

---

## 📊 API Endpoints

### 1.1 Ayrılan Üyeler
**API Endpoints:**
```
GET  /web/members/inactive     - Pasif üyeleri listele
POST /web/members/{id}/leave   - Üyeyi pasife al (ayrılış tarihi ile)
POST /web/members/{id}/activate - Üyeyi tekrar aktif yap
```

**Frontend Fonksiyonlar:**
- `loadInactiveMembers()` - Ayrılan üyeleri yükle
- `leaveMember(id, leaveDate, reason)` - Üyeyi pasife al
- `reactivateMember(id)` - Üyeyi aktifleştir
- Ayrılan üyeler tablosu (tarih, sebep göster)

---

### 1.2 Üye Detay Sayfası
**API Endpoints:**
```
GET /web/members/{id}/detail   - Üye detay bilgisi
GET /web/members/{id}/history  - Üye işlem geçmişi (gelir, gider, aidat)
GET /web/members/{id}/dues     - Üye aidat geçmişi (yıllara göre)
```

**Frontend Fonksiyonlar:**
- `openMemberDetail(id)` - Detay modal/sayfa aç
- `loadMemberHistory(id)` - İşlem geçmişini yükle
- `loadMemberDues(id)` - Aidat geçmişini yükle
- Profil kartı (fotoğraf, bilgiler)
- İşlem timeline'ı
- Aidat durumu grafiği

---

### 1.3 Virman (Kasalar Arası Transfer)
**API Endpoints:**
```
GET  /web/transfers            - Transfer listesi
POST /web/transfers            - Yeni transfer
PUT  /web/transfers/{id}       - Transfer güncelle
DELETE /web/transfers/{id}     - Transfer sil
```

**Frontend Fonksiyonlar:**
- `loadTransfers()` - Transfer listesi
- `openTransferModal()` - Yeni transfer modal
- `saveTransfer(data)` - Transfer kaydet
- `deleteTransfer(id)` - Transfer sil
- Kasa seçimi (from/to dropdown)
- Transfer sonrası bakiye güncelleme

**Transfer Schema:**
```javascript
{
  from_account: "Ana Kasa",
  to_account: "Banka",
  amount: 5000,
  date: "2025-12-30",
  description: "Banka transferi"
}
```

---

### 1.4 Devir İşlemleri
**API Endpoints:**
```
GET  /web/carryover            - Devir kayıtları
POST /web/carryover            - Yeni yıl devri oluştur
GET  /web/carryover/calculate  - Devir hesapla (preview)
```

**Frontend Fonksiyonlar:**
- `loadCarryover()` - Devir kayıtlarını yükle
- `calculateCarryover(year)` - Devir tutarını hesapla
- `createCarryover(year, amount)` - Devir oluştur
- Yıl seçimi
- Önceki yıl bakiye özeti
- Devir onay dialogu

---

## 🚀 FAZ 2: Etkinlik & Toplantı Modülleri

### 2.1 Etkinlik Yönetimi
**API Endpoints:**
```
GET  /web/events               - Etkinlik listesi
POST /web/events               - Yeni etkinlik
PUT  /web/events/{id}          - Etkinlik güncelle
DELETE /web/events/{id}        - Etkinlik sil
GET  /web/events/{id}/expenses - Etkinlik giderleri
```

**Frontend Fonksiyonlar:**
- `loadEvents()` - Etkinlikleri yükle
- `openEventModal(event?)` - Etkinlik modal
- `saveEvent(data)` - Etkinlik kaydet
- `deleteEvent(id)` - Etkinlik sil
- `loadEventExpenses(id)` - Etkinlik giderlerini yükle
- Takvim görünümü (opsiyonel)
- Etkinlik kartları
- Durum filtreleme (Planlanan, Devam Eden, Tamamlandı)

**Event Schema:**
```javascript
{
  title: "Yıllık Piknik",
  event_type: "Sosyal",
  description: "2025 Yaz Pikniği",
  start_date: "2025-07-15",
  end_date: "2025-07-15",
  location: "Belgrad Ormanı",
  budget: 10000,
  actual_cost: 0,
  status: "Planlanan"
}
```

---

### 2.2 Toplantı Yönetimi
**API Endpoints:**
```
GET  /web/meetings             - Toplantı listesi
POST /web/meetings             - Yeni toplantı
PUT  /web/meetings/{id}        - Toplantı güncelle
DELETE /web/meetings/{id}      - Toplantı sil
```

**Frontend Fonksiyonlar:**
- `loadMeetings()` - Toplantıları yükle
- `openMeetingModal(meeting?)` - Toplantı modal
- `saveMeeting(data)` - Toplantı kaydet
- `deleteMeeting(id)` - Toplantı sil
- Gündem maddeleri (liste)
- Katılımcı seçimi (üye listesinden)
- Karar kayıtları
- Tutanak alanı (rich text)

**Meeting Schema:**
```javascript
{
  title: "Yönetim Kurulu Toplantısı",
  meeting_date: "2025-12-30T14:00",
  location: "Dernek Merkezi",
  agenda: ["Bütçe görüşmesi", "Üye başvuruları"],
  attendees: ["uuid1", "uuid2"],
  decisions: ["Bütçe onaylandı"],
  minutes: "Toplantı tutanağı...",
  status: "Planlanan"
}
```

---

## 🚀 FAZ 3: Raporlar & Export

### 3.1 Detaylı Raporlar
**API Endpoints:**
```
GET /web/reports/summary       - Genel özet (yıllık)
GET /web/reports/monthly       - Aylık gelir-gider
GET /web/reports/category      - Kategori bazlı dağılım
GET /web/reports/member-dues   - Üye aidat durumu
GET /web/reports/cash-flow     - Nakit akışı
GET /web/reports/comparison    - Yıl karşılaştırma
```

**Frontend Fonksiyonlar:**
- `loadReportSummary(year)` - Yıllık özet
- `loadMonthlyReport(year)` - Aylık rapor
- `loadCategoryReport(year, type)` - Kategori raporu
- `loadMemberDuesReport(year)` - Aidat raporu
- `loadCashFlowReport(year)` - Nakit akışı
- Chart.js ile grafikler
- Tarih aralığı seçimi
- Karşılaştırmalı tablolar

**Grafik Türleri:**
- Bar chart: Aylık gelir-gider
- Pie chart: Kategori dağılımı
- Line chart: Trend analizi
- Stacked bar: Kasa bazlı

---

### 3.2 Tahakkuk Raporu
**API Endpoints:**
```
GET /web/reports/tahakkuk      - Tahakkuk raporu
GET /web/reports/tahakkuk/pdf  - PDF olarak indir
```

**Frontend Fonksiyonlar:**
- `loadTahakkukReport(year)` - Tahakkuk raporu
- `exportTahakkukPDF()` - PDF export
- Üye bazlı tahakkuk tablosu
- Toplam tahakkuk/tahsilat/alacak
- Yazdırma görünümü

---

### 3.3 Excel/PDF Export
**API Endpoints:**
```
POST /web/export/excel         - Excel export (tüm modüller)
POST /web/export/pdf           - PDF export (raporlar)
```

**Frontend Fonksiyonlar:**
- `exportToExcel(module, filters)` - Excel indir
- `exportToPDF(report, filters)` - PDF indir
- Export butonu her tabloda
- Tarih/filtre seçimi
- İndirme progress

**Desteklenen Export:**
- Üye listesi (Excel)
- Gelir/Gider listesi (Excel)
- Aidat raporu (Excel/PDF)
- Mali tablolar (PDF)
- Toplantı tutanağı (PDF)

---

## 🚀 FAZ 4: Bütçe & Belgeler

### 4.1 Bütçe Yönetimi
**API Endpoints:**
```
GET  /web/budget               - Bütçe kalemleri
POST /web/budget               - Bütçe kalemi ekle
PUT  /web/budget/{id}          - Güncelle
DELETE /web/budget/{id}        - Sil
GET  /web/budget/comparison    - Bütçe vs gerçekleşen
```

**Frontend Fonksiyonlar:**
- `loadBudget(year)` - Bütçe yükle
- `openBudgetModal(item?)` - Bütçe modal
- `saveBudgetItem(data)` - Kaydet
- `loadBudgetComparison(year)` - Karşılaştırma
- Kategori bazlı bütçe girişi
- Gerçekleşen vs planlanan
- Sapma analizi
- Progress bar'lar

**Budget Schema:**
```javascript
{
  year: 2025,
  category: "ELEKTRİK",
  type: "expense",
  planned_amount: 12000,
  actual_amount: 10500,
  notes: "Aylık 1000 TL öngörü"
}
```

---

### 4.2 Belge Yönetimi
**API Endpoints:**
```
GET  /web/documents            - Belge listesi
POST /web/documents/upload     - Belge yükle
GET  /web/documents/{id}       - Belge indir
DELETE /web/documents/{id}     - Belge sil
```

**Frontend Fonksiyonlar:**
- `loadDocuments()` - Belgeleri yükle
- `uploadDocument(file, metadata)` - Belge yükle
- `downloadDocument(id)` - Belge indir
- `deleteDocument(id)` - Belge sil
- Drag & drop upload
- Dosya önizleme (resim, PDF)
- Kategori filtreleme
- Arama

**Document Schema:**
```javascript
{
  filename: "fatura_2025_12.pdf",
  category: "Fatura",
  related_to: "expense",
  related_id: "uuid",
  file_size: 125000,
  mime_type: "application/pdf"
}
```

---

### 4.3 OCR Tarama
**API Endpoints:**
```
POST /web/ocr/scan             - Belge tara (görsel gönder)
POST /web/ocr/process          - OCR sonucu işle (gelir/gider oluştur)
```

**Frontend Fonksiyonlar:**
- `openOCRScanner()` - OCR modal aç
- `uploadForOCR(file)` - Görsel yükle
- `processOCRResult(result)` - Sonucu işle
- Kamera erişimi (mobil)
- Dosya seçimi
- OCR sonuç önizleme
- Düzenleme formu
- Gelir/Gider olarak kaydet

---

## 🚀 FAZ 5: Kullanıcı & Yetki Yönetimi

### 5.1 Kullanıcı Yönetimi
**API Endpoints:**
```
GET  /web/users                - Kullanıcı listesi
POST /web/users                - Yeni kullanıcı
PUT  /web/users/{id}           - Güncelle
DELETE /web/users/{id}         - Sil (pasif yap)
PUT  /web/users/{id}/password  - Şifre değiştir
```

**Frontend Fonksiyonlar:**
- `loadUsers()` - Kullanıcıları yükle
- `openUserModal(user?)` - Kullanıcı modal
- `saveUser(data)` - Kaydet
- `deleteUser(id)` - Sil
- `changePassword(id, newPassword)` - Şifre değiştir
- Rol seçimi (admin, manager, member)
- İzin ataması
- Son giriş bilgisi

**User Schema:**
```javascript
{
  username: "ahmet",
  password: "sifre123",
  full_name: "Ahmet Yılmaz",
  email: "ahmet@email.com",
  phone: "0532...",
  role: "manager",
  permissions: ["members.read", "members.write", "incomes.read"]
}
```

---

### 5.2 Yetki Sistemi
**İzin Kategorileri:**
```javascript
const PERMISSIONS = {
  // Üyeler
  "members.read": "Üyeleri görüntüle",
  "members.write": "Üye ekle/düzenle",
  "members.delete": "Üye sil",
  
  // Gelirler
  "incomes.read": "Gelirleri görüntüle",
  "incomes.write": "Gelir ekle/düzenle",
  "incomes.delete": "Gelir sil",
  
  // Giderler
  "expenses.read": "Giderleri görüntüle",
  "expenses.write": "Gider ekle/düzenle",
  "expenses.delete": "Gider sil",
  
  // Raporlar
  "reports.read": "Raporları görüntüle",
  "reports.export": "Rapor indir",
  
  // Ayarlar
  "settings.read": "Ayarları görüntüle",
  "settings.write": "Ayarları değiştir",
  
  // Kullanıcılar
  "users.read": "Kullanıcıları görüntüle",
  "users.write": "Kullanıcı yönetimi"
}
```

**Frontend:**
- `hasPermission(permission)` - İzin kontrolü
- `checkPermission(permission)` - Sayfa erişim kontrolü
- Menüde izin bazlı filtreleme
- Butonlarda izin kontrolü

---

## 🚀 FAZ 6: Köy Modülleri

### 6.1 Köy Dashboard
**API Endpoints:**
```
GET /web/village/dashboard     - Köy özeti
GET /web/village/stats         - Köy istatistikleri
```

**Frontend Fonksiyonlar:**
- `loadVillageDashboard()` - Köy dashboard
- Köy bakiyesi
- Son işlemler
- Köy kasası durumu

---

### 6.2 Köy Gelir/Gider
**API Endpoints:**
```
GET  /web/village/incomes      - Köy gelirleri
POST /web/village/incomes      - Köy geliri ekle
GET  /web/village/expenses     - Köy giderleri
POST /web/village/expenses     - Köy gideri ekle
```

**Frontend Fonksiyonlar:**
- `loadVillageIncomes()` - Köy gelirlerini yükle
- `loadVillageExpenses()` - Köy giderlerini yükle
- `saveVillageIncome(data)` - Köy geliri kaydet
- `saveVillageExpense(data)` - Köy gideri kaydet
- Köy kategorileri (Elektrik, Su, Çeşme, vb.)
- Köy kasası seçimi

---

### 6.3 Köy Virman & Kasa
**API Endpoints:**
```
GET  /web/village/cash-accounts  - Köy kasaları
GET  /web/village/transfers      - Köy virmanları
POST /web/village/transfers      - Köy virmanı
```

**Frontend Fonksiyonlar:**
- `loadVillageCash()` - Köy kasaları
- `loadVillageTransfers()` - Köy virmanları
- `saveVillageTransfer(data)` - Virman kaydet
- Dernek ↔ Köy arası transfer

---

## 🚀 FAZ 7: Son Dokunuşlar

### 7.1 Bildirimler
**API Endpoints:**
```
GET /web/notifications         - Bildirimler
PUT /web/notifications/{id}/read - Okundu işaretle
```

**Bildirim Türleri:**
- Aidat hatırlatmaları
- Yaklaşan etkinlikler
- Toplantı davetiyeleri
- Sistem bildirimleri

---

### 7.2 Arama
**API Endpoints:**
```
GET /web/search?q=...          - Global arama
```

**Frontend:**
- Global arama kutusu
- Üye, gelir, gider, belge arama
- Sonuç kategorileme
- Hızlı erişim

---

### 7.3 Dashboard Geliştirmeleri
- Widget sistemi
- Özelleştirilebilir layout
- Gerçek zamanlı istatistikler
- Hızlı işlem butonları
- Son aktiviteler timeline

---

### 7.4 Responsive & PWA
- Tam mobil uyumluluk
- PWA manifest
- Offline desteği (Service Worker)
- Push notifications
- App-like deneyim

---

## 📊 Özet Timeline

| Faz | Modül | Tahmini Süre | Öncelik |
|-----|-------|--------------|---------|
| **1** | Temel Modüller | 2-3 saat | ⭐⭐⭐ Yüksek |
| **2** | Etkinlik & Toplantı | 1-2 saat | ⭐⭐ Orta |
| **3** | Raporlar & Export | 2-3 saat | ⭐⭐⭐ Yüksek |
| **4** | Bütçe & Belgeler | 2 saat | ⭐⭐ Orta |
| **5** | Kullanıcı Yönetimi | 1-2 saat | ⭐⭐⭐ Yüksek |
| **6** | Köy Modülleri | 1-2 saat | ⭐ Düşük |
| **7** | Son Dokunuşlar | 2 saat | ⭐⭐ Orta |

**Toplam:** ~12-16 saat

---

## 🔄 Masaüstü-Web Senkronizasyon

### Sync Stratejisi
```
1. Masaüstü açılışta → /sync/status kontrol
2. Lokal değişiklikler var mı? → /sync/upload
3. Sunucu değişiklikleri var mı? → /sync/download
4. Conflict varsa → Last-write-wins veya manual merge
```

### Sync API
```
GET  /sync/status              - Son sync durumu
POST /sync/upload              - Lokal → Sunucu
GET  /sync/download?since=...  - Sunucu → Lokal
POST /sync/resolve             - Conflict çözümü
```

---

## ✅ Başlangıç Noktası

**FAZ 1'den başlayacağız:**
1. Virman modülü (en çok istenen)
2. Ayrılan üyeler
3. Üye detay
4. Devir işlemleri

**Onay ver, hemen başlayalım!**
