"""
BADER OCR Servisi - PaddleOCR Entegrasyonu
==========================================

Bu modül belge tarama ve metin çıkarma işlemlerini yönetir.
Sunucu bilgisi sonradan yapılandırılabilir.

Kullanım:
    from ocr_service import OCRService
    
    service = OCRService()
    result = service.process_image(image_path)
"""

import re
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# PaddleOCR lazy import - sunucu modu kullanılırsa gerekmez
_paddle_ocr = None


class OCRMode(Enum):
    """OCR çalışma modu"""
    LOCAL = "local"       # Yerelde PaddleOCR çalıştır
    SERVER = "server"     # Uzak sunucuya istek gönder


@dataclass
class OCRConfig:
    """OCR yapılandırması"""
    mode: OCRMode = OCRMode.SERVER      # Varsayılan: Sunucu modu
    server_url: str = "http://157.90.154.48:8080/api"  # BADER API Sunucusu
    server_api_key: str = ""           # API anahtarı (müşteriye özel)
    language: str = "tr"           # Dil: tr, en, ch
    use_gpu: bool = False          # GPU kullanımı
    det_model_dir: str = ""        # Detection model path
    rec_model_dir: str = ""        # Recognition model path
    timeout: int = 30              # İstek timeout (saniye)


@dataclass
class DocumentField:
    """Belgeden çıkarılan alan"""
    field_name: str       # Alan adı: tutar, tarih, aciklama, vb.
    value: str            # Ham değer
    parsed_value: Any     # İşlenmiş değer
    confidence: float     # Güven skoru (0-1)
    bbox: Optional[List[int]] = None  # Bounding box [x1, y1, x2, y2]


@dataclass 
class OCRResult:
    """OCR sonucu"""
    success: bool
    raw_text: str                          # Ham OCR çıktısı
    lines: List[str]                       # Satır satır metin
    fields: List[DocumentField]            # Çıkarılan alanlar
    document_type: Optional[str] = None    # Tespit edilen belge tipi
    confidence: float = 0.0                # Genel güven skoru
    error_message: str = ""
    processing_time: float = 0.0           # İşlem süresi (saniye)


class TurkishPatterns:
    """Türkçe belge desenleri"""
    
    # Para tutarı desenleri
    AMOUNT_PATTERNS = [
        r'(?:toplam|tutar|bedel|ücret|fiyat|amount|total)\s*[:\s]*([0-9.,]+)\s*(?:TL|₺|TRY)?',
        r'([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2})?)\s*(?:TL|₺|TRY)',
        r'(?:TL|₺|TRY)\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2})?)',
        r'TOPLAM\s*[:\s]*([0-9.,]+)',
        r'GENEL TOPLAM\s*[:\s]*([0-9.,]+)',
    ]
    
    # Tarih desenleri
    DATE_PATTERNS = [
        r'(\d{2})[./](\d{2})[./](\d{4})',  # 25.12.2024 veya 25/12/2024
        r'(\d{4})[./\-](\d{2})[./\-](\d{2})',  # 2024-12-25
        r'(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+(\d{4})',
    ]
    
    # IBAN deseni
    IBAN_PATTERN = r'TR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}'
    
    # Vergi numarası deseni
    TAX_NUMBER_PATTERN = r'(?:V\.?D\.?|Vergi\s*(?:No|Dairesi)?)\s*[:\s]*(\d{10,11})'
    
    # Fiş/Fatura numarası
    RECEIPT_NUMBER_PATTERNS = [
        r'(?:Fiş|Fatura|Dekont)\s*(?:No|Numarası)?\s*[:\s]*([A-Z0-9\-]+)',
        r'(?:No|Number)\s*[:\s]*([A-Z0-9\-]+)',
    ]
    
    # Belge tipi anahtar kelimeleri
    DOCUMENT_KEYWORDS = {
        'fatura': ['fatura', 'invoice', 'satış faturası', 'e-fatura'],
        'fiş': ['fiş', 'yazar kasa', 'pos', 'slip', 'receipt'],
        'dekont': ['dekont', 'banka dekontu', 'havale', 'eft', 'transfer'],
        'makbuz': ['makbuz', 'tahsilat', 'ödeme makbuzu'],
        'aidat': ['aidat', 'üyelik', 'yıllık aidat', 'aylık aidat'],
    }
    
    # Ay isimleri (Türkçe -> sayı)
    MONTHS_TR = {
        'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
        'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
        'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
    }


class OCRService:
    """PaddleOCR tabanlı OCR servisi"""
    
    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self._ocr_engine = None
        self._patterns = TurkishPatterns()
    
    def _init_local_ocr(self):
        """Yerel PaddleOCR motorunu başlat"""
        global _paddle_ocr
        
        if self._ocr_engine is not None:
            return
        
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr = PaddleOCR
            
            # Türkçe için en uygun yapılandırma
            # PaddleOCR Türkçe'yi "tr" olarak destekler
            self._ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang='tr',  # Türkçe
                use_gpu=self.config.use_gpu,
                show_log=False,
                det_db_thresh=0.3,
                det_db_box_thresh=0.5,
            )
        except ImportError:
            raise ImportError(
                "PaddleOCR yüklü değil. Yüklemek için:\n"
                "pip install paddlepaddle paddleocr"
            )
    
    def _call_server_ocr(self, image_path: str) -> Dict[str, Any]:
        """Uzak sunucuya OCR isteği gönder"""
        import requests
        import os
        
        if not self.config.server_url:
            raise ValueError(
                "Sunucu URL'si yapılandırılmamış.\n"
                "OCRConfig.server_url değerini ayarlayın."
            )
        
        url = f"{self.config.server_url.rstrip('/')}/ocr"
        headers = {}
        
        if self.config.server_api_key:
            headers['Authorization'] = f"Bearer {self.config.server_api_key}"
        
        filename = os.path.basename(image_path)
        with open(image_path, 'rb') as f:
            files = {'image': (filename, f, 'image/jpeg')}
            response = requests.post(
                url,
                files=files,
                headers=headers,
                timeout=self.config.timeout
            )
        
        response.raise_for_status()
        return response.json()
    
    def process_image(self, image_path: str) -> OCRResult:
        """
        Görüntüyü işle ve OCR sonucunu döndür
        
        Args:
            image_path: Görüntü dosyası yolu
            
        Returns:
            OCRResult: OCR sonucu
        """
        import time
        start_time = time.time()
        
        try:
            if self.config.mode == OCRMode.SERVER:
                # Sunucu modunda çalış
                server_result = self._call_server_ocr(image_path)
                raw_text = server_result.get('text', '')
                lines = server_result.get('lines', raw_text.split('\n'))
                confidence = server_result.get('confidence', 0.0)
            else:
                # Yerel modda çalış
                self._init_local_ocr()
                result = self._ocr_engine.ocr(image_path, cls=True)
                
                lines = []
                confidences = []
                
                if result and result[0]:
                    for line in result[0]:
                        text = line[1][0]
                        conf = line[1][1]
                        lines.append(text)
                        confidences.append(conf)
                
                raw_text = '\n'.join(lines)
                confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Alanları çıkar
            fields = self._extract_fields(raw_text, lines)
            
            # Belge tipini tespit et
            doc_type = self._detect_document_type(raw_text)
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                success=True,
                raw_text=raw_text,
                lines=lines,
                fields=fields,
                document_type=doc_type,
                confidence=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            return OCRResult(
                success=False,
                raw_text="",
                lines=[],
                fields=[],
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def process_image_bytes(self, image_bytes: bytes) -> OCRResult:
        """
        Bytes olarak gelen görüntüyü işle (Streamlit file uploader için)
        
        Args:
            image_bytes: Görüntü bytes
            
        Returns:
            OCRResult: OCR sonucu
        """
        import tempfile
        
        # Geçici dosyaya yaz
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            return self.process_image(tmp_path)
        finally:
            # Geçici dosyayı sil
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def _extract_fields(self, raw_text: str, lines: List[str]) -> List[DocumentField]:
        """Metinden alanları çıkar"""
        fields = []
        text_lower = raw_text.lower()
        
        # Tutar çıkar
        amount = self._extract_amount(raw_text)
        if amount:
            fields.append(DocumentField(
                field_name="tutar",
                value=amount[0],
                parsed_value=amount[1],
                confidence=0.8
            ))
        
        # Tarih çıkar
        date = self._extract_date(raw_text)
        if date:
            fields.append(DocumentField(
                field_name="tarih",
                value=date[0],
                parsed_value=date[1],
                confidence=0.85
            ))
        
        # IBAN çıkar
        iban = self._extract_iban(raw_text)
        if iban:
            fields.append(DocumentField(
                field_name="iban",
                value=iban,
                parsed_value=iban.replace(' ', ''),
                confidence=0.95
            ))
        
        # Vergi numarası çıkar
        tax_no = self._extract_tax_number(raw_text)
        if tax_no:
            fields.append(DocumentField(
                field_name="vergi_no",
                value=tax_no,
                parsed_value=tax_no,
                confidence=0.9
            ))
        
        # Fiş/Fatura numarası çıkar
        receipt_no = self._extract_receipt_number(raw_text)
        if receipt_no:
            fields.append(DocumentField(
                field_name="belge_no",
                value=receipt_no,
                parsed_value=receipt_no,
                confidence=0.85
            ))
        
        return fields
    
    def _extract_amount(self, text: str) -> Optional[Tuple[str, float]]:
        """Para tutarı çıkar"""
        for pattern in self._patterns.AMOUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_value = match.group(1)
                # Türkçe format: 1.234,56 -> 1234.56
                cleaned = raw_value.replace('.', '').replace(',', '.')
                try:
                    amount = float(cleaned)
                    return (raw_value, amount)
                except ValueError:
                    continue
        return None
    
    def _extract_date(self, text: str) -> Optional[Tuple[str, str]]:
        """Tarih çıkar ve ISO formatına dönüştür"""
        # Gün/Ay/Yıl formatı
        for pattern in self._patterns.DATE_PATTERNS[:2]:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    iso_date = f"{groups[0]}-{groups[1]}-{groups[2]}"
                else:  # DD.MM.YYYY
                    iso_date = f"{groups[2]}-{groups[1]}-{groups[0]}"
                return (match.group(0), iso_date)
        
        # Türkçe ay isimli format
        pattern = self._patterns.DATE_PATTERNS[2]
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))
            month = self._patterns.MONTHS_TR.get(month_name, 1)
            iso_date = f"{year}-{month:02d}-{day:02d}"
            return (match.group(0), iso_date)
        
        return None
    
    def _extract_iban(self, text: str) -> Optional[str]:
        """IBAN çıkar"""
        match = re.search(self._patterns.IBAN_PATTERN, text)
        return match.group(0) if match else None
    
    def _extract_tax_number(self, text: str) -> Optional[str]:
        """Vergi numarası çıkar"""
        match = re.search(self._patterns.TAX_NUMBER_PATTERN, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extract_receipt_number(self, text: str) -> Optional[str]:
        """Fiş/Fatura numarası çıkar"""
        for pattern in self._patterns.RECEIPT_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _detect_document_type(self, text: str) -> Optional[str]:
        """Belge tipini tespit et"""
        text_lower = text.lower()
        
        scores = {}
        for doc_type, keywords in self._patterns.DOCUMENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[doc_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def get_suggested_fields(self, document_type: str) -> Dict[str, Any]:
        """
        Belge tipine göre önerilen alanları döndür
        
        Args:
            document_type: Belge tipi (fatura, fiş, dekont, makbuz, aidat)
            
        Returns:
            Önerilen alanlar ve varsayılan değerler
        """
        suggestions = {
            'fatura': {
                'islem_tipi': 'gider',
                'kategori': 'Fatura Ödemesi',
                'required_fields': ['tutar', 'tarih', 'aciklama'],
                'optional_fields': ['belge_no', 'vergi_no']
            },
            'fiş': {
                'islem_tipi': 'gider',
                'kategori': 'Nakit Harcama',
                'required_fields': ['tutar', 'tarih'],
                'optional_fields': ['aciklama']
            },
            'dekont': {
                'islem_tipi': 'gider',  # veya gelir, kullanıcı seçer
                'kategori': 'Banka İşlemi',
                'required_fields': ['tutar', 'tarih', 'iban'],
                'optional_fields': ['aciklama', 'belge_no']
            },
            'makbuz': {
                'islem_tipi': 'gelir',
                'kategori': 'Tahsilat',
                'required_fields': ['tutar', 'tarih'],
                'optional_fields': ['aciklama', 'belge_no']
            },
            'aidat': {
                'islem_tipi': 'aidat',
                'kategori': 'Üye Aidatı',
                'required_fields': ['tutar', 'tarih', 'uye_bilgisi'],
                'optional_fields': ['donem']
            }
        }
        
        return suggestions.get(document_type, {
            'islem_tipi': 'gider',
            'kategori': 'Diğer',
            'required_fields': ['tutar', 'tarih'],
            'optional_fields': ['aciklama']
        })


# Yapılandırma dosyası yönetimi
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'ocr_config.json')


def load_ocr_config() -> OCRConfig:
    """Yapılandırma dosyasından ayarları yükle"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return OCRConfig(
                mode=OCRMode(data.get('mode', 'local')),
                server_url=data.get('server_url', ''),
                server_api_key=data.get('server_api_key', ''),
                language=data.get('language', 'tr'),
                use_gpu=data.get('use_gpu', False),
                timeout=data.get('timeout', 30)
            )
        except Exception:
            pass
    return OCRConfig()


def save_ocr_config(config: OCRConfig):
    """Yapılandırmayı dosyaya kaydet"""
    data = {
        'mode': config.mode.value,
        'server_url': config.server_url,
        'server_api_key': config.server_api_key,
        'language': config.language,
        'use_gpu': config.use_gpu,
        'timeout': config.timeout
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Singleton instance
_service_instance: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Tekil OCR servisi instance'ı döndür"""
    global _service_instance
    if _service_instance is None:
        config = load_ocr_config()
        _service_instance = OCRService(config)
    return _service_instance


def configure_server(url: str, api_key: str = ""):
    """
    Sunucu modunu yapılandır
    
    Kullanım:
        from ocr_service import configure_server
        configure_server("http://192.168.1.100:8000", "your-api-key")
    """
    global _service_instance
    
    config = OCRConfig(
        mode=OCRMode.SERVER,
        server_url=url,
        server_api_key=api_key
    )
    save_ocr_config(config)
    _service_instance = OCRService(config)
    
    return _service_instance


if __name__ == "__main__":
    # Test
    print("BADER OCR Servisi")
    print("=" * 40)
    
    config = load_ocr_config()
    print(f"Mod: {config.mode.value}")
    print(f"Sunucu URL: {config.server_url or '(yapılandırılmamış)'}")
    print(f"Dil: {config.language}")
    print(f"GPU: {config.use_gpu}")
