"""
PDF metinlerinden banka tespiti yapan modül.

Her banka için karakteristik keywords ve banka isimleri tanımlanır.
PDF metninde bu keywords'ler aranarak en uygun banka tespit edilir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Logo tabanlı tespit için import (opsiyonel bağımlılık)
try:
    from .logo_detector import detect_bank_from_logos
    LOGO_DETECTION_AVAILABLE = True
except ImportError:
    LOGO_DETECTION_AVAILABLE = False
    detect_bank_from_logos = None


# Her banka için karakteristik keywords ve banka isimleri
BANK_KEYWORDS: Dict[str, List[str]] = {
    "halkbank": [
        "halkbank",
        "halk bankası",
        "halk bank",
        "t.c. halk bankası",
        "finanskent",
        "halkbank.com.tr",
        "www.halkbank.com.tr",
        "finanskent mahallesi",
    ],
    "yapikredi": [
        "yapı kredi",
        "yapıkredi",
        "yapı ve kredi bankası",
        "yapı kredi bankası",
        "yapi kredi",
        "yapıkredi.com.tr",
        "www.yapikredi.com.tr",
        "yapı kredi plaza",
        "e-dekont",
        "muhasebe işlem dekontu",
    ],
    "kuveytturk": [
        "kuveyt türk",
        "kuveytturk",
        "kuveyt türk katılım bankası",
        "kuveyt türk katılım",
        "www.kuveytturk.com.tr",
        "kuveytturk.com.tr",
        "büyükdere cad",
        "esentepe",
        "iban'a para transferi",
    ],
    "ziraatbank": [
        "ziraat bankası",
        "ziraatbank",
        "t.c. ziraat bankası",
        "www.ziraatbank.com.tr",
        "ziraatbank.com.tr",
        "finanskent mahallesi finans caddesi",
        "hesaptan fast",
        "ziraat mobil",
        "ziraat süper şube",
    ],
    "vakifbank": [
        "vakıfbank",
        "vakıf bank",
        "vakıf bankası",
        "t.c. vakıfbank",
        "www.vakifbank.com.tr",
        "vakifbank.com.tr",
    ],
}


def detect_bank(text: str) -> Optional[str]:
    """
    PDF metninden bankayı otomatik olarak tespit eder.

    Parametreler:
        text: PDF'den çıkarılan ham metin.

    Dönen:
        Tespit edilen banka adı (ör. "halkbank", "yapikredi") veya None.
    """
    if not text:
        return None

    text_lower = text.lower()

    # Her banka için eşleşme skorunu hesapla
    bank_scores: Dict[str, int] = {}

    for bank_name, keywords in BANK_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                # Uzun keywords daha yüksek öncelikli
                score += len(keyword)

        if score > 0:
            bank_scores[bank_name] = score

    if not bank_scores:
        return None

    # En yüksek skorlu bankayı döndür
    best_bank = max(bank_scores.items(), key=lambda x: x[1])[0]
    return best_bank


def detect_bank_with_confidence(text: str) -> Tuple[Optional[str], float]:
    """
    PDF metninden bankayı tespit eder ve güven skoru döndürür.

    Parametreler:
        text: PDF'den çıkarılan ham metin.

    Dönen:
        (banka_adı, güven_skoru) tuple'ı.
        Güven skoru 0.0 ile 1.0 arasında bir değerdir.
    """
    if not text:
        return None, 0.0

    text_lower = text.lower()
    bank_scores: Dict[str, int] = {}

    for bank_name, keywords in BANK_KEYWORDS.items():
        score = 0
        matches = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += len(keyword)
                matches += 1

        if score > 0:
            bank_scores[bank_name] = score

    if not bank_scores:
        return None, 0.0

    # En yüksek skorlu bankayı bul
    best_bank, best_score = max(bank_scores.items(), key=lambda x: x[1])

    # Toplam skoru hesapla
    total_score = sum(bank_scores.values())

    # Güven skoru: En iyi bankanın skorunun toplam skora oranı
    confidence = best_score / total_score if total_score > 0 else 0.0

    # Eğer sadece bir banka bulunduysa veya fark çok büyükse, güven skorunu artır
    if len(bank_scores) == 1 or best_score > (total_score - best_score) * 2:
        confidence = min(confidence * 1.5, 1.0)

    return best_bank, confidence


def detect_bank_hybrid(text: str, pdf_path: Optional[str | Path] = None) -> Optional[str]:
    """
    Hibrit yaklaşım: Hem metin hem logo tabanlı tespit.

    Önce metin tabanlı tespit yapar, eğer güvenilir sonuç yoksa logo tabanlı tespit dener.

    Parametreler:
        text: PDF'den çıkarılan metin.
        pdf_path: PDF dosyasının yolu (logo tespiti için).

    Dönen:
        Tespit edilen banka adı veya None.
    """
    # Önce metin tabanlı tespit
    text_bank = detect_bank(text)
    
    # Eğer metin tabanlı tespit yüksek güvenilirliğe sahipse, onu kullan
    if text_bank:
        _, confidence = detect_bank_with_confidence(text)
        if confidence >= 0.7:
            return text_bank
    
    # Logo tabanlı tespit (eğer mümkünse)
    if LOGO_DETECTION_AVAILABLE and pdf_path:
        logo_bank = detect_bank_from_logos(pdf_path)
        if logo_bank:
            return logo_bank
    
    # Son çare olarak metin tabanlı sonucu döndür
    return text_bank


__all__ = [
    "detect_bank",
    "detect_bank_with_confidence",
    "detect_bank_hybrid",
    "BANK_KEYWORDS",
]

