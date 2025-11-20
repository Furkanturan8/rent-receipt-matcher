# Dekont Eşleştirme Sistemi

Bu dokümantasyon, OCR ile çıkarılan dekont verilerini backend database'deki kayıtlarla eşleştirme sistemini açıklar.

## Genel Bakış

Sistem 3 ana bileşenden oluşur:

1. **OCR Extraction**: PDF'den veri çıkarma (`ocr.extraction`)
2. **Normalization**: Verileri normalize etme (`ocr.matching.normalizers`)
3. **Matching**: Database kayıtlarıyla eşleştirme (`ocr.matching.matcher`)

## Eşleştirme Algoritması

Mock data'daki öncelik sırasına göre:

### 1. IBAN Eşleşmesi (Öncelik: 1, Güven: 95)
- Alıcı IBAN'ı Owner IBAN ile tam eşleşmeli
- Normalize edilmiş IBAN'lar karşılaştırılır
- OCR hataları düzeltilir (O→0, I→1)

### 2. Tutar Eşleşmesi (Öncelik: 2, Güven: 85)
- Dekont tutarı property price ile eşleşmeli
- ±%5 tolerans kabul edilir
- Farklı formatlar normalize edilir (45.000,00 → 45000.00)

### 3. İsim Benzerliği (Öncelik: 3, Güven: 75)
- Alıcı adı Owner ismi ile fuzzy match
- Levenshtein distance + Jaccard similarity
- Türkçe karakterler normalize edilir

### 4. Adres Bilgisi (Öncelik: 4, Güven: 70)
- Açıklama içinde property address parçaları
- Mahalle, sokak, daire no gibi keywords çıkarılır
- Keyword bazlı Jaccard similarity

### 5. Gönderen Bilgisi (Öncelik: 5, Güven: 60)
- Gönderen adı Customer ismi ile eşleşmeli
- Fuzzy matching kullanılır

## Kullanım

### Backend'de Kullanım (Django)

```python
from ocr.extraction.extractor import extract_fields
from ocr.extraction.bank_detector import detect_bank
from ocr.matching.matcher import match_receipt
from ocr.matching.mapper import map_ocr_to_receipt_fields, update_receipt_with_match
from pdfminer.high_level import extract_text
from .models import RentReceipt, Owner, Customer, Property

def process_receipt_upload(pdf_file):
    # 1. PDF'den metin çıkar
    text = extract_text(pdf_file)
    
    # 2. Bankayı tespit et
    detected_bank = detect_bank(text)
    
    # 3. OCR ile alanları çıkar
    ocr_data = extract_fields(text, bank_hint=detected_bank)
    
    # 4. RentReceipt oluştur
    receipt = RentReceipt()
    receipt_fields = map_ocr_to_receipt_fields(ocr_data)
    for key, value in receipt_fields.items():
        setattr(receipt, key, value)
    receipt.save()
    
    # 5. Database kayıtlarını al
    owners = list(Owner.objects.values('id', 'full_name', 'iban'))
    customers = list(Customer.objects.values('id', 'full_name'))
    properties = list(Property.objects.values('id', 'owner_id', 'address', 'price'))
    
    # 6. Eşleştirme yap
    match_result = match_receipt(
        ocr_data=ocr_data,
        owners=owners,
        customers=customers,
        properties=properties,
        min_confidence=70.0,
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
    receipt.matching_details = {
        "iban_match_score": match_result.iban_match_score,
        "amount_match_score": match_result.amount_match_score,
        "name_match_score": match_result.name_match_score,
        "address_match_score": match_result.address_match_score,
        "sender_match_score": match_result.sender_match_score,
        "messages": match_result.messages,
        **match_result.matching_details,
    }
    receipt.save()
    
    return receipt
```

### Eşleştirme Durumları

- **pending**: İlk kayıt, henüz eşleştirilmedi
- **matched**: Başarıyla eşleştirildi (güven skoru ≥70)
- **manual_review**: Manuel inceleme gerekli (düşük güven veya çoklu aday)
- **rejected**: Reddedildi

### Güven Skoru Hesaplama

Toplam güven skoru, her kriterin ağırlıklı ortalamasıdır:

```
Total Score = (IBAN×95 + Amount×85 + Name×75 + Address×70 + Sender×60) / 385
```

- **≥90**: Yüksek güven, otomatik eşleştirme
- **70-89**: Orta güven, eşleştirme yapılır ama kontrol edilebilir
- **<70**: Düşük güven, manuel inceleme gerekli

## Normalizasyon Kuralları

### IBAN
- Boşlukları kaldır
- Büyük harfe çevir
- OCR hataları: O→0, I→1

### İsim
- Büyük harfe çevir
- Türkçe karakterleri normalize et (ı→I, ş→S, ğ→G, ü→U, ö→O, ç→C)
- Çift boşlukları temizle

### Tutar
- Nokta/virgül standardize et
- TL/TRY/₺ temizle
- Float'a çevir

### Tarih
- Farklı formatları destekle (DD.MM.YYYY, DD/MM/YYYY)
- OCR hataları için 0/O kontrolü

## Test

Mock data ile test:

```bash
python -m ocr.matching.example_usage
```

## Modüller

- `ocr.matching.normalizers`: Veri normalizasyonu
- `ocr.matching.fuzzy`: Fuzzy matching algoritmaları
- `ocr.matching.matcher`: Ana eşleştirme motoru
- `ocr.matching.mapper`: OCR→Model mapping

