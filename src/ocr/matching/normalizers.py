"""
Dekont verilerini normalize eden yardımcı fonksiyonlar.

Mock data'daki normalizasyon kurallarına göre implement edilmiştir.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


def normalize_iban(iban: Optional[str]) -> str:
    """
    IBAN'ı normalize eder.
    
    Kurallar (mock-data.json'dan):
    - Tüm boşlukları kaldır
    - Büyük harfe çevir
    - O harfi yerine 0 (sıfır) kontrol et
    - I/l harfi yerine 1 kontrol et
    
    Parametreler:
        iban: Ham IBAN string'i.
    
    Dönen:
        Normalize edilmiş IBAN.
    """
    if not iban:
        return ""
    
    # Boşlukları ve tireleri kaldır
    normalized = iban.replace(" ", "").replace("-", "").upper()
    
    # OCR hataları: O harfi yerine 0, I/l harfi yerine 1
    # Ancak dikkatli olmalıyız - TR kısmında O olabilir
    # Sadece sayısal kısımda dönüşüm yapalım
    if len(normalized) >= 4:
        country_code = normalized[:2]
        check_digits = normalized[2:4]
        account_part = normalized[4:]
        
        # Sayısal kısımda O -> 0, I/l -> 1 dönüşümü
        account_part = account_part.replace("O", "0").replace("I", "1").replace("l", "1")
        
        normalized = country_code + check_digits + account_part
    
    return normalized


def normalize_name(name: Optional[str]) -> str:
    """
    İsim/şirket adını normalize eder.
    
    Kurallar (mock-data.json'dan):
    - Büyük harfe çevir
    - Türkçe karakterleri normalize et (ı->I, ş->S, ğ->G, ü->U, ö->O, ç->C)
    - Çift boşlukları tek boşluğa indir
    - Başta/sonda boşlukları temizle
    
    Parametreler:
        name: Ham isim string'i.
    
    Dönen:
        Normalize edilmiş isim.
    """
    if not name:
        return ""
    
    # Büyük harfe çevir
    normalized = name.upper()
    
    # Türkçe karakterleri normalize et
    turkish_chars = {
        "ı": "I",
        "İ": "I",
        "ş": "S",
        "Ş": "S",
        "ğ": "G",
        "Ğ": "G",
        "ü": "U",
        "Ü": "U",
        "ö": "O",
        "Ö": "O",
        "ç": "C",
        "Ç": "C",
    }
    
    for turkish, ascii_char in turkish_chars.items():
        normalized = normalized.replace(turkish, ascii_char)
    
    # Çift boşlukları tek boşluğa indir
    normalized = re.sub(r"\s+", " ", normalized)
    
    # Başta/sonda boşlukları temizle
    normalized = normalized.strip()
    
    return normalized


def normalize_amount(amount_text: Optional[str]) -> Optional[float]:
    """
    Tutar metnini float'a çevirir.
    
    Kurallar (mock-data.json'dan):
    - Nokta ve virgül işaretlerini standardize et
    - TL/TRY/₺ ifadelerini temizle
    - Decimal olarak parse et
    
    Parametreler:
        amount_text: Ham tutar string'i (örn. "45.000,00", "35000.00").
    
    Dönen:
        Float tutar veya None.
    """
    if not amount_text:
        return None
    
    # TL/TRY/₺ ifadelerini temizle
    cleaned = amount_text.replace("TL", "").replace("TRY", "").replace("₺", "").strip()
    
    # OCR hataları: O harfi yerine 0
    cleaned = cleaned.replace("O", "0").replace("o", "0")
    
    # Nokta ve virgül işaretlerini standardize et
    # Türk formatı: 45.000,00 -> 45000.00
    # İngiliz formatı: 45000.00 -> 45000.00
    
    # Binlik ayırıcı nokta, ondalık ayırıcı virgül ise
    if "," in cleaned and "." in cleaned:
        # Son virgülden önceki kısım ondalık
        parts = cleaned.rsplit(",", 1)
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Virgül ondalık ayırıcı
            decimal_part = parts[1]
            integer_part = parts[0].replace(".", "")
            cleaned = f"{integer_part}.{decimal_part}"
        else:
            # Nokta ondalık ayırıcı, virgül binlik
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        # Sadece virgül var - ondalık ayırıcı olabilir
        if cleaned.count(",") == 1 and len(cleaned.split(",")[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            # Binlik ayırıcı
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        # Sadece nokta var
        parts = cleaned.split(".")
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Ondalık ayırıcı
            pass
        else:
            # Binlik ayırıcı
            cleaned = cleaned.replace(".", "")
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def normalize_date(date_text: Optional[str]) -> Optional[datetime]:
    """
    Tarih metnini datetime'a çevirir.
    
    Kurallar (mock-data.json'dan):
    - Farklı formatları destekle (DD.MM.YYYY, DD/MM/YYYY)
    - OCR hataları için 0/O kontrolü
    
    Parametreler:
        date_text: Ham tarih string'i.
    
    Dönen:
        Datetime objesi veya None.
    """
    if not date_text:
        return None
    
    # OCR hataları: O harfi yerine 0
    cleaned = date_text.replace("O", "0").replace("o", "0")
    
    # Farklı formatları dene
    formats = [
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%y",
        "%d/%m/%y",
        "%Y-%m-%d",
        "%Y.%m.%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(cleaned.strip(), fmt)
        except (ValueError, TypeError):
            continue
    
    return None


__all__ = [
    "normalize_iban",
    "normalize_name",
    "normalize_amount",
    "normalize_date",
]

