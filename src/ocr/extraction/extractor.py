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

    if "amount" not in best_fields or not best_fields["amount"]:
        fallback_match = GENERIC_AMOUNT_FALLBACK.search(normalized_text)
        if fallback_match and fallback_match.group(1):
            best_fields["amount"] = clean_field_value(fallback_match.group(1))
            if fallback_match.lastindex and fallback_match.group(2):
                best_fields["currency"] = normalize_currency(fallback_match.group(2))

    currency_value = best_fields.pop("currency", "")
    if currency_value:
        best_fields["amount_currency"] = normalize_currency(currency_value)
    elif "amount" in best_fields and best_fields["amount"]:
        # Eğer para birimi belirtilmemişse ve tutar varsa, varsayılan olarak TRY ekle
        # (Türk bankalarında genellikle TL/TRY kullanılır)
        best_fields["amount_currency"] = "TRY"

    if best_fields.get("sender_iban"):
        best_fields["sender_iban"] = best_fields["sender_iban"].replace(" ", "").upper()
    
    if best_fields.get("receiver_iban"):
        best_fields["receiver_iban"] = best_fields["receiver_iban"].replace(" ", "").upper()

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

