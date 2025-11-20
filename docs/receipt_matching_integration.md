# Dekont Eşleştirme Sistemi - Backend Entegrasyonu

Bu dokümantasyon, OCR çıktısını backend database ile eşleştirme sisteminin Django backend'e nasıl entegre edileceğini açıklar.

## Sistem Mimarisi

```
PDF Upload → OCR Extraction → Normalization → Matching → RentReceipt Model
```

## Adım Adım Entegrasyon

### 1. PDF Upload ve OCR İşleme

```python
# views.py veya services/receipt_service.py
from ocr.extraction.extractor import extract_fields
from ocr.extraction.bank_detector import detect_bank
from ocr.matching.matcher import match_receipt
from ocr.matching.mapper import map_ocr_to_receipt_fields, update_receipt_with_match
from pdfminer.high_level import extract_text
from .models import RentReceipt, Owner, Customer, Property

def process_receipt_upload(pdf_file, user=None):
    """
    PDF dekontunu yükle, OCR yap, eşleştir ve kaydet.
    """
    # 1. PDF'den metin çıkar
    text = extract_text(pdf_file)
    
    # 2. Bankayı otomatik tespit et
    detected_bank = detect_bank(text)
    
    # 3. OCR ile alanları çıkar
    ocr_data = extract_fields(text, bank_hint=detected_bank)
    
    # 4. RentReceipt oluştur
    receipt = RentReceipt()
    
    # OCR çıktısını model alanlarına map et
    receipt_fields = map_ocr_to_receipt_fields(ocr_data)
    for key, value in receipt_fields.items():
        setattr(receipt, key, value)
    
    # Görsel dosyasını kaydet
    receipt.receipt_image = pdf_file
    receipt.save()
    
    # 5. Database kayıtlarını al (queryset'ten dict'e çevir)
    owners = list(Owner.objects.values('id', 'full_name', 'iban'))
    customers = list(Customer.objects.values('id', 'full_name'))
    properties = list(Property.objects.values('id', 'owner_id', 'address', 'price'))
    
    # 6. Eşleştirme yap
    match_result = match_receipt(
        ocr_data=ocr_data,
        owners=owners,
        customers=customers,
        properties=properties,
        min_confidence=70.0,  # %70 minimum güven
    )
    
    # 7. Eşleştirme sonucunu kaydet
    if match_result.owner_id:
        receipt.matched_owner_id = match_result.owner_id
    if match_result.property_id:
        receipt.matched_property_id = match_result.property_id
    if match_result.customer_id:
        receipt.matched_customer_id = match_result.customer_id
    
    receipt.match_status = match_result.match_status
    receipt.match_confidence = match_result.confidence_score
    
    # Detaylı eşleştirme bilgileri
    receipt.matching_details = {
        "iban_match_score": match_result.iban_match_score,
        "amount_match_score": match_result.amount_match_score,
        "name_match_score": match_result.name_match_score,
        "address_match_score": match_result.address_match_score,
        "sender_match_score": match_result.sender_match_score,
        "messages": match_result.messages,
        "detected_bank": detected_bank,
        **match_result.matching_details,
    }
    
    receipt.save()
    
    return receipt
```

### 2. API Endpoint Örneği

```python
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.receipt_service import process_receipt_upload

class ReceiptUploadView(APIView):
    def post(self, request):
        pdf_file = request.FILES.get('receipt')
        if not pdf_file:
            return Response(
                {"error": "PDF dosyası gerekli"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            receipt = process_receipt_upload(pdf_file, user=request.user)
            
            return Response({
                "receipt_id": receipt.id,
                "match_status": receipt.match_status,
                "confidence_score": float(receipt.match_confidence) if receipt.match_confidence else None,
                "matched_owner_id": receipt.matched_owner_id,
                "matched_property_id": receipt.matched_property_id,
                "matched_customer_id": receipt.matched_customer_id,
                "messages": receipt.matching_details.get("messages", []),
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### 3. Eşleştirme Durumlarına Göre İşlem

```python
def handle_receipt_match_status(receipt):
    """
    Eşleştirme durumuna göre işlem yap.
    """
    if receipt.match_status == ReceiptMatchStatus.MATCHED:
        # Otomatik eşleştirme başarılı
        if receipt.match_confidence >= 90:
            # Yüksek güven - otomatik ödeme kaydı oluştur
            create_payment_from_receipt(receipt)
        else:
            # Orta güven - bildirim gönder, onay bekle
            send_receipt_review_notification(receipt)
    
    elif receipt.match_status == ReceiptMatchStatus.MANUAL_REVIEW:
        # Manuel inceleme gerekli
        send_manual_review_notification(receipt)
    
    elif receipt.match_status == ReceiptMatchStatus.REJECTED:
        # Reddedildi
        send_rejection_notification(receipt)
```

### 4. Manuel Eşleştirme Override

```python
def manual_match_receipt(receipt_id, owner_id, property_id, customer_id=None, user=None):
    """
    Manuel eşleştirme override.
    """
    receipt = RentReceipt.objects.get(id=receipt_id)
    
    receipt.matched_owner_id = owner_id
    receipt.matched_property_id = property_id
    if customer_id:
        receipt.matched_customer_id = customer_id
    
    receipt.match_status = ReceiptMatchStatus.MATCHED
    receipt.manually_verified = True
    receipt.verified_by = user.username if user else "system"
    receipt.verified_at = timezone.now()
    receipt.save()
    
    # Ödeme kaydı oluştur
    create_payment_from_receipt(receipt)
```

## Eşleştirme Kriterleri ve Ağırlıklar

Mock data'daki öncelik sırasına göre:

| Kriter | Öncelik | Ağırlık | Açıklama |
|--------|---------|---------|----------|
| IBAN | 1 | 95 | Alıcı IBAN = Owner IBAN (tam eşleşme) |
| Tutar | 2 | 85 | Dekont tutarı = Property price (±%5 tolerans) |
| İsim | 3 | 75 | Alıcı adı ≈ Owner ismi (fuzzy match) |
| Adres | 4 | 70 | Açıklama içinde property address keywords |
| Gönderen | 5 | 60 | Gönderen adı ≈ Customer ismi |

**Güven Skoru Hesaplama:**
```
Total Score = (IBAN×95 + Amount×85 + Name×75 + Address×70 + Sender×60) / 385 × 100
```

- **≥90**: Yüksek güven, otomatik eşleştirme
- **70-89**: Orta güven, eşleştirme yapılır
- **<70**: Düşük güven, manuel inceleme

## Normalizasyon

Tüm veriler eşleştirme öncesi normalize edilir:

- **IBAN**: Boşluk kaldır, büyük harf, OCR hataları düzelt (O→0, I→1)
- **İsim**: Büyük harf, Türkçe karakter normalize (ı→I, ş→S, etc.)
- **Tutar**: Format standardize et (45.000,00 → 45000.00)
- **Tarih**: Farklı formatları destekle

## Fuzzy Matching

- **Levenshtein Distance**: Karakter bazlı benzerlik
- **Jaccard Similarity**: N-gram bazlı benzerlik
- **Hibrit**: Her ikisinin ağırlıklı ortalaması

## Test Senaryoları

Mock data'daki örnekler:

1. **DEKONT_001**: Standart kira ödemesi - IBAN + Tutar + İsim eşleşmesi
2. **DEKONT_002**: İsim farklılıkları - Fuzzy matching gerekli
3. **DEKONT_003**: Kurumsal ödeme - Gönderen kurum adı
4. **DEKONT_004**: Eksik bilgili - Sadece IBAN ve tutar
5. **DEKONT_005**: OCR hataları - Normalizasyon kritik

## Öneriler

1. **Async Processing**: Büyük PDF'ler için background task kullan
2. **Caching**: Owner/Customer/Property listelerini cache'le
3. **Logging**: Tüm eşleştirme adımlarını logla
4. **Monitoring**: Güven skoru dağılımını izle
5. **Feedback Loop**: Manuel düzeltmeleri öğrenme için kullan

