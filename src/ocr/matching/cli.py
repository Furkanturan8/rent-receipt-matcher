"""
Dekont eşleştirme CLI aracı.

Mock data veya gerçek OCR çıktısı ile eşleştirme testi yapar.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    from pdfminer.high_level import extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

from ocr.extraction.extractor import extract_fields
from ocr.extraction.bank_detector import detect_bank
from ocr.matching.matcher import match_receipt, ReceiptMatchResult
from ocr.matching.mapper import map_ocr_to_receipt_fields


def load_mock_data(mock_data_path: Path | str) -> Dict[str, Any]:
    """Mock data JSON dosyasını yükle."""
    path = Path(mock_data_path)
    if not path.exists():
        raise FileNotFoundError(f"Mock data dosyası bulunamadı: {path}")
    
    with open(path) as f:
        return json.load(f)


def match_from_pdf(
    pdf_path: Path | str,
    mock_data_path: Path | str = "tests/mock-data.json",
    min_confidence: float = 70.0,
) -> ReceiptMatchResult:
    """
    PDF'den OCR yap ve eşleştir.
    
    Parametreler:
        pdf_path: PDF dosyası yolu.
        mock_data_path: Mock data JSON dosyası yolu.
        min_confidence: Minimum güven skoru.
    
    Dönen:
        ReceiptMatchResult objesi.
    """
    if not PDFMINER_AVAILABLE:
        raise ImportError("pdfminer kurulu değil. pip install pdfminer.six")
    
    # PDF'den OCR yap
    text = extract_text(str(pdf_path))
    detected_bank = detect_bank(text)
    ocr_data = extract_fields(text, bank_hint=detected_bank)
    
    # Mock data'yı yükle
    mock_data = load_mock_data(mock_data_path)
    owners = mock_data["database_records"]["owners"]
    customers = mock_data["database_records"]["customers"]
    properties = mock_data["database_records"]["properties"]
    
    # Eşleştir
    result = match_receipt(
        ocr_data=ocr_data,
        owners=owners,
        customers=customers,
        properties=properties,
        min_confidence=min_confidence,
    )
    
    return result, ocr_data, detected_bank


def match_from_ocr_json(
    ocr_json_path: Path | str,
    mock_data_path: Path | str = "tests/mock-data.json",
    min_confidence: float = 70.0,
) -> ReceiptMatchResult:
    """
    JSON dosyasından OCR çıktısını oku ve eşleştir.
    
    Parametreler:
        ocr_json_path: OCR çıktısı JSON dosyası.
        mock_data_path: Mock data JSON dosyası yolu.
        min_confidence: Minimum güven skoru.
    
    Dönen:
        ReceiptMatchResult objesi.
    """
    # OCR JSON'ı yükle
    with open(ocr_json_path) as f:
        ocr_data = json.load(f)
    
    # Mock data'yı yükle
    mock_data = load_mock_data(mock_data_path)
    owners = mock_data["database_records"]["owners"]
    customers = mock_data["database_records"]["customers"]
    properties = mock_data["database_records"]["properties"]
    
    # Eşleştir
    result = match_receipt(
        ocr_data=ocr_data,
        owners=owners,
        customers=customers,
        properties=properties,
        min_confidence=min_confidence,
    )
    
    return result, ocr_data, None


def match_mock_receipt(
    receipt_id: str,
    mock_data_path: Path | str = "tests/mock-data.json",
    min_confidence: float = 70.0,
) -> ReceiptMatchResult:
    """
    Mock data'dan belirli bir dekontu eşleştir.
    
    Parametreler:
        receipt_id: Dekont ID (örn. "DEKONT_001").
        mock_data_path: Mock data JSON dosyası yolu.
        min_confidence: Minimum güven skoru.
    
    Dönen:
        ReceiptMatchResult objesi.
    """
    mock_data = load_mock_data(mock_data_path)
    
    # Dekontu bul
    receipt = None
    for dekont in mock_data.get("dekont_ornekleri", []):
        if dekont.get("dekont_id") == receipt_id:
            receipt = dekont
            break
    
    if not receipt:
        raise ValueError(f"Dekont bulunamadı: {receipt_id}")
    
    ocr_data = receipt["ocr_cikti"]
    owners = mock_data["database_records"]["owners"]
    customers = mock_data["database_records"]["customers"]
    properties = mock_data["database_records"]["properties"]
    
    # OCR verisini extract_fields formatına çevir
    ocr_formatted = {
        "recipient": ocr_data.get("alici_adi"),
        "receiver_account": ocr_data.get("alici_hesap"),
        "receiver_iban": ocr_data.get("alici_hesap"),
        "sender": ocr_data.get("gonderen_adi"),
        "sender_account": ocr_data.get("gonderen_hesap"),
        "sender_iban": ocr_data.get("gonderen_hesap"),
        "amount": ocr_data.get("tutar"),
        "amount_text": ocr_data.get("tutar"),
        "description": ocr_data.get("aciklama"),
        "date": ocr_data.get("islem_tarihi"),
    }
    
    # Eşleştir
    result = match_receipt(
        ocr_data=ocr_formatted,
        owners=owners,
        customers=customers,
        properties=properties,
        min_confidence=min_confidence,
    )
    
    return result, ocr_formatted, receipt.get("beklenen_esleme")


def print_match_result(
    result: ReceiptMatchResult,
    ocr_data: Dict[str, Any],
    expected: Dict[str, Any] | None = None,
    detected_bank: str | None = None,
) -> None:
    """Eşleştirme sonucunu güzel formatta yazdır."""
    print("=" * 70)
    print("DEKONT EŞLEŞTİRME SONUCU")
    print("=" * 70)
    
    if detected_bank:
        print(f"🏦 Tespit edilen banka: {detected_bank}")
    
    print(f"\n📋 OCR Çıktısı:")
    if ocr_data.get("sender"):
        print(f"   Gönderen: {ocr_data.get('sender')}")
    if ocr_data.get("recipient") or ocr_data.get("receiver_name"):
        print(f"   Alıcı: {ocr_data.get('recipient') or ocr_data.get('receiver_name')}")
    if ocr_data.get("amount"):
        print(f"   Tutar: {ocr_data.get('amount')} {ocr_data.get('amount_currency', 'TRY')}")
    if ocr_data.get("description"):
        desc = ocr_data.get("description")
        if len(desc) > 60:
            desc = desc[:57] + "..."
        print(f"   Açıklama: {desc}")
    
    print(f"\n✅ Eşleştirme Sonuçları:")
    if expected:
        owner_match = "✓" if result.owner_id == expected.get("owner_id") else "✗"
        property_match = "✓" if result.property_id == expected.get("property_id") else "✗"
        customer_match = "✓" if result.customer_id == expected.get("customer_id") else "✗"
        
        print(f"   Owner ID: {result.owner_id} (Beklenen: {expected.get('owner_id')}) {owner_match}")
        print(f"   Property ID: {result.property_id} (Beklenen: {expected.get('property_id')}) {property_match}")
        print(f"   Customer ID: {result.customer_id} (Beklenen: {expected.get('customer_id')}) {customer_match}")
    else:
        print(f"   Owner ID: {result.owner_id}")
        print(f"   Property ID: {result.property_id}")
        print(f"   Customer ID: {result.customer_id}")
    
    print(f"\n📊 Güven Skoru: {result.confidence_score:.1f}/100")
    print(f"📌 Durum: {result.match_status}")
    
    print(f"\n🔍 Detay Skorlar:")
    print(f"   IBAN: {result.iban_match_score:.2f} (ağırlık: 95)")
    print(f"   Tutar: {result.amount_match_score:.2f} (ağırlık: 85)")
    print(f"   İsim: {result.name_match_score:.2f} (ağırlık: 75)")
    print(f"   Adres: {result.address_match_score:.2f} (ağırlık: 70)")
    print(f"   Gönderen: {result.sender_match_score:.2f} (ağırlık: 60)")
    
    if result.messages:
        print(f"\n💬 Mesajlar: {', '.join(result.messages)}")
    
    print("=" * 70)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI argümanlarını parse et."""
    parser = argparse.ArgumentParser(
        description="Dekont eşleştirme test aracı."
    )
    
    parser.add_argument(
        "--pdf",
        help="PDF dosyası yolu (OCR yapılacak).",
        type=Path,
    )
    parser.add_argument(
        "--ocr-json",
        help="OCR çıktısı JSON dosyası yolu.",
        type=Path,
    )
    parser.add_argument(
        "--receipt-id",
        help="Mock data'dan dekont ID (örn. DEKONT_001).",
    )
    parser.add_argument(
        "--mock-data",
        help="Mock data JSON dosyası yolu.",
        type=Path,
        default=Path("tests/mock-data.json"),
    )
    parser.add_argument(
        "--min-confidence",
        help="Minimum güven skoru (0-100).",
        type=float,
        default=70.0,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON formatında çıktı ver.",
    )
    
    return parser.parse_args(argv or sys.argv[1:])


def main(argv: list[str] | None = None) -> int:
    """Ana CLI fonksiyonu."""
    args = parse_args(argv or sys.argv[1:])
    
    try:
        if args.pdf:
            # PDF'den eşleştir
            if not args.pdf.exists():
                print(f"Hata: PDF dosyası bulunamadı: {args.pdf}", file=sys.stderr)
                return 1
            
            result, ocr_data, detected_bank = match_from_pdf(
                pdf_path=args.pdf,
                mock_data_path=args.mock_data,
                min_confidence=args.min_confidence,
            )
            expected = None
        
        elif args.ocr_json:
            # OCR JSON'dan eşleştir
            if not args.ocr_json.exists():
                print(f"Hata: OCR JSON dosyası bulunamadı: {args.ocr_json}", file=sys.stderr)
                return 1
            
            result, ocr_data, detected_bank = match_from_ocr_json(
                ocr_json_path=args.ocr_json,
                mock_data_path=args.mock_data,
                min_confidence=args.min_confidence,
            )
            expected = None
        
        elif args.receipt_id:
            # Mock data'dan eşleştir
            result, ocr_data, expected = match_mock_receipt(
                receipt_id=args.receipt_id,
                mock_data_path=args.mock_data,
                min_confidence=args.min_confidence,
            )
            detected_bank = None
        
        else:
            print("Hata: --pdf, --ocr-json veya --receipt-id parametrelerinden biri gerekli.", file=sys.stderr)
            return 1
        
        # Çıktı
        if args.json:
            output = {
                "owner_id": result.owner_id,
                "property_id": result.property_id,
                "customer_id": result.customer_id,
                "match_status": result.match_status,
                "confidence_score": result.confidence_score,
                "iban_match_score": result.iban_match_score,
                "amount_match_score": result.amount_match_score,
                "name_match_score": result.name_match_score,
                "address_match_score": result.address_match_score,
                "sender_match_score": result.sender_match_score,
                "messages": result.messages,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print_match_result(result, ocr_data, expected, detected_bank)
        
        return 0
    
    except Exception as e:
        print(f"Hata: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

