"""
Yıl Bazlı Muhasebe Sistemi - Veritabanı Migration
Mevcut tabloları günceller ve yeni tabloları ekler
"""

from database import Database
import sqlite3

def migrate_database():
    """Ana migration fonksiyonu"""
    db = Database()
    db.connect()
    
    print("🚀 Yıl Bazlı Muhasebe Migration Başlıyor...")
    print("=" * 60)
    
    try:
        # 1. GELİRLER tablosuna yeni kolonlar ekle
        print("\n1️⃣  GELİRLER tablosuna yeni kolonlar ekleniyor...")
        add_columns_to_gelirler(db)
        
        # 2. GİDERLER tablosuna yeni kolonlar ekle
        print("\n2️⃣  GİDERLER tablosuna yeni kolonlar ekleniyor...")
        add_columns_to_giderler(db)
        
        # 3. KASALAR tablosuna yeni kolonlar ekle
        print("\n3️⃣  KASALAR tablosuna yeni kolonlar ekleniyor...")
        add_columns_to_kasalar(db)
        
        # 4. AİDAT_ÖDEMELERİ tablosunu güncelle
        print("\n4️⃣  AİDAT_ÖDEMELERİ tablosu güncelleniyor...")
        update_aidat_odemeleri(db)
        
        # 5. Yeni AIDAT_ODEME_DETAY tablosu
        print("\n5️⃣  AIDAT_ODEME_DETAY tablosu oluşturuluyor...")
        create_aidat_odeme_detay(db)
        
        # 6. Yeni TAHAKKUKLAR tablosu
        print("\n6️⃣  TAHAKKUKLAR tablosu oluşturuluyor...")
        create_tahakkuklar(db)
        
        # 7. Yeni DEVİR_İŞLEMLERİ tablosu
        print("\n7️⃣  DEVİR_İŞLEMLERİ tablosu oluşturuluyor...")
        create_devir_islemleri(db)
        
        # 8. Mevcut verileri güncelle
        print("\n8️⃣  Mevcut veriler güncelleniyor...")
        update_existing_data(db)
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ Migration başarıyla tamamlandı!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration hatası: {e}")
        db.conn.rollback()
        raise
    
    finally:
        db.close()


def add_columns_to_gelirler(db):
    """GELİRLER tablosuna yeni kolonlar ekle"""
    
    # ait_oldugu_yil kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE gelirler 
            ADD COLUMN ait_oldugu_yil INTEGER
        """)
        print("   ✓ ait_oldugu_yil kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  ait_oldugu_yil kolonu zaten mevcut")
        else:
            raise
    
    # tahakkuk_durumu kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE gelirler 
            ADD COLUMN tahakkuk_durumu TEXT DEFAULT 'NORMAL'
        """)
        print("   ✓ tahakkuk_durumu kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  tahakkuk_durumu kolonu zaten mevcut")
        else:
            raise
    
    # coklu_odeme_grup_id kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE gelirler 
            ADD COLUMN coklu_odeme_grup_id TEXT
        """)
        print("   ✓ coklu_odeme_grup_id kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  coklu_odeme_grup_id kolonu zaten mevcut")
        else:
            raise


def add_columns_to_giderler(db):
    """GİDERLER tablosuna yeni kolonlar ekle"""
    
    # ait_oldugu_yil kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE giderler 
            ADD COLUMN ait_oldugu_yil INTEGER
        """)
        print("   ✓ ait_oldugu_yil kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  ait_oldugu_yil kolonu zaten mevcut")
        else:
            raise
    
    # tahakkuk_durumu kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE giderler 
            ADD COLUMN tahakkuk_durumu TEXT DEFAULT 'NORMAL'
        """)
        print("   ✓ tahakkuk_durumu kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  tahakkuk_durumu kolonu zaten mevcut")
        else:
            raise


def add_columns_to_kasalar(db):
    """KASALAR tablosuna yeni kolonlar ekle"""
    
    # serbest_devir_bakiye kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE kasalar 
            ADD COLUMN serbest_devir_bakiye REAL DEFAULT 0
        """)
        print("   ✓ serbest_devir_bakiye kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  serbest_devir_bakiye kolonu zaten mevcut")
        else:
            raise
    
    # tahakkuk_toplami kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE kasalar 
            ADD COLUMN tahakkuk_toplami REAL DEFAULT 0
        """)
        print("   ✓ tahakkuk_toplami kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  tahakkuk_toplami kolonu zaten mevcut")
        else:
            raise
    
    # son_devir_tarihi kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE kasalar 
            ADD COLUMN son_devir_tarihi TIMESTAMP
        """)
        print("   ✓ son_devir_tarihi kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  son_devir_tarihi kolonu zaten mevcut")
        else:
            raise


def update_aidat_odemeleri(db):
    """AİDAT_ÖDEMELERİ tablosuna yeni kolonlar ekle"""
    
    # odeme_grup_id kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE aidat_odemeleri 
            ADD COLUMN odeme_grup_id TEXT
        """)
        print("   ✓ odeme_grup_id kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  odeme_grup_id kolonu zaten mevcut")
        else:
            raise
    
    # toplam_tutar kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE aidat_odemeleri 
            ADD COLUMN toplam_tutar REAL
        """)
        print("   ✓ toplam_tutar kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  toplam_tutar kolonu zaten mevcut")
        else:
            raise
    
    # kasa_id kolonu
    try:
        db.cursor.execute("""
            ALTER TABLE aidat_odemeleri 
            ADD COLUMN kasa_id INTEGER
        """)
        print("   ✓ kasa_id kolonu eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⚠️  kasa_id kolonu zaten mevcut")
        else:
            raise


def create_aidat_odeme_detay(db):
    """AIDAT_ODEME_DETAY tablosunu oluştur"""
    
    db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS aidat_odeme_detay (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            odeme_grup_id TEXT NOT NULL,
            aidat_id INTEGER NOT NULL,
            tutar REAL NOT NULL,
            gelir_id INTEGER,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (aidat_id) REFERENCES aidat_takip(aidat_id) ON DELETE CASCADE,
            FOREIGN KEY (gelir_id) REFERENCES gelirler(gelir_id) ON DELETE SET NULL
        )
    """)
    print("   ✓ aidat_odeme_detay tablosu oluşturuldu")


def create_tahakkuklar(db):
    """TAHAKKUKLAR tablosunu oluştur"""
    
    db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tahakkuklar (
            tahakkuk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            tahakkuk_turu TEXT NOT NULL CHECK(tahakkuk_turu IN ('GELİR', 'GİDER')),
            kaynak_tablo TEXT NOT NULL,
            kaynak_id INTEGER NOT NULL,
            
            tahsil_yili INTEGER NOT NULL,
            ait_oldugu_yil INTEGER NOT NULL,
            
            tutar REAL NOT NULL,
            durum TEXT DEFAULT 'AKTİF' CHECK(durum IN ('AKTİF', 'KULLANILDI', 'İADE_EDİLDİ')),
            
            aciklama TEXT,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ tahakkuklar tablosu oluşturuldu")
    
    # İndeksler
    db.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tahakkuk_yil 
        ON tahakkuklar(ait_oldugu_yil, durum)
    """)
    db.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tahakkuk_kaynak 
        ON tahakkuklar(kaynak_tablo, kaynak_id)
    """)
    print("   ✓ İndeksler oluşturuldu")


def create_devir_islemleri(db):
    """DEVİR_İŞLEMLERİ tablosunu oluştur"""
    
    db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS devir_islemleri (
            devir_id INTEGER PRIMARY KEY AUTOINCREMENT,
            yil INTEGER NOT NULL UNIQUE,
            devir_tarihi TIMESTAMP NOT NULL,
            
            toplam_fiziksel REAL NOT NULL,
            toplam_tahakkuk REAL NOT NULL,
            toplam_serbest REAL NOT NULL,
            
            rapor_json TEXT,
            aciklama TEXT,
            
            olusturan TEXT,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ devir_islemleri tablosu oluşturuldu")


def update_existing_data(db):
    """Mevcut verileri güncelle"""
    
    # 1. GELİRLER - ait_oldugu_yil'i tarihten hesapla
    db.cursor.execute("""
        UPDATE gelirler 
        SET ait_oldugu_yil = CAST(strftime('%Y', tarih) AS INTEGER)
        WHERE ait_oldugu_yil IS NULL
    """)
    gelir_count = db.cursor.rowcount
    print(f"   ✓ {gelir_count} gelir kaydı güncellendi (ait_oldugu_yil)")
    
    # 2. GİDERLER - ait_oldugu_yil'i tarihten hesapla
    db.cursor.execute("""
        UPDATE giderler 
        SET ait_oldugu_yil = CAST(strftime('%Y', tarih) AS INTEGER)
        WHERE ait_oldugu_yil IS NULL
    """)
    gider_count = db.cursor.rowcount
    print(f"   ✓ {gider_count} gider kaydı güncellendi (ait_oldugu_yil)")
    
    # 3. GELİRLER - tahakkuk_durumu'nu NORMAL yap
    db.cursor.execute("""
        UPDATE gelirler 
        SET tahakkuk_durumu = 'NORMAL'
        WHERE tahakkuk_durumu IS NULL OR tahakkuk_durumu = ''
    """)
    print(f"   ✓ Gelir tahakkuk durumları güncellendi")
    
    # 4. GİDERLER - tahakkuk_durumu'nu NORMAL yap
    db.cursor.execute("""
        UPDATE giderler 
        SET tahakkuk_durumu = 'NORMAL'
        WHERE tahakkuk_durumu IS NULL OR tahakkuk_durumu = ''
    """)
    print(f"   ✓ Gider tahakkuk durumları güncellendi")
    
    # 5. KASALAR - serbest_devir_bakiye'yi devir_bakiye ile eşitle
    db.cursor.execute("""
        UPDATE kasalar 
        SET serbest_devir_bakiye = devir_bakiye
        WHERE serbest_devir_bakiye IS NULL OR serbest_devir_bakiye = 0
    """)
    print(f"   ✓ Kasa serbest bakiyeleri güncellendi")


if __name__ == "__main__":
    migrate_database()
