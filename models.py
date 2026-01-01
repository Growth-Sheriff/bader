"""
BADER Derneği - İş Mantığı Katmanı
Tüm CRUD işlemleri ve hesaplamalar
"""

from database import Database, get_license_mode, get_api_config
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
import json
import requests


class UyeYoneticisi:
    """Üye yönetim işlemleri - Online/Offline hybrid"""
    
    def __init__(self, db: Database):
        self.db = db
        self.online_mode = get_license_mode() == 'online'
        if self.online_mode:
            config = get_api_config()
            self.api_url = config.get('api_url', '')
            self.api_key = config.get('api_key', '')
            self.headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
    
    def _api_request(self, method, endpoint, data=None):
        """Online API isteği"""
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
        
    def uye_ekle(self, ad_soyad: str, telefon: str = "", email: str = "", 
                 durum: str = "Aktif", notlar: str = "", kan_grubu: str = "",
                 aile_durumu: str = "Bekar", cocuk_sayisi: int = 0,
                 il: str = "", ilce: str = "", mahalle: str = "", 
                 adres: str = "", posta_kodu: str = "", dogum_tarihi: str = None,
                 uye_no: str = "", tc_kimlik: str = "", telefon2: str = "",
                 uyelik_tipi: str = "Asil", cinsiyet: str = "", dogum_yeri: str = "",
                 meslek: str = "", is_yeri: str = "", egitim_durumu: str = "",
                 referans_uye_id: int = None, ozel_aidat_tutari: float = None,
                 aidat_indirimi_yuzde: float = 0) -> int:
        """Yeni üye ekle"""
        
        if self.online_mode:
            data = {
                'ad_soyad': ad_soyad, 'telefon': telefon, 'telefon2': telefon2,
                'email': email, 'durum': durum, 'notlar': notlar,
                'kan_grubu': kan_grubu, 'aile_durumu': aile_durumu,
                'cocuk_sayisi': cocuk_sayisi, 'il': il, 'ilce': ilce,
                'mahalle': mahalle, 'adres': adres, 'posta_kodu': posta_kodu,
                'dogum_tarihi': dogum_tarihi, 'uye_no': uye_no or None,
                'tc_kimlik': tc_kimlik, 'uyelik_tipi': uyelik_tipi,
                'cinsiyet': cinsiyet, 'dogum_yeri': dogum_yeri,
                'meslek': meslek, 'is_yeri': is_yeri, 'egitim_durumu': egitim_durumu,
                'referans_uye_id': referans_uye_id,
                'ozel_aidat_tutari': ozel_aidat_tutari,
                'aidat_indirimi_yuzde': aidat_indirimi_yuzde
            }
            data = {k: v for k, v in data.items() if v is not None and v != ''}
            result = self._api_request('POST', '/db/uyeler', data)
            if result and result.get('uye_id'):
                return result.get('uye_id', 0)
            # API başarısız - offline'a devam et
        
        self.db.cursor.execute("""
            INSERT INTO uyeler (ad_soyad, telefon, telefon2, email, durum, notlar,
                               kan_grubu, aile_durumu, cocuk_sayisi,
                               il, ilce, mahalle, adres, posta_kodu, dogum_tarihi,
                               uye_no, tc_kimlik, uyelik_tipi, cinsiyet, dogum_yeri,
                               meslek, is_yeri, egitim_durumu, referans_uye_id,
                               ozel_aidat_tutari, aidat_indirimi_yuzde)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ad_soyad, telefon, telefon2, email, durum, notlar, kan_grubu, aile_durumu,
              cocuk_sayisi, il, ilce, mahalle, adres, posta_kodu, dogum_tarihi,
              uye_no or None, tc_kimlik, uyelik_tipi, cinsiyet, dogum_yeri,
              meslek, is_yeri, egitim_durumu, referans_uye_id,
              ozel_aidat_tutari, aidat_indirimi_yuzde))
        self.db.commit()
        uye_id = self.db.cursor.lastrowid
        self.db.log_islem("Sistem", "EKLE", "uyeler", uye_id, f"Yeni üye eklendi: {ad_soyad}")
        return uye_id
        
    def uye_guncelle(self, uye_id: int, ad_soyad: str, telefon: str = "", 
                     email: str = "", durum: str = "Aktif", notlar: str = "",
                     kan_grubu: str = "", aile_durumu: str = "Bekar", cocuk_sayisi: int = 0,
                     il: str = "", ilce: str = "", mahalle: str = "",
                     adres: str = "", posta_kodu: str = "", dogum_tarihi: str = None,
                     # Yeni alanlar
                     uye_no: str = "", tc_kimlik: str = "", telefon2: str = "",
                     uyelik_tipi: str = "Asil", cinsiyet: str = "", dogum_yeri: str = "",
                     meslek: str = "", is_yeri: str = "", egitim_durumu: str = "",
                     referans_uye_id: int = None, ozel_aidat_tutari: float = None,
                     aidat_indirimi_yuzde: float = 0):
        """Üye bilgilerini güncelle (genişletilmiş alanlarla v2)"""
        
        if self.online_mode:
            data = {
                'ad_soyad': ad_soyad, 'telefon': telefon, 'telefon2': telefon2,
                'email': email, 'durum': durum, 'notlar': notlar,
                'kan_grubu': kan_grubu, 'aile_durumu': aile_durumu,
                'cocuk_sayisi': cocuk_sayisi, 'il': il, 'ilce': ilce,
                'mahalle': mahalle, 'adres': adres, 'posta_kodu': posta_kodu,
                'dogum_tarihi': dogum_tarihi, 'uye_no': uye_no or None,
                'tc_kimlik': tc_kimlik, 'uyelik_tipi': uyelik_tipi,
                'cinsiyet': cinsiyet, 'dogum_yeri': dogum_yeri,
                'meslek': meslek, 'is_yeri': is_yeri, 'egitim_durumu': egitim_durumu,
                'referans_uye_id': referans_uye_id,
                'ozel_aidat_tutari': ozel_aidat_tutari,
                'aidat_indirimi_yuzde': aidat_indirimi_yuzde
            }
            result = self._api_request('PUT', f'/db/uyeler/{uye_id}', data)
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
        
        self.db.cursor.execute("""
            UPDATE uyeler 
            SET ad_soyad = ?, telefon = ?, telefon2 = ?, email = ?, durum = ?, notlar = ?,
                kan_grubu = ?, aile_durumu = ?, cocuk_sayisi = ?,
                il = ?, ilce = ?, mahalle = ?, adres = ?, posta_kodu = ?, dogum_tarihi = ?,
                uye_no = ?, tc_kimlik = ?, uyelik_tipi = ?, cinsiyet = ?, dogum_yeri = ?,
                meslek = ?, is_yeri = ?, egitim_durumu = ?, referans_uye_id = ?,
                ozel_aidat_tutari = ?, aidat_indirimi_yuzde = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE uye_id = ?
        """, (ad_soyad, telefon, telefon2, email, durum, notlar, kan_grubu, aile_durumu,
              cocuk_sayisi, il, ilce, mahalle, adres, posta_kodu, dogum_tarihi,
              uye_no or None, tc_kimlik, uyelik_tipi, cinsiyet, dogum_yeri,
              meslek, is_yeri, egitim_durumu, referans_uye_id,
              ozel_aidat_tutari, aidat_indirimi_yuzde, uye_id))
        self.db.commit()
        self.db.log_islem("Sistem", "GÜNCELLE", "uyeler", uye_id, f"Üye güncellendi: {ad_soyad}")
    
    def uye_ayir(self, uye_id: int):
        """Üyeyi ayrılan olarak işaretle (soft delete)"""
        if self.online_mode:
            result = self._api_request('PUT', f'/db/uyeler/{uye_id}', {'durum': 'Ayrıldı'})
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
        
        self.db.cursor.execute("SELECT ad_soyad FROM uyeler WHERE uye_id = ?", (uye_id,))
        result = self.db.cursor.fetchone()
        ad_soyad = result['ad_soyad'] if result else "Bilinmeyen"
        
        self.db.cursor.execute("""
            UPDATE uyeler 
            SET durum = 'Ayrıldı', ayrilma_tarihi = DATE('now'),
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE uye_id = ?
        """, (uye_id,))
        self.db.commit()
        self.db.log_islem("Sistem", "AYRILDI", "uyeler", uye_id, f"Üye ayrıldı: {ad_soyad}")
        
    def uye_sil(self, uye_id: int, mode: str = "soft_delete"):
        """
        Üye sil 
        mode: 'cascade' = tamamen sil, 'soft_delete' = ayrılan olarak işaretle
        """
        if self.online_mode:
            if mode == "cascade":
                result = self._api_request('DELETE', f'/db/uyeler/{uye_id}')
                if result and result.get('success'):
                    return
            else:
                self.uye_ayir(uye_id)
                return
            # API başarısız - offline'a devam et
        
        self.db.cursor.execute("SELECT ad_soyad FROM uyeler WHERE uye_id = ?", (uye_id,))
        result = self.db.cursor.fetchone()
        ad_soyad = result['ad_soyad'] if result else "Bilinmeyen"
        
        if mode == "cascade":
            # Tamamen sil (CASCADE ile)
            self.db.cursor.execute("DELETE FROM uyeler WHERE uye_id = ?", (uye_id,))
            self.db.commit()
            self.db.log_islem("Sistem", "SİL", "uyeler", uye_id, f"Üye silindi: {ad_soyad}")
        else:
            # Soft delete - ayrılan olarak işaretle
            self.uye_ayir(uye_id)
        
    def uye_listesi(self, durum: Optional[str] = None, dahil_ayrilan: bool = False) -> List[Dict]:
        """Üye listesini getir"""
        if self.online_mode:
            params = {}
            if durum:
                params['durum'] = durum
            elif dahil_ayrilan:
                params['dahil_ayrilan'] = 'true'
            result = self._api_request('GET', '/db/uyeler', params)
            if result and (result.get('data') or isinstance(result, list)):
                return result.get('data', result) if isinstance(result, dict) else result
            # API başarısız - offline'a devam et
        
        if durum:
            self.db.cursor.execute("""
                SELECT * FROM uyeler WHERE durum = ? ORDER BY ad_soyad
            """, (durum,))
        elif dahil_ayrilan:
            self.db.cursor.execute("SELECT * FROM uyeler ORDER BY ad_soyad")
        else:
            # Varsayılan: ayrılan üyeleri gösterme
            self.db.cursor.execute("""
                SELECT * FROM uyeler WHERE durum != 'Ayrıldı' ORDER BY ad_soyad
            """)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def ayrilan_uyeler(self) -> List[Dict]:
        """Ayrılan üyeleri listele"""
        if self.online_mode:
            result = self._api_request('GET', '/db/uyeler', {'durum': 'Ayrıldı'})
            if result and (result.get('data') or isinstance(result, list)):
                return result.get('data', result) if isinstance(result, dict) else result
            # API başarısız - offline'a devam et
        
        self.db.cursor.execute("""
            SELECT * FROM uyeler WHERE durum = 'Ayrıldı' ORDER BY ayrilma_tarihi DESC
        """)
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def uye_getir(self, uye_id: int) -> Optional[Dict]:
        """Tek bir üyeyi getir"""
        if self.online_mode:
            result = self._api_request('GET', f'/db/uyeler/{uye_id}')
            return result.get('data') if result else None
        
        self.db.cursor.execute("SELECT * FROM uyeler WHERE uye_id = ?", (uye_id,))
        result = self.db.cursor.fetchone()
        return dict(result) if result else None
    
    def uye_aidat_ozeti(self, uye_id: int) -> Dict:
        """Üyenin aidat özetini getir"""
        self.db.cursor.execute("""
            SELECT 
                COUNT(*) as toplam_yil,
                SUM(CASE WHEN durum = 'Tamamlandı' THEN 1 ELSE 0 END) as odenen_yil,
                SUM(yillik_aidat_tutari) as toplam_borc,
                SUM(CASE WHEN durum = 'Tamamlandı' THEN yillik_aidat_tutari ELSE 0 END) as odenen_toplam,
                SUM(odenecek_tutar) as kalan_borc
            FROM aidat_takip
            WHERE uye_id = ?
        """, (uye_id,))
        result = self.db.cursor.fetchone()
        return dict(result) if result else {}
    
    def uye_aidat_yillari(self, uye_id: int) -> List[Dict]:
        """Üyenin tüm aidat yıllarını getir"""
        self.db.cursor.execute("""
            SELECT at.*, 
                   (SELECT COALESCE(SUM(tutar), 0) FROM aidat_odemeleri WHERE aidat_id = at.aidat_id) as toplam_odenen
            FROM aidat_takip at
            WHERE at.uye_id = ?
            ORDER BY at.yil DESC
        """, (uye_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def uye_ara(self, arama_metni: str, dahil_ayrilan: bool = False) -> List[Dict]:
        """Üye ara (ad, telefon, email'de)"""
        arama = f"%{arama_metni}%"
        if dahil_ayrilan:
            self.db.cursor.execute("""
                SELECT * FROM uyeler 
                WHERE ad_soyad LIKE ? OR telefon LIKE ? OR email LIKE ?
                ORDER BY ad_soyad
            """, (arama, arama, arama))
        else:
            self.db.cursor.execute("""
                SELECT * FROM uyeler 
                WHERE (ad_soyad LIKE ? OR telefon LIKE ? OR email LIKE ?)
                AND durum != 'Ayrıldı'
                ORDER BY ad_soyad
            """, (arama, arama, arama))
        return [dict(row) for row in self.db.cursor.fetchall()]


class AidatYoneticisi:
    """Aidat takip ve ödeme işlemleri - Online/Offline hybrid"""
    
    def __init__(self, db: Database):
        self.db = db
        self.online_mode = get_license_mode() == 'online'
        if self.online_mode:
            config = get_api_config()
            self.api_url = config.get('api_url', '')
            self.api_key = config.get('api_key', '')
            self.headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
    
    def _api_request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """API isteği gönder"""
        if not self.online_mode:
            return None
        try:
            import requests
            url = f"{self.api_url}{endpoint}"
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return None
            if response.status_code in [200, 201]:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None
        
    def aidat_kaydi_olustur(self, uye_id: int, yil: int, yillik_aidat_tutari: float) -> int:
        """Bir üye için yıllık aidat kaydı oluştur"""
        if self.online_mode:
            data = {
                'uye_id': uye_id,
                'yil': yil,
                'yillik_aidat_tutari': yillik_aidat_tutari,
                'odenecek_tutar': yillik_aidat_tutari
            }
            result = self._api_request('POST', '/db/aidat_takip', data)
            if result and result.get('aidat_id'):
                return result.get('aidat_id', -1)
            # API başarısız - offline'a devam et
            
        try:
            self.db.cursor.execute("""
                INSERT INTO aidat_takip (uye_id, yil, yillik_aidat_tutari, odenecek_tutar)
                VALUES (?, ?, ?, ?)
            """, (uye_id, yil, yillik_aidat_tutari, yillik_aidat_tutari))
            self.db.commit()
            aidat_id = self.db.cursor.lastrowid
            self.db.log_islem("Sistem", "EKLE", "aidat_takip", aidat_id, 
                            f"Aidat kaydı oluşturuldu: Üye {uye_id}, Yıl {yil}")
            return aidat_id
        except Exception as e:
            print(f"Aidat kaydı oluşturma hatası: {e}")
            return -1
            
    def aidat_odeme_ekle(self, aidat_id: int, tarih: str, tutar: float, 
                        aciklama: str = "", tahsilat_turu: str = "Nakit",
                        dekont_no: str = "") -> int:
        """Aidat ödemesi ekle"""
        # Otomatik açıklama etiketi
        if not aciklama:
            aciklama = "Aidattan gelen ödeme"
        
        if self.online_mode:
            data = {
                'aidat_id': aidat_id,
                'tarih': tarih,
                'tutar': tutar,
                'aciklama': aciklama,
                'tahsilat_turu': tahsilat_turu,
                'dekont_no': dekont_no
            }
            result = self._api_request('POST', '/db/aidat_odemeleri', data)
            if result and result.get('odeme_id'):
                return result.get('odeme_id', -1)
            # API başarısız - offline'a devam et
        
        self.db.cursor.execute("""
            INSERT INTO aidat_odemeleri (aidat_id, tarih, tutar, aciklama, tahsilat_turu, dekont_no)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (aidat_id, tarih, tutar, aciklama, tahsilat_turu, dekont_no))
        self.db.commit()
        odeme_id = self.db.cursor.lastrowid
        
        # Aidat durumunu güncelle
        self._aidat_durumunu_guncelle(aidat_id)
        
        self.db.log_islem("Sistem", "EKLE", "aidat_odemeleri", odeme_id, 
                         f"Aidat ödemesi eklendi: {tutar} TL")
        return odeme_id
        
    def aidat_odeme_sil(self, odeme_id: int):
        """Aidat ödemesini sil"""
        if self.online_mode:
            result = self._api_request('DELETE', f'/db/aidat_odemeleri/{odeme_id}')
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
            
        # Önce aidat_id'yi al
        self.db.cursor.execute("SELECT aidat_id, tutar FROM aidat_odemeleri WHERE odeme_id = ?", (odeme_id,))
        result = self.db.cursor.fetchone()
        
        if result:
            aidat_id = result['aidat_id']
            tutar = result['tutar']
            
            self.db.cursor.execute("DELETE FROM aidat_odemeleri WHERE odeme_id = ?", (odeme_id,))
            self.db.commit()
            
            # Aidat durumunu güncelle
            self._aidat_durumunu_guncelle(aidat_id)
            
            self.db.log_islem("Sistem", "SİL", "aidat_odemeleri", odeme_id, 
                            f"Aidat ödemesi silindi: {tutar} TL")
        
    def _aidat_durumunu_guncelle(self, aidat_id: int):
        """
        Aidat durumunu kontrol et ve gerekirse Gelir kaydı oluştur/sil
        KRİTİK FONKSİYON: Aidat <-> Gelir senkronizasyonu
        """
        # Toplam ödenen tutarı hesapla
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) as toplam_odenen
            FROM aidat_odemeleri
            WHERE aidat_id = ?
        """, (aidat_id,))
        result = self.db.cursor.fetchone()
        toplam_odenen = result['toplam_odenen']
        
        # Aidat bilgilerini al
        self.db.cursor.execute("""
            SELECT yillik_aidat_tutari, durum, aktarim_durumu, gelir_id, uye_id, yil
            FROM aidat_takip
            WHERE aidat_id = ?
        """, (aidat_id,))
        aidat = self.db.cursor.fetchone()
        
        if not aidat:
            return
            
        yillik_aidat = aidat['yillik_aidat_tutari']
        eski_durum = aidat['durum']
        aktarim_durumu = aidat['aktarim_durumu']
        gelir_id = aidat['gelir_id']
        uye_id = aidat['uye_id']
        yil = aidat['yil']
        
        # Kalan borcu hesapla
        kalan = yillik_aidat - toplam_odenen
        
        # Yeni durumu belirle
        if toplam_odenen >= yillik_aidat:
            yeni_durum = "Tamamlandı"
        elif toplam_odenen > 0:
            yeni_durum = "Kısmi"
        else:
            yeni_durum = "Eksik"
            
        # Durumu güncelle
        self.db.cursor.execute("""
            UPDATE aidat_takip
            SET durum = ?, odenecek_tutar = ?
            WHERE aidat_id = ?
        """, (yeni_durum, kalan, aidat_id))
        
        # Gelir kaydı yönetimi
        if yeni_durum == "Tamamlandı" and aktarim_durumu != "Aktarıldı":
            # Yeni gelir kaydı oluştur
            gelir_yoneticisi = GelirYoneticisi(self.db)
            
            # Üye adını al
            self.db.cursor.execute("SELECT ad_soyad FROM uyeler WHERE uye_id = ?", (uye_id,))
            uye = self.db.cursor.fetchone()
            ad_soyad = uye['ad_soyad'] if uye else "Bilinmeyen"
            
            # Varsayılan kasa (DERNEK KASA TL)
            self.db.cursor.execute("SELECT kasa_id FROM kasalar WHERE kasa_adi = 'DERNEK KASA TL' LIMIT 1")
            kasa = self.db.cursor.fetchone()
            kasa_id = kasa['kasa_id'] if kasa else 1
            
            gelir_id = gelir_yoneticisi.gelir_ekle(
                tarih=datetime.now().strftime("%Y-%m-%d"),
                gelir_turu="AİDAT",
                aciklama=f"{ad_soyad} - {yil} Yılı Aidatı",
                tutar=yillik_aidat,
                kasa_id=kasa_id,
                aidat_id=aidat_id
            )
            
            # Aktarım durumunu güncelle
            self.db.cursor.execute("""
                UPDATE aidat_takip
                SET aktarim_durumu = 'Aktarıldı', gelir_id = ?
                WHERE aidat_id = ?
            """, (gelir_id, aidat_id))
            
            self.db.log_islem("Sistem", "OTOMATIK", "gelirler", gelir_id, 
                            f"Aidat tamamlandı, otomatik gelir kaydı oluşturuldu")
            
        elif yeni_durum != "Tamamlandı" and aktarim_durumu == "Aktarıldı" and gelir_id:
            # Gelir kaydını sil
            gelir_yoneticisi = GelirYoneticisi(self.db)
            gelir_yoneticisi.gelir_sil(gelir_id)
            
            # Aktarım durumunu temizle
            self.db.cursor.execute("""
                UPDATE aidat_takip
                SET aktarim_durumu = '', gelir_id = NULL
                WHERE aidat_id = ?
            """, (aidat_id,))
            
            self.db.log_islem("Sistem", "OTOMATIK", "aidat_takip", aidat_id, 
                            f"Aidat tamamlanmadı, gelir kaydı silindi")
        
        self.db.commit()
        
    def aidat_listesi(self, uye_id: Optional[int] = None, yil: Optional[int] = None) -> List[Dict]:
        """Aidat kayıtlarını listele"""
        query = """
            SELECT at.*, u.ad_soyad,
                   (SELECT COALESCE(SUM(tutar), 0) FROM aidat_odemeleri WHERE aidat_id = at.aidat_id) as toplam_odenen
            FROM aidat_takip at
            JOIN uyeler u ON at.uye_id = u.uye_id
        """
        params = []
        
        if uye_id:
            query += " WHERE at.uye_id = ?"
            params.append(uye_id)
            
        if yil:
            query += " AND at.yil = ?" if uye_id else " WHERE at.yil = ?"
            params.append(yil)
            
        query += " ORDER BY u.ad_soyad, at.yil DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def uye_aidat_odemeleri(self, aidat_id: int) -> List[Dict]:
        """Bir aidatın tüm ödemelerini getir"""
        self.db.cursor.execute("""
            SELECT * FROM aidat_odemeleri 
            WHERE aidat_id = ? 
            ORDER BY tarih DESC
        """, (aidat_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def toplu_aidat_olustur(self, yil: int, yillik_aidat_tutari: float):
        """Tüm aktif üyeler için aidat kaydı oluştur"""
        self.db.cursor.execute("SELECT uye_id FROM uyeler WHERE durum = 'Aktif'")
        uyeler = self.db.cursor.fetchall()
        
        olusturulan = 0
        for uye in uyeler:
            try:
                self.aidat_kaydi_olustur(uye['uye_id'], yil, yillik_aidat_tutari)
                olusturulan += 1
            except:
                pass  # Zaten varsa atla
                
        return olusturulan
    
    def aidat_olustur_veya_getir(self, uye_id: int, yil: int) -> int:
        """Aidat kaydı oluştur veya mevcut kaydı getir"""
        # Önce var mı kontrol et
        self.db.cursor.execute("""
            SELECT aidat_id FROM aidat_takip
            WHERE uye_id = ? AND yil = ?
        """, (uye_id, yil))
        result = self.db.cursor.fetchone()
        
        if result:
            return result['aidat_id']
        
        # Yoksa oluştur - üyenin özel aidat tutarını al
        self.db.cursor.execute("""
            SELECT ozel_aidat_tutari FROM uyeler WHERE uye_id = ?
        """, (uye_id,))
        uye = self.db.cursor.fetchone()
        
        # Varsayılan aidat tutarı (ayarlardan al)
        self.db.cursor.execute("""
            SELECT ayar_degeri FROM ayarlar WHERE ayar_adi = 'yillik_aidat_tutari'
        """)
        ayar = self.db.cursor.fetchone()
        varsayilan_tutar = float(ayar['ayar_degeri']) if ayar and ayar['ayar_degeri'] else 100.0
        
        # Üyenin özel tutarı varsa onu kullan
        yillik_tutar = uye['ozel_aidat_tutari'] if uye and uye['ozel_aidat_tutari'] else varsayilan_tutar
        
        return self.aidat_kaydi_olustur(uye_id, yil, yillik_tutar)


class GelirYoneticisi:
    """Gelir yönetim işlemleri - Online/Offline hybrid"""
    
    def __init__(self, db: Database):
        self.db = db
        self.online_mode = get_license_mode() == 'online'
        if self.online_mode:
            config = get_api_config()
            self.api_url = config.get('api_url', '')
            self.api_key = config.get('api_key', '')
            self.headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
    
    def _api_request(self, method, endpoint, data=None):
        """Online API isteği"""
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
        
    def gelir_ekle(self, tarih: str, gelir_turu: str, aciklama: str, 
                   tutar: float, kasa_id: int, tahsil_eden: str = "", 
                   notlar: str = "", aidat_id: Optional[int] = None,
                   dekont_no: str = "", ait_oldugu_yil: Optional[int] = None,
                   tahakkuk_durumu: str = 'NORMAL', coklu_odeme_grup_id: Optional[str] = None) -> int:
        """Yeni gelir kaydı ekle (Yıl bazlı muhasebe desteği ile)"""
        
        # Eğer ait_oldugu_yil belirtilmemişse, tarihten çıkar
        if ait_oldugu_yil is None:
            ait_oldugu_yil = int(tarih[:4])
        
        if self.online_mode:
            data = {
                'tarih': tarih, 'gelir_turu': gelir_turu, 'aciklama': aciklama,
                'tutar': tutar, 'kasa_id': kasa_id, 'tahsil_eden': tahsil_eden,
                'notlar': notlar, 'aidat_id': aidat_id, 'dekont_no': dekont_no,
                'ait_oldugu_yil': ait_oldugu_yil, 'tahakkuk_durumu': tahakkuk_durumu,
                'coklu_odeme_grup_id': coklu_odeme_grup_id
            }
            data = {k: v for k, v in data.items() if v is not None and v != ''}
            result = self._api_request('POST', '/db/gelirler', data)
            if result and result.get('gelir_id'):
                return result.get('gelir_id', 0)
            # API başarısız - offline'a devam et
        
        belge_no = self.db.get_next_belge_no()
        
        self.db.cursor.execute("""
            INSERT INTO gelirler 
            (tarih, belge_no, gelir_turu, aciklama, tutar, kasa_id, tahsil_eden, notlar, aidat_id, dekont_no,
             ait_oldugu_yil, tahakkuk_durumu, coklu_odeme_grup_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tarih, belge_no, gelir_turu, aciklama, tutar, kasa_id, tahsil_eden, notlar, aidat_id, dekont_no,
              ait_oldugu_yil, tahakkuk_durumu, coklu_odeme_grup_id))
        self.db.commit()
        
        gelir_id = self.db.cursor.lastrowid
        
        # Tahakkuk kaydı (eğer peşin ödeme ise)
        if tahakkuk_durumu == 'PEŞİN':
            self._tahakkuk_kaydet('GELİR', gelir_id, int(tarih[:4]), ait_oldugu_yil, tutar)
        
        self.db.log_islem("Sistem", "EKLE", "gelirler", gelir_id, 
                         f"Gelir eklendi: {gelir_turu} - {tutar} TL (Yıl: {ait_oldugu_yil})")
        return gelir_id
        
    def gelir_guncelle(self, gelir_id: int, tarih: str, gelir_turu: str, 
                      aciklama: str, tutar: float, kasa_id: int, 
                      tahsil_eden: str = "", notlar: str = "", dekont_no: str = ""):
        """Gelir kaydını güncelle"""
        if self.online_mode:
            data = {
                'tarih': tarih, 'gelir_turu': gelir_turu, 'aciklama': aciklama,
                'tutar': tutar, 'kasa_id': kasa_id, 'tahsil_eden': tahsil_eden,
                'notlar': notlar, 'dekont_no': dekont_no
            }
            result = self._api_request('PUT', f'/db/gelirler/{gelir_id}', data)
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
            
        self.db.cursor.execute("""
            UPDATE gelirler
            SET tarih = ?, gelir_turu = ?, aciklama = ?, tutar = ?, 
                kasa_id = ?, tahsil_eden = ?, notlar = ?, dekont_no = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE gelir_id = ?
        """, (tarih, gelir_turu, aciklama, tutar, kasa_id, tahsil_eden, notlar, dekont_no, gelir_id))
        self.db.commit()
        self.db.log_islem("Sistem", "GÜNCELLE", "gelirler", gelir_id, f"Gelir güncellendi")
        
    def gelir_sil(self, gelir_id: int):
        """Gelir kaydını sil"""
        if self.online_mode:
            result = self._api_request('DELETE', f'/db/gelirler/{gelir_id}')
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
            
        # Önce gelir bilgilerini al
        self.db.cursor.execute("SELECT tutar, gelir_turu, aidat_id FROM gelirler WHERE gelir_id = ?", (gelir_id,))
        result = self.db.cursor.fetchone()
        
        if result:
            tutar = result['tutar']
            gelir_turu = result['gelir_turu']
            aidat_id = result['aidat_id']
            
            # Eğer aidat geliri ise, aidat kaydını güncelle
            if aidat_id:
                self.db.cursor.execute("""
                    UPDATE aidat_takip
                    SET aktarim_durumu = '', gelir_id = NULL
                    WHERE aidat_id = ?
                """, (aidat_id,))
            
            self.db.cursor.execute("DELETE FROM gelirler WHERE gelir_id = ?", (gelir_id,))
            self.db.commit()
            self.db.log_islem("Sistem", "SİL", "gelirler", gelir_id, 
                            f"Gelir silindi: {gelir_turu} - {tutar} TL")
        
    def gelir_listesi(self, baslangic_tarih: Optional[str] = None, 
                     bitis_tarih: Optional[str] = None, 
                     gelir_turu: Optional[str] = None,
                     kasa_id: Optional[int] = None) -> List[Dict]:
        """Gelir listesini getir (filtreli)"""
        if self.online_mode:
            params = {}
            if baslangic_tarih:
                params['baslangic_tarih'] = baslangic_tarih
            if bitis_tarih:
                params['bitis_tarih'] = bitis_tarih
            if gelir_turu:
                params['gelir_turu'] = gelir_turu
            if kasa_id:
                params['kasa_id'] = kasa_id
            result = self._api_request('GET', '/db/gelirler', params)
            if result:
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict) and 'gelirler' in result:
                    return result['gelirler']
                elif isinstance(result, dict) and 'incomes' in result:
                    return result['incomes']
            # Online başarısız olursa offline'a düş
            
        query = """
            SELECT g.*, k.kasa_adi, k.para_birimi
            FROM gelirler g
            JOIN kasalar k ON g.kasa_id = k.kasa_id
            WHERE 1=1
        """
        params = []
        
        if baslangic_tarih:
            query += " AND g.tarih >= ?"
            params.append(baslangic_tarih)
            
        if bitis_tarih:
            query += " AND g.tarih <= ?"
            params.append(bitis_tarih)
            
        if gelir_turu:
            query += " AND g.gelir_turu = ?"
            params.append(gelir_turu)
            
        if kasa_id:
            query += " AND g.kasa_id = ?"
            params.append(kasa_id)
            
        query += " ORDER BY g.tarih DESC, g.gelir_id DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def coklu_yil_gelir_ekle(self, gelir_turu: str, kasa_id: int,
                             baslangic_yil: int, bitis_yil: int,
                             yillik_tutar: float, tahsil_tarihi: str = None,
                             uye_id: int = None, aciklama: str = "", 
                             tahsil_eden: str = "") -> str:
        """
        Çok yıllık ödeme (örn: 10 yıllık aidat)
        
        Returns: odeme_grup_id
        """
        if tahsil_tarihi is None:
            tahsil_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        tahsil_yili = int(tahsil_tarihi[:4])
        odeme_grup_id = f"GRUP_{tahsil_yili}_{self._get_next_grup_no()}"
        
        gelir_idler = []
        
        for yil in range(baslangic_yil, bitis_yil + 1):
            # Tahakkuk durumu belirle
            if yil == tahsil_yili:
                tahakkuk = 'NORMAL'
            elif yil < tahsil_yili:
                tahakkuk = 'GERİYE_DÖNÜK'
            else:
                tahakkuk = 'PEŞİN'
            
            # Gelir kaydı
            gelir_id = self.gelir_ekle(
                tarih=tahsil_tarihi,
                gelir_turu=gelir_turu,
                aciklama=f"{aciklama} ({yil} yılı)",
                tutar=yillik_tutar,
                kasa_id=kasa_id,
                tahsil_eden=tahsil_eden,
                ait_oldugu_yil=yil,
                tahakkuk_durumu=tahakkuk,
                coklu_odeme_grup_id=odeme_grup_id
            )
            
            gelir_idler.append((yil, gelir_id))
        
        # Aidat bağlantısı (eğer üye ve aidat ise)
        if uye_id and gelir_turu == 'AİDAT':
            self._aidat_odemesi_bagla(uye_id, baslangic_yil, bitis_yil,
                                     yillik_tutar, odeme_grup_id, gelir_idler, 
                                     tahsil_tarihi, kasa_id)
        
        self.db.log_islem("Sistem", "EKLE", "gelirler", 0, 
                         f"Çok yıllık gelir eklendi: {baslangic_yil}-{bitis_yil} ({bitis_yil-baslangic_yil+1} yıl)")
        
        return odeme_grup_id
    
    def _get_next_grup_no(self) -> int:
        """Sonraki grup numarasını al"""
        yil = datetime.now().year
        self.db.cursor.execute("""
            SELECT COUNT(*) as adet FROM gelirler
            WHERE coklu_odeme_grup_id LIKE ?
        """, (f"GRUP_{yil}_%",))
        result = self.db.cursor.fetchone()
        return (result['adet'] if result else 0) + 1
    
    def _aidat_odemesi_bagla(self, uye_id, baslangic_yil, bitis_yil,
                            yillik_tutar, odeme_grup_id, gelir_idler, 
                            tahsil_tarihi, kasa_id):
        """Aidat sistemine çok yıllık ödemeyi bağla"""
        from models import AidatYoneticisi
        aidat_yoneticisi = AidatYoneticisi(self.db)
        
        # Ana ödeme kaydı
        toplam_tutar = yillik_tutar * (bitis_yil - baslangic_yil + 1)
        self.db.cursor.execute("""
            INSERT INTO aidat_odemeleri
            (odeme_grup_id, tarih, toplam_tutar, kasa_id)
            VALUES (?, ?, ?, ?)
        """, (odeme_grup_id, tahsil_tarihi, toplam_tutar, kasa_id))
        
        # Her yıl için detay
        for yil, gelir_id in gelir_idler:
            # Aidat kaydı oluştur/bul
            aidat_id = aidat_yoneticisi.aidat_olustur_veya_getir(uye_id, yil)
            
            # Detay kaydı
            self.db.cursor.execute("""
                INSERT INTO aidat_odeme_detay
                (odeme_grup_id, aidat_id, tutar, gelir_id)
                VALUES (?, ?, ?, ?)
            """, (odeme_grup_id, aidat_id, yillik_tutar, gelir_id))
            
            # Aidat durumunu güncelle
            aidat_yoneticisi._aidat_durumunu_guncelle(aidat_id)
        
        self.db.commit()
    
    def _tahakkuk_kaydet(self, tahakkuk_turu: str, kaynak_id: int,
                        tahsil_yili: int, ait_oldugu_yil: int, tutar: float):
        """Tahakkuk kaydı oluştur"""
        self.db.cursor.execute("""
            INSERT INTO tahakkuklar
            (tahakkuk_turu, kaynak_tablo, kaynak_id, tahsil_yili, ait_oldugu_yil, tutar, durum)
            VALUES (?, 'gelirler', ?, ?, ?, ?, 'AKTİF')
        """, (tahakkuk_turu, kaynak_id, tahsil_yili, ait_oldugu_yil, tutar))
    
    def gelir_alt_kategorileri(self, tur_adi: str) -> List[str]:
        """Gelir türüne göre alt kategorileri getir"""
        alt_kategoriler = {
            "KİRA": ["Salon Kirası", "Düğün Salonu", "Toplantı Salonu", "Depo Kirası"],
            "BAĞIŞ": ["Nakdi Bağış", "Ayni Bağış", "Koşullu Bağış"],
            "DÜĞÜN": ["Düğün Salonu", "Ses Sistemi", "Aydınlatma", "Catering"],
            "KINA": ["Kına Salonu", "Organizasyon"],
            "TOPLANTI": ["Toplantı Salonu", "İkram"],
            "DAVET": ["Taziye", "Mevlit", "Bayramlaşma"],
            "AİDAT": ["Yıllık Aidat", "Giriş Aidatı"],
            "DİĞER": ["Genel Gelir", "Faiz Geliri", "Ceza Geliri"]
        }
        return alt_kategoriler.get(tur_adi.upper(), [])


class GiderYoneticisi:
    """Gider yönetim işlemleri - Online/Offline hybrid"""
    
    def __init__(self, db: Database):
        self.db = db
        self.online_mode = get_license_mode() == 'online'
        if self.online_mode:
            config = get_api_config()
            self.api_url = config.get('api_url', '')
            self.api_key = config.get('api_key', '')
            self.headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
    
    def _api_request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """API isteği gönder"""
        if not self.online_mode:
            return None
        try:
            import requests
            url = f"{self.api_url}{endpoint}"
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return None
            if response.status_code in [200, 201]:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None
        
    def gider_ekle(self, tarih: str, gider_turu: str, aciklama: str, 
                   tutar: float, kasa_id: int, odeyen: str = "", notlar: str = "",
                   ait_oldugu_yil: Optional[int] = None, tahakkuk_durumu: str = 'NORMAL') -> int:
        """Yeni gider kaydı ekle (Yıl bazlı muhasebe desteği ile)"""
        # Eğer ait_oldugu_yil belirtilmemişse, tarihten çıkar
        if ait_oldugu_yil is None:
            ait_oldugu_yil = int(tarih[:4])
        
        if self.online_mode:
            data = {
                'tarih': tarih,
                'gider_turu': gider_turu,
                'aciklama': aciklama,
                'tutar': tutar,
                'kasa_id': kasa_id,
                'odeyen': odeyen,
                'notlar': notlar,
                'ait_oldugu_yil': ait_oldugu_yil,
                'tahakkuk_durumu': tahakkuk_durumu
            }
            result = self._api_request('POST', '/db/giderler', data)
            if result and result.get('gider_id'):
                return result.get('gider_id', 0)
            # API başarısız - offline'a devam et
        
        islem_no = self.db.get_next_islem_no()
        self.db.cursor.execute("""
            INSERT INTO giderler 
            (tarih, islem_no, gider_turu, aciklama, tutar, kasa_id, odeyen, notlar,
             ait_oldugu_yil, tahakkuk_durumu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tarih, islem_no, gider_turu, aciklama, tutar, kasa_id, odeyen, notlar, ait_oldugu_yil, tahakkuk_durumu))
        self.db.commit()
        
        gider_id = self.db.cursor.lastrowid
        self.db.log_islem("Sistem", "EKLE", "giderler", gider_id, 
                         f"Gider eklendi: {gider_turu} - {tutar} TL")
        return gider_id
        
    def gider_guncelle(self, gider_id: int, tarih: str, gider_turu: str, 
                      aciklama: str, tutar: float, kasa_id: int, 
                      odeyen: str = "", notlar: str = ""):
        """Gider kaydını güncelle"""
        if self.online_mode:
            data = {
                'tarih': tarih,
                'gider_turu': gider_turu,
                'aciklama': aciklama,
                'tutar': tutar,
                'kasa_id': kasa_id,
                'odeyen': odeyen,
                'notlar': notlar
            }
            result = self._api_request('PUT', f'/db/giderler/{gider_id}', data)
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
            
        self.db.cursor.execute("""
            UPDATE giderler
            SET tarih = ?, gider_turu = ?, aciklama = ?, tutar = ?, 
                kasa_id = ?, odeyen = ?, notlar = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE gider_id = ?
        """, (tarih, gider_turu, aciklama, tutar, kasa_id, odeyen, notlar, gider_id))
        self.db.commit()
        self.db.log_islem("Sistem", "GÜNCELLE", "giderler", gider_id, f"Gider güncellendi")
        
    def gider_sil(self, gider_id: int):
        """Gider kaydını sil"""
        if self.online_mode:
            result = self._api_request('DELETE', f'/db/giderler/{gider_id}')
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
            
        self.db.cursor.execute("SELECT tutar, gider_turu FROM giderler WHERE gider_id = ?", (gider_id,))
        result = self.db.cursor.fetchone()
        
        if result:
            tutar = result['tutar']
            gider_turu = result['gider_turu']
            
            self.db.cursor.execute("DELETE FROM giderler WHERE gider_id = ?", (gider_id,))
            self.db.commit()
            self.db.log_islem("Sistem", "SİL", "giderler", gider_id, 
                            f"Gider silindi: {gider_turu} - {tutar} TL")
        
    def gider_listesi(self, baslangic_tarih: Optional[str] = None, 
                     bitis_tarih: Optional[str] = None, 
                     gider_turu: Optional[str] = None,
                     kasa_id: Optional[int] = None) -> List[Dict]:
        """Gider listesini getir (filtreli)"""
        if self.online_mode:
            params = {}
            if baslangic_tarih:
                params['baslangic_tarih'] = baslangic_tarih
            if bitis_tarih:
                params['bitis_tarih'] = bitis_tarih
            if gider_turu:
                params['gider_turu'] = gider_turu
            if kasa_id:
                params['kasa_id'] = kasa_id
            result = self._api_request('GET', '/db/giderler', params)
            if result:
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict) and 'giderler' in result:
                    return result['giderler']
                elif isinstance(result, dict) and 'expenses' in result:
                    return result['expenses']
            # Online başarısız olursa offline'a düş
            
        query = """
            SELECT g.*, k.kasa_adi, k.para_birimi
            FROM giderler g
            JOIN kasalar k ON g.kasa_id = k.kasa_id
            WHERE 1=1
        """
        params = []
        
        if baslangic_tarih:
            query += " AND g.tarih >= ?"
            params.append(baslangic_tarih)
            
        if bitis_tarih:
            query += " AND g.tarih <= ?"
            params.append(bitis_tarih)
            
        if gider_turu:
            query += " AND g.gider_turu = ?"
            params.append(gider_turu)
            
        if kasa_id:
            query += " AND g.kasa_id = ?"
            params.append(kasa_id)
            
        query += " ORDER BY g.tarih DESC, g.gider_id DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def gider_turleri_listesi(self) -> List[str]:
        """Gider türlerini getir"""
        self.db.cursor.execute("SELECT tur_adi FROM gider_turleri WHERE aktif = 1 ORDER BY tur_adi")
        return [row['tur_adi'] for row in self.db.cursor.fetchall()]
    
    def gider_alt_kategorileri(self, tur_adi: str) -> List[str]:
        """Gider türüne göre alt kategorileri getir"""
        # Alt kategori tablosu yoksa varsayılan listeden döndür
        alt_kategoriler = {
            "PERSONEL": ["Maaş", "SSK Primi", "İşsizlik Primi", "Kıdem Tazminatı", "İkramiye"],
            "KİRA": ["Bina Kirası", "Arsa Kirası", "Depo Kirası"],
            "FATURA": ["Elektrik", "Su", "Doğalgaz", "Telefon", "İnternet"],
            "BAKIM": ["Bina Bakım", "Araç Bakım", "Cihaz Bakım", "Bahçe Bakım"],
            "MALZEME": ["Kırtasiye", "Temizlik", "Mutfak", "Teknik Malzeme"],
            "TAŞIT": ["Yakıt", "Sigorta", "Muayene", "Tamir"],
            "VERGİ": ["Gelir Vergisi", "KDV", "Damga Vergisi", "Emlak Vergisi"],
            "DİĞER": ["Genel Gider", "Temsil Ağırlama", "Avukatlık", "Danışmanlık"]
        }
        return alt_kategoriler.get(tur_adi.upper(), [])
        
    def gider_turu_ekle(self, tur_adi: str):
        """Yeni gider türü ekle"""
        try:
            self.db.cursor.execute("INSERT INTO gider_turleri (tur_adi) VALUES (?)", (tur_adi,))
            self.db.commit()
            return True
        except:
            return False


class VirmanYoneticisi:
    """Kasa transfer işlemleri - Online/Offline hybrid"""
    
    def __init__(self, db: Database):
        self.db = db
        self.online_mode = get_license_mode() == 'online'
        if self.online_mode:
            config = get_api_config()
            self.api_url = config.get('api_url', '')
            self.api_key = config.get('api_key', '')
            self.headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
    
    def _api_request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """API isteği gönder"""
        if not self.online_mode:
            return None
        try:
            import requests
            url = f"{self.api_url}{endpoint}"
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return None
            if response.status_code in [200, 201]:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None
        
    def virman_ekle(self, tarih: str, gonderen_kasa_id: int, alan_kasa_id: int, 
                    tutar: float, aciklama: str = "") -> int:
        """Kasalar arası transfer yap"""
        if gonderen_kasa_id == alan_kasa_id:
            raise ValueError("Gönderen ve alan kasa aynı olamaz!")
        
        if self.online_mode:
            data = {
                'tarih': tarih,
                'gonderen_kasa_id': gonderen_kasa_id,
                'alan_kasa_id': alan_kasa_id,
                'tutar': tutar,
                'aciklama': aciklama
            }
            result = self._api_request('POST', '/db/virmanlar', data)
            if result and result.get('virman_id'):
                return result.get('virman_id', 0)
            # API başarısız - offline'a devam et
            
        self.db.cursor.execute("""
            INSERT INTO virmanlar (tarih, gonderen_kasa_id, alan_kasa_id, tutar, aciklama)
            VALUES (?, ?, ?, ?, ?)
        """, (tarih, gonderen_kasa_id, alan_kasa_id, tutar, aciklama))
        self.db.commit()
        
        virman_id = self.db.cursor.lastrowid
        self.db.log_islem("Sistem", "EKLE", "virmanlar", virman_id, 
                         f"Virman yapıldı: {tutar} TL")
        return virman_id
        
    def virman_sil(self, virman_id: int):
        """Virman işlemini sil"""
        if self.online_mode:
            result = self._api_request('DELETE', f'/db/virmanlar/{virman_id}')
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
            
        self.db.cursor.execute("SELECT tutar FROM virmanlar WHERE virman_id = ?", (virman_id,))
        result = self.db.cursor.fetchone()
        
        if result:
            tutar = result['tutar']
            self.db.cursor.execute("DELETE FROM virmanlar WHERE virman_id = ?", (virman_id,))
            self.db.commit()
            self.db.log_islem("Sistem", "SİL", "virmanlar", virman_id, f"Virman silindi: {tutar} TL")
        
    def virman_listesi(self, baslangic_tarih: Optional[str] = None, 
                      bitis_tarih: Optional[str] = None) -> List[Dict]:
        """Virman listesini getir"""
        if self.online_mode:
            params = {}
            if baslangic_tarih:
                params['baslangic_tarih'] = baslangic_tarih
            if bitis_tarih:
                params['bitis_tarih'] = bitis_tarih
            result = self._api_request('GET', '/db/virmanlar', params)
            if result:
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict) and 'virmanlar' in result:
                    return result['virmanlar']
            # Online başarısız olursa offline'a düş
            
        query = """
            SELECT v.*, 
                   k1.kasa_adi as gonderen_kasa_adi, k1.para_birimi as gonderen_para_birimi,
                   k2.kasa_adi as alan_kasa_adi, k2.para_birimi as alan_para_birimi
            FROM virmanlar v
            JOIN kasalar k1 ON v.gonderen_kasa_id = k1.kasa_id
            JOIN kasalar k2 ON v.alan_kasa_id = k2.kasa_id
            WHERE 1=1
        """
        params = []
        
        if baslangic_tarih:
            query += " AND v.tarih >= ?"
            params.append(baslangic_tarih)
            
        if bitis_tarih:
            query += " AND v.tarih <= ?"
            params.append(bitis_tarih)
            
        query += " ORDER BY v.tarih DESC, v.virman_id DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]


class KasaYoneticisi:
    """Kasa yönetim ve hesaplama işlemleri - Online/Offline hybrid"""
    
    def __init__(self, db: Database):
        self.db = db
        self.online_mode = get_license_mode() == 'online'
        if self.online_mode:
            config = get_api_config()
            self.api_url = config.get('api_url', '')
            self.api_key = config.get('api_key', '')
            self.headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
    
    def _api_request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """API isteği gönder"""
        if not self.online_mode:
            return None
        try:
            import requests
            url = f"{self.api_url}{endpoint}"
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return None
            if response.status_code in [200, 201]:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None
        
    def kasa_ekle(self, kasa_adi: str, para_birimi: str = "TL", 
                  devir_bakiye: float = 0, aciklama: str = "") -> int:
        """Yeni kasa ekle"""
        if self.online_mode:
            data = {
                'kasa_adi': kasa_adi,
                'para_birimi': para_birimi,
                'devir_bakiye': devir_bakiye,
                'aciklama': aciklama
            }
            result = self._api_request('POST', '/db/kasalar', data)
            if result and result.get('kasa_id'):
                return result.get('kasa_id', -1)
            # API başarısız - offline'a devam et
            
        try:
            self.db.cursor.execute("""
                INSERT INTO kasalar (kasa_adi, para_birimi, devir_bakiye, aciklama)
                VALUES (?, ?, ?, ?)
            """, (kasa_adi, para_birimi, devir_bakiye, aciklama))
            self.db.commit()
            kasa_id = self.db.cursor.lastrowid
            self.db.log_islem("Sistem", "EKLE", "kasalar", kasa_id, f"Yeni kasa eklendi: {kasa_adi}")
            return kasa_id
        except Exception as e:
            print(f"Kasa ekleme hatası: {e}")
            return -1
            
    def kasa_guncelle(self, kasa_id: int, kasa_adi: str, para_birimi: str, 
                     devir_bakiye: float, aciklama: str = ""):
        """Kasa bilgilerini güncelle"""
        if self.online_mode:
            data = {
                'kasa_adi': kasa_adi,
                'para_birimi': para_birimi,
                'devir_bakiye': devir_bakiye,
                'aciklama': aciklama
            }
            result = self._api_request('PUT', f'/db/kasalar/{kasa_id}', data)
            if result and result.get('success'):
                return
            # API başarısız - offline'a devam et
            
        self.db.cursor.execute("""
            UPDATE kasalar
            SET kasa_adi = ?, para_birimi = ?, devir_bakiye = ?, aciklama = ?
            WHERE kasa_id = ?
        """, (kasa_adi, para_birimi, devir_bakiye, aciklama, kasa_id))
        self.db.commit()
        self.db.log_islem("Sistem", "GÜNCELLE", "kasalar", kasa_id, f"Kasa güncellendi: {kasa_adi}")
        
    def kasa_listesi(self) -> List[Dict]:
        """Tüm kasaları listele"""
        if self.online_mode:
            result = self._api_request('GET', '/db/kasalar')
            # API sonucu liste ise direkt döndür, dict ise içinden listeyi çıkar
            if result:
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict) and 'accounts' in result:
                    return result['accounts']
                elif isinstance(result, dict) and 'kasalar' in result:
                    return result['kasalar']
            # Online başarısız olursa offline'a düş
            
        self.db.cursor.execute("SELECT * FROM kasalar WHERE aktif = 1 ORDER BY kasa_adi")
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def kasa_bakiye_hesapla(self, kasa_id: int, baslangic_tarih: Optional[str] = None,
                           bitis_tarih: Optional[str] = None) -> Dict:
        """Bir kasanın bakiyesini hesapla"""
        # Kasa bilgileri
        self.db.cursor.execute("SELECT * FROM kasalar WHERE kasa_id = ?", (kasa_id,))
        kasa = self.db.cursor.fetchone()
        
        if not kasa:
            return {}
            
        devir = kasa['devir_bakiye']
        
        # Gelirler
        query_gelir = "SELECT COALESCE(SUM(tutar), 0) as toplam FROM gelirler WHERE kasa_id = ?"
        params_gelir = [kasa_id]
        
        if baslangic_tarih:
            query_gelir += " AND tarih >= ?"
            params_gelir.append(baslangic_tarih)
            
        if bitis_tarih:
            query_gelir += " AND tarih <= ?"
            params_gelir.append(bitis_tarih)
            
        self.db.cursor.execute(query_gelir, params_gelir)
        toplam_gelir = self.db.cursor.fetchone()['toplam']
        
        # Giderler
        query_gider = "SELECT COALESCE(SUM(tutar), 0) as toplam FROM giderler WHERE kasa_id = ?"
        params_gider = [kasa_id]
        
        if baslangic_tarih:
            query_gider += " AND tarih >= ?"
            params_gider.append(baslangic_tarih)
            
        if bitis_tarih:
            query_gider += " AND tarih <= ?"
            params_gider.append(bitis_tarih)
            
        self.db.cursor.execute(query_gider, params_gider)
        toplam_gider = self.db.cursor.fetchone()['toplam']
        
        # Virman giden
        query_virman_giden = "SELECT COALESCE(SUM(tutar), 0) as toplam FROM virmanlar WHERE gonderen_kasa_id = ?"
        params_virman_giden = [kasa_id]
        
        if baslangic_tarih:
            query_virman_giden += " AND tarih >= ?"
            params_virman_giden.append(baslangic_tarih)
            
        if bitis_tarih:
            query_virman_giden += " AND tarih <= ?"
            params_virman_giden.append(bitis_tarih)
            
        self.db.cursor.execute(query_virman_giden, params_virman_giden)
        virman_giden = self.db.cursor.fetchone()['toplam']
        
        # Virman gelen
        query_virman_gelen = "SELECT COALESCE(SUM(tutar), 0) as toplam FROM virmanlar WHERE alan_kasa_id = ?"
        params_virman_gelen = [kasa_id]
        
        if baslangic_tarih:
            query_virman_gelen += " AND tarih >= ?"
            params_virman_gelen.append(baslangic_tarih)
            
        if bitis_tarih:
            query_virman_gelen += " AND tarih <= ?"
            params_virman_gelen.append(bitis_tarih)
            
        self.db.cursor.execute(query_virman_gelen, params_virman_gelen)
        virman_gelen = self.db.cursor.fetchone()['toplam']
        
        # Net bakiye
        net_bakiye = devir + toplam_gelir - toplam_gider - virman_giden + virman_gelen
        
        return {
            'kasa_id': kasa_id,
            'kasa_adi': kasa['kasa_adi'],
            'para_birimi': kasa['para_birimi'],
            'devir_bakiye': devir,
            'toplam_gelir': toplam_gelir,
            'toplam_gider': toplam_gider,
            'virman_giden': virman_giden,
            'virman_gelen': virman_gelen,
            'net_bakiye': net_bakiye
        }
        
    def tum_kasalar_ozet(self, baslangic_tarih: Optional[str] = None,
                        bitis_tarih: Optional[str] = None) -> List[Dict]:
        """Tüm kasaların özetini getir"""
        kasalar = self.kasa_listesi()
        ozet = []
        
        for kasa in kasalar:
            bakiye = self.kasa_bakiye_hesapla(kasa['kasa_id'], baslangic_tarih, bitis_tarih)
            ozet.append(bakiye)
            
        return ozet
    
    def kasa_bakiye_tip(self, kasa_id: int, tarih: str = None, tip: str = 'fiziksel') -> float:
        """
        Kasa bakiyesini hesapla
        tip: 'fiziksel' (kasadaki gerçek para) veya 'serbest' (tahakkuksuz)
        """
        if tarih is None:
            tarih = datetime.now().strftime("%Y-%m-%d")
        
        # Fiziksel bakiye
        bakiye_detay = self.kasa_bakiye_hesapla(kasa_id, bitis_tarih=tarih)
        fiziksel = bakiye_detay.get('net_bakiye', 0)
        
        if tip == 'fiziksel':
            return fiziksel
        
        elif tip == 'serbest':
            yil = int(tarih[:4])
            
            # Gelir tahakkukları (gelecek yıllara ait)
            self.db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) as toplam FROM gelirler
                WHERE kasa_id = ?
                AND tarih <= ?
                AND ait_oldugu_yil > ?
                AND tahakkuk_durumu = 'PEŞİN'
            """, (kasa_id, tarih, yil))
            gelir_tahakkuk = self.db.cursor.fetchone()['toplam']
            
            # Gider tahakkukları (gelecek için peşin ödemeler)
            self.db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) as toplam FROM giderler
                WHERE kasa_id = ?
                AND tarih <= ?
                AND ait_oldugu_yil > ?
                AND tahakkuk_durumu = 'PEŞİN'
            """, (kasa_id, tarih, yil))
            gider_tahakkuk = self.db.cursor.fetchone()['toplam']
            
            serbest = fiziksel - gelir_tahakkuk + gider_tahakkuk
            return serbest
    
    def kasa_tahakkuk_detay(self, kasa_id: int, tarih: str = None) -> Dict:
        """Kasanın tahakkuk detayı"""
        if tarih is None:
            tarih = datetime.now().strftime("%Y-%m-%d")
        
        yil = int(tarih[:4])
        
        # Gelecek yıl tahakkukları (yıl bazlı)
        self.db.cursor.execute("""
            SELECT 
                ait_oldugu_yil as yil,
                COUNT(*) as adet,
                SUM(tutar) as tutar
            FROM gelirler
            WHERE kasa_id = ?
            AND tarih <= ?
            AND ait_oldugu_yil > ?
            AND tahakkuk_durumu = 'PEŞİN'
            GROUP BY ait_oldugu_yil
            ORDER BY ait_oldugu_yil
        """, (kasa_id, tarih, yil))
        
        gelecek_yil_tahakkuklari = [dict(row) for row in self.db.cursor.fetchall()]
        
        toplam_tahakkuk = sum([t['tutar'] for t in gelecek_yil_tahakkuklari])
        
        fiziksel = self.kasa_bakiye_tip(kasa_id, tarih, 'fiziksel')
        serbest = self.kasa_bakiye_tip(kasa_id, tarih, 'serbest')
        
        return {
            'fiziksel_bakiye': fiziksel,
            'tahakkuk_toplami': toplam_tahakkuk,
            'serbest_bakiye': serbest,
            'gelecek_yil_detay': gelecek_yil_tahakkuklari
        }


class DevirYoneticisi:
    """Yıl sonu devir işlemleri yöneticisi"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def yil_sonu_devir(self, yil: int, onay: bool = False) -> Dict:
        """
        Yıl sonu kapanış ve devir işlemi
        
        onay=False: Sadece rapor (simülasyon)
        onay=True: Gerçek devir
        """
        kasa_yoneticisi = KasaYoneticisi(self.db)
        
        tarih = f"{yil}-12-31"
        kasalar = kasa_yoneticisi.kasa_listesi()
        
        devir_raporu = {
            'yil': yil,
            'tarih': tarih,
            'kasalar': [],
            'uyarilar': [],
            'toplam': {
                'fiziksel': 0,
                'tahakkuk': 0,
                'serbest': 0
            }
        }
        
        for kasa in kasalar:
            kasa_id = kasa['kasa_id']
            
            # Tahakkuk detayı
            detay = kasa_yoneticisi.kasa_tahakkuk_detay(kasa_id, tarih)
            
            kasa_devir = {
                'kasa_id': kasa_id,
                'kasa_adi': kasa['kasa_adi'],
                'fiziksel_bakiye': detay['fiziksel_bakiye'],
                'tahakkuk_toplami': detay['tahakkuk_toplami'],
                'serbest_bakiye': detay['serbest_bakiye'],
                'gelecek_yil_tahakkuklari': detay['gelecek_yil_detay']
            }
            
            # Uyarı kontrolleri
            if detay['serbest_bakiye'] < 0:
                devir_raporu['uyarilar'].append({
                    'tip': 'CARİ_AÇIK',
                    'kasa': kasa['kasa_adi'],
                    'mesaj': f"Serbest bakiye negatif: {detay['serbest_bakiye']:,.2f} TL. "
                            f"Gelecek yılların parasını kullanmış durumdasınız!"
                })
            
            if detay['fiziksel_bakiye'] > 0 and detay['tahakkuk_toplami'] > detay['fiziksel_bakiye'] * 0.8:
                devir_raporu['uyarilar'].append({
                    'tip': 'YÜKSEK_TAHAKKUK',
                    'kasa': kasa['kasa_adi'],
                    'mesaj': f"Tahakkuk oranı çok yüksek (%{detay['tahakkuk_toplami']/detay['fiziksel_bakiye']*100:.0f}). "
                            f"Üye ayrılma riski!"
                })
            
            devir_raporu['kasalar'].append(kasa_devir)
            
            # Toplamlar
            devir_raporu['toplam']['fiziksel'] += detay['fiziksel_bakiye']
            devir_raporu['toplam']['tahakkuk'] += detay['tahakkuk_toplami']
            devir_raporu['toplam']['serbest'] += detay['serbest_bakiye']
        
        # Gerçek devir
        if onay:
            self._devri_uygula(yil, devir_raporu)
        
        return devir_raporu
    
    def _devri_uygula(self, yil: int, rapor: Dict):
        """Devir işlemini uygula"""
        for kasa_devir in rapor['kasalar']:
            self.db.cursor.execute("""
                UPDATE kasalar
                SET devir_bakiye = ?,
                    serbest_devir_bakiye = ?,
                    tahakkuk_toplami = ?,
                    son_devir_tarihi = CURRENT_TIMESTAMP
                WHERE kasa_id = ?
            """, (
                kasa_devir['fiziksel_bakiye'],
                kasa_devir['serbest_bakiye'],
                kasa_devir['tahakkuk_toplami'],
                kasa_devir['kasa_id']
            ))
        
        # Devir log kaydı
        self.db.cursor.execute("""
            INSERT INTO devir_islemleri
            (yil, devir_tarihi, toplam_fiziksel, toplam_tahakkuk, 
             toplam_serbest, rapor_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            yil,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            rapor['toplam']['fiziksel'],
            rapor['toplam']['tahakkuk'],
            rapor['toplam']['serbest'],
            json.dumps(rapor, ensure_ascii=False)
        ))
        
        self.db.commit()
        self.db.log_islem("Sistem", "DEVİR", "devir_islemleri", yil, 
                         f"Yıl sonu devir: {yil}")


class TahakkukYoneticisi:
    """Tahakkuk takip ve raporlama yöneticisi"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def tahakkuk_listesi(self, yil: int = None, durum: str = 'AKTİF') -> List[Dict]:
        """Tahakkuk listesi"""
        query = """
            SELECT 
                t.*,
                g.gelir_turu,
                g.aciklama,
                k.kasa_adi,
                u.ad_soyad as uye_adi
            FROM tahakkuklar t
            LEFT JOIN gelirler g ON t.kaynak_id = g.gelir_id
            LEFT JOIN kasalar k ON g.kasa_id = k.kasa_id
            LEFT JOIN aidat_takip a ON g.aidat_id = a.aidat_id
            LEFT JOIN uyeler u ON a.uye_id = u.uye_id
            WHERE t.tahakkuk_turu = 'GELİR'
        """
        params = []
        
        if yil:
            query += " AND t.ait_oldugu_yil = ?"
            params.append(yil)
        
        if durum:
            query += " AND t.durum = ?"
            params.append(durum)
        
        query += " ORDER BY t.ait_oldugu_yil, t.tutar DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def tahakkuk_ozet(self) -> List[Dict]:
        """Yıl bazlı tahakkuk özeti"""
        self.db.cursor.execute("""
            SELECT 
                ait_oldugu_yil as yil,
                COUNT(*) as adet,
                SUM(tutar) as tutar,
                durum
            FROM tahakkuklar
            WHERE tahakkuk_turu = 'GELİR'
            GROUP BY ait_oldugu_yil, durum
            ORDER BY ait_oldugu_yil
        """)
        
        return [dict(row) for row in self.db.cursor.fetchall()]


class RaporYoneticisi:
    """Raporlama ve istatistik işlemleri"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def genel_ozet(self, yil: Optional[int] = None) -> Dict:
        """Genel mali durum özeti"""
        if yil:
            baslangic = f"{yil}-01-01"
            bitis = f"{yil}-12-31"
        else:
            baslangic = None
            bitis = None
            
        # Toplam gelir
        query_gelir = "SELECT COALESCE(SUM(tutar), 0) as toplam FROM gelirler"
        params_gelir = []
        if baslangic:
            query_gelir += " WHERE tarih >= ? AND tarih <= ?"
            params_gelir = [baslangic, bitis]
            
        self.db.cursor.execute(query_gelir, params_gelir)
        toplam_gelir = self.db.cursor.fetchone()['toplam']
        
        # Toplam gider
        query_gider = "SELECT COALESCE(SUM(tutar), 0) as toplam FROM giderler"
        params_gider = []
        if baslangic:
            query_gider += " WHERE tarih >= ? AND tarih <= ?"
            params_gider = [baslangic, bitis]
            
        self.db.cursor.execute(query_gider, params_gider)
        toplam_gider = self.db.cursor.fetchone()['toplam']
        
        # Aidat istatistikleri
        query_aidat = "SELECT COUNT(*) as toplam FROM uyeler WHERE durum = 'Aktif'"
        self.db.cursor.execute(query_aidat)
        toplam_uye = self.db.cursor.fetchone()['toplam']
        
        if yil:
            query_odenen = """
                SELECT COUNT(DISTINCT uye_id) as sayi 
                FROM aidat_takip 
                WHERE yil = ? AND durum = 'Tamamlandı'
            """
            self.db.cursor.execute(query_odenen, (yil,))
            aidat_odenen = self.db.cursor.fetchone()['sayi']
            
            query_eksik = """
                SELECT COUNT(DISTINCT uye_id) as sayi 
                FROM aidat_takip 
                WHERE yil = ? AND durum IN ('Eksik', 'Kısmi')
            """
            self.db.cursor.execute(query_eksik, (yil,))
            aidat_eksik = self.db.cursor.fetchone()['sayi']
        else:
            aidat_odenen = 0
            aidat_eksik = 0
            
        # Kasa toplam
        kasa_yoneticisi = KasaYoneticisi(self.db)
        kasa_ozet = kasa_yoneticisi.tum_kasalar_ozet(baslangic, bitis)
        toplam_kasa = sum([k['net_bakiye'] for k in kasa_ozet])
        
        return {
            'toplam_gelir': toplam_gelir,
            'toplam_gider': toplam_gider,
            'net_sonuc': toplam_gelir - toplam_gider,
            'toplam_uye': toplam_uye,
            'aidat_odenen_uye': aidat_odenen,
            'aidat_eksik_uye': aidat_eksik,
            'toplam_kasa_bakiye': toplam_kasa,
            'kasa_detay': kasa_ozet
        }
        
    def gelir_turu_dagilimi(self, baslangic_tarih: Optional[str] = None,
                           bitis_tarih: Optional[str] = None) -> List[Dict]:
        """Gelir türlerine göre dağılım"""
        query = """
            SELECT gelir_turu, COUNT(*) as adet, SUM(tutar) as toplam
            FROM gelirler
            WHERE 1=1
        """
        params = []
        
        if baslangic_tarih:
            query += " AND tarih >= ?"
            params.append(baslangic_tarih)
            
        if bitis_tarih:
            query += " AND tarih <= ?"
            params.append(bitis_tarih)
            
        query += " GROUP BY gelir_turu ORDER BY toplam DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def gider_turu_dagilimi(self, baslangic_tarih: Optional[str] = None,
                           bitis_tarih: Optional[str] = None) -> List[Dict]:
        """Gider türlerine göre dağılım"""
        query = """
            SELECT gider_turu, COUNT(*) as adet, SUM(tutar) as toplam
            FROM giderler
            WHERE 1=1
        """
        params = []
        
        if baslangic_tarih:
            query += " AND tarih >= ?"
            params.append(baslangic_tarih)
            
        if bitis_tarih:
            query += " AND tarih <= ?"
            params.append(bitis_tarih)
            
        query += " GROUP BY gider_turu ORDER BY toplam DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def aylik_gelir_gider(self, yil: int) -> List[Dict]:
        """Aylık gelir-gider karşılaştırması"""
        aylar = []
        for ay in range(1, 13):
            baslangic = f"{yil}-{ay:02d}-01"
            if ay == 12:
                bitis = f"{yil}-12-31"
            else:
                import calendar
                son_gun = calendar.monthrange(yil, ay)[1]
                bitis = f"{yil}-{ay:02d}-{son_gun}"
            
            # Gelir
            self.db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) as toplam
                FROM gelirler
                WHERE tarih BETWEEN ? AND ?
            """, (baslangic, bitis))
            gelir = self.db.cursor.fetchone()['toplam']
            
            # Gider
            self.db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) as toplam
                FROM giderler
                WHERE tarih BETWEEN ? AND ?
            """, (baslangic, bitis))
            gider = self.db.cursor.fetchone()['toplam']
            
            aylar.append({
                'ay': ay,
                'ay_adi': ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                          'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'][ay-1],
                'gelir': gelir,
                'gider': gider,
                'fark': gelir - gider
            })
        
        return aylar


class MaliTabloYoneticisi:
    """Mali tablolar ve bilanço işlemleri"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def bilanco_raporu(self, tarih: str = None) -> Dict:
        """
        Bilanço benzeri rapor (Dernek muhasebesi için basitleştirilmiş)
        Tarih: YYYY-MM-DD formatında, belirtilmezse bugün
        """
        if not tarih:
            from datetime import datetime
            tarih = datetime.now().strftime("%Y-%m-%d")
        
        # === VARLIKLAR ===
        
        # 1. Kasalar (Dönen Varlıklar)
        kasa_yoneticisi = KasaYoneticisi(self.db)
        kasalar = kasa_yoneticisi.tum_kasalar_ozet(bitis_tarih=tarih)
        toplam_kasa = sum([k['net_bakiye'] for k in kasalar])
        
        # 2. Aidat Alacakları
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(odenecek_tutar), 0) as toplam
            FROM aidat_takip
            WHERE durum IN ('Eksik', 'Kısmi')
        """)
        aidat_alacaklari = self.db.cursor.fetchone()['toplam']
        
        # 3. Diğer Alacaklar (Alacak-Verecek Sistemi)
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(kalan_tutar), 0) as toplam
            FROM alacaklar
            WHERE alacak_tarihi <= ?
            AND durum NOT IN ('İptal', 'Tahsil Edildi')
        """, (tarih,))
        diger_alacaklar = self.db.cursor.fetchone()['toplam']
        
        # Toplam Dönen Varlıklar
        donen_varliklar = toplam_kasa + aidat_alacaklari + diger_alacaklar
        
        # 4. Duran Varlıklar (Şimdilik 0, demirbaş eklendikçe artacak)
        duran_varliklar = 0
        
        # TOPLAM VARLIK
        toplam_varlik = donen_varliklar + duran_varliklar
        
        # === KAYNAKLAR ===
        
        # 1. Kısa Vadeli Yükümlülükler (Verecekler)
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(kalan_tutar), 0) as toplam
            FROM verecekler
            WHERE verecek_tarihi <= ?
            AND durum NOT IN ('İptal', 'Ödendi')
        """, (tarih,))
        kisa_vadeli_yukumlulukler = self.db.cursor.fetchone()['toplam']
        
        # 2. Dernek Sermayesi (Başlangıç devir)
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(devir_bakiye), 0) as toplam
            FROM kasalar
        """)
        dernek_sermayesi = self.db.cursor.fetchone()['toplam']
        
        # 2. Dönem Karı/Zararı
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) as toplam
            FROM gelirler
            WHERE tarih <= ?
        """, (tarih,))
        toplam_gelir = self.db.cursor.fetchone()['toplam']
        
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) as toplam
            FROM giderler
            WHERE tarih <= ?
        """, (tarih,))
        toplam_gider = self.db.cursor.fetchone()['toplam']
        
        donem_sonucu = toplam_gelir - toplam_gider
        
        # TOPLAM KAYNAK
        toplam_kaynak = kisa_vadeli_yukumlulukler + dernek_sermayesi + donem_sonucu
        
        # Bilanço dengesizliği (olmaması gerekir ama kontrol edelim)
        denge_farki = toplam_varlik - toplam_kaynak
        
        return {
            'tarih': tarih,
            'varliklar': {
                'donen_varliklar': {
                    'kasalar': {
                        'toplam': toplam_kasa,
                        'detay': kasalar
                    },
                    'aidat_alacaklari': aidat_alacaklari,
                    'diger_alacaklar': diger_alacaklar,
                    'toplam': donen_varliklar
                },
                'duran_varliklar': {
                    'demirbaslar': duran_varliklar,
                    'toplam': duran_varliklar
                },
                'toplam': toplam_varlik
            },
            'kaynaklar': {
                'kisa_vadeli_yukumlulukler': kisa_vadeli_yukumlulukler,
                'dernek_sermayesi': dernek_sermayesi,
                'donem_sonucu': {
                    'toplam_gelir': toplam_gelir,
                    'toplam_gider': toplam_gider,
                    'net': donem_sonucu
                },
                'toplam': toplam_kaynak
            },
            'denge': {
                'varlik': toplam_varlik,
                'kaynak': toplam_kaynak,
                'fark': denge_farki,
                'dengeli': abs(denge_farki) < 0.01
            }
        }
    
    def gelir_tablosu(self, baslangic: str, bitis: str) -> Dict:
        """
        Gelir Tablosu (Dönem sonuçları)
        """
        # Gelirler (türlerine göre)
        self.db.cursor.execute("""
            SELECT 
                gelir_turu,
                COUNT(*) as adet,
                SUM(tutar) as tutar
            FROM gelirler
            WHERE tarih BETWEEN ? AND ?
            GROUP BY gelir_turu
            ORDER BY tutar DESC
        """, (baslangic, bitis))
        gelir_detay = [dict(row) for row in self.db.cursor.fetchall()]
        toplam_gelir = sum([g['tutar'] for g in gelir_detay])
        
        # Giderler (türlerine göre)
        self.db.cursor.execute("""
            SELECT 
                gider_turu,
                COUNT(*) as adet,
                SUM(tutar) as tutar
            FROM giderler
            WHERE tarih BETWEEN ? AND ?
            GROUP BY gider_turu
            ORDER BY tutar DESC
        """, (baslangic, bitis))
        gider_detay = [dict(row) for row in self.db.cursor.fetchall()]
        toplam_gider = sum([g['tutar'] for g in gider_detay])
        
        # Net sonuç
        net_sonuc = toplam_gelir - toplam_gider
        
        return {
            'donem': {
                'baslangic': baslangic,
                'bitis': bitis
            },
            'gelirler': {
                'detay': gelir_detay,
                'toplam': toplam_gelir
            },
            'giderler': {
                'detay': gider_detay,
                'toplam': toplam_gider
            },
            'sonuc': {
                'net': net_sonuc,
                'durum': 'KAR' if net_sonuc > 0 else 'ZARAR' if net_sonuc < 0 else 'BAŞABAŞ'
            }
        }
    
    def nakit_akis_tablosu(self, baslangic: str, bitis: str) -> Dict:
        """
        Nakit Akış Tablosu (Basitleştirilmiş)
        """
        # Dönem başı kasa
        kasa_yoneticisi = KasaYoneticisi(self.db)
        
        # Dönem başı
        kasalar_baslangic = kasa_yoneticisi.tum_kasalar_ozet(bitis_tarih=baslangic)
        donem_basi = sum([k['net_bakiye'] for k in kasalar_baslangic])
        
        # Nakit girişleri
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) as toplam
            FROM gelirler
            WHERE tarih BETWEEN ? AND ?
        """, (baslangic, bitis))
        nakit_giris = self.db.cursor.fetchone()['toplam']
        
        # Nakit çıkışları
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) as toplam
            FROM giderler
            WHERE tarih BETWEEN ? AND ?
        """, (baslangic, bitis))
        nakit_cikis = self.db.cursor.fetchone()['toplam']
        
        # Net nakit akışı
        net_akis = nakit_giris - nakit_cikis
        
        # Dönem sonu
        kasalar_bitis = kasa_yoneticisi.tum_kasalar_ozet(bitis_tarih=bitis)
        donem_sonu = sum([k['net_bakiye'] for k in kasalar_bitis])
        
        return {
            'donem': {
                'baslangic': baslangic,
                'bitis': bitis
            },
            'donem_basi_nakit': donem_basi,
            'isletme_faaliyetleri': {
                'nakit_giris': nakit_giris,
                'nakit_cikis': nakit_cikis,
                'net': net_akis
            },
            'donem_sonu_nakit': donem_sonu,
            'dogrulama': {
                'hesaplanan': donem_basi + net_akis,
                'gercek': donem_sonu,
                'fark': abs((donem_basi + net_akis) - donem_sonu),
                'dogru': abs((donem_basi + net_akis) - donem_sonu) < 0.01
            }
        }


# ========================================
# KÖY İŞLEMLERİ MODÜLÜ YÖNETİCİLERİ
# ========================================

class KoyKasaYoneticisi:
    """Köy kasa yönetim ve hesaplama işlemleri"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def kasa_ekle(self, kasa_adi: str, para_birimi: str = "TL", 
                  devir_bakiye: float = 0, aciklama: str = "") -> int:
        """Yeni köy kasası ekle"""
        try:
            self.db.cursor.execute("""
                INSERT INTO koy_kasalar (kasa_adi, para_birimi, devir_bakiye, aciklama)
                VALUES (?, ?, ?, ?)
            """, (kasa_adi, para_birimi, devir_bakiye, aciklama))
            self.db.commit()
            kasa_id = self.db.cursor.lastrowid
            self.db.log_islem("Sistem", "EKLE", "koy_kasalar", kasa_id, f"Yeni köy kasası: {kasa_adi}")
            return kasa_id
        except Exception as e:
            print(f"Köy kasa ekleme hatası: {e}")
            return -1
            
    def kasa_guncelle(self, kasa_id: int, kasa_adi: str, para_birimi: str, 
                     devir_bakiye: float, aciklama: str = ""):
        """Köy kasa bilgilerini güncelle"""
        self.db.cursor.execute("""
            UPDATE koy_kasalar
            SET kasa_adi = ?, para_birimi = ?, devir_bakiye = ?, aciklama = ?
            WHERE kasa_id = ?
        """, (kasa_adi, para_birimi, devir_bakiye, aciklama, kasa_id))
        self.db.commit()
        self.db.log_islem("Sistem", "GÜNCELLE", "koy_kasalar", kasa_id, f"Köy kasası güncellendi: {kasa_adi}")
        
    def kasa_listesi(self) -> List[Dict]:
        """Tüm köy kasalarını listele"""
        self.db.cursor.execute("SELECT * FROM koy_kasalar WHERE aktif = 1 ORDER BY kasa_adi")
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def kasa_bakiye_hesapla(self, kasa_id: int) -> Dict:
        """Bir köy kasasının bakiyesini hesapla"""
        self.db.cursor.execute("SELECT * FROM koy_kasalar WHERE kasa_id = ?", (kasa_id,))
        kasa = self.db.cursor.fetchone()
        
        if not kasa:
            return {}
            
        devir = kasa['devir_bakiye']
        
        # Gelirler
        self.db.cursor.execute(
            "SELECT COALESCE(SUM(tutar), 0) as toplam FROM koy_gelirleri WHERE kasa_id = ?", 
            (kasa_id,)
        )
        toplam_gelir = self.db.cursor.fetchone()['toplam']
        
        # Giderler
        self.db.cursor.execute(
            "SELECT COALESCE(SUM(tutar), 0) as toplam FROM koy_giderleri WHERE kasa_id = ?", 
            (kasa_id,)
        )
        toplam_gider = self.db.cursor.fetchone()['toplam']
        
        # Virman giden
        self.db.cursor.execute(
            "SELECT COALESCE(SUM(tutar), 0) as toplam FROM koy_virmanlar WHERE gonderen_kasa_id = ?", 
            (kasa_id,)
        )
        virman_giden = self.db.cursor.fetchone()['toplam']
        
        # Virman gelen
        self.db.cursor.execute(
            "SELECT COALESCE(SUM(tutar), 0) as toplam FROM koy_virmanlar WHERE alan_kasa_id = ?", 
            (kasa_id,)
        )
        virman_gelen = self.db.cursor.fetchone()['toplam']
        
        net_bakiye = devir + toplam_gelir - toplam_gider - virman_giden + virman_gelen
        
        return {
            'kasa_id': kasa_id,
            'kasa_adi': kasa['kasa_adi'],
            'para_birimi': kasa['para_birimi'],
            'devir_bakiye': devir,
            'toplam_gelir': toplam_gelir,
            'toplam_gider': toplam_gider,
            'virman_giden': virman_giden,
            'virman_gelen': virman_gelen,
            'net_bakiye': net_bakiye
        }
    
    def tum_kasalar_ozet(self) -> List[Dict]:
        """Tüm köy kasalarının özetini getir"""
        kasalar = self.kasa_listesi()
        return [self.kasa_bakiye_hesapla(k['kasa_id']) for k in kasalar]


class KoyGelirYoneticisi:
    """Köy gelir yönetim işlemleri"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def gelir_ekle(self, tarih: str, gelir_turu: str, aciklama: str, 
                   tutar: float, kasa_id: int, tahsil_eden: str = "", 
                   notlar: str = "", dekont_no: str = "") -> int:
        """Yeni köy gelir kaydı ekle"""
        belge_no = self.db.get_next_koy_belge_no()
        
        self.db.cursor.execute("""
            INSERT INTO koy_gelirleri 
            (tarih, belge_no, gelir_turu, aciklama, tutar, kasa_id, tahsil_eden, notlar, dekont_no)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tarih, belge_no, gelir_turu, aciklama, tutar, kasa_id, tahsil_eden, notlar, dekont_no))
        self.db.commit()
        
        gelir_id = self.db.cursor.lastrowid
        self.db.log_islem("Sistem", "EKLE", "koy_gelirleri", gelir_id, 
                         f"Köy geliri eklendi: {gelir_turu} - {tutar} TL")
        return gelir_id
        
    def gelir_guncelle(self, gelir_id: int, tarih: str, gelir_turu: str, 
                      aciklama: str, tutar: float, kasa_id: int, 
                      tahsil_eden: str = "", notlar: str = "", dekont_no: str = ""):
        """Köy gelir kaydını güncelle"""
        self.db.cursor.execute("""
            UPDATE koy_gelirleri
            SET tarih = ?, gelir_turu = ?, aciklama = ?, tutar = ?, 
                kasa_id = ?, tahsil_eden = ?, notlar = ?, dekont_no = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE gelir_id = ?
        """, (tarih, gelir_turu, aciklama, tutar, kasa_id, tahsil_eden, notlar, dekont_no, gelir_id))
        self.db.commit()
        self.db.log_islem("Sistem", "GÜNCELLE", "koy_gelirleri", gelir_id, f"Köy geliri güncellendi")
        
    def gelir_sil(self, gelir_id: int):
        """Köy gelir kaydını sil"""
        self.db.cursor.execute("SELECT tutar, gelir_turu FROM koy_gelirleri WHERE gelir_id = ?", (gelir_id,))
        result = self.db.cursor.fetchone()
        
        if result:
            self.db.cursor.execute("DELETE FROM koy_gelirleri WHERE gelir_id = ?", (gelir_id,))
            self.db.commit()
            self.db.log_islem("Sistem", "SİL", "koy_gelirleri", gelir_id, 
                            f"Köy geliri silindi: {result['gelir_turu']} - {result['tutar']} TL")
        
    def gelir_listesi(self, baslangic_tarih: Optional[str] = None, 
                     bitis_tarih: Optional[str] = None, 
                     gelir_turu: Optional[str] = None,
                     kasa_id: Optional[int] = None) -> List[Dict]:
        """Köy gelir listesini getir (filtreli)"""
        query = """
            SELECT g.*, k.kasa_adi, k.para_birimi
            FROM koy_gelirleri g
            JOIN koy_kasalar k ON g.kasa_id = k.kasa_id
            WHERE 1=1
        """
        params = []
        
        if baslangic_tarih:
            query += " AND g.tarih >= ?"
            params.append(baslangic_tarih)
        if bitis_tarih:
            query += " AND g.tarih <= ?"
            params.append(bitis_tarih)
        if gelir_turu:
            query += " AND g.gelir_turu = ?"
            params.append(gelir_turu)
        if kasa_id:
            query += " AND g.kasa_id = ?"
            params.append(kasa_id)
            
        query += " ORDER BY g.tarih DESC, g.gelir_id DESC"
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def gelir_turleri_listesi(self) -> List[str]:
        """Köy gelir türlerini getir"""
        self.db.cursor.execute("SELECT tur_adi FROM koy_gelir_turleri WHERE aktif = 1 ORDER BY tur_adi")
        return [row['tur_adi'] for row in self.db.cursor.fetchall()]
    
    def gelir_alt_kategorileri(self, tur_adi: str) -> List[str]:
        """Gelir türüne göre alt kategorileri getir"""
        alt_kategoriler = {
            "KİRA": ["Salon Kirası", "Düğün Salonu", "Toplantı Salonu", "Depo Kirası"],
            "BAĞIŞ": ["Nakdi Bağış", "Ayni Bağış", "Koşullu Bağış"],
            "DÜĞÜN": ["Düğün Salonu", "Ses Sistemi", "Aydınlatma", "Catering"],
            "KINA": ["Kına Salonu", "Organizasyon"],
            "TOPLANTI": ["Toplantı Salonu", "İkram"],
            "DAVET": ["Taziye", "Mevlit", "Bayramlaşma"],
            "AİDAT": ["Yıllık Aidat", "Giriş Aidatı"],
            "DİĞER": ["Genel Gelir", "Faiz Geliri", "Ceza Geliri"]
        }
        return alt_kategoriler.get(tur_adi.upper(), [])


class KoyGiderYoneticisi:
    """Köy gider yönetim işlemleri"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def gider_ekle(self, tarih: str, gider_turu: str, aciklama: str, 
                   tutar: float, kasa_id: int, odeyen: str = "", 
                   notlar: str = "", dekont_no: str = "") -> int:
        """Yeni köy gider kaydı ekle"""
        islem_no = self.db.get_next_koy_islem_no()
        
        self.db.cursor.execute("""
            INSERT INTO koy_giderleri 
            (tarih, islem_no, gider_turu, aciklama, tutar, kasa_id, odeyen, notlar, dekont_no)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tarih, islem_no, gider_turu, aciklama, tutar, kasa_id, odeyen, notlar, dekont_no))
        self.db.commit()
        
        gider_id = self.db.cursor.lastrowid
        self.db.log_islem("Sistem", "EKLE", "koy_giderleri", gider_id, 
                         f"Köy gideri eklendi: {gider_turu} - {tutar} TL")
        return gider_id
        
    def gider_guncelle(self, gider_id: int, tarih: str, gider_turu: str, 
                      aciklama: str, tutar: float, kasa_id: int, 
                      odeyen: str = "", notlar: str = "", dekont_no: str = ""):
        """Köy gider kaydını güncelle"""
        self.db.cursor.execute("""
            UPDATE koy_giderleri
            SET tarih = ?, gider_turu = ?, aciklama = ?, tutar = ?, 
                kasa_id = ?, odeyen = ?, notlar = ?, dekont_no = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE gider_id = ?
        """, (tarih, gider_turu, aciklama, tutar, kasa_id, odeyen, notlar, dekont_no, gider_id))
        self.db.commit()
        self.db.log_islem("Sistem", "GÜNCELLE", "koy_giderleri", gider_id, f"Köy gideri güncellendi")
        
    def gider_sil(self, gider_id: int):
        """Köy gider kaydını sil"""
        self.db.cursor.execute("SELECT tutar, gider_turu FROM koy_giderleri WHERE gider_id = ?", (gider_id,))
        result = self.db.cursor.fetchone()
        
        if result:
            self.db.cursor.execute("DELETE FROM koy_giderleri WHERE gider_id = ?", (gider_id,))
            self.db.commit()
            self.db.log_islem("Sistem", "SİL", "koy_giderleri", gider_id, 
                            f"Köy gideri silindi: {result['gider_turu']} - {result['tutar']} TL")
        
    def gider_listesi(self, baslangic_tarih: Optional[str] = None, 
                     bitis_tarih: Optional[str] = None, 
                     gider_turu: Optional[str] = None,
                     kasa_id: Optional[int] = None) -> List[Dict]:
        """Köy gider listesini getir (filtreli)"""
        query = """
            SELECT g.*, k.kasa_adi, k.para_birimi
            FROM koy_giderleri g
            JOIN koy_kasalar k ON g.kasa_id = k.kasa_id
            WHERE 1=1
        """
        params = []
        
        if baslangic_tarih:
            query += " AND g.tarih >= ?"
            params.append(baslangic_tarih)
        if bitis_tarih:
            query += " AND g.tarih <= ?"
            params.append(bitis_tarih)
        if gider_turu:
            query += " AND g.gider_turu = ?"
            params.append(gider_turu)
        if kasa_id:
            query += " AND g.kasa_id = ?"
            params.append(kasa_id)
            
        query += " ORDER BY g.tarih DESC, g.gider_id DESC"
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def gider_turleri_listesi(self) -> List[str]:
        """Köy gider türlerini getir"""
        self.db.cursor.execute("SELECT tur_adi FROM koy_gider_turleri WHERE aktif = 1 ORDER BY tur_adi")
        return [row['tur_adi'] for row in self.db.cursor.fetchall()]


class KoyVirmanYoneticisi:
    """Köy virman (kasa transfer) işlemleri"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def virman_ekle(self, tarih: str, gonderen_kasa_id: int, alan_kasa_id: int, 
                    tutar: float, aciklama: str = "") -> int:
        """Köy kasaları arası transfer"""
        if gonderen_kasa_id == alan_kasa_id:
            raise ValueError("Gönderen ve alan kasa aynı olamaz!")
            
        self.db.cursor.execute("""
            INSERT INTO koy_virmanlar (tarih, gonderen_kasa_id, alan_kasa_id, tutar, aciklama)
            VALUES (?, ?, ?, ?, ?)
        """, (tarih, gonderen_kasa_id, alan_kasa_id, tutar, aciklama))
        self.db.commit()
        
        virman_id = self.db.cursor.lastrowid
        self.db.log_islem("Sistem", "EKLE", "koy_virmanlar", virman_id, 
                         f"Köy virmanı: {tutar} TL")
        return virman_id
        
    def virman_sil(self, virman_id: int):
        """Köy virman işlemini sil"""
        self.db.cursor.execute("SELECT tutar FROM koy_virmanlar WHERE virman_id = ?", (virman_id,))
        result = self.db.cursor.fetchone()
        
        if result:
            self.db.cursor.execute("DELETE FROM koy_virmanlar WHERE virman_id = ?", (virman_id,))
            self.db.commit()
            self.db.log_islem("Sistem", "SİL", "koy_virmanlar", virman_id, f"Köy virmanı silindi: {result['tutar']} TL")
        
    def virman_listesi(self, baslangic_tarih: Optional[str] = None, 
                      bitis_tarih: Optional[str] = None) -> List[Dict]:
        """Köy virman listesini getir"""
        query = """
            SELECT v.*, 
                   k1.kasa_adi as gonderen_kasa_adi, k1.para_birimi as gonderen_para_birimi,
                   k2.kasa_adi as alan_kasa_adi, k2.para_birimi as alan_para_birimi
            FROM koy_virmanlar v
            JOIN koy_kasalar k1 ON v.gonderen_kasa_id = k1.kasa_id
            JOIN koy_kasalar k2 ON v.alan_kasa_id = k2.kasa_id
            WHERE 1=1
        """
        params = []
        
        if baslangic_tarih:
            query += " AND v.tarih >= ?"
            params.append(baslangic_tarih)
        if bitis_tarih:
            query += " AND v.tarih <= ?"
            params.append(bitis_tarih)
            
        query += " ORDER BY v.tarih DESC, v.virman_id DESC"
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]


# ========================================
# KULLANICI YÖNETİMİ
# ========================================

class KullaniciYoneticisi:
    """Kullanıcı ve yetki yönetimi"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def kullanici_ekle(self, kullanici_adi: str, sifre: str, ad_soyad: str,
                       email: str = "", rol: str = "görüntüleyici") -> int:
        """Yeni kullanıcı ekle"""
        import hashlib
        sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()
        
        try:
            self.db.cursor.execute("""
                INSERT INTO kullanicilar (kullanici_adi, sifre_hash, ad_soyad, email, rol)
                VALUES (?, ?, ?, ?, ?)
            """, (kullanici_adi, sifre_hash, ad_soyad, email, rol))
            self.db.commit()
            return self.db.cursor.lastrowid
        except Exception as e:
            print(f"Kullanıcı ekleme hatası: {e}")
            return -1
    
    def giris_kontrol(self, kullanici_adi: str, sifre: str) -> Optional[Dict]:
        """Kullanıcı girişi kontrol et"""
        import hashlib
        sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()
        
        self.db.cursor.execute("""
            SELECT * FROM kullanicilar 
            WHERE kullanici_adi = ? AND sifre_hash = ? AND aktif = 1
        """, (kullanici_adi, sifre_hash))
        
        kullanici = self.db.cursor.fetchone()
        
        if kullanici:
            # Son giriş güncelle
            self.db.cursor.execute("""
                UPDATE kullanicilar SET son_giris = CURRENT_TIMESTAMP
                WHERE kullanici_id = ?
            """, (kullanici['kullanici_id'],))
            self.db.commit()
            return dict(kullanici)
        return None
    
    def sifre_degistir(self, kullanici_id: int, yeni_sifre: str) -> bool:
        """Şifre değiştir"""
        import hashlib
        sifre_hash = hashlib.sha256(yeni_sifre.encode()).hexdigest()
        
        try:
            self.db.cursor.execute("""
                UPDATE kullanicilar SET sifre_hash = ? WHERE kullanici_id = ?
            """, (sifre_hash, kullanici_id))
            self.db.commit()
            return True
        except:
            return False
    
    def kullanici_listesi(self) -> List[Dict]:
        """Tüm kullanıcıları listele"""
        self.db.cursor.execute("""
            SELECT kullanici_id, kullanici_adi, ad_soyad, email, rol, aktif, son_giris
            FROM kullanicilar ORDER BY ad_soyad
        """)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def yetki_kontrol(self, kullanici_id: int, gerekli_rol: str) -> bool:
        """Kullanıcının yetkisini kontrol et"""
        rol_sirasi = {'admin': 3, 'muhasebeci': 2, 'görüntüleyici': 1}
        
        self.db.cursor.execute("SELECT rol FROM kullanicilar WHERE kullanici_id = ?", (kullanici_id,))
        result = self.db.cursor.fetchone()
        
        if result:
            kullanici_rol = result['rol']
            return rol_sirasi.get(kullanici_rol, 0) >= rol_sirasi.get(gerekli_rol, 0)
        return False


# ========================================
# ETKİNLİK YÖNETİMİ
# ========================================

class EtkinlikYoneticisi:
    """Etkinlik yönetimi"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def etkinlik_ekle(self, etkinlik_turu: str, baslik: str, tarih: str,
                      aciklama: str = "", saat: str = "", bitis_tarihi: str = None,
                      mekan: str = "", tahmini_gelir: float = 0, tahmini_gider: float = 0,
                      sorumlu_uye_id: int = None, notlar: str = "") -> int:
        """Yeni etkinlik ekle"""
        self.db.cursor.execute("""
            INSERT INTO etkinlikler 
            (etkinlik_turu, baslik, tarih, aciklama, saat, bitis_tarihi, mekan,
             tahmini_gelir, tahmini_gider, sorumlu_uye_id, notlar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (etkinlik_turu, baslik, tarih, aciklama, saat, bitis_tarihi, mekan,
              tahmini_gelir, tahmini_gider, sorumlu_uye_id, notlar))
        self.db.commit()
        return self.db.cursor.lastrowid
    
    def etkinlik_guncelle(self, etkinlik_id: int, **kwargs):
        """Etkinlik güncelle"""
        updates = []
        values = []
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            values.append(value)
        
        if updates:
            values.append(etkinlik_id)
            self.db.cursor.execute(f"""
                UPDATE etkinlikler 
                SET {', '.join(updates)}, guncelleme_tarihi = CURRENT_TIMESTAMP
                WHERE etkinlik_id = ?
            """, values)
            self.db.commit()
    
    def etkinlik_sil(self, etkinlik_id: int):
        """Etkinlik sil"""
        self.db.cursor.execute("DELETE FROM etkinlikler WHERE etkinlik_id = ?", (etkinlik_id,))
        self.db.commit()
    
    def etkinlik_listesi(self, tarih_baslangic: str = None, tarih_bitis: str = None,
                        etkinlik_turu: str = None, durum: str = None) -> List[Dict]:
        """Etkinlik listesi"""
        query = """
            SELECT e.*, u.ad_soyad as sorumlu_adi
            FROM etkinlikler e
            LEFT JOIN uyeler u ON e.sorumlu_uye_id = u.uye_id
            WHERE 1=1
        """
        params = []
        
        if tarih_baslangic:
            query += " AND e.tarih >= ?"
            params.append(tarih_baslangic)
        if tarih_bitis:
            query += " AND e.tarih <= ?"
            params.append(tarih_bitis)
        if etkinlik_turu:
            query += " AND e.etkinlik_turu = ?"
            params.append(etkinlik_turu)
        if durum:
            query += " AND e.durum = ?"
            params.append(durum)
            
        query += " ORDER BY e.tarih DESC"
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def etkinlik_getir(self, etkinlik_id: int) -> Optional[Dict]:
        """Tek etkinlik getir"""
        self.db.cursor.execute("""
            SELECT e.*, u.ad_soyad as sorumlu_adi
            FROM etkinlikler e
            LEFT JOIN uyeler u ON e.sorumlu_uye_id = u.uye_id
            WHERE e.etkinlik_id = ?
        """, (etkinlik_id,))
        result = self.db.cursor.fetchone()
        return dict(result) if result else None
    
    def katilimci_ekle(self, etkinlik_id: int, uye_id: int = None, 
                       katilimci_adi: str = "", kisi_sayisi: int = 1,
                       katilim_durumu: str = "Katılacak", notlar: str = "") -> int:
        """Etkinliğe katılımcı ekle"""
        self.db.cursor.execute("""
            INSERT INTO etkinlik_katilimcilari 
            (etkinlik_id, uye_id, katilimci_adi, kisi_sayisi, katilim_durumu, notlar)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (etkinlik_id, uye_id, katilimci_adi, kisi_sayisi, katilim_durumu, notlar))
        self.db.commit()
        
        # Katılımcı sayısını güncelle
        self._katilimci_sayisi_guncelle(etkinlik_id)
        return self.db.cursor.lastrowid
    
    def _katilimci_sayisi_guncelle(self, etkinlik_id: int):
        """Etkinlik katılımcı sayısını güncelle"""
        self.db.cursor.execute("""
            SELECT COALESCE(SUM(kisi_sayisi), 0) as toplam
            FROM etkinlik_katilimcilari
            WHERE etkinlik_id = ? AND katilim_durumu IN ('Katılacak', 'Katıldı')
        """, (etkinlik_id,))
        toplam = self.db.cursor.fetchone()['toplam']
        
        self.db.cursor.execute("""
            UPDATE etkinlikler SET katilimci_sayisi = ? WHERE etkinlik_id = ?
        """, (toplam, etkinlik_id))
        self.db.commit()
    
    def katilimci_listesi(self, etkinlik_id: int) -> List[Dict]:
        """Etkinlik katılımcıları"""
        self.db.cursor.execute("""
            SELECT ek.*, u.ad_soyad as uye_adi
            FROM etkinlik_katilimcilari ek
            LEFT JOIN uyeler u ON ek.uye_id = u.uye_id
            WHERE ek.etkinlik_id = ?
            ORDER BY ek.katilim_id
        """, (etkinlik_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]


# ========================================
# TOPLANTI YÖNETİMİ
# ========================================

class ToplantiYoneticisi:
    """Toplantı yönetimi"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def toplanti_ekle(self, toplanti_turu: str, baslik: str, tarih: str,
                      saat: str = "", mekan: str = "", gundem: str = "",
                      katilimcilar: str = "") -> int:
        """Yeni toplantı ekle"""
        self.db.cursor.execute("""
            INSERT INTO toplantilar 
            (toplanti_turu, baslik, tarih, saat, mekan, gundem, katilimcilar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (toplanti_turu, baslik, tarih, saat, mekan, gundem, katilimcilar))
        self.db.commit()
        return self.db.cursor.lastrowid
    
    def toplanti_guncelle(self, toplanti_id: int, **kwargs):
        """Toplantı güncelle"""
        updates = []
        values = []
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            values.append(value)
        
        if updates:
            values.append(toplanti_id)
            self.db.cursor.execute(f"""
                UPDATE toplantilar SET {', '.join(updates)} WHERE toplanti_id = ?
            """, values)
            self.db.commit()
    
    def toplanti_sil(self, toplanti_id: int):
        """Toplantı sil"""
        self.db.cursor.execute("DELETE FROM toplantilar WHERE toplanti_id = ?", (toplanti_id,))
        self.db.commit()
    
    def toplanti_listesi(self, toplanti_turu: str = None) -> List[Dict]:
        """Toplantı listesi"""
        query = "SELECT * FROM toplantilar WHERE 1=1"
        params = []
        
        if toplanti_turu:
            query += " AND toplanti_turu = ?"
            params.append(toplanti_turu)
            
        query += " ORDER BY tarih DESC"
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def toplanti_getir(self, toplanti_id: int) -> Optional[Dict]:
        """Tek toplantı getir"""
        self.db.cursor.execute("SELECT * FROM toplantilar WHERE toplanti_id = ?", (toplanti_id,))
        result = self.db.cursor.fetchone()
        return dict(result) if result else None


# ========================================
# BÜTÇE YÖNETİMİ
# ========================================

class ButceYoneticisi:
    """Bütçe planlama yönetimi"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def butce_ekle(self, yil: int, kategori: str, tur: str, 
                   planlanan_tutar: float, ay: int = None, aciklama: str = "") -> int:
        """Bütçe kalemi ekle"""
        try:
            self.db.cursor.execute("""
                INSERT INTO butce_planlari (yil, ay, kategori, tur, planlanan_tutar, aciklama)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (yil, ay, kategori, tur, planlanan_tutar, aciklama))
            self.db.commit()
            return self.db.cursor.lastrowid
        except:
            return -1
    
    def butce_guncelle(self, butce_id: int, planlanan_tutar: float = None, 
                       gerceklesen_tutar: float = None, aciklama: str = None):
        """Bütçe güncelle"""
        updates = []
        values = []
        
        if planlanan_tutar is not None:
            updates.append("planlanan_tutar = ?")
            values.append(planlanan_tutar)
        if gerceklesen_tutar is not None:
            updates.append("gerceklesen_tutar = ?")
            values.append(gerceklesen_tutar)
        if aciklama is not None:
            updates.append("aciklama = ?")
            values.append(aciklama)
        
        if updates:
            values.append(butce_id)
            self.db.cursor.execute(f"""
                UPDATE butce_planlari SET {', '.join(updates)} WHERE butce_id = ?
            """, values)
            self.db.commit()
    
    def butce_listesi(self, yil: int, ay: int = None) -> List[Dict]:
        """Bütçe listesi"""
        query = "SELECT * FROM butce_planlari WHERE yil = ?"
        params = [yil]
        
        if ay:
            query += " AND ay = ?"
            params.append(ay)
        else:
            query += " AND ay IS NULL"
            
        query += " ORDER BY tur, kategori"
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def butce_ozeti(self, yil: int) -> Dict:
        """Yıllık bütçe özeti"""
        self.db.cursor.execute("""
            SELECT 
                SUM(CASE WHEN tur = 'GELİR' THEN planlanan_tutar ELSE 0 END) as planlanan_gelir,
                SUM(CASE WHEN tur = 'GİDER' THEN planlanan_tutar ELSE 0 END) as planlanan_gider,
                SUM(CASE WHEN tur = 'GELİR' THEN gerceklesen_tutar ELSE 0 END) as gerceklesen_gelir,
                SUM(CASE WHEN tur = 'GİDER' THEN gerceklesen_tutar ELSE 0 END) as gerceklesen_gider
            FROM butce_planlari
            WHERE yil = ?
        """, (yil,))
        result = self.db.cursor.fetchone()
        return dict(result) if result else {}


# ========================================
# BELGE YÖNETİMİ
# ========================================

class BelgeYoneticisi:
    """Belge/dosya yönetimi"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def belge_ekle(self, belge_turu: str, baslik: str, dosya_adi: str, 
                   dosya_yolu: str, dosya_boyutu: int = 0,
                   ilgili_tablo: str = None, ilgili_kayit_id: int = None,
                   aciklama: str = "", yukleyen_kullanici_id: int = None) -> int:
        """Yeni belge ekle"""
        self.db.cursor.execute("""
            INSERT INTO belgeler 
            (belge_turu, baslik, dosya_adi, dosya_yolu, dosya_boyutu,
             ilgili_tablo, ilgili_kayit_id, aciklama, yukleyen_kullanici_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (belge_turu, baslik, dosya_adi, dosya_yolu, dosya_boyutu,
              ilgili_tablo, ilgili_kayit_id, aciklama, yukleyen_kullanici_id))
        self.db.commit()
        return self.db.cursor.lastrowid
    
    def belge_sil(self, belge_id: int) -> str:
        """Belge sil ve dosya yolunu döndür"""
        self.db.cursor.execute("SELECT dosya_yolu FROM belgeler WHERE belge_id = ?", (belge_id,))
        result = self.db.cursor.fetchone()
        dosya_yolu = result['dosya_yolu'] if result else None
        
        self.db.cursor.execute("DELETE FROM belgeler WHERE belge_id = ?", (belge_id,))
        self.db.commit()
        return dosya_yolu
    
    def belge_listesi(self, ilgili_tablo: str = None, ilgili_kayit_id: int = None,
                      belge_turu: str = None) -> List[Dict]:
        """Belge listesi"""
        query = "SELECT * FROM belgeler WHERE 1=1"
        params = []
        
        if ilgili_tablo:
            query += " AND ilgili_tablo = ?"
            params.append(ilgili_tablo)
        if ilgili_kayit_id:
            query += " AND ilgili_kayit_id = ?"
            params.append(ilgili_kayit_id)
        if belge_turu:
            query += " AND belge_turu = ?"
            params.append(belge_turu)
            
        query += " ORDER BY olusturma_tarihi DESC"
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]


# ========================================
# ALACAK-VERECEK YÖNETİMİ
# ========================================

class AlacakYoneticisi:
    """Alacak takip yöneticisi"""
    
    def __init__(self, db: Database):
        self.db = db
        from models import GelirYoneticisi
        self.gelir_yoneticisi = GelirYoneticisi(db)
    
    def alacak_ekle(self, alacak_turu: str, aciklama: str, kisi_kurum: str,
                    toplam_tutar: float, para_birimi: str = 'TRY',
                    alacak_tarihi: str = None, vade_tarihi: str = None,
                    ilk_tahsilat: float = 0, kasa_id: int = None,
                    kisi_telefon: str = "", kisi_adres: str = "",
                    uye_id: int = None, senet_no: str = "",
                    notlar: str = "", kullanici_id: int = None) -> int:
        """Yeni alacak ekle"""
        if alacak_tarihi is None:
            alacak_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        kalan = toplam_tutar - ilk_tahsilat
        durum = 'Kısmi' if ilk_tahsilat > 0 else 'Bekliyor'
        
        self.db.cursor.execute("""
            INSERT INTO alacaklar 
            (alacak_turu, aciklama, kisi_kurum, kisi_telefon, kisi_adres,
             uye_id, toplam_tutar, tahsil_edilen, kalan_tutar, para_birimi,
             alacak_tarihi, vade_tarihi, durum, senet_no, notlar, kullanici_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (alacak_turu, aciklama, kisi_kurum, kisi_telefon, kisi_adres,
              uye_id, toplam_tutar, ilk_tahsilat, kalan, para_birimi,
              alacak_tarihi, vade_tarihi, durum, senet_no, notlar, kullanici_id))
        
        alacak_id = self.db.cursor.lastrowid
        
        # İlk tahsilat varsa kaydet
        if ilk_tahsilat > 0 and kasa_id:
            self.tahsilat_ekle(alacak_id, ilk_tahsilat, kasa_id, alacak_tarihi,
                              aciklama=f"İlk tahsilat - {aciklama}")
        
        self.db.commit()
        return alacak_id
    
    def tahsilat_ekle(self, alacak_id: int, tutar: float, kasa_id: int,
                      tahsilat_tarihi: str = None, odeme_sekli: str = 'Nakit',
                      aciklama: str = "", kullanici_id: int = None) -> int:
        """Alacak tahsilatı ekle"""
        if tahsilat_tarihi is None:
            tahsilat_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        # Alacak bilgisini al
        self.db.cursor.execute("SELECT * FROM alacaklar WHERE id=?", (alacak_id,))
        alacak = dict(self.db.cursor.fetchone())
        
        # Gelir kaydı oluştur
        gelir_id = self.gelir_yoneticisi.gelir_ekle(
            gelir_turu='DİĞER',
            tutar=tutar,
            kasa_id=kasa_id,
            aciklama=f"Alacak Tahsilatı: {alacak['kisi_kurum']} - {alacak['aciklama']}",
            gelir_tarihi=tahsilat_tarihi
        )
        
        # Tahsilat kaydı
        self.db.cursor.execute("""
            INSERT INTO alacak_tahsilatlari
            (alacak_id, tutar, para_birimi, tahsilat_tarihi, kasa_id,
             gelir_id, odeme_sekli, aciklama, kullanici_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (alacak_id, tutar, alacak['para_birimi'], tahsilat_tarihi,
              kasa_id, gelir_id, odeme_sekli, aciklama, kullanici_id))
        
        tahsilat_id = self.db.cursor.lastrowid
        
        # Alacak bilgisini güncelle
        yeni_tahsil = alacak['tahsil_edilen'] + tutar
        yeni_kalan = alacak['toplam_tutar'] - yeni_tahsil
        
        if yeni_kalan <= 0:
            durum = 'Tahsil Edildi'
        elif yeni_tahsil > 0:
            durum = 'Kısmi'
        else:
            durum = 'Bekliyor'
        
        self.db.cursor.execute("""
            UPDATE alacaklar
            SET tahsil_edilen = ?,
                kalan_tutar = ?,
                durum = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (yeni_tahsil, yeni_kalan, durum, alacak_id))
        
        self.db.commit()
        return tahsilat_id
    
    def alacak_iptal(self, alacak_id: int, iade_tutari: float = 0,
                     kasa_id: int = None, aciklama: str = "") -> bool:
        """Alacağı iptal et"""
        if iade_tutari > 0 and kasa_id:
            # İade gideri
            from models import GiderYoneticisi
            gider_yoneticisi = GiderYoneticisi(self.db)
            gider_yoneticisi.gider_ekle(
                gider_turu='DİĞER',
                tutar=iade_tutari,
                kasa_id=kasa_id,
                aciklama=f"Alacak iadesi - {aciklama}",
                gider_tarihi=datetime.now().strftime("%Y-%m-%d")
            )
        
        self.db.cursor.execute("""
            UPDATE alacaklar
            SET durum = 'İptal',
                notlar = COALESCE(notlar || ' | ', '') || 'İPTAL: ' || ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (aciklama, alacak_id))
        
        self.db.commit()
        return True
    
    def alacak_guncelle(self, alacak_id: int, **kwargs) -> bool:
        """Alacak bilgilerini güncelle"""
        guncellenebilir = ['alacak_turu', 'aciklama', 'kisi_kurum', 'kisi_telefon',
                           'kisi_adres', 'vade_tarihi', 'senet_no', 'notlar']
        
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in guncellenebilir:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        updates.append("guncelleme_tarihi = CURRENT_TIMESTAMP")
        values.append(alacak_id)
        
        query = f"UPDATE alacaklar SET {', '.join(updates)} WHERE id = ?"
        self.db.cursor.execute(query, values)
        self.db.commit()
        return True
    
    def liste_getir(self, durum: str = None, vade_gecmis: bool = False,
                    uye_id: int = None) -> List[Dict]:
        """Alacak listesi"""
        query = "SELECT * FROM alacaklar WHERE 1=1"
        params = []
        
        if durum:
            query += " AND durum = ?"
            params.append(durum)
        
        if vade_gecmis:
            query += " AND vade_tarihi < date('now') AND durum NOT IN ('Tahsil Edildi', 'İptal')"
        
        if uye_id:
            query += " AND uye_id = ?"
            params.append(uye_id)
        
        query += " ORDER BY alacak_tarihi DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def ozet(self) -> Dict:
        """Alacak özeti"""
        self.db.cursor.execute("""
            SELECT 
                COUNT(*) as toplam_alacak,
                SUM(CASE WHEN durum='Bekliyor' THEN 1 ELSE 0 END) as bekleyen,
                SUM(CASE WHEN durum='Kısmi' THEN 1 ELSE 0 END) as kismi,
                SUM(CASE WHEN durum='Tahsil Edildi' THEN 1 ELSE 0 END) as tahsil_edildi,
                COALESCE(SUM(kalan_tutar), 0) as toplam_kalan_tutar,
                COALESCE(SUM(tahsil_edilen), 0) as toplam_tahsil_edilen,
                COALESCE(SUM(CASE WHEN vade_tarihi < date('now') AND durum NOT IN ('Tahsil Edildi', 'İptal')
                    THEN kalan_tutar ELSE 0 END), 0) as vade_gecmis_tutar,
                SUM(CASE WHEN vade_tarihi < date('now') AND durum NOT IN ('Tahsil Edildi', 'İptal')
                    THEN 1 ELSE 0 END) as vade_gecmis_adet
            FROM alacaklar
            WHERE durum != 'İptal'
        """)
        
        return dict(self.db.cursor.fetchone())
    
    def tahsilat_gecmisi(self, alacak_id: int) -> List[Dict]:
        """Bir alacağın tahsilat geçmişi"""
        self.db.cursor.execute("""
            SELECT t.*, k.kasa_adi
            FROM alacak_tahsilatlari t
            LEFT JOIN kasalar k ON t.kasa_id = k.kasa_id
            WHERE t.alacak_id = ?
            ORDER BY t.tahsilat_tarihi DESC
        """, (alacak_id,))
        
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def alacak_detay(self, alacak_id: int) -> Dict:
        """Alacak detayı (tahsilatlar dahil)"""
        self.db.cursor.execute("""
            SELECT a.*, u.ad_soyad as uye_adi
            FROM alacaklar a
            LEFT JOIN uyeler u ON a.uye_id = u.uye_id
            WHERE a.id = ?
        """, (alacak_id,))
        
        alacak = dict(self.db.cursor.fetchone())
        alacak['tahsilatlar'] = self.tahsilat_gecmisi(alacak_id)
        return alacak


class VerecekYoneticisi:
    """Verecek (borç) takip yöneticisi"""
    
    def __init__(self, db: Database):
        self.db = db
        from models import GiderYoneticisi
        self.gider_yoneticisi = GiderYoneticisi(db)
    
    def verecek_ekle(self, verecek_turu: str, aciklama: str, kisi_kurum: str,
                     toplam_tutar: float, para_birimi: str = 'TRY',
                     verecek_tarihi: str = None, vade_tarihi: str = None,
                     kisi_telefon: str = "", kisi_adres: str = "",
                     fatura_no: str = "", notlar: str = "",
                     kullanici_id: int = None) -> int:
        """Yeni borç ekle"""
        if verecek_tarihi is None:
            verecek_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        self.db.cursor.execute("""
            INSERT INTO verecekler
            (verecek_turu, aciklama, kisi_kurum, kisi_telefon, kisi_adres,
             toplam_tutar, odenen, kalan_tutar, para_birimi, verecek_tarihi,
             vade_tarihi, durum, fatura_no, notlar, kullanici_id)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 'Bekliyor', ?, ?, ?)
        """, (verecek_turu, aciklama, kisi_kurum, kisi_telefon, kisi_adres,
              toplam_tutar, toplam_tutar, para_birimi, verecek_tarihi,
              vade_tarihi, fatura_no, notlar, kullanici_id))
        
        verecek_id = self.db.cursor.lastrowid
        self.db.commit()
        return verecek_id
    
    def odeme_yap(self, verecek_id: int, tutar: float, kasa_id: int,
                  odeme_tarihi: str = None, odeme_sekli: str = 'Nakit',
                  aciklama: str = "", kullanici_id: int = None) -> int:
        """Borç ödemesi yap"""
        if odeme_tarihi is None:
            odeme_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        # Verecek bilgisini al
        self.db.cursor.execute("SELECT * FROM verecekler WHERE id=?", (verecek_id,))
        verecek = dict(self.db.cursor.fetchone())
        
        # Gider kaydı oluştur
        gider_id = self.gider_yoneticisi.gider_ekle(
            gider_turu='DİĞER',
            tutar=tutar,
            kasa_id=kasa_id,
            aciklama=f"Borç Ödemesi: {verecek['kisi_kurum']} - {verecek['aciklama']}",
            gider_tarihi=odeme_tarihi
        )
        
        # Ödeme kaydı
        self.db.cursor.execute("""
            INSERT INTO verecek_odemeleri
            (verecek_id, tutar, para_birimi, odeme_tarihi, kasa_id,
             gider_id, odeme_sekli, aciklama, kullanici_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (verecek_id, tutar, verecek['para_birimi'], odeme_tarihi,
              kasa_id, gider_id, odeme_sekli, aciklama, kullanici_id))
        
        odeme_id = self.db.cursor.lastrowid
        
        # Verecek bilgisini güncelle
        yeni_odenen = verecek['odenen'] + tutar
        yeni_kalan = verecek['toplam_tutar'] - yeni_odenen
        
        if yeni_kalan <= 0:
            durum = 'Ödendi'
        elif yeni_odenen > 0:
            durum = 'Kısmi'
        else:
            durum = 'Bekliyor'
        
        self.db.cursor.execute("""
            UPDATE verecekler
            SET odenen = ?,
                kalan_tutar = ?,
                durum = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (yeni_odenen, yeni_kalan, durum, verecek_id))
        
        self.db.commit()
        return odeme_id
    
    def verecek_iptal(self, verecek_id: int, aciklama: str = "") -> bool:
        """Verece iptal et"""
        self.db.cursor.execute("""
            UPDATE verecekler
            SET durum = 'İptal',
                notlar = COALESCE(notlar || ' | ', '') || 'İPTAL: ' || ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (aciklama, verecek_id))
        
        self.db.commit()
        return True
    
    def verecek_guncelle(self, verecek_id: int, **kwargs) -> bool:
        """Verecek bilgilerini güncelle"""
        guncellenebilir = ['verecek_turu', 'aciklama', 'kisi_kurum', 'kisi_telefon',
                           'kisi_adres', 'vade_tarihi', 'fatura_no', 'notlar']
        
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in guncellenebilir:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        updates.append("guncelleme_tarihi = CURRENT_TIMESTAMP")
        values.append(verecek_id)
        
        query = f"UPDATE verecekler SET {', '.join(updates)} WHERE id = ?"
        self.db.cursor.execute(query, values)
        self.db.commit()
        return True
    
    def liste_getir(self, durum: str = None, vade_gecmis: bool = False) -> List[Dict]:
        """Verecek listesi"""
        query = "SELECT * FROM verecekler WHERE 1=1"
        params = []
        
        if durum:
            query += " AND durum = ?"
            params.append(durum)
        
        if vade_gecmis:
            query += " AND vade_tarihi < date('now') AND durum NOT IN ('Ödendi', 'İptal')"
        
        query += " ORDER BY verecek_tarihi DESC"
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def ozet(self) -> Dict:
        """Verecek özeti"""
        self.db.cursor.execute("""
            SELECT 
                COUNT(*) as toplam_verecek,
                SUM(CASE WHEN durum='Bekliyor' THEN 1 ELSE 0 END) as bekleyen,
                SUM(CASE WHEN durum='Kısmi' THEN 1 ELSE 0 END) as kismi,
                SUM(CASE WHEN durum='Ödendi' THEN 1 ELSE 0 END) as odendi,
                COALESCE(SUM(kalan_tutar), 0) as toplam_kalan_tutar,
                COALESCE(SUM(odenen), 0) as toplam_odenen,
                COALESCE(SUM(CASE WHEN vade_tarihi < date('now') AND durum NOT IN ('Ödendi', 'İptal')
                    THEN kalan_tutar ELSE 0 END), 0) as vade_gecmis_tutar,
                SUM(CASE WHEN vade_tarihi < date('now') AND durum NOT IN ('Ödendi', 'İptal')
                    THEN 1 ELSE 0 END) as vade_gecmis_adet
            FROM verecekler
            WHERE durum != 'İptal'
        """)
        
        return dict(self.db.cursor.fetchone())
    
    def odeme_gecmisi(self, verecek_id: int) -> List[Dict]:
        """Bir verecek'in ödeme geçmişi"""
        self.db.cursor.execute("""
            SELECT o.*, k.kasa_adi
            FROM verecek_odemeleri o
            LEFT JOIN kasalar k ON o.kasa_id = k.kasa_id
            WHERE o.verecek_id = ?
            ORDER BY o.odeme_tarihi DESC
        """, (verecek_id,))
        
        return [dict(row) for row in self.db.cursor.fetchall()]
    
    def verecek_detay(self, verecek_id: int) -> Dict:
        """Verecek detayı (ödemeler dahil)"""
        self.db.cursor.execute("SELECT * FROM verecekler WHERE id = ?", (verecek_id,))
        verecek = dict(self.db.cursor.fetchone())
        verecek['odemeler'] = self.odeme_gecmisi(verecek_id)
        return verecek
