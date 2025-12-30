"""
BADER Derneği - E-posta Servisi
Aidat hatırlatma, duyuru gönderme
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from database import Database
from datetime import datetime
import os


class EmailConfig:
    """E-posta sunucu yapılandırması"""
    
    def __init__(self, db: Database):
        self.db = db
        self.smtp_server = ""
        self.smtp_port = 587
        self.smtp_user = ""
        self.smtp_password = ""
        self.sender_name = "BADER Derneği"
        self.sender_email = ""
        self.load_config()
        
    def load_config(self):
        """Veritabanından e-posta ayarlarını yükle"""
        try:
            self.db.cursor.execute("SELECT ayar_adi, ayar_degeri FROM ayarlar")
            for row in self.db.cursor.fetchall():
                if row['ayar_adi'] == 'smtp_server':
                    self.smtp_server = row['ayar_degeri']
                elif row['ayar_adi'] == 'smtp_port':
                    self.smtp_port = int(row['ayar_degeri']) if row['ayar_degeri'] else 587
                elif row['ayar_adi'] == 'smtp_user':
                    self.smtp_user = row['ayar_degeri']
                elif row['ayar_adi'] == 'smtp_password':
                    self.smtp_password = row['ayar_degeri']
                elif row['ayar_adi'] == 'dernek_adi':
                    self.sender_name = row['ayar_degeri']
                elif row['ayar_adi'] == 'dernek_email':
                    self.sender_email = row['ayar_degeri']
        except Exception as e:
            print(f"E-posta ayarları yüklenemedi: {e}")
            
    def is_configured(self) -> bool:
        """E-posta yapılandırması yapılmış mı?"""
        return all([self.smtp_server, self.smtp_user, self.smtp_password, self.sender_email])
    
    def save_config(self, server: str, port: int, user: str, password: str, email: str):
        """E-posta ayarlarını kaydet"""
        settings = [
            ('smtp_server', server),
            ('smtp_port', str(port)),
            ('smtp_user', user),
            ('smtp_password', password),
            ('dernek_email', email)
        ]
        
        for name, value in settings:
            self.db.cursor.execute("""
                INSERT OR REPLACE INTO ayarlar (ayar_adi, ayar_degeri)
                VALUES (?, ?)
            """, (name, value))
        
        self.db.commit()
        self.load_config()


class EmailService:
    """E-posta gönderme servisi"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        
    def send_email(self, to_email: str, subject: str, body_html: str, 
                   attachments: List[str] = None) -> tuple[bool, str]:
        """E-posta gönder"""
        
        if not self.config.is_configured():
            return False, "E-posta yapılandırması eksik!"
        
        try:
            # Mesaj oluştur
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.sender_name} <{self.config.sender_email}>"
            msg['To'] = to_email
            
            # HTML içerik
            html_part = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Ekler
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(filepath)
                            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                            msg.attach(part)
            
            # Gönder
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)
            
            return True, "E-posta başarıyla gönderildi"
            
        except smtplib.SMTPAuthenticationError:
            return False, "E-posta kimlik doğrulama hatası!"
        except smtplib.SMTPConnectError:
            return False, "E-posta sunucusuna bağlanılamadı!"
        except Exception as e:
            return False, f"E-posta gönderim hatası: {str(e)}"
    
    def send_bulk(self, recipients: List[Dict], subject: str, body_template: str) -> Dict:
        """Toplu e-posta gönder"""
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        for r in recipients:
            email = r.get('email')
            if not email:
                continue
                
            # Şablonda değişkenleri değiştir
            body = body_template
            for key, value in r.items():
                body = body.replace(f'{{{{{key}}}}}', str(value) if value else '')
            
            success, msg = self.send_email(email, subject, body)
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"{email}: {msg}")
        
        return results


class EmailTemplates:
    """E-posta şablonları"""
    
    @staticmethod
    def aidat_hatirlatma(dernek_adi: str, ad_soyad: str, yil: int, 
                         toplam_borc: float, son_odeme: str = None) -> str:
        """Aidat hatırlatma e-postası"""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #64B5F6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .amount {{ font-size: 24px; color: #f44336; font-weight: bold; }}
                .footer {{ padding: 15px; text-align: center; color: #888; font-size: 12px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #64B5F6; color: white; 
                       text-decoration: none; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{dernek_adi}</h1>
                </div>
                <div class="content">
                    <p>Sayın <strong>{ad_soyad}</strong>,</p>
                    
                    <p>{yil} yılına ait aidat borcunuzun ödenmediğini hatırlatmak isteriz.</p>
                    
                    <p><span class="amount">Toplam Borç: {toplam_borc:,.2f} ₺</span></p>
                    
                    {f'<p>Son ödeme tarihiniz: {son_odeme}</p>' if son_odeme else ''}
                    
                    <p>Aidat ödemelerinizi dernek merkezimize uğrayarak veya banka havalesi ile 
                       yapabilirsiniz.</p>
                    
                    <p>Sorularınız için bizimle iletişime geçebilirsiniz.</p>
                    
                    <p>Saygılarımızla,<br>
                    <strong>{dernek_adi} Yönetimi</strong></p>
                </div>
                <div class="footer">
                    <p>Bu e-posta {dernek_adi} tarafından gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def odeme_teshektur(dernek_adi: str, ad_soyad: str, tutar: float, tarih: str) -> str:
        """Ödeme teşekkür e-postası"""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .amount {{ font-size: 24px; color: #4CAF50; font-weight: bold; }}
                .footer {{ padding: 15px; text-align: center; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✓ Ödeme Alındı</h1>
                </div>
                <div class="content">
                    <p>Sayın <strong>{ad_soyad}</strong>,</p>
                    
                    <p>Ödemeniz başarıyla alınmıştır.</p>
                    
                    <table style="width:100%; margin: 20px 0;">
                        <tr>
                            <td><strong>Ödeme Tutarı:</strong></td>
                            <td class="amount">{tutar:,.2f} ₺</td>
                        </tr>
                        <tr>
                            <td><strong>Ödeme Tarihi:</strong></td>
                            <td>{tarih}</td>
                        </tr>
                    </table>
                    
                    <p>Desteğiniz için teşekkür ederiz!</p>
                    
                    <p>Saygılarımızla,<br>
                    <strong>{dernek_adi} Yönetimi</strong></p>
                </div>
                <div class="footer">
                    <p>Bu e-posta {dernek_adi} tarafından gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def duyuru(dernek_adi: str, baslik: str, icerik: str) -> str:
        """Genel duyuru e-postası"""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #64B5F6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 15px; text-align: center; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{dernek_adi}</h1>
                    <h2>{baslik}</h2>
                </div>
                <div class="content">
                    {icerik}
                </div>
                <div class="footer">
                    <p>Bu e-posta {dernek_adi} tarafından gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def etkinlik_davet(dernek_adi: str, ad_soyad: str, etkinlik_adi: str,
                       tarih: str, saat: str, mekan: str, aciklama: str = "") -> str:
        """Etkinlik davet e-postası"""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .event-details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .footer {{ padding: 15px; text-align: center; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Etkinlik Daveti</h1>
                    <h2>{etkinlik_adi}</h2>
                </div>
                <div class="content">
                    <p>Sayın <strong>{ad_soyad}</strong>,</p>
                    
                    <p>Derneğimizin düzenlediği etkinliğe sizi de bekliyoruz!</p>
                    
                    <div class="event-details">
                        <p>📅 <strong>Tarih:</strong> {tarih}</p>
                        <p>⏰ <strong>Saat:</strong> {saat}</p>
                        <p>📍 <strong>Mekan:</strong> {mekan}</p>
                        {f'<p>📝 {aciklama}</p>' if aciklama else ''}
                    </div>
                    
                    <p>Katılımınızı bekliyoruz!</p>
                    
                    <p>Saygılarımızla,<br>
                    <strong>{dernek_adi} Yönetimi</strong></p>
                </div>
                <div class="footer">
                    <p>Bu e-posta {dernek_adi} tarafından gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """


