"""
Türk bankalarına ait dekont alanlarını tespit etmek için kullanılan regex desenleri.

Metin çıkarım aşamasında OCR çıktılarından hedef alanları seçebilmek için
Python ortamında kullanılmaya hazır hale getirilmiştir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Pattern


@dataclass(frozen=True)
class ReceiptPatterns:
    """Dekont alanlarını temsil eden regex desenleri."""

    recipient: Pattern[str] | None = None
    receiver_iban: Pattern[str] | None = None
    sender: Pattern[str] | None = None
    sender_iban: Pattern[str] | None = None
    description: Pattern[str] | None = None
    amount: Pattern[str] | None = None
    currency: Pattern[str] | None = None
    date: Pattern[str] | None = None


def _compile(pattern: str) -> Pattern[str]:
    """Kullanışlı olması için inline flag içeren regexleri derler."""

    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


BANK_SPECIFIC_PATTERNS: Dict[str, ReceiptPatterns] = {
    "vakifbank": ReceiptPatterns(
        recipient=_compile(
            r"ALICI\s*(?:AD\s*SOYAD/UNVAN)?\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
        receiver_iban=_compile(
            r"ALICI\s*(?:HESAP|IBAN)\s*[:\-]?\s*(TR\d{2}[\s\d]{10,34})"
        ),
        sender=_compile(
            r"G[\u00d6O]NDEREN\s*(?:AD\s*SOYAD\s*/?\s*UNVAN)?\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
        description=_compile(r"\u0130[\u015eS]LEM\s*A[\u00c7C]IKLAMASI\s*[:\-]?\s*(.+?)(?:\n|$)"),
        amount=_compile(
            r"\u0130[\u015eS]LEM\s*TUTARI\s*[:\-]?\s*(?:.*?)?([0-9]+(?:[.,][0-9]{1,3})*(?:[.,][0-9]{2})?)\s*(?:TL|\u20ba|USD|EUR|GBP)?"
        ),
        currency=_compile(
            r"\u0130[\u015eS]LEM\s*TUTARI\s*[:\-]?\s*(?:.*?)?[0-9,.]+\s*(TL|\u20ba|USD|EUR|GBP)"
        ),
        date=_compile(r"\u0130[\u015eS]LEM\s*TAR\u0130H\u0130\s*[:\-]?\s*(.+?)(?:\n|$)"),
    ),
    "yapikredi": ReceiptPatterns(
        recipient=_compile(
            r"(?::\s*([A-ZÇĞİÖŞÜa-zçğıöşü0-9&\.\s]{3,}?)\s+[İIia-zçğıöşü'][^\n]*TAMAMLAN|ALICI[:\-]?\s*(.+?)(?:\n|$))"
        ),
        receiver_iban=_compile(
            r"ALICI\s*(?:HESAP|IBAN)\s*[:\-]?\s*(TR\d{2}[\s\d]{10,34})"
        ),
        sender=_compile(
            r"(?:BORÇ/ALACAK\s+KAYDED[İI]LM[İI][ŞS]T[İI]R\.\s*(.+?)(?:\n|$)|\n([A-ZÇĞİÖŞÜ\s]{3,})\n\s*Ticari\s+Unvan)"
        ),
        sender_iban=_compile(
            r"(?:IBAN\s+NO\s*[:\-]?\s*([A-Z0-9\s]{10,34})|ODENEN\s+HESAP/IBAN.*?[:\-]\s*([A-Z0-9\*]+))"
        ),
        description=_compile(
            r"A[\u00c7C]IKLAMA\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
        amount=_compile(
            r"(?:İŞLEM\s+TUTARI\s*[:\-]?\s*-?([0-9]+(?:[.,][0-9]{1,3})*(?:[.,][0-9]{2})?)|ODENEN\s+TOPLAM\s+TUTAR[^\d]*[:\-]?\s*-?([0-9]+(?:[.,][0-9]{1,3})*(?:[.,][0-9]{2})?))"
        ),
        currency=_compile(
            r"(?:D|P)[ÓÖO]V[İI]Z\s*C[İI]NS[İI]\s*(?:[:\-]\s*)*\s*([A-Z]{2,3})"
        ),
        date=_compile(
            r"I[ŞS]LEM\s*TAR[İI]H[İI]\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
    ),
    "kuveytturk": ReceiptPatterns(
        recipient=_compile(r"ALICI\s*[:\-]?\s*(.+?)(?:\n|$)"),
        receiver_iban=_compile(
            r"G[\u00d6O]NDER[İI]LEN\s*IBAN\s*[:\-]?\s*(TR\d{2}[\s\d]{10,34})"
        ),
        sender=_compile(
            r"G[\u00d6O]NDEREN\s*(?:K[\u0130I][\u015eS][\u0130I])\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
        sender_iban=None,  # KuveytTürk'te gönderen IBAN genelde yok
        description=_compile(r"A[\u00c7C]IKLAMA\s*[:\-]?\s*(.+?)(?:\n|$)"),
        amount=_compile(
            r"TUTARI?\s*[:\-]?\s*(?:.*?)?([0-9]+(?:[.,][0-9]{1,3})*(?:[.,][0-9]{2})?)\s*(?:TL|\u20ba|USD|EUR|GBP)?"
        ),
        currency=_compile(
            r"TUTARI?\s*[:\-]?\s*(?:.*?)?[0-9,.]+\s*(TL|\u20ba|USD|EUR|GBP)"
        ),
        date=_compile(
            r"\u0130[\u015eS]LEM\s*TAR[\u0130I]H[\u0130I]\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
    ),
    "halkbank": ReceiptPatterns(
        recipient=_compile(
            r"(?:ALICI|LEHDAR\s*ADI)\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
        receiver_iban=_compile(
            r"(?:ALICI|LEHDAR)\s*IBAN\s*[:\-]?\s*(TR\d{2}[\s\d]{10,34})"
        ),
        sender=_compile(
            r"(?:GÖNDEREN|G[\u00d6O]NDEREN)\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
        sender_iban=_compile(
            r"(?:GÖNDEREN\s+IBAN|G[\u00d6O]NDEREN\s+IBAN)\s*[:\-]?\s*([A-Z0-9\s]{10,34})"
        ),
        description=_compile(
            r"A[\u00c7C]IKLAMA\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
        amount=_compile(
            r"(?:\u0130[\u015eS]LEM\s*TUTARI(?:\s*\(TL\))?|"
            r"\u0130TH\.?\s*DI[\u015eS]I\s*TRANS\.?\s*BED\.?|"
            r"TOPLAM\s*TUTAR)\s*(?:\([A-Z]{3}\))?\s*[:\-]?\s*(?:.*?)?([0-9]+(?:[.,][0-9]{1,3})*(?:[.,][0-9]{2})?)"
        ),
        currency=_compile(
            r"(?:\u0130[\u015eS]LEM\s*TUTARI\s*\(([A-Z]{2,3})\)|"
            r"TOPLAM\s*\(([A-Z]{2,3})\)|"
            r"DÖVİZ\s+CİNSİ\s*[:\-]?\s*([A-Z]{2,3}))"
        ),
        date=_compile(
            r"(?:İŞLEM\s+TARİHİ|\u0130[\u015eS]LEM\s*TAR[\u0130I]H[\u0130I]|Tarih|Val[öo]r)\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
    ),
    "ziraatbank": ReceiptPatterns(
        recipient=_compile(
            r"Alıcı\s*Hesap\s*[:\-]?\s*[A-Z0-9\s]+\s+Alıcı\s*[:\-]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+?)(?:\s*İşlem|$)"
        ),
        receiver_iban=_compile(
            r"Alıcı\s*Hesap\s*[:\-]?\s*(TR\d{2}[\s\d]{10,34})"
        ),
        sender=_compile(
            r"(?:Gönderen|GÖNDEREN)\s*[:\-]?\s*(.+?)(?:\n|$)"
        ),
        sender_iban=_compile(
            r"IBAN\s*(?:\n.*?){7,9}:\s*([A-Z]{2}[0-9\s]{10,34})"
        ),
        description=_compile(
            r"(?:[A-ZÇĞİÖŞÜ\s]+\n)?([A-ZÇĞİÖŞÜa-zçğıöşü0-9\.\s]{5,}?)\s+Fast\s+Mesaj"
        ),
        amount=_compile(
            r"İşlem\s+Tutarı\s*[:\-]?\s*(?:.*?)?([0-9]+(?:[.,][0-9]{1,3})*(?:[.,][0-9]{2})?)\s*(?:TRY|TL|\u20ba)?"
        ),
        currency=_compile(
            r"İşlem\s+Tutarı\s*[:\-]?\s*(?:.*?)?[0-9,.]+\s*(TRY|TL|\u20ba|USD|EUR|GBP)"
        ),
        date=_compile(
            r"İŞLEM\s+TARİHİ\s*[:\-]?\s*(?:\n.*?){7,9}:\s*([0-9/]+-[0-9:]+)"
        ),
    ),
}


GENERIC_PATTERNS = ReceiptPatterns(
    recipient=_compile(r"ALICI\s*(?:AD\s*SOYAD/UNVAN)?\s*[:\-]?\s*(.+?)(?:\n|$)"),
    receiver_iban=_compile(
        r"(?:ALICI|LEHDAR)\s*(?:HESAP|IBAN)\s*[:\-]?\s*(TR\d{2}[\s\d]{10,34})"
    ),
    description=_compile(r"A[ÇC]IKLAMA\s*[:\-]?\s*(.+?)(?:\n|$)"),
    amount=_compile(
        r"(?:\u0130[\u015eS]LEM\s*TUTARI|I[\u015eS]LEM\s*TUTARI|TUTAR[I\u0130\u011e]?|HAVALE\s*TUTARI|G[\u0130I]DEN\s*EFT\s*TUTARI|EFT\s*TUTARI|TRANSFER\s*TUTARI|PARA\s*TUTARI|M[\u0130I]KTAR)\s*(?:\(TL\))?\s*[:\-\s]*(?:.*?)?([0-9]+(?:[.,][0-9]{1,3})*(?:[.,][0-9]{2})?)\s*(?:TL|\u20ba|USD|EUR|GBP)?"
    ),
    currency=_compile(
        r"(?:TUTAR|TUTARI)\s*[:\-]?\s*(?:.*?)?[0-9,.]+\s*(TL|\u20ba|USD|EUR|GBP)"
    ),
    date=_compile(
        r"(?:\u0130[\u015eS]LEM\s*TAR[\u0130I]H[\u0130I]|I[\u015eS]LEM\s*TAR[İI]H[İI]|TAR[\u0130I]H|Tarih)\s*[:\-]?\s*(.+?)(?:\n|$)"
    ),
)


GENERIC_AMOUNT_FALLBACK = _compile(
    r"([0-9]+(?:[.,][0-9]{1,3})*[.,][0-9]{2})\s*(TL|\u20ba|USD|EUR|GBP)?"
)

