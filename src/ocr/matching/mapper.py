"""
OCR çıktısını RentReceipt modeline map eden fonksiyonlar.

extract_fields çıktısını Django model formatına dönüştürür.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .matcher import ReceiptMatchResult

from .normalizers import normalize_amount, normalize_date


def map_ocr_to_receipt_fields(ocr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    OCR çıktısını RentReceipt model alanlarına map eder.
    
    Parametreler:
        ocr_data: extract_fields fonksiyonundan gelen çıktı.
    
    Dönen:
        RentReceipt model alanlarına uygun dictionary.
    """
    fields = {
        "ocr_raw_data": ocr_data,
    }
    
    # Banka bilgileri
    if "bank" in ocr_data:
        fields["bank_name"] = ocr_data["bank"]
    
    # Gönderen bilgileri (Kiracı)
    if "sender" in ocr_data:
        fields["sender_name"] = ocr_data["sender"]
    if "sender_iban" in ocr_data:
        fields["sender_account"] = ocr_data["sender_iban"]
    
    # Alıcı bilgileri (Mülk Sahibi)
    if "recipient" in ocr_data:
        fields["receiver_name"] = ocr_data["recipient"]
    # receiver_account için IBAN bilgisi yoksa OCR'dan çıkarılamaz
    # (PDF'de genelde gönderen IBAN'ı yok)
    
    # Tutar
    amount_text = ocr_data.get("amount", "")
    if amount_text:
        fields["amount_text"] = str(amount_text)
        amount_value = normalize_amount(amount_text)
        if amount_value is not None:
            # MoneyField için amount ve currency
            fields["amount"] = amount_value
            fields["amount_currency"] = ocr_data.get("amount_currency", "TRY")
    
    # Tarih
    date_text = ocr_data.get("date", "")
    if date_text:
        date_obj = normalize_date(date_text)
        if date_obj:
            fields["transaction_date"] = date_obj.date()
            if hasattr(date_obj, "time"):
                fields["transaction_time"] = date_obj.time()
    
    # Açıklama
    if "description" in ocr_data:
        fields["description"] = ocr_data["description"]
    
    # Referans numarası (varsa)
    if "reference_number" in ocr_data:
        fields["reference_number"] = ocr_data["reference_number"]
    
    return fields


def update_receipt_with_match(
    receipt_fields: Dict[str, Any],
    match_result: Any,  # ReceiptMatchResult
) -> Dict[str, Any]:
    """
    ReceiptMatchResult'ı receipt fields'a ekler.
    
    Parametreler:
        receipt_fields: RentReceipt model alanları.
        match_result: Eşleştirme sonucu.
    
    Dönen:
        Güncellenmiş receipt fields.
    """
    # Eşleştirme durumu
    receipt_fields["match_status"] = match_result.match_status
    receipt_fields["match_confidence"] = match_result.confidence_score
    
    # Eşleşen kayıtlar
    if match_result.owner_id:
        receipt_fields["matched_owner_id"] = match_result.owner_id
    if match_result.customer_id:
        receipt_fields["matched_customer_id"] = match_result.customer_id
    if match_result.property_id:
        receipt_fields["matched_property_id"] = match_result.property_id
    
    # Eşleştirme detayları
    receipt_fields["matching_details"] = {
        "iban_match_score": match_result.iban_match_score,
        "amount_match_score": match_result.amount_match_score,
        "name_match_score": match_result.name_match_score,
        "address_match_score": match_result.address_match_score,
        "sender_match_score": match_result.sender_match_score,
        "messages": match_result.messages,
        **match_result.matching_details,
    }
    
    return receipt_fields


__all__ = [
    "map_ocr_to_receipt_fields",
    "update_receipt_with_match",
]

