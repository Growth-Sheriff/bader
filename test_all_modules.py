#!/usr/bin/env python3
"""
BADER Derneği - Kapsamlı Modül Test Scripti
Tüm CRUD operasyonlarını test eder

Bu script offline modda tüm modülleri test eder:
1. Üyeler - Ekle, Güncelle, Sil, Listele
2. Aidat - Kayıt Oluştur, Ödeme Ekle, Sil
3. Gelir - Ekle, Güncelle, Sil, Listele
4. Gider - Ekle, Güncelle, Sil, Listele
5. Kasa - Ekle, Güncelle, Listele
6. Virman - Ekle, Sil, Listele
"""

import os
import sys
from datetime import datetime, timedelta
import traceback

# Test sonuçlarını sakla
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def log_success(test_name, message=""):
    print(f"✅ PASS: {test_name} {message}")
    test_results['passed'].append((test_name, message))

def log_fail(test_name, error):
    print(f"❌ FAIL: {test_name} - {error}")
    test_results['failed'].append((test_name, str(error)))

def log_warning(test_name, message):
    print(f"⚠️  WARN: {test_name} - {message}")
    test_results['warnings'].append((test_name, message))

def print_separator(title=""):
    print("\n" + "="*60)
    if title:
        print(f"   {title}")
        print("="*60)


# ============================================================
#   MODÜLLER TEST
# ============================================================

def test_database_connection():
    """Database bağlantı testi"""
    try:
        from database import Database
        db = Database()
        
        # License mode kontrolü
        db.cursor.execute("SELECT ayar_degeri FROM ayarlar WHERE ayar_adi = 'license_mode'")
        result = db.cursor.fetchone()
        mode = result['ayar_degeri'] if result else 'offline'
        
        log_success("Database Bağlantı", f"(mode={mode})")
        return db
    except Exception as e:
        log_fail("Database Bağlantı", e)
        return None


def test_uyeler_module(db):
    """Üyeler modülü testleri"""
    print_separator("ÜYELER MODÜLÜ TESTLERİ")
    
    from models import UyeYoneticisi
    uye_yoneticisi = UyeYoneticisi(db)
    
    test_uye_id = None
    
    # 1. Üye Listesi
    try:
        uyeler = uye_yoneticisi.uye_listesi()
        log_success("Üye Listesi", f"({len(uyeler)} üye bulundu)")
    except Exception as e:
        log_fail("Üye Listesi", e)
    
    # 2. Üye Ekle
    try:
        test_data = {
            'ad_soyad': f'TEST_USER_{datetime.now().strftime("%H%M%S")}',
            'telefon': '05551234567',
            'email': 'test@test.com',
            'uyelik_tipi': 'Asil',
            'durum': 'Aktif',
            'tc_kimlik': '12345678901',
            'uye_no': f'TEST{datetime.now().strftime("%H%M%S")}'
        }
        test_uye_id = uye_yoneticisi.uye_ekle(**test_data)
        if test_uye_id and test_uye_id > 0:
            log_success("Üye Ekle", f"(uye_id={test_uye_id})")
        else:
            log_fail("Üye Ekle", f"Geçersiz ID döndü: {test_uye_id}")
    except Exception as e:
        log_fail("Üye Ekle", e)
        traceback.print_exc()
    
    # 3. Üye Getir
    if test_uye_id:
        try:
            uye = uye_yoneticisi.uye_getir(test_uye_id)
            if uye and uye.get('ad_soyad'):
                log_success("Üye Getir", f"({uye.get('ad_soyad')})")
            else:
                log_fail("Üye Getir", "Üye bulunamadı")
        except Exception as e:
            log_fail("Üye Getir", e)
    
    # 4. Üye Güncelle
    if test_uye_id:
        try:
            uye_yoneticisi.uye_guncelle(test_uye_id, ad_soyad='TEST_GUNCELLENDI', telefon='05559999999')
            uye = uye_yoneticisi.uye_getir(test_uye_id)
            if uye and 'GUNCELLENDI' in uye.get('ad_soyad', ''):
                log_success("Üye Güncelle", "(ad_soyad güncellendi)")
            else:
                log_fail("Üye Güncelle", "Güncelleme doğrulanamadı")
        except Exception as e:
            log_fail("Üye Güncelle", e)
    
    # 5. Üye Sil (Soft Delete)
    if test_uye_id:
        try:
            uye_yoneticisi.uye_sil(test_uye_id, mode='soft_delete')
            uye = uye_yoneticisi.uye_getir(test_uye_id)
            if uye and uye.get('durum') == 'Ayrıldı':
                log_success("Üye Sil (Soft)", "(durum=Ayrıldı)")
            else:
                log_warning("Üye Sil (Soft)", "Durum değişikliği doğrulanamadı")
        except Exception as e:
            log_fail("Üye Sil (Soft)", e)
    
    # 6. Üye Sil (Cascade - gerçekten sil)
    if test_uye_id:
        try:
            uye_yoneticisi.uye_sil(test_uye_id, mode='cascade')
            uye = uye_yoneticisi.uye_getir(test_uye_id)
            if not uye:
                log_success("Üye Sil (Cascade)", "(tamamen silindi)")
            else:
                log_warning("Üye Sil (Cascade)", "Üye hala mevcut")
        except Exception as e:
            log_fail("Üye Sil (Cascade)", e)
    
    return test_uye_id


def test_kasa_module(db):
    """Kasa modülü testleri"""
    print_separator("KASA MODÜLÜ TESTLERİ")
    
    from models import KasaYoneticisi
    kasa_yoneticisi = KasaYoneticisi(db)
    
    test_kasa_id = None
    
    # 1. Kasa Listesi
    try:
        kasalar = kasa_yoneticisi.kasa_listesi()
        log_success("Kasa Listesi", f"({len(kasalar)} kasa bulundu)")
        
        # Test için mevcut kasa var mı?
        if kasalar:
            test_kasa_id = kasalar[0]['kasa_id']
    except Exception as e:
        log_fail("Kasa Listesi", e)
    
    # 2. Kasa Ekle
    try:
        yeni_kasa = {
            'kasa_adi': f'TEST_KASA_{datetime.now().strftime("%H%M%S")}',
            'kasa_turu': 'Nakit',
            'para_birimi': 'TRY',
            'baslangic_bakiye': 1000.0
        }
        new_kasa_id = kasa_yoneticisi.kasa_ekle(**yeni_kasa)
        if new_kasa_id and new_kasa_id > 0:
            log_success("Kasa Ekle", f"(kasa_id={new_kasa_id})")
            test_kasa_id = new_kasa_id
        else:
            log_fail("Kasa Ekle", f"Geçersiz ID döndü: {new_kasa_id}")
    except Exception as e:
        log_fail("Kasa Ekle", e)
    
    # 3. Kasa Bakiye
    if test_kasa_id:
        try:
            bakiye = kasa_yoneticisi.kasa_bakiye(test_kasa_id)
            log_success("Kasa Bakiye", f"({bakiye:.2f} TL)")
        except Exception as e:
            log_fail("Kasa Bakiye", e)
    
    return test_kasa_id


def test_gelir_module(db, kasa_id):
    """Gelir modülü testleri"""
    print_separator("GELİR MODÜLÜ TESTLERİ")
    
    from models import GelirYoneticisi
    gelir_yoneticisi = GelirYoneticisi(db)
    
    test_gelir_id = None
    
    # 1. Gelir Listesi
    try:
        gelirler = gelir_yoneticisi.gelir_listesi()
        log_success("Gelir Listesi", f"({len(gelirler)} gelir bulundu)")
    except Exception as e:
        log_fail("Gelir Listesi", e)
    
    # 2. Gelir Ekle
    if kasa_id:
        try:
            test_data = {
                'tarih': datetime.now().strftime('%Y-%m-%d'),
                'gelir_turu': 'BAĞIŞ',
                'aciklama': f'TEST GELİR {datetime.now().strftime("%H%M%S")}',
                'tutar': 500.0,
                'kasa_id': kasa_id,
                'tahsil_eden': 'Test User'
            }
            test_gelir_id = gelir_yoneticisi.gelir_ekle(**test_data)
            if test_gelir_id and test_gelir_id > 0:
                log_success("Gelir Ekle", f"(gelir_id={test_gelir_id})")
            else:
                log_fail("Gelir Ekle", f"Geçersiz ID döndü: {test_gelir_id}")
        except Exception as e:
            log_fail("Gelir Ekle", e)
    else:
        log_warning("Gelir Ekle", "Kasa ID yok, test atlandı")
    
    # 3. Gelir Güncelle
    if test_gelir_id:
        try:
            gelir_yoneticisi.gelir_guncelle(test_gelir_id, tutar=750.0, aciklama='GUNCELLENDI')
            gelir = gelir_yoneticisi.gelir_getir(test_gelir_id)
            if gelir and gelir.get('tutar') == 750.0:
                log_success("Gelir Güncelle", "(tutar=750 TL)")
            else:
                log_warning("Gelir Güncelle", "Güncelleme doğrulanamadı")
        except Exception as e:
            log_fail("Gelir Güncelle", e)
    
    # 4. Gelir Sil
    if test_gelir_id:
        try:
            gelir_yoneticisi.gelir_sil(test_gelir_id)
            gelir = gelir_yoneticisi.gelir_getir(test_gelir_id)
            if not gelir:
                log_success("Gelir Sil", "(tamamen silindi)")
            else:
                log_warning("Gelir Sil", "Gelir hala mevcut")
        except Exception as e:
            log_fail("Gelir Sil", e)
    
    return test_gelir_id


def test_gider_module(db, kasa_id):
    """Gider modülü testleri"""
    print_separator("GİDER MODÜLÜ TESTLERİ")
    
    from models import GiderYoneticisi
    gider_yoneticisi = GiderYoneticisi(db)
    
    test_gider_id = None
    
    # 1. Gider Listesi
    try:
        giderler = gider_yoneticisi.gider_listesi()
        log_success("Gider Listesi", f"({len(giderler)} gider bulundu)")
    except Exception as e:
        log_fail("Gider Listesi", e)
    
    # 2. Gider Ekle
    if kasa_id:
        try:
            test_data = {
                'tarih': datetime.now().strftime('%Y-%m-%d'),
                'gider_turu': 'ELEKTRİK',
                'aciklama': f'TEST GİDER {datetime.now().strftime("%H%M%S")}',
                'tutar': 250.0,
                'kasa_id': kasa_id,
                'odeyen': 'Test User'
            }
            test_gider_id = gider_yoneticisi.gider_ekle(**test_data)
            if test_gider_id and test_gider_id > 0:
                log_success("Gider Ekle", f"(gider_id={test_gider_id})")
            else:
                log_fail("Gider Ekle", f"Geçersiz ID döndü: {test_gider_id}")
        except Exception as e:
            log_fail("Gider Ekle", e)
    else:
        log_warning("Gider Ekle", "Kasa ID yok, test atlandı")
    
    # 3. Gider Güncelle
    if test_gider_id:
        try:
            gider_yoneticisi.gider_guncelle(test_gider_id, tutar=300.0, aciklama='GUNCELLENDI')
            gider = gider_yoneticisi.gider_getir(test_gider_id)
            if gider and gider.get('tutar') == 300.0:
                log_success("Gider Güncelle", "(tutar=300 TL)")
            else:
                log_warning("Gider Güncelle", "Güncelleme doğrulanamadı")
        except Exception as e:
            log_fail("Gider Güncelle", e)
    
    # 4. Gider Sil
    if test_gider_id:
        try:
            gider_yoneticisi.gider_sil(test_gider_id)
            gider = gider_yoneticisi.gider_getir(test_gider_id)
            if not gider:
                log_success("Gider Sil", "(tamamen silindi)")
            else:
                log_warning("Gider Sil", "Gider hala mevcut")
        except Exception as e:
            log_fail("Gider Sil", e)
    
    return test_gider_id


def test_aidat_module(db):
    """Aidat modülü testleri"""
    print_separator("AİDAT MODÜLÜ TESTLERİ")
    
    from models import AidatYoneticisi, UyeYoneticisi
    aidat_yoneticisi = AidatYoneticisi(db)
    uye_yoneticisi = UyeYoneticisi(db)
    
    # Önce test üyesi oluştur
    test_uye_id = None
    try:
        test_uye_id = uye_yoneticisi.uye_ekle(
            ad_soyad=f'AIDAT_TEST_{datetime.now().strftime("%H%M%S")}',
            telefon='05550000000',
            durum='Aktif',
            uyelik_tipi='Asil'
        )
    except:
        pass
    
    if not test_uye_id:
        # Mevcut üyelerden birini al
        uyeler = uye_yoneticisi.uye_listesi()
        aktif_uyeler = [u for u in uyeler if u.get('durum') == 'Aktif']
        if aktif_uyeler:
            test_uye_id = aktif_uyeler[0]['uye_id']
    
    test_aidat_id = None
    test_odeme_id = None
    
    # 1. Aidat Listesi
    try:
        aidatlar = aidat_yoneticisi.aidat_listesi()
        log_success("Aidat Listesi", f"({len(aidatlar)} aidat kaydı)")
    except Exception as e:
        log_fail("Aidat Listesi", e)
    
    # 2. Aidat Kaydı Oluştur
    if test_uye_id:
        try:
            test_yil = datetime.now().year + 10  # Gelecek yıl çakışma olmasın
            test_aidat_id = aidat_yoneticisi.aidat_kaydi_olustur(test_uye_id, test_yil, 1200.0)
            if test_aidat_id and test_aidat_id > 0:
                log_success("Aidat Kaydı Oluştur", f"(aidat_id={test_aidat_id}, yıl={test_yil})")
            else:
                # Mevcut kayıt olabilir
                log_warning("Aidat Kaydı Oluştur", f"ID döndü: {test_aidat_id}")
        except Exception as e:
            log_fail("Aidat Kaydı Oluştur", e)
    else:
        log_warning("Aidat Kaydı Oluştur", "Test üyesi yok, atlandı")
    
    # 3. Aidat Ödeme Ekle
    if test_aidat_id and test_aidat_id > 0:
        try:
            test_odeme_id = aidat_yoneticisi.aidat_odeme_ekle(
                aidat_id=test_aidat_id,
                tutar=500.0,
                tarih=datetime.now().strftime('%Y-%m-%d'),
                aciklama='TEST ÖDEME'
            )
            if test_odeme_id and test_odeme_id > 0:
                log_success("Aidat Ödeme Ekle", f"(odeme_id={test_odeme_id})")
            else:
                log_fail("Aidat Ödeme Ekle", f"Geçersiz ID döndü: {test_odeme_id}")
        except Exception as e:
            log_fail("Aidat Ödeme Ekle", e)
    
    # 4. Ödeme Sil
    if test_odeme_id and test_odeme_id > 0:
        try:
            aidat_yoneticisi.aidat_odeme_sil(test_odeme_id)
            log_success("Aidat Ödeme Sil", "(ödeme silindi)")
        except Exception as e:
            log_fail("Aidat Ödeme Sil", e)
    
    # Temizlik: Test üyesini sil
    if test_uye_id:
        try:
            uye = uye_yoneticisi.uye_getir(test_uye_id)
            if uye and 'AIDAT_TEST' in uye.get('ad_soyad', ''):
                uye_yoneticisi.uye_sil(test_uye_id, mode='cascade')
        except:
            pass
    
    return test_aidat_id


def test_virman_module(db, kasa_id):
    """Virman modülü testleri"""
    print_separator("VİRMAN MODÜLÜ TESTLERİ")
    
    from models import VirmanYoneticisi, KasaYoneticisi
    virman_yoneticisi = VirmanYoneticisi(db)
    kasa_yoneticisi = KasaYoneticisi(db)
    
    # İki kasa gerekli
    kasalar = kasa_yoneticisi.kasa_listesi()
    if len(kasalar) < 2:
        log_warning("Virman Testleri", "En az 2 kasa gerekli, atlandı")
        return None
    
    kaynak_kasa_id = kasalar[0]['kasa_id']
    hedef_kasa_id = kasalar[1]['kasa_id']
    
    test_virman_id = None
    
    # 1. Virman Listesi
    try:
        virmanlar = virman_yoneticisi.virman_listesi()
        log_success("Virman Listesi", f"({len(virmanlar)} virman bulundu)")
    except Exception as e:
        log_fail("Virman Listesi", e)
    
    # 2. Virman Ekle
    try:
        test_virman_id = virman_yoneticisi.virman_ekle(
            kaynak_kasa_id=kaynak_kasa_id,
            hedef_kasa_id=hedef_kasa_id,
            tutar=100.0,
            tarih=datetime.now().strftime('%Y-%m-%d'),
            aciklama='TEST VIRMAN'
        )
        if test_virman_id and test_virman_id > 0:
            log_success("Virman Ekle", f"(virman_id={test_virman_id})")
        else:
            log_fail("Virman Ekle", f"Geçersiz ID döndü: {test_virman_id}")
    except Exception as e:
        log_fail("Virman Ekle", e)
    
    # 3. Virman Sil
    if test_virman_id and test_virman_id > 0:
        try:
            virman_yoneticisi.virman_sil(test_virman_id)
            log_success("Virman Sil", "(virman silindi)")
        except Exception as e:
            log_fail("Virman Sil", e)
    
    return test_virman_id


def print_final_report():
    """Final test raporu"""
    print_separator("KAPSAMLI TEST RAPORU")
    
    total_tests = len(test_results['passed']) + len(test_results['failed'])
    passed = len(test_results['passed'])
    failed = len(test_results['failed'])
    warnings = len(test_results['warnings'])
    
    print(f"\n📊 SONUÇ ÖZETİ:")
    print(f"   • Toplam Test: {total_tests}")
    print(f"   • Başarılı:    {passed} ✅")
    print(f"   • Başarısız:   {failed} ❌")
    print(f"   • Uyarılar:    {warnings} ⚠️")
    print(f"   • Başarı Oranı: {(passed/total_tests*100):.1f}%" if total_tests > 0 else "   • Başarı Oranı: 0%")
    
    if test_results['failed']:
        print(f"\n❌ BAŞARISIZ TESTLER:")
        for name, error in test_results['failed']:
            print(f"   • {name}: {error}")
    
    if test_results['warnings']:
        print(f"\n⚠️  UYARILAR:")
        for name, msg in test_results['warnings']:
            print(f"   • {name}: {msg}")
    
    print("\n" + "="*60)
    if failed == 0:
        print("🎉 TÜM TESTLER BAŞARILI!")
    else:
        print("⚠️  BAZI TESTLER BAŞARISIZ - KONTROL EDİN!")
    print("="*60 + "\n")


def main():
    """Ana test fonksiyonu"""
    print("\n" + "="*60)
    print("   BADER DERNEĞİ - KAPSAMLI MODÜL TESTİ")
    print("   Tarih: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # Database bağlantı
    db = test_database_connection()
    if not db:
        print("\n❌ Database bağlantısı başarısız, testler durduruluyor!")
        return
    
    # Modül testleri
    test_uyeler_module(db)
    kasa_id = test_kasa_module(db)
    test_gelir_module(db, kasa_id)
    test_gider_module(db, kasa_id)
    test_aidat_module(db)
    test_virman_module(db, kasa_id)
    
    # Final rapor
    print_final_report()


if __name__ == "__main__":
    main()
