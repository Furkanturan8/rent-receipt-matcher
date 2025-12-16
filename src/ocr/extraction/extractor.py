"""
OCR sonrası çıkarılan metinler üzerinde regex tabanlı alan yakalama yardımcıları.

`regex_patterns.py` içinde tanımlı banka bazlı desenleri kullanarak
kiracı/ödeme bilgilerini yakalamaya odaklanır.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Mapping, MutableMapping, Optional, Tuple

from .regex_patterns import (
    BANK_SPECIFIC_PATTERNS,
    GENERIC_AMOUNT_FALLBACK,
    GENERIC_PATTERNS,
    ReceiptPatterns,
)


FieldMap = Dict[str, str]


def clean_field_value(value: Optional[str]) -> str:
    """Regex yakalamalarında dönen alanları sadeleştir."""

    if not value:
        return ""

    result = value.strip()

    strip_pairs = (
        (":", ""),
        ("-", ""),
        ("\u2013", ""),
        ("\u2014", ""),
        ("\u20ba", ""),  # ₺
        ("(", ""),
        (")", ""),
    )

    for original, replacement in strip_pairs:
        result = result.strip(original).strip()
        if replacement:
            result = result.replace(original, replacement)

    # Noktalı sıra numaralarını (örn. "1.") temizle
    if result and result[0].isdigit():
        split = result.split(maxsplit=1)
        if split and split[0].rstrip(".").isdigit():
            result = split[1] if len(split) > 1 else ""

    result = result.strip()

    if result:
        result = " ".join(result.split())

    return result


def normalize_currency(value: str) -> str:
    """Para birimlerini standart forma çevir."""

    mapping = {
        "TL": "TRY",
        "₺": "TRY",
    }
    upper_value = value.upper()
    return mapping.get(upper_value, upper_value)


def normalize_amount_ocr(amount: str) -> str:
    """
    Amount string'indeki OCR hatalarını düzelt.
    
    OCR hataları:
    - O harfi → 0 (sıfır)
    - l/I harfi → 1
    """
    if not amount:
        return amount
    
    # OCR hataları: O → 0, I/l → 1
    normalized = amount.replace("O", "0").replace("o", "0")
    normalized = normalized.replace("I", "1").replace("l", "1")
    
    return normalized


def normalize_name_ocr(name: str) -> str:
    """
    Name string'indeki OCR hatalarını düzelt.
    
    OCR hataları (ters yönde):
    - 1 → I (İsim için: "1BRAH1M" → "IBRAHIM")
    - 0 → O (İsim için: "0SMAN" → "OSMAN")
    """
    if not name:
        return name
    
    # OCR hataları (isim için): 1 → I, 0 → O
    # Ancak dikkatli olmalıyız - sadece kelime başında veya kelimenin ortasında
    normalized = name
    
    # Kelime başındaki 1'leri I yap
    if normalized.startswith("1"):
        normalized = "I" + normalized[1:]
    
    # Kelime aralarındaki 1'leri I yap (boşluktan sonra)
    normalized = normalized.replace(" 1", " I")
    
    # Harflerle çevrili 1'leri I yap (örn: 1BRAH1M)
    import re
    # A-Z arasında 1 varsa I yap
    normalized = re.sub(r'([A-ZÇĞİÖŞÜa-zçğıöşü])1([A-ZÇĞİÖŞÜa-zçğıöşü])', r'\1I\2', normalized)
    
    # 0 için benzer mantık (0SMAN -> OSMAN)
    if normalized.startswith("0"):
        normalized = "O" + normalized[1:]
    normalized = normalized.replace(" 0", " O")
    normalized = re.sub(r'([A-ZÇĞİÖŞÜa-zçğıöşü])0([A-ZÇĞİÖŞÜa-zçğıöşü])', r'\1O\2', normalized)
    
    return normalized


def _apply_patterns(text: str, patterns: ReceiptPatterns) -> FieldMap:
    """Pattern setindeki alanları yakalayarak sözlük döndür."""

    matches: MutableMapping[str, str] = {}

    for field_name, pattern in asdict(patterns).items():
        if pattern is None:
            continue
        match = pattern.search(text)
        if match and match.group(1):
            matches[field_name] = clean_field_value(match.group(1))

    return dict(matches)


def _choose_best_result(candidate_results: Mapping[str, FieldMap]) -> Tuple[str, FieldMap]:
    """En çok alanı yakalayan banka sonucunu seç."""

    best_bank = "generic"
    best_fields = candidate_results.get(best_bank, {})

    for bank, fields in candidate_results.items():
        if bank == "generic":
            continue
        if len([v for v in fields.values() if v]) > len(
            [v for v in best_fields.values() if v]
        ):
            best_bank = bank
            best_fields = fields

    return best_bank, best_fields


def extract_fields(text: str, bank_hint: Optional[str] = None) -> FieldMap:
    """
    OCR çıktısından (ham metin) temel ödeme alanlarını çıkar.

    Parametreler:
        text: PDF/OCR sonrası elde edilen metin.
        bank_hint: (opsiyonel) Banka adı tahmini (ör. "halkbank").

    Dönen:
        Yakalanan alan adlarını anahtar olarak içeren sözlük.
        `amount` bulunamazsa genel fallback deseni denenir.
    """

    if not text:
        return {}

    normalized_text = text.strip()

    candidate_results: Dict[str, FieldMap] = {"generic": _apply_patterns(normalized_text, GENERIC_PATTERNS)}

    if bank_hint:
        patterns = BANK_SPECIFIC_PATTERNS.get(bank_hint.lower())
        if patterns:
            candidate_results[bank_hint.lower()] = _apply_patterns(normalized_text, patterns)
    else:
        for bank, patterns in BANK_SPECIFIC_PATTERNS.items():
            candidate_results[bank] = _apply_patterns(normalized_text, patterns)

    _, best_fields = _choose_best_result(candidate_results)

    # Normalize amount (OCR error correction)
    if "amount" in best_fields and best_fields["amount"]:
        best_fields["amount"] = normalize_amount_ocr(best_fields["amount"])

    if "amount" not in best_fields or not best_fields["amount"]:
        fallback_match = GENERIC_AMOUNT_FALLBACK.search(normalized_text)
        if fallback_match and fallback_match.group(1):
            best_fields["amount"] = normalize_amount_ocr(clean_field_value(fallback_match.group(1)))
            if fallback_match.lastindex and fallback_match.group(2):
                best_fields["currency"] = normalize_currency(fallback_match.group(2))

    currency_value = best_fields.pop("currency", "")
    if currency_value:
        best_fields["amount_currency"] = normalize_currency(currency_value)
    elif "amount" in best_fields and best_fields["amount"]:
        # Eğer para birimi belirtilmemişse ve tutar varsa, varsayılan olarak TRY ekle
        # (Türk bankalarında genellikle TL/TRY kullanılır)
        best_fields["amount_currency"] = "TRY"
    
    # İsimleri normalize et (OCR hataları: 1 -> I, 0 -> O)
    if best_fields.get("sender"):
        best_fields["sender"] = normalize_name_ocr(best_fields["sender"])
    
    if best_fields.get("recipient"):
        best_fields["recipient"] = normalize_name_ocr(best_fields["recipient"])

    if best_fields.get("sender_iban"):
        iban = best_fields["sender_iban"].replace(" ", "").upper()
        # OCR hataları: Sadece sayı kısmında O→0, I/l→1 (TR kodu hariç)
        if len(iban) >= 4:
            country = iban[:2]
            check = iban[2:4]
            rest = iban[4:].replace("O", "0").replace("I", "1")
            best_fields["sender_iban"] = country + check + rest
        else:
            best_fields["sender_iban"] = iban
    
    if best_fields.get("receiver_iban"):
        iban = best_fields["receiver_iban"].replace(" ", "").upper()
        # OCR hataları: Sadece sayı kısmında O→0, I/l→1 (TR kodu hariç)
        if len(iban) >= 4:
            country = iban[:2]
            check = iban[2:4]
            rest = iban[4:].replace("O", "0").replace("I", "1")
            best_fields["receiver_iban"] = country + check + rest
        else:
            best_fields["receiver_iban"] = iban
    
    # Description'dan istenmeyen prefix'leri temizle + OCR hataları düzelt
    if best_fields.get("description"):
        import re
        desc = best_fields["description"]
        # VALÖR tarihini kaldır
        desc = re.sub(r'VALÖR\s*[:\-]?\s*\d{2}\.\d{2}\.\d{4}\s*', '', desc, flags=re.IGNORECASE)
        # İŞLEM YERİ + banka adını kaldır
        desc = re.sub(r'İŞLEM\s+YERİ\s*[:\-]?\s*[A-ZÇĞİÖŞÜ\s]+', '', desc, flags=re.IGNORECASE)
        # Banka mobil uygulamalarını kaldır
        desc = re.sub(r'(ZİRAAT|HALKBANK|KUVEYT\s+TÜRK|YAPI\s+KREDİ)\s+MOBİL\s*', '', desc, flags=re.IGNORECASE)
        # Başta kalan iki nokta, tire, boşlukları temizle
        desc = re.sub(r'^[:\-\s]+', '', desc)
        # OCR hataları: 0 yerine O, 1 yerine l/I
        desc = desc.replace("0", "O").replace("1", "I")  # Descriptive text için tersini yap - sayıları harfleştirme
        # Çift boşlukları tek yap
        desc = ' '.join(desc.split())
        best_fields["description"] = desc.strip()

    # Standart sırada çıktı oluştur: sender, sender_iban, description, amount, amount_currency, date, recipient, receiver_iban
    standard_fields = {}
    field_order = ["sender", "sender_iban", "description", "amount", "amount_currency", "date", "recipient", "receiver_iban"]
    
    # Önce field_order'daki alanları ekle (boş olsa bile)
    for field in field_order:
        if field in best_fields:
            standard_fields[field] = best_fields[field]
        else:
            # sender_iban ve receiver_iban için boş string ekle
            if field in ["sender_iban", "receiver_iban"]:
                standard_fields[field] = ""
    
    # Diğer alanları da ekle (field_order'da olmayanlar)
    for key, value in best_fields.items():
        if key not in standard_fields:
            standard_fields[key] = value

    # Boş string'leri filtrele, ama sender_iban ve receiver_iban her zaman olsun
    # field_order'a göre sıralı çıktı oluştur
    result = {}
    
    # Önce field_order'daki alanları sırayla ekle
    for field in field_order:
        if field in standard_fields:
            value = standard_fields[field]
            if field in ["sender_iban", "receiver_iban"]:
                # Bu alanlar her zaman olsun (boş olsa bile)
                result[field] = value if value else ""
            elif value:  # Diğer alanlar sadece doluysa
                result[field] = value
    
    # Sonra field_order'da olmayan diğer alanları ekle
    for k, v in standard_fields.items():
        if k not in result and v:
            result[k] = v
    
    return result


__all__ = [
    "extract_fields",
    "clean_field_value",
    "ReceiptPatterns",
    "BANK_SPECIFIC_PATTERNS",
    "GENERIC_PATTERNS",
]

