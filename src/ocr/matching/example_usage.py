"""
Dekont eşleştirme sistemi kullanım örneği.

Bu dosya, OCR çıktısını database kayıtlarıyla nasıl eşleştireceğinizi gösterir.
"""

import json
from pathlib import Path

# OCR extraction
from ocr.extraction.extractor import extract_fields
from ocr.extraction.bank_detector import detect_bank
from pdfminer.high_level import extract_text

# Matching
from ocr.matching.matcher import match_receipt, ReceiptMatchResult
from ocr.matching.mapper import map_ocr_to_receipt_fields, update_receipt_with_match
from ocr.matching.normalizers import normalize_iban, normalize_name, normalize_amount


def process_receipt_pdf(
    pdf_path: str,
    owners: list,
    customers: list,
    properties: list,
) -> dict:
    """
    PDF dekontunu işle ve database ile eşleştir.
    
    Parametreler:
        pdf_path: PDF dosyasının yolu.
        owners: Mülk sahipleri listesi (mock-data.json formatında).
        customers: Müşteriler listesi.
        properties: Mülkler listesi.
    
    Dönen:
        İşlem sonucu dictionary'si.
    """
    # 1. PDF'den metin çıkar
    text = extract_text(pdf_path)
    
    # 2. Bankayı otomatik tespit et
    detected_bank = detect_bank(text)
    print(f"Tespit edilen banka: {detected_bank}")
    
    # 3. OCR ile alanları çıkar
    ocr_data = extract_fields(text, bank_hint=detected_bank)
    print(f"OCR çıktısı: {ocr_data}")
    
    # 4. OCR çıktısını RentReceipt model formatına çevir
    receipt_fields = map_ocr_to_receipt_fields(ocr_data)
    
    # 5. Database kayıtlarıyla eşleştir
    match_result = match_receipt(
        ocr_data=ocr_data,
        owners=owners,
        customers=customers,
        properties=properties,
        min_confidence=70.0,
    )
    
    # 6. Eşleştirme sonucunu receipt fields'a ekle
    receipt_fields = update_receipt_with_match(receipt_fields, match_result)
    
    return {
        "receipt_fields": receipt_fields,
        "match_result": {
            "owner_id": match_result.owner_id,
            "property_id": match_result.property_id,
            "customer_id": match_result.customer_id,
            "match_status": match_result.match_status,
            "confidence_score": match_result.confidence_score,
            "messages": match_result.messages,
        },
        "ocr_data": ocr_data,
    }


def example_usage():
    """Örnek kullanım."""
    # Mock data'yı yükle
    mock_data_path = Path(__file__).parent.parent.parent.parent / "tests" / "mock-data.json"
    
    with open(mock_data_path) as f:
        mock_data = json.load(f)
    
    owners = mock_data["database_records"]["owners"]
    customers = mock_data["database_records"]["customers"]
    properties = mock_data["database_records"]["properties"]
    
    # Örnek dekont OCR çıktısı (mock-data'dan)
    example_receipt = mock_data["dekont_ornekleri"][0]
    ocr_data = example_receipt["ocr_cikti"]
    
    # Eşleştirme yap
    match_result = match_receipt(
        ocr_data=ocr_data,
        owners=owners,
        customers=customers,
        properties=properties,
    )
    
    print("Eşleştirme Sonucu:")
    print(f"  Owner ID: {match_result.owner_id}")
    print(f"  Property ID: {match_result.property_id}")
    print(f"  Customer ID: {match_result.customer_id}")
    print(f"  Durum: {match_result.match_status}")
    print(f"  Güven Skoru: {match_result.confidence_score:.1f}")
    print(f"  Mesajlar: {match_result.messages}")
    print(f"  IBAN Skoru: {match_result.iban_match_score:.2f}")
    print(f"  Tutar Skoru: {match_result.amount_match_score:.2f}")
    print(f"  İsim Skoru: {match_result.name_match_score:.2f}")


if __name__ == "__main__":
    example_usage()

