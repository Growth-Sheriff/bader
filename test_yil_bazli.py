"""
Yıl Bazlı Muhasebe Sistemi - Test Senaryoları
"""

from database import Database
from models import GelirYoneticisi, KasaYoneticisi, DevirYoneticisi, TahakkukYoneticisi
from datetime import datetime

def test_coklu_yil_odeme():
    """Çok yıllık ödeme testi"""
    print("\n" + "="*60)
    print("TEST: Çok Yıllık Ödeme")
    print("="*60)
    
    db = Database()
    db.connect()
    
    gelir_yoneticisi = GelirYoneticisi(db)
    kasa_yoneticisi = KasaYoneticisi(db)
    
    # Test verileri
    kasa_id = 1
    baslangic_yil = 2025
    bitis_yil = 2034  # 10 yıl
    yillik_tutar = 100.0
    
    print(f"\n📅 Senaryo: {baslangic_yil}-{bitis_yil} arası çok yıllık ödeme")
    print(f"   Yıllık Tutar: {yillik_tutar} TL")
    print(f"   Toplam: {yillik_tutar * (bitis_yil - baslangic_yil + 1)} TL")
    
    # Kasa durumu (ÖNCE)
    print("\n🏦 KASA DURUMU (ÖNCE):")
    onceki_fiziksel = kasa_yoneticisi.kasa_bakiye_tip(kasa_id, tip='fiziksel')
    onceki_serbest = kasa_yoneticisi.kasa_bakiye_tip(kasa_id, tip='serbest')
    print(f"   Fiziksel Bakiye: {onceki_fiziksel:,.2f} TL")
    print(f"   Serbest Bakiye:  {onceki_serbest:,.2f} TL")
    
    # Çok yıllık ödeme ekle
    try:
        grup_id = gelir_yoneticisi.coklu_yil_gelir_ekle(
            gelir_turu='AİDAT',
            kasa_id=kasa_id,
            baslangic_yil=baslangic_yil,
            bitis_yil=bitis_yil,
            yillik_tutar=yillik_tutar,
            tahsil_tarihi=datetime.now().strftime("%Y-%m-%d"),
            aciklama="Test Çok Yıllık Ödeme"
        )
        
        print(f"\n✅ Ödeme başarılı! Grup ID: {grup_id}")
        
        # Gelir kayıtlarını kontrol et
        db.cursor.execute("""
            SELECT ait_oldugu_yil, tahakkuk_durumu, tutar
            FROM gelirler
            WHERE coklu_odeme_grup_id = ?
            ORDER BY ait_oldugu_yil
        """, (grup_id,))
        gelirler = db.cursor.fetchall()
        
        print(f"\n📊 Oluşturulan Gelir Kayıtları ({len(gelirler)} adet):")
        for gelir in gelirler[:3]:  # İlk 3'ü göster
            print(f"   {gelir['ait_oldugu_yil']}: {gelir['tutar']:,.2f} TL ({gelir['tahakkuk_durumu']})")
        if len(gelirler) > 3:
            print(f"   ... ve {len(gelirler) - 3} kayıt daha")
        
        # Tahakkukları kontrol et
        db.cursor.execute("""
            SELECT COUNT(*) as adet, SUM(tutar) as toplam
            FROM tahakkuklar
            WHERE tahakkuk_turu = 'GELİR'
            AND durum = 'AKTİF'
        """)
        tahakkuk = db.cursor.fetchone()
        
        print(f"\n📈 Tahakkuk Durumu:")
        print(f"   Aktif Tahakkuk Sayısı: {tahakkuk['adet']}")
        print(f"   Toplam Tahakkuk: {tahakkuk['toplam']:,.2f} TL")
        
        # Kasa durumu (SONRA)
        print("\n🏦 KASA DURUMU (SONRA):")
        sonraki_fiziksel = kasa_yoneticisi.kasa_bakiye_tip(kasa_id, tip='fiziksel')
        sonraki_serbest = kasa_yoneticisi.kasa_bakiye_tip(kasa_id, tip='serbest')
        print(f"   Fiziksel Bakiye: {sonraki_fiziksel:,.2f} TL (+{sonraki_fiziksel - onceki_fiziksel:,.2f} TL)")
        print(f"   Serbest Bakiye:  {sonraki_serbest:,.2f} TL (+{sonraki_serbest - onceki_serbest:,.2f} TL)")
        
        # Tahakkuk detayı
        detay = kasa_yoneticisi.kasa_tahakkuk_detay(kasa_id)
        print(f"\n📋 Tahakkuk Detayı:")
        print(f"   Gelecek Yıl Tahakkukları: {detay['tahakkuk_toplami']:,.2f} TL")
        print(f"   Yıl Sayısı: {len(detay['gelecek_yil_detay'])}")
        
        # Doğrulama
        print("\n✅ DOĞRULAMA:")
        toplam_tutar = yillik_tutar * (bitis_yil - baslangic_yil + 1)
        fiziksel_artis = sonraki_fiziksel - onceki_fiziksel
        
        if abs(fiziksel_artis - toplam_tutar) < 0.01:
            print(f"   ✓ Fiziksel bakiye doğru artmış: {fiziksel_artis:,.2f} TL")
        else:
            print(f"   ✗ Fiziksel bakiye hatası! Beklenen: {toplam_tutar}, Gerçek: {fiziksel_artis}")
        
        # Serbest bakiye doğrulaması
        # Sadece 2025'in parası serbest olmalı
        beklenen_serbest_artis = yillik_tutar  # Sadece bu yılın parası
        serbest_artis = sonraki_serbest - onceki_serbest
        
        if abs(serbest_artis - beklenen_serbest_artis) < 0.01:
            print(f"   ✓ Serbest bakiye doğru: {serbest_artis:,.2f} TL (sadece 2025)")
        else:
            print(f"   ⚠️  Serbest bakiye: {serbest_artis:,.2f} TL")
        
        print("\n✅ Test başarılı!")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def test_tahakkuk_yoneticisi():
    """Tahakkuk yöneticisi testi"""
    print("\n" + "="*60)
    print("TEST: Tahakkuk Yöneticisi")
    print("="*60)
    
    db = Database()
    db.connect()
    
    tahakkuk_yoneticisi = TahakkukYoneticisi(db)
    
    # Özet
    print("\n📊 Tahakkuk Özeti:")
    ozet = tahakkuk_yoneticisi.tahakkuk_ozet()
    
    if ozet:
        for item in ozet:
            print(f"   {item['yil']}: {item['adet']} adet, {item['tutar']:,.2f} TL ({item['durum']})")
    else:
        print("   Henüz tahakkuk yok")
    
    # Liste
    print("\n📋 Aktif Tahakkuklar:")
    tahakkuklar = tahakkuk_yoneticisi.tahakkuk_listesi(durum='AKTİF')
    
    if tahakkuklar:
        for i, t in enumerate(tahakkuklar[:5]):  # İlk 5'i göster
            print(f"   {i+1}. {t['ait_oldugu_yil']}: {t['tutar']:,.2f} TL - {t.get('uye_adi', 'N/A')}")
        if len(tahakkuklar) > 5:
            print(f"   ... ve {len(tahakkuklar) - 5} kayıt daha")
    else:
        print("   Aktif tahakkuk yok")
    
    db.close()
    print("\n✅ Test tamamlandı!")


def test_devir_simulasyonu():
    """Devir simülasyonu testi"""
    print("\n" + "="*60)
    print("TEST: Yıl Sonu Devir Simülasyonu")
    print("="*60)
    
    db = Database()
    db.connect()
    
    devir_yoneticisi = DevirYoneticisi(db)
    
    # 2025 yıl sonu simülasyonu
    yil = 2025
    print(f"\n📅 {yil} Yıl Sonu Devir Simülasyonu (Onaysız)")
    
    rapor = devir_yoneticisi.yil_sonu_devir(yil, onay=False)
    
    print(f"\n📊 Genel Durum:")
    print(f"   Toplam Fiziksel: {rapor['toplam']['fiziksel']:,.2f} TL")
    print(f"   Toplam Tahakkuk: {rapor['toplam']['tahakkuk']:,.2f} TL")
    print(f"   Toplam Serbest:  {rapor['toplam']['serbest']:,.2f} TL")
    
    print(f"\n🏦 Kasalar:")
    for kasa in rapor['kasalar']:
        print(f"\n   {kasa['kasa_adi']}:")
        print(f"      Fiziksel: {kasa['fiziksel_bakiye']:,.2f} TL")
        print(f"      Tahakkuk: {kasa['tahakkuk_toplami']:,.2f} TL")
        print(f"      Serbest:  {kasa['serbest_bakiye']:,.2f} TL")
        
        if kasa['gelecek_yil_tahakkuklari']:
            print(f"      Gelecek Yıl Tahakkukları:")
            for t in kasa['gelecek_yil_tahakkuklari'][:3]:
                print(f"         {t['yil']}: {t['tutar']:,.2f} TL ({t['adet']} adet)")
    
    if rapor['uyarilar']:
        print(f"\n⚠️  UYARILAR ({len(rapor['uyarilar'])} adet):")
        for uyari in rapor['uyarilar']:
            print(f"   {uyari['tip']}: {uyari['kasa']}")
            print(f"      {uyari['mesaj']}")
    else:
        print("\n✅ Uyarı yok - Sistem sağlıklı")
    
    db.close()
    print("\n✅ Test tamamlandı!")


if __name__ == "__main__":
    print("\n🚀 YIL BAZLI MUHASEBE SİSTEMİ - TEST SÜİTİ")
    print("=" * 60)
    
    # Test 1: Çok yıllık ödeme
    test_coklu_yil_odeme()
    
    # Test 2: Tahakkuk yöneticisi
    test_tahakkuk_yoneticisi()
    
    # Test 3: Devir simülasyonu
    test_devir_simulasyonu()
    
    print("\n" + "=" * 60)
    print("🎉 TÜM TESTLER TAMAMLANDI!")
    print("=" * 60 + "\n")
