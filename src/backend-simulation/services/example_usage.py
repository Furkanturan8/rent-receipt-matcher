"""
Servis katmanı örnek kullanım senaryoları.

Bu dosya receipt_processor, validator ve transaction_manager 
servislerinin nasıl kullanılacağını gösterir.
"""

from pathlib import Path

from data_loader import DataLoader
from receipt_processor import ReceiptProcessor
from transaction_manager import TransactionManager
from validators import ReceiptValidator


def example_1_process_single_receipt():
    """
    Senaryo 1: Tek bir dekontun işlenmesi
    
    Bu senaryo:
    1. PDF dekontunu OCR ile işler
    2. Banka tespiti yapar
    3. Alanları çıkarır
    4. Database ile eşleştirir
    5. Validasyon yapar
    6. Sonucu döner
    """
    print("=" * 80)
    print("SENARYO 1: Tek Dekont İşleme")
    print("=" * 80)
    
    # 1. Verileri yükle
    data_loader = DataLoader("../backend-models")
    data = data_loader.load_all()
    
    # 2. Receipt processor oluştur
    processor = ReceiptProcessor(
        owners=data["owners"],
        customers=data["customers"],
        properties=data["properties"],
        rental_contracts=data["rental_contracts"],
    )
    
    # 3. Dekontu işle
    pdf_path = Path("../../../data/halkbank.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF dosyası bulunamadı: {pdf_path}")
        print("Lütfen data/ klasörüne örnek dekont ekleyin.")
        return
    
    result = processor.process_receipt(
        pdf_path=pdf_path,
        expected_amount=15000.0,  # Beklenen kira tutarı
        expected_owner_id=1,  # Beklenen mülk sahibi
        min_confidence=70.0,
    )
    
    # 4. Sonuçları göster
    print("\n📋 İşlem Sonucu:")
    print(f"  ✓ Başarı: {result.success}")
    print(f"  ✓ Durum: {result.status}")
    print(f"  ✓ Banka: {result.detected_bank or 'Tespit edilemedi'}")
    print(f"  ✓ Eşleşme Güveni: {result.match_confidence:.1f}%")
    print(f"  ✓ Validasyon: {'✓ Geçerli' if result.is_valid else '✗ Geçersiz'}")
    
    print("\n📝 Çıkarılan Alanlar:")
    for key, value in result.extracted_fields.items():
        print(f"  • {key}: {value}")
    
    print("\n🔗 Eşleştirme Sonuçları:")
    print(f"  • Owner ID: {result.matched_owner_id}")
    print(f"  • Customer ID: {result.matched_customer_id}")
    print(f"  • Property ID: {result.matched_property_id}")
    
    if result.validation_errors:
        print("\n❌ Validasyon Hataları:")
        for error in result.validation_errors:
            print(f"  • {error}")
    
    if result.validation_warnings:
        print("\n⚠️  Validasyon Uyarıları:")
        for warning in result.validation_warnings:
            print(f"  • {warning}")
    
    print("\n💬 Mesajlar:")
    for message in result.messages:
        print(f"  • {message}")
    
    return result


def example_2_create_transaction():
    """
    Senaryo 2: İşlenmiş dekonttan Transaction oluşturma
    
    Bu senaryo:
    1. Dekontu işler
    2. Sonucu kullanarak Transaction verisi oluşturur
    3. Transaction'ı kaydeder (simulasyon)
    """
    print("\n\n" + "=" * 80)
    print("SENARYO 2: Transaction Oluşturma")
    print("=" * 80)
    
    # 1. Önce dekontu işle
    data_loader = DataLoader("../backend-models")
    data = data_loader.load_all()
    
    processor = ReceiptProcessor(
        owners=data["owners"],
        customers=data["customers"],
        properties=data["properties"],
        rental_contracts=data["rental_contracts"],
    )
    
    pdf_path = Path("../../../data/halkbank.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF dosyası bulunamadı: {pdf_path}")
        return
    
    result = processor.process_receipt(
        pdf_path=pdf_path,
        expected_amount=15000.0,
        min_confidence=70.0,
    )
    
    # 2. Transaction manager oluştur
    transaction_manager = TransactionManager(
        owners=data["owners"],
        properties=data["properties"],
        rental_contracts=data["rental_contracts"],
        accounts=data["accounts"],
    )
    
    # 3. Transaction verisi oluştur
    transaction_data = transaction_manager.create_transaction_from_receipt(
        extracted_fields=result.extracted_fields,
        matched_owner_id=result.matched_owner_id,
        matched_customer_id=result.matched_customer_id,
        matched_property_id=result.matched_property_id,
        receipt_status=result.status,
    )
    
    # 4. Sonuçları göster
    print("\n💰 Oluşturulan Transaction:")
    print(f"  • Tutar: {transaction_data.amount:.2f} {transaction_data.amount_currency}")
    print(f"  • Durum: {transaction_data.status}")
    print(f"  • Tip: {transaction_data.transaction_type}")
    print(f"  • Yön: {transaction_data.direction}")
    print(f"  • Property ID: {transaction_data.rental_property_id}")
    print(f"  • Contract ID: {transaction_data.rental_contract_id}")
    print(f"  • Account ID: {transaction_data.account_id}")
    print(f"  • Ödeme Tarihi: {transaction_data.payment_date}")
    print(f"  • Vade Tarihi: {transaction_data.due_date}")
    print(f"  • Referans No: {transaction_data.reference_number}")
    print(f"  • Açıklama: {transaction_data.description[:100]}...")
    
    print("\n💾 Transaction Dictionary:")
    import json
    print(json.dumps(transaction_data.to_dict(), indent=2, ensure_ascii=False))
    
    return transaction_data


def example_3_multiple_receipts():
    """
    Senaryo 3: Birden fazla dekontun toplu işlenmesi
    
    Bu senaryo:
    1. Birden fazla PDF dekontunu işler
    2. Her biri için sonuç üretir
    3. Toplu rapor gösterir
    """
    print("\n\n" + "=" * 80)
    print("SENARYO 3: Toplu Dekont İşleme")
    print("=" * 80)
    
    # 1. Verileri yükle
    data_loader = DataLoader("../backend-models")
    data = data_loader.load_all()
    
    # 2. Receipt processor oluştur
    processor = ReceiptProcessor(
        owners=data["owners"],
        customers=data["customers"],
        properties=data["properties"],
        rental_contracts=data["rental_contracts"],
    )
    
    # 3. Dekont listesi
    pdf_paths = [
        Path("../../../data/halkbank.pdf"),
        Path("../../../data/yapikredi.pdf"),
        Path("../../../data/kuveytturk.pdf"),
        Path("../../../data/ziraatbank.pdf"),
    ]
    
    # Mevcut dosyaları filtrele
    existing_pdfs = [p for p in pdf_paths if p.exists()]
    
    if not existing_pdfs:
        print("❌ Hiç PDF dosyası bulunamadı!")
        print("Lütfen data/ klasörüne örnek dekontlar ekleyin.")
        return
    
    print(f"\n📁 İşlenecek {len(existing_pdfs)} dekont bulundu.")
    
    # 4. Dekontları işle
    results = processor.process_multiple_receipts(
        pdf_paths=existing_pdfs,
        expected_amounts=[15000.0] * len(existing_pdfs),
        min_confidence=70.0,
    )
    
    # 5. Özet rapor
    print("\n📊 Özet Rapor:")
    print(f"  • Toplam İşlenen: {len(results)}")
    
    approved = sum(1 for r in results if r.status == "approved")
    rejected = sum(1 for r in results if r.status == "rejected")
    manual_review = sum(1 for r in results if r.status == "manual_review")
    
    print(f"  • Onaylanan: {approved}")
    print(f"  • Reddedilen: {rejected}")
    print(f"  • Manuel İnceleme: {manual_review}")
    
    # 6. Detaylı sonuçlar
    print("\n📋 Detaylı Sonuçlar:")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. Dekont ({existing_pdfs[i-1].name}):")
        print(f"     • Durum: {result.status}")
        print(f"     • Banka: {result.detected_bank or 'Tespit edilemedi'}")
        print(f"     • Tutar: {result.extracted_fields.get('amount', 'N/A')}")
        print(f"     • Eşleşme: {result.match_confidence:.1f}%")
        print(f"     • Validasyon: {'✓' if result.is_valid else '✗'}")
        
        if result.validation_errors:
            print(f"     • Hatalar: {len(result.validation_errors)}")
    
    return results


def example_4_manual_validation():
    """
    Senaryo 4: Manuel validasyon
    
    Bu senaryo:
    1. OCR çıktısını manuel olarak validasyon yapar
    2. Hata ve uyarıları gösterir
    """
    print("\n\n" + "=" * 80)
    print("SENARYO 4: Manuel Validasyon")
    print("=" * 80)
    
    # 1. Verileri yükle
    data_loader = DataLoader("../backend-models")
    data = data_loader.load_all()
    
    # 2. Validator oluştur
    validator = ReceiptValidator(
        owners=data["owners"],
        customers=data["customers"],
        properties=data["properties"],
        rental_contracts=data["rental_contracts"],
    )
    
    # 3. Örnek OCR çıktısı (manuel)
    extracted_fields = {
        "sender": "Ali Veli",
        "sender_iban": "TR640001000268320315270001",
        "recipient": "Ahmet Yılmaz",
        "receiver_iban": "TR330006100519786457841326",
        "amount": "15.000,00",
        "amount_currency": "TRY",
        "date": "21.11.2024",
        "description": "Kira ödemesi - Kadıköy Daire",
    }
    
    print("\n📝 Test Edilen Veriler:")
    for key, value in extracted_fields.items():
        print(f"  • {key}: {value}")
    
    # 4. Validasyon yap
    result = validator.validate(
        extracted_fields=extracted_fields,
        matched_owner_id=1,
        matched_customer_id=1,
        matched_property_id=1,
        expected_amount=15000.0,
    )
    
    # 5. Sonuçları göster
    print(f"\n✅ Validasyon Sonucu: {'BAŞARILI' if result.is_valid else 'BAŞARISIZ'}")
    
    if result.messages:
        print("\n💬 Mesajlar:")
        for message in result.messages:
            print(f"  • {message}")
    
    if result.errors:
        print("\n❌ Hatalar:")
        for error in result.errors:
            print(f"  • {error}")
    
    if result.warnings:
        print("\n⚠️  Uyarılar:")
        for warning in result.warnings:
            print(f"  • {warning}")
    
    if result.details:
        print("\n📊 Detaylar:")
        import json
        print(json.dumps(result.details, indent=2, ensure_ascii=False))
    
    return result


def example_5_transaction_approval_flow():
    """
    Senaryo 5: Transaction onay akışı
    
    Bu senaryo tam bir iş akışını gösterir:
    1. Dekont işleme
    2. Transaction oluşturma
    3. Onay/Red işlemleri
    """
    print("\n\n" + "=" * 80)
    print("SENARYO 5: Transaction Onay Akışı")
    print("=" * 80)
    
    # 1. Verileri yükle ve dekontu işle
    data_loader = DataLoader("../backend-models")
    data = data_loader.load_all()
    
    processor = ReceiptProcessor(
        owners=data["owners"],
        customers=data["customers"],
        properties=data["properties"],
        rental_contracts=data["rental_contracts"],
    )
    
    pdf_path = Path("../../../data/halkbank.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF dosyası bulunamadı: {pdf_path}")
        return
    
    result = processor.process_receipt(
        pdf_path=pdf_path,
        expected_amount=15000.0,
        min_confidence=70.0,
    )
    
    # 2. Transaction oluştur
    transaction_manager = TransactionManager(
        owners=data["owners"],
        properties=data["properties"],
        rental_contracts=data["rental_contracts"],
        accounts=data["accounts"],
    )
    
    transaction_data = transaction_manager.create_transaction_from_receipt(
        extracted_fields=result.extracted_fields,
        matched_owner_id=result.matched_owner_id,
        matched_customer_id=result.matched_customer_id,
        matched_property_id=result.matched_property_id,
        receipt_status=result.status,
    )
    
    print(f"\n1️⃣  Dekont işlendi - Durum: {result.status}")
    print(f"2️⃣  Transaction oluşturuldu - ID: 123 (simülasyon)")
    
    # 3. Onay/Red senaryoları
    transaction_id = 123  # Simülasyon ID
    
    if result.status == "approved":
        # Otomatik onay
        print("\n3️⃣  Otomatik onay gerçekleşti")
        approve_result = transaction_manager.approve_transaction(
            transaction_id=transaction_id,
            approved_by="SYSTEM",
        )
        print(f"   ✓ Transaction onaylandı")
        print(f"   ✓ Durum: {approve_result['new_status']}")
        print(f"   ✓ Neden: {approve_result['reason']}")
        
    elif result.status == "manual_review":
        # Manuel onay
        print("\n3️⃣  Manuel onay bekleniyor")
        print("   ⏳ Emlakçı incelemesi gerekiyor...")
        
        # Simülasyon: Emlakçı onayladı
        approve_result = transaction_manager.approve_transaction(
            transaction_id=transaction_id,
            approved_by="admin@emlak.com",
        )
        print(f"   ✓ Manuel onay yapıldı")
        print(f"   ✓ Durum: {approve_result['new_status']}")
        print(f"   ✓ Onaylayan: admin@emlak.com")
        
    else:
        # Red
        print("\n3️⃣  Transaction reddedildi")
        reject_result = transaction_manager.reject_transaction(
            transaction_id=transaction_id,
            rejection_reason="Tutar uyuşmazlığı",
            rejected_by="admin@emlak.com",
        )
        print(f"   ✗ Durum: {reject_result['new_status']}")
        print(f"   ✗ Neden: {reject_result['reason']}")
    
    print("\n✅ İş akışı tamamlandı!")


def main():
    """Ana fonksiyon - Tüm senaryoları çalıştırır."""
    print("\n" + "=" * 80)
    print("BACKEND-OCR ENTEGRASYON SERVİSİ - ÖRNEK KULLANIM SENARYOLARI")
    print("=" * 80)
    
    try:
        # Senaryo 1: Tek dekont işleme
        example_1_process_single_receipt()
        
        # Senaryo 2: Transaction oluşturma
        example_2_create_transaction()
        
        # Senaryo 3: Toplu işleme
        # example_3_multiple_receipts()  # Tüm PDF'ler hazırsa yorum satırını kaldır
        
        # Senaryo 4: Manuel validasyon
        example_4_manual_validation()
        
        # Senaryo 5: Tam akış
        example_5_transaction_approval_flow()
        
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

