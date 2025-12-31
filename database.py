"""
BADER Derneği - Veritabanı Modelleri
SQLite tabanlı veritabanı yönetimi + Online PostgreSQL desteği
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
import os
import sys
import requests
import json


def get_license_mode():
    """Lisans modunu kontrol et (online/offline)"""
    try:
        db_path = get_data_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT deger FROM sistem_ayarlari WHERE anahtar = 'license_mode'")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'offline'
    except:
        return 'offline'


def get_api_config():
    """API yapılandırmasını al"""
    try:
        db_path = get_data_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT anahtar, deger FROM sistem_ayarlari WHERE anahtar IN ('api_url', 'api_key', 'customer_id')")
        results = cursor.fetchall()
        conn.close()
        config = {row[0]: row[1] for row in results}
        return config
    except:
        return {}


def get_data_path():
    """Veritabanı için doğru yolu al"""
    # macOS'ta kullanıcının Application Support klasörünü kullan
    if sys.platform == 'darwin':
        home = os.path.expanduser('~')
        data_dir = os.path.join(home, 'Library', 'Application Support', 'BADER')
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'bader_dernegi.db')
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bader_dernegi.db')


class OnlineDatabase:
    """Online PostgreSQL API üzerinden veritabanı işlemleri"""
    
    def __init__(self):
        config = get_api_config()
        self.api_url = config.get('api_url', 'http://157.90.154.48:8080/api')
        self.api_key = config.get('api_key', '')
        self.customer_id = config.get('customer_id', '')
        self.headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
    
    def _request(self, method, endpoint, data=None):
        """API isteği gönder"""
        try:
            url = f"{self.api_url}{endpoint}"
            if method == 'GET':
                resp = requests.get(url, headers=self.headers, params=data, timeout=10)
            elif method == 'POST':
                resp = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PUT':
                resp = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                resp = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return None
            if resp.status_code in [200, 201]:
                return resp.json()
            return None
        except Exception as e:
            print(f"API Hatası: {e}")
            return None
    
    def get_uyeler(self, durum='Aktif'):
        """Üyeleri getir"""
        result = self._request('GET', '/db/uyeler', {'durum': durum})
        return result.get('data', []) if result else []
    
    def get_uye(self, uye_id):
        """Tek üye getir"""
        result = self._request('GET', f'/db/uyeler/{uye_id}')
        return result.get('data') if result else None
    
    def add_uye(self, uye_data):
        """Üye ekle"""
        return self._request('POST', '/db/uyeler', uye_data)
    
    def update_uye(self, uye_id, uye_data):
        """Üye güncelle"""
        return self._request('PUT', f'/db/uyeler/{uye_id}', uye_data)
    
    def delete_uye(self, uye_id):
        """Üye sil"""
        return self._request('DELETE', f'/db/uyeler/{uye_id}')
    
    def get_gelirler(self, limit=100):
        """Gelirleri getir"""
        result = self._request('GET', '/db/gelirler', {'limit': limit})
        return result.get('data', []) if result else []
    
    def add_gelir(self, gelir_data):
        """Gelir ekle"""
        return self._request('POST', '/db/gelirler', gelir_data)
    
    def get_giderler(self, limit=100):
        """Giderleri getir"""
        result = self._request('GET', '/db/giderler', {'limit': limit})
        return result.get('data', []) if result else []
    
    def add_gider(self, gider_data):
        """Gider ekle"""
        return self._request('POST', '/db/giderler', gider_data)
    
    def get_kasalar(self):
        """Kasaları getir"""
        result = self._request('GET', '/db/kasalar')
        return result.get('data', []) if result else []
    
    def get_dashboard(self):
        """Dashboard istatistiklerini getir"""
        return self._request('GET', '/web/dashboard')
    
    def execute_query(self, query, params=None):
        """Genel SQL sorgusu çalıştır"""
        return self._request('POST', '/db/query', {'query': query, 'params': params})


class Database:
    """Veritabanı bağlantı ve işlem yöneticisi - Hybrid (Online/Offline)"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = get_data_path()
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.online_mode = get_license_mode() == 'online'
        self.online_db = OnlineDatabase() if self.online_mode else None
        
    def is_online(self):
        """Online mod aktif mi?"""
        return self.online_mode and self.online_db is not None
        
    def connect(self):
        """Veritabanı bağlantısı oluştur"""
        # check_same_thread=False: Thread güvenliği sorununu çözer
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Dict-like access
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            
    def commit(self):
        """Değişiklikleri kaydet"""
        if self.conn:
            self.conn.commit()
            
    def initialize_database(self):
        """Tüm tabloları oluştur"""
        self.connect()
        
        # 1. ÜYELER TABLOSU (Genişletilmiş - v2)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS uyeler (
                uye_id INTEGER PRIMARY KEY AUTOINCREMENT,
                uye_no TEXT UNIQUE,
                tc_kimlik TEXT,
                ad_soyad TEXT NOT NULL,
                telefon TEXT,
                telefon2 TEXT,
                email TEXT,
                durum TEXT DEFAULT 'Aktif' CHECK(durum IN ('Aktif', 'Pasif', 'Ayrıldı')),
                uyelik_tipi TEXT DEFAULT 'Asil' CHECK(uyelik_tipi IN ('Asil', 'Onursal', 'Fahri', 'Kurumsal')),
                notlar TEXT,
                -- Kişisel bilgiler
                kan_grubu TEXT,
                cinsiyet TEXT CHECK(cinsiyet IN ('Erkek', 'Kadın', '')),
                aile_durumu TEXT DEFAULT 'Bekar' CHECK(aile_durumu IN ('Bekar', 'Evli', 'Dul', 'Boşanmış')),
                cocuk_sayisi INTEGER DEFAULT 0,
                dogum_tarihi DATE,
                dogum_yeri TEXT,
                -- Meslek bilgileri
                meslek TEXT,
                is_yeri TEXT,
                egitim_durumu TEXT CHECK(egitim_durumu IN ('İlkokul', 'Ortaokul', 'Lise', 'Ön Lisans', 'Lisans', 'Yüksek Lisans', 'Doktora', '')),
                -- Adres bilgileri
                il TEXT,
                ilce TEXT,
                mahalle TEXT,
                adres TEXT,
                posta_kodu TEXT,
                -- Referans
                referans_uye_id INTEGER,
                -- Aidat bilgileri
                ozel_aidat_tutari REAL,
                aidat_indirimi_yuzde REAL DEFAULT 0,
                -- Tarihler
                ayrilma_tarihi DATE,
                ayrilma_nedeni TEXT,
                kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referans_uye_id) REFERENCES uyeler(uye_id) ON DELETE SET NULL
            )
        """)
        
        # 2. AİDAT TAKIP TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS aidat_takip (
                aidat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                uye_id INTEGER NOT NULL,
                yil INTEGER NOT NULL,
                yillik_aidat_tutari REAL NOT NULL DEFAULT 0,
                odenecek_tutar REAL DEFAULT 0,
                durum TEXT DEFAULT 'Eksik' CHECK(durum IN ('Tamamlandı', 'Eksik', 'Kısmi')),
                aktarim_durumu TEXT DEFAULT '' CHECK(aktarim_durumu IN ('', 'Aktarıldı')),
                gelir_id INTEGER DEFAULT NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uye_id) REFERENCES uyeler(uye_id) ON DELETE CASCADE,
                FOREIGN KEY (gelir_id) REFERENCES gelirler(gelir_id) ON DELETE SET NULL,
                UNIQUE(uye_id, yil)
            )
        """)
        
        # 3. AİDAT ÖDEMELERİ TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS aidat_odemeleri (
                odeme_id INTEGER PRIMARY KEY AUTOINCREMENT,
                aidat_id INTEGER NOT NULL,
                tarih DATE NOT NULL,
                tutar REAL NOT NULL,
                aciklama TEXT,
                tahsilat_turu TEXT DEFAULT 'Nakit',
                dekont_no TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (aidat_id) REFERENCES aidat_takip(aidat_id) ON DELETE CASCADE
            )
        """)
        
        # 4. KASALAR TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS kasalar (
                kasa_id INTEGER PRIMARY KEY AUTOINCREMENT,
                kasa_adi TEXT NOT NULL UNIQUE,
                para_birimi TEXT DEFAULT 'TL' CHECK(para_birimi IN ('TL', 'USD', 'EUR')),
                devir_bakiye REAL DEFAULT 0,
                aktif INTEGER DEFAULT 1,
                aciklama TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. GELİRLER TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS gelirler (
                gelir_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih DATE NOT NULL,
                belge_no TEXT UNIQUE,
                gelir_turu TEXT NOT NULL CHECK(gelir_turu IN 
                    ('AİDAT', 'KİRA', 'BAĞIŞ', 'DÜĞÜN', 'KINA', 'TOPLANTI', 'DAVET', 'DİĞER')),
                aciklama TEXT,
                tutar REAL NOT NULL,
                kasa_id INTEGER NOT NULL,
                tahsil_eden TEXT,
                notlar TEXT,
                dekont_no TEXT,
                aidat_id INTEGER DEFAULT NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kasa_id) REFERENCES kasalar(kasa_id),
                FOREIGN KEY (aidat_id) REFERENCES aidat_takip(aidat_id) ON DELETE SET NULL
            )
        """)
        
        # 6. GİDERLER TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS giderler (
                gider_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih DATE NOT NULL,
                islem_no TEXT UNIQUE,
                gider_turu TEXT NOT NULL,
                aciklama TEXT,
                tutar REAL NOT NULL,
                kasa_id INTEGER NOT NULL,
                odeyen TEXT,
                notlar TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kasa_id) REFERENCES kasalar(kasa_id)
            )
        """)
        
        # 7. VİRMAN İŞLEMLERİ TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS virmanlar (
                virman_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih DATE NOT NULL,
                gonderen_kasa_id INTEGER NOT NULL,
                alan_kasa_id INTEGER NOT NULL,
                tutar REAL NOT NULL,
                aciklama TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gonderen_kasa_id) REFERENCES kasalar(kasa_id),
                FOREIGN KEY (alan_kasa_id) REFERENCES kasalar(kasa_id),
                CHECK (gonderen_kasa_id != alan_kasa_id)
            )
        """)
        
        # 8. GİDER TÜRLERİ TABLOSU (Dinamik gider kategorileri)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS gider_turleri (
                tur_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tur_adi TEXT NOT NULL UNIQUE,
                aktif INTEGER DEFAULT 1,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 9. SİSTEM AYARLARI TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ayarlar (
                ayar_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ayar_adi TEXT NOT NULL UNIQUE,
                ayar_degeri TEXT,
                aciklama TEXT
            )
        """)
        
        # 10. LOG TABLOSU (Denetim İzi)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS islem_loglari (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                kullanici TEXT,
                islem_turu TEXT,
                tablo_adi TEXT,
                kayit_id INTEGER,
                aciklama TEXT,
                eski_deger TEXT,
                yeni_deger TEXT
            )
        """)
        
        # ========================================
        # KÖY İŞLEMLERİ MODÜLÜ TABLOLARI
        # ========================================
        
        # 11. KÖY KASALARI TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS koy_kasalar (
                kasa_id INTEGER PRIMARY KEY AUTOINCREMENT,
                kasa_adi TEXT NOT NULL UNIQUE,
                para_birimi TEXT DEFAULT 'TL' CHECK(para_birimi IN ('TL', 'USD', 'EUR')),
                devir_bakiye REAL DEFAULT 0,
                aktif INTEGER DEFAULT 1,
                aciklama TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 12. KÖY GELİRLERİ TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS koy_gelirleri (
                gelir_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih DATE NOT NULL,
                belge_no TEXT UNIQUE,
                gelir_turu TEXT NOT NULL,
                aciklama TEXT,
                tutar REAL NOT NULL,
                kasa_id INTEGER NOT NULL,
                tahsil_eden TEXT,
                notlar TEXT,
                dekont_no TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kasa_id) REFERENCES koy_kasalar(kasa_id)
            )
        """)
        
        # 13. KÖY GİDERLERİ TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS koy_giderleri (
                gider_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih DATE NOT NULL,
                islem_no TEXT UNIQUE,
                gider_turu TEXT NOT NULL,
                aciklama TEXT,
                tutar REAL NOT NULL,
                kasa_id INTEGER NOT NULL,
                odeyen TEXT,
                notlar TEXT,
                dekont_no TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kasa_id) REFERENCES koy_kasalar(kasa_id)
            )
        """)
        
        # 14. KÖY VİRMANLARI TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS koy_virmanlar (
                virman_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih DATE NOT NULL,
                gonderen_kasa_id INTEGER NOT NULL,
                alan_kasa_id INTEGER NOT NULL,
                tutar REAL NOT NULL,
                aciklama TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gonderen_kasa_id) REFERENCES koy_kasalar(kasa_id),
                FOREIGN KEY (alan_kasa_id) REFERENCES koy_kasalar(kasa_id),
                CHECK (gonderen_kasa_id != alan_kasa_id)
            )
        """)
        
        # 15. KÖY GELİR TÜRLERİ TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS koy_gelir_turleri (
                tur_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tur_adi TEXT NOT NULL UNIQUE,
                aktif INTEGER DEFAULT 1,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 16. KÖY GİDER TÜRLERİ TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS koy_gider_turleri (
                tur_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tur_adi TEXT NOT NULL UNIQUE,
                aktif INTEGER DEFAULT 1,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========================================
        # KULLANICI VE YETKİ SİSTEMİ
        # ========================================
        
        # 17. KULLANICILAR TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS kullanicilar (
                kullanici_id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_adi TEXT NOT NULL UNIQUE,
                sifre_hash TEXT NOT NULL,
                ad_soyad TEXT NOT NULL,
                email TEXT,
                rol TEXT DEFAULT 'görüntüleyici' CHECK(rol IN ('admin', 'muhasebeci', 'görüntüleyici')),
                izinler TEXT,
                aktif INTEGER DEFAULT 1,
                son_giris TIMESTAMP,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sistem Ayarları Tablosu
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sistem_ayarlari (
                anahtar TEXT PRIMARY KEY,
                deger TEXT,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========================================
        # ETKİNLİK VE TOPLANTI SİSTEMİ
        # ========================================
        
        # 18. ETKİNLİKLER TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS etkinlikler (
                etkinlik_id INTEGER PRIMARY KEY AUTOINCREMENT,
                etkinlik_turu TEXT NOT NULL CHECK(etkinlik_turu IN 
                    ('DÜĞÜN', 'NİŞAN', 'KINA', 'SÜNNET', 'CENAZE', 'MEVLİT', 
                     'TOPLANTI', 'GENEL KURUL', 'DAVET', 'PİKNİK', 'GEZİ', 'DİĞER')),
                baslik TEXT NOT NULL,
                aciklama TEXT,
                tarih DATE NOT NULL,
                saat TIME,
                bitis_tarihi DATE,
                mekan TEXT,
                durum TEXT DEFAULT 'Planlandı' CHECK(durum IN ('Planlandı', 'Devam Ediyor', 'Tamamlandı', 'İptal')),
                katilimci_sayisi INTEGER DEFAULT 0,
                tahmini_gelir REAL DEFAULT 0,
                tahmini_gider REAL DEFAULT 0,
                gerceklesen_gelir REAL DEFAULT 0,
                gerceklesen_gider REAL DEFAULT 0,
                notlar TEXT,
                sorumlu_uye_id INTEGER,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sorumlu_uye_id) REFERENCES uyeler(uye_id) ON DELETE SET NULL
            )
        """)
        
        # 19. ETKİNLİK KATILIMCILARI TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS etkinlik_katilimcilari (
                katilim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                etkinlik_id INTEGER NOT NULL,
                uye_id INTEGER,
                katilimci_adi TEXT,
                katilim_durumu TEXT DEFAULT 'Katılacak' CHECK(katilim_durumu IN ('Katılacak', 'Katıldı', 'Katılmadı', 'Belirsiz')),
                kisi_sayisi INTEGER DEFAULT 1,
                notlar TEXT,
                FOREIGN KEY (etkinlik_id) REFERENCES etkinlikler(etkinlik_id) ON DELETE CASCADE,
                FOREIGN KEY (uye_id) REFERENCES uyeler(uye_id) ON DELETE SET NULL
            )
        """)
        
        # 20. TOPLANTILAR TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS toplantilar (
                toplanti_id INTEGER PRIMARY KEY AUTOINCREMENT,
                toplanti_turu TEXT NOT NULL CHECK(toplanti_turu IN 
                    ('Yönetim Kurulu', 'Genel Kurul', 'Denetim Kurulu', 'Komisyon', 'Diğer')),
                baslik TEXT NOT NULL,
                tarih DATE NOT NULL,
                saat TIME,
                mekan TEXT,
                gundem TEXT,
                kararlar TEXT,
                katilimcilar TEXT,
                tutanak TEXT,
                sonuc TEXT,
                bir_sonraki_toplanti DATE,
                dosya_yolu TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========================================
        # BÜTÇE PLANLAMA SİSTEMİ
        # ========================================
        
        # 21. BÜTÇE PLANLARI TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS butce_planlari (
                butce_id INTEGER PRIMARY KEY AUTOINCREMENT,
                yil INTEGER NOT NULL,
                ay INTEGER,
                kategori TEXT NOT NULL,
                tur TEXT NOT NULL CHECK(tur IN ('GELİR', 'GİDER')),
                planlanan_tutar REAL NOT NULL DEFAULT 0,
                gerceklesen_tutar REAL DEFAULT 0,
                aciklama TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(yil, ay, kategori, tur)
            )
        """)
        
        # ========================================
        # BELGE/DOSYA SİSTEMİ
        # ========================================
        
        # 22. BELGELER TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS belgeler (
                belge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                belge_turu TEXT NOT NULL CHECK(belge_turu IN 
                    ('DEKONT', 'FATURA', 'MAKBUZ', 'SÖZLEŞME', 'TUTANAK', 'KARAR', 'DİĞER')),
                baslik TEXT NOT NULL,
                dosya_adi TEXT NOT NULL,
                dosya_yolu TEXT NOT NULL,
                dosya_boyutu INTEGER,
                ilgili_tablo TEXT,
                ilgili_kayit_id INTEGER,
                aciklama TEXT,
                yukleyen_kullanici_id INTEGER,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (yukleyen_kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE SET NULL
            )
        """)
        
        # İndeksler (Performans için)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_aidat_uye ON aidat_takip(uye_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_aidat_yil ON aidat_takip(yil)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_gelir_tarih ON gelirler(tarih)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_gider_tarih ON giderler(tarih)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_gelir_kasa ON gelirler(kasa_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_gider_kasa ON giderler(kasa_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_uye_durum ON uyeler(durum)")
        
        # Köy modülü indeksleri
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_koy_gelir_tarih ON koy_gelirleri(tarih)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_koy_gider_tarih ON koy_giderleri(tarih)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_koy_gelir_kasa ON koy_gelirleri(kasa_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_koy_gider_kasa ON koy_giderleri(kasa_id)")
        
        self.commit()
        self._populate_initial_data()
        self._run_migrations()
        
    def _populate_initial_data(self):
        """İlk kurulumda varsayılan verileri ekle"""
        
        # Varsayılan kasalar
        default_kasalar = [
            ("BANKA TL", "TL", 0, "Banka hesabı - Türk Lirası"),
            ("BANKA USD", "USD", 0, "Banka hesabı - Dolar"),
            ("DERNEK KASA TL", "TL", 0, "Fiziki kasa - Türk Lirası"),
            ("SAYMAN TL", "TL", 0, "Sayman kasası - Türk Lirası"),
            ("ŞEREF USD", "USD", 0, "Şeref kasası - Dolar"),
            ("ŞEREF TL", "TL", 0, "Şeref kasası - Türk Lirası"),
            ("EURO KASA", "EUR", 0, "Euro kasası"),
        ]
        
        for kasa in default_kasalar:
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO kasalar (kasa_adi, para_birimi, devir_bakiye, aciklama)
                    VALUES (?, ?, ?, ?)
                """, kasa)
            except sqlite3.IntegrityError:
                pass  # Kasa zaten mevcut
                
        # Varsayılan gider türleri
        default_gider_turleri = [
            "ELEKTRİK", "SU", "DOĞALGAZ", "İNTERNET", "TELEFON",
            "KİRA", "TEMİZLİK", "BAKIM-ONARIM", "KIRTASIYE",
            "ORGANİZASYON", "YEMEK", "ULAŞIM", "PERSONEL",
            "VERGİ-HARÇ", "SİGORTA", "DİĞER"
        ]
        
        for tur in default_gider_turleri:
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO gider_turleri (tur_adi)
                    VALUES (?)
                """, (tur,))
            except sqlite3.IntegrityError:
                pass
                
        # Varsayılan ayarlar
        default_ayarlar = [
            ("varsayilan_aidat_tutari", "1000", "Yıllık varsayılan aidat tutarı (TL)"),
            ("usd_kuru", "30.0", "USD/TL kuru"),
            ("eur_kuru", "33.0", "EUR/TL kuru"),
            ("dernek_adi", "BADER Derneği", "Dernek adı"),
            ("dernek_adres", "", "Dernek adresi"),
            ("dernek_telefon", "", "Dernek telefon"),
            ("dernek_email", "", "Dernek e-posta"),
            ("uye_silme_modu", "soft_delete", "Üye silme modu: cascade veya soft_delete"),
        ]
        
        for ayar in default_ayarlar:
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO ayarlar (ayar_adi, ayar_degeri, aciklama)
                    VALUES (?, ?, ?)
                """, ayar)
            except sqlite3.IntegrityError:
                pass
        
        # Varsayılan köy kasaları
        default_koy_kasalar = [
            ("KÖY KASA TL", "TL", 0, "Köy kasası - Türk Lirası"),
        ]
        
        for kasa in default_koy_kasalar:
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO koy_kasalar (kasa_adi, para_birimi, devir_bakiye, aciklama)
                    VALUES (?, ?, ?, ?)
                """, kasa)
            except sqlite3.IntegrityError:
                pass
        
        # Varsayılan köy gelir türleri
        default_koy_gelir_turleri = [
            "KİRA", "BAĞIŞ", "TARIMSAL GELİR", "HAYVANCILIK", "PROJE DESTEĞİ", "DİĞER"
        ]
        
        for tur in default_koy_gelir_turleri:
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO koy_gelir_turleri (tur_adi)
                    VALUES (?)
                """, (tur,))
            except sqlite3.IntegrityError:
                pass
        
        # Varsayılan köy gider türleri
        default_koy_gider_turleri = [
            "ELEKTRİK", "SU", "YOL BAKIM", "ALTYAPI", "TAMIRAT", 
            "PERSONEL", "YAKIT", "MALZEME", "DİĞER"
        ]
        
        for tur in default_koy_gider_turleri:
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO koy_gider_turleri (tur_adi)
                    VALUES (?)
                """, (tur,))
            except sqlite3.IntegrityError:
                pass
        
        # Varsayılan admin kullanıcısı
        import hashlib
        default_password = hashlib.sha256("admin123".encode()).hexdigest()
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO kullanicilar 
                (kullanici_adi, sifre_hash, ad_soyad, email, rol)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", default_password, "Sistem Yöneticisi", "admin@bader.org", "admin"))
        except:
            pass
                
        self.commit()
        
    def _run_migrations(self):
        """Mevcut veritabanını güncelle (yeni kolonlar ekle)"""
        try:
            # uyeler tablosuna yeni alanlar ekle
            migrations = [
                # Temel alanlar
                ("uyeler", "kan_grubu", "TEXT"),
                ("uyeler", "aile_durumu", "TEXT DEFAULT 'Bekar'"),
                ("uyeler", "cocuk_sayisi", "INTEGER DEFAULT 0"),
                ("uyeler", "il", "TEXT"),
                ("uyeler", "ilce", "TEXT"),
                ("uyeler", "mahalle", "TEXT"),
                ("uyeler", "adres", "TEXT"),
                ("uyeler", "posta_kodu", "TEXT"),
                ("uyeler", "dogum_tarihi", "DATE"),
                ("uyeler", "ayrilma_tarihi", "DATE"),
                ("aidat_odemeleri", "dekont_no", "TEXT"),
                ("gelirler", "dekont_no", "TEXT"),
                # v2 - Yeni alanlar
                ("uyeler", "uye_no", "TEXT UNIQUE"),
                ("uyeler", "tc_kimlik", "TEXT"),
                ("uyeler", "telefon2", "TEXT"),
                ("uyeler", "uyelik_tipi", "TEXT DEFAULT 'Asil'"),
                ("uyeler", "cinsiyet", "TEXT"),
                ("uyeler", "dogum_yeri", "TEXT"),
                ("uyeler", "meslek", "TEXT"),
                ("uyeler", "is_yeri", "TEXT"),
                ("uyeler", "egitim_durumu", "TEXT"),
                ("uyeler", "referans_uye_id", "INTEGER"),
                ("uyeler", "ozel_aidat_tutari", "REAL"),
                ("uyeler", "aidat_indirimi_yuzde", "REAL DEFAULT 0"),
                ("uyeler", "ayrilma_nedeni", "TEXT"),
                # v3 - Kullanıcı izinleri
                ("kullanicilar", "izinler", "TEXT"),
                # v4 - Yıl bazlı muhasebe sistemi
                ("gelirler", "ait_oldugu_yil", "INTEGER"),
                ("gelirler", "tahakkuk_durumu", "TEXT DEFAULT 'NORMAL'"),
                ("gelirler", "coklu_odeme_grup_id", "TEXT"),
                ("giderler", "ait_oldugu_yil", "INTEGER"),
                ("giderler", "tahakkuk_durumu", "TEXT DEFAULT 'NORMAL'"),
                ("kasalar", "serbest_devir_bakiye", "REAL DEFAULT 0"),
                ("kasalar", "tahakkuk_toplami", "REAL DEFAULT 0"),
                ("kasalar", "son_devir_tarihi", "DATE"),
            ]
            
            for table, column, col_type in migrations:
                try:
                    self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                except sqlite3.OperationalError:
                    pass  # Kolon zaten var
            
            # Yeni tablolar oluştur
            self._create_additional_tables()
            
            self.commit()
        except Exception as e:
            print(f"Migration hatası: {e}")
    
    def _create_additional_tables(self):
        """Yıl bazlı muhasebe için ek tablolar"""
        # TAHAKKUKLAR tablosu
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tahakkuklar (
                tahakkuk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                yil INTEGER NOT NULL,
                ay INTEGER,
                tahakkuk_tipi TEXT NOT NULL CHECK(tahakkuk_tipi IN ('GELIR', 'GIDER')),
                aciklama TEXT NOT NULL,
                tutar REAL NOT NULL,
                kasa_id INTEGER,
                durum TEXT DEFAULT 'BEKLIYOR' CHECK(durum IN ('BEKLIYOR', 'GERCEKLESTI', 'IPTAL')),
                gerceklesme_tarihi DATE,
                ilgili_kayit_id INTEGER,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kasa_id) REFERENCES kasalar(kasa_id)
            )
        """)
        
        # DEVİR_İŞLEMLERİ tablosu
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS devir_islemleri (
                devir_id INTEGER PRIMARY KEY AUTOINCREMENT,
                yil INTEGER NOT NULL,
                devir_tarihi DATE NOT NULL,
                kasa_id INTEGER NOT NULL,
                onceki_bakiye REAL DEFAULT 0,
                devir_bakiye REAL DEFAULT 0,
                serbest_bakiye REAL DEFAULT 0,
                tahakkuk_bakiye REAL DEFAULT 0,
                aciklama TEXT,
                islem_yapan TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kasa_id) REFERENCES kasalar(kasa_id)
            )
        """)
        
        # AIDAT_ODEME_DETAY tablosu
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS aidat_odeme_detay (
                detay_id INTEGER PRIMARY KEY AUTOINCREMENT,
                odeme_id INTEGER NOT NULL,
                yil INTEGER NOT NULL,
                ay INTEGER,
                tutar REAL NOT NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (odeme_id) REFERENCES aidat_odemeleri(odeme_id) ON DELETE CASCADE
            )
        """)
    
    def log_islem(self, kullanici: str, islem_turu: str, tablo_adi: str, 
                  kayit_id: int, aciklama: str, eski_deger: str = "", yeni_deger: str = ""):
        """İşlem logu kaydet"""
        self.cursor.execute("""
            INSERT INTO islem_loglari 
            (kullanici, islem_turu, tablo_adi, kayit_id, aciklama, eski_deger, yeni_deger)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (kullanici, islem_turu, tablo_adi, kayit_id, aciklama, eski_deger, yeni_deger))
        self.commit()
        
    def get_next_belge_no(self) -> str:
        """Yeni belge numarası üret (Gelirler için)"""
        self.cursor.execute("SELECT MAX(CAST(SUBSTR(belge_no, 4) AS INTEGER)) FROM gelirler WHERE belge_no LIKE 'GEL%'")
        result = self.cursor.fetchone()
        max_no = result[0] if result[0] else 0
        return f"GEL{max_no + 1:06d}"
        
    def get_next_islem_no(self) -> str:
        """Yeni işlem numarası üret (Giderler için)"""
        self.cursor.execute("SELECT MAX(CAST(SUBSTR(islem_no, 4) AS INTEGER)) FROM giderler WHERE islem_no LIKE 'GID%'")
        result = self.cursor.fetchone()
        max_no = result[0] if result[0] else 0
        return f"GID{max_no + 1:06d}"
    
    def get_next_koy_belge_no(self) -> str:
        """Yeni belge numarası üret (Köy Gelirleri için)"""
        self.cursor.execute("SELECT MAX(CAST(SUBSTR(belge_no, 4) AS INTEGER)) FROM koy_gelirleri WHERE belge_no LIKE 'KGE%'")
        result = self.cursor.fetchone()
        max_no = result[0] if result[0] else 0
        return f"KGE{max_no + 1:06d}"
    
    def get_next_koy_islem_no(self) -> str:
        """Yeni işlem numarası üret (Köy Giderleri için)"""
        self.cursor.execute("SELECT MAX(CAST(SUBSTR(islem_no, 4) AS INTEGER)) FROM koy_giderleri WHERE islem_no LIKE 'KGI%'")
        result = self.cursor.fetchone()
        max_no = result[0] if result[0] else 0
        return f"KGI{max_no + 1:06d}"
    
    def add_alacak_verecek_tables(self):
        """Alacak-Verecek tablolarını ekle"""
        # ALACAKLAR TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alacaklar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alacak_turu TEXT NOT NULL,
                aciklama TEXT NOT NULL,
                kisi_kurum TEXT NOT NULL,
                kisi_telefon TEXT,
                kisi_adres TEXT,
                uye_id INTEGER,
                toplam_tutar REAL NOT NULL,
                tahsil_edilen REAL DEFAULT 0,
                kalan_tutar REAL NOT NULL,
                para_birimi TEXT DEFAULT 'TRY',
                alacak_tarihi TEXT NOT NULL,
                vade_tarihi TEXT,
                durum TEXT DEFAULT 'Bekliyor',
                gelir_id INTEGER,
                senet_no TEXT,
                notlar TEXT,
                olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
                kullanici_id INTEGER,
                FOREIGN KEY (uye_id) REFERENCES uyeler(uye_id),
                FOREIGN KEY (gelir_id) REFERENCES gelirler(gelir_id)
            )
        """)
        
        # ALACAK TAHSİLATLARI TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alacak_tahsilatlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alacak_id INTEGER NOT NULL,
                tutar REAL NOT NULL,
                para_birimi TEXT DEFAULT 'TRY',
                tahsilat_tarihi TEXT NOT NULL,
                kasa_id INTEGER NOT NULL,
                gelir_id INTEGER NOT NULL,
                odeme_sekli TEXT DEFAULT 'Nakit',
                aciklama TEXT,
                olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
                kullanici_id INTEGER,
                FOREIGN KEY (alacak_id) REFERENCES alacaklar(id),
                FOREIGN KEY (kasa_id) REFERENCES kasalar(kasa_id),
                FOREIGN KEY (gelir_id) REFERENCES gelirler(gelir_id)
            )
        """)
        
        # VERECEKLER TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS verecekler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verecek_turu TEXT NOT NULL,
                aciklama TEXT NOT NULL,
                kisi_kurum TEXT NOT NULL,
                kisi_telefon TEXT,
                kisi_adres TEXT,
                toplam_tutar REAL NOT NULL,
                odenen REAL DEFAULT 0,
                kalan_tutar REAL NOT NULL,
                para_birimi TEXT DEFAULT 'TRY',
                verecek_tarihi TEXT NOT NULL,
                vade_tarihi TEXT,
                durum TEXT DEFAULT 'Bekliyor',
                gider_id INTEGER,
                fatura_no TEXT,
                notlar TEXT,
                olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
                kullanici_id INTEGER,
                FOREIGN KEY (gider_id) REFERENCES giderler(gider_id)
            )
        """)
        
        # VERECEK ÖDEMELERİ TABLOSU
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS verecek_odemeleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verecek_id INTEGER NOT NULL,
                tutar REAL NOT NULL,
                para_birimi TEXT DEFAULT 'TRY',
                odeme_tarihi TEXT NOT NULL,
                kasa_id INTEGER NOT NULL,
                gider_id INTEGER NOT NULL,
                odeme_sekli TEXT DEFAULT 'Nakit',
                aciklama TEXT,
                olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
                kullanici_id INTEGER,
                FOREIGN KEY (verecek_id) REFERENCES verecekler(id),
                FOREIGN KEY (kasa_id) REFERENCES kasalar(kasa_id),
                FOREIGN KEY (gider_id) REFERENCES giderler(gider_id)
            )
        """)
        
        self.conn.commit()
        
    def backup_database(self, backup_path: str) -> bool:
        """Veritabanını yedekle"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Yedekleme hatası: {e}")
            return False
            
    def restore_database(self, backup_path: str) -> bool:
        """Veritabanını geri yükle"""
        try:
            import shutil
            self.close()
            shutil.copy2(backup_path, self.db_path)
            self.connect()
            return True
        except Exception as e:
            print(f"Geri yükleme hatası: {e}")
            return False

