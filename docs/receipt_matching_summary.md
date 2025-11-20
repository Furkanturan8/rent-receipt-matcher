# Dekont Eşleştirme Sistemi - Özet

## 🎯 Sistem Genel Bakış

OCR ile çıkarılan dekont verilerini backend database'deki kayıtlarla otomatik eşleştiren bir sistem.

### Akış
```
PDF Upload → OCR Extraction → Normalization → Matching → RentReceipt Model
```

## 📦 Oluşturulan Modüller

### 1. `ocr.matching.normalizers`
Veri normalizasyonu:
- `normalize_iban()`: IBAN'ı standardize et (boşluk kaldır, OCR hataları düzelt)
- `normalize_name()`: İsimleri normalize et (Türkçe karakterler, büyük harf)
- `normalize_amount()`: Tutar metnini float'a çevir
- `normalize_date()`: Tarih formatlarını parse et

### 2. `ocr.matching.fuzzy`
Fuzzy matching algoritmaları:
- `levenshtein_similarity()`: Karakter bazlı benzerlik
- `jaccard_similarity()`: N-gram bazlı benzerlik
- `name_similarity()`: İsim benzerliği (hibrit)
- `address_similarity()`: Adres benzerliği (keyword bazlı)

### 3. `ocr.matching.matcher`
Ana eşleştirme motoru:
- `match_receipt()`: OCR çıktısını database ile eşleştir
- `ReceiptMatchResult`: Eşleştirme sonucu dataclass
- Mock data'daki öncelik sırasına göre implement edildi

### 4. `ocr.matching.mapper`
OCR → Model mapping:
- `map_ocr_to_receipt_fields()`: OCR çıktısını RentReceipt alanlarına map et
- `update_receipt_with_match()`: Eşleştirme sonucunu receipt'e ekle

## 🔍 Eşleştirme Algoritması

Mock data'daki öncelik sırası:

| # | Kriter | Ağırlık | Açıklama |
|---|--------|---------|----------|
| 1 | IBAN | 95 | Alıcı IBAN = Owner IBAN (tam eşleşme) |
| 2 | Tutar | 85 | Dekont tutarı = Property price (±%5) |
| 3 | İsim | 75 | Alıcı adı ≈ Owner ismi (fuzzy) |
| 4 | Adres | 70 | Açıklama içinde property address |
| 5 | Gönderen | 60 | Gönderen adı ≈ Customer ismi |

**Güven Skoru:**
```
(IBAN×95 + Amount×85 + Name×75 + Address×70 + Sender×60) / 385 × 100
```

- **≥90**: Yüksek güven, otomatik eşleştirme
- **70-89**: Orta güven, eşleştirme yapılır
- **<70**: Manuel inceleme gerekli

## 🚀 Kullanım Örneği

### Backend'de (Django)

```python
from ocr.extraction.extractor import extract_fields
from ocr.extraction.bank_detector import detect_bank
from ocr.matching.matcher import match_receipt
from ocr.matching.mapper import map_ocr_to_receipt_fields, update_receipt_with_match
from pdfminer.high_level import extract_text

def process_receipt(pdf_file):
    # 1. OCR
    text = extract_text(pdf_file)
    bank = detect_bank(text)
    ocr_data = extract_fields(text, bank_hint=bank)
    
    # 2. RentReceipt oluştur
    receipt = RentReceipt()
    receipt_fields = map_ocr_to_receipt_fields(ocr_data)
    for key, value in receipt_fields.items():
        setattr(receipt, key, value)
    receipt.save()
    
    # 3. Eşleştir
    owners = list(Owner.objects.values('id', 'full_name', 'iban'))
    customers = list(Customer.objects.values('id', 'full_name'))
    properties = list(Property.objects.values('id', 'owner_id', 'address', 'price'))
    
    match_result = match_receipt(
        ocr_data=ocr_data,
        owners=owners,
        customers=customers,
        properties=properties,
        min_confidence=70.0,
    )
    
    # 4. Sonuçları kaydet
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
    }
    receipt.save()
    
    return receipt
```

## ✅ Test Sonuçları

Mock data ile test edildi:

```
DEKONT_001: Standart kira ödemesi
  ✓ Owner ID: 1 (Beklenen: 1)
  ✓ Property ID: 1 (Beklenen: 1)
  ✓ Customer ID: 1 (Beklenen: 1)
  Güven Skoru: 81.8/100
  Durum: matched
```

## 📁 Dosya Yapısı

```
src/ocr/
├── extraction/          # OCR ve banka tespiti
│   ├── extractor.py
│   ├── bank_detector.py
│   ├── logo_detector.py
│   └── regex_patterns.py
└── matching/            # Eşleştirme sistemi
    ├── matcher.py       # Ana eşleştirme motoru
    ├── normalizers.py   # Veri normalizasyonu
    ├── fuzzy.py         # Fuzzy matching
    └── mapper.py        # OCR→Model mapping
```

## 🎯 Özellikler

- ✅ Mock data'daki öncelik sırasına göre implement edildi
- ✅ Fuzzy matching (Levenshtein + Jaccard)
- ✅ OCR hatalarına karşı dayanıklı normalizasyon
- ✅ Ağırlıklı güven skoru hesaplama
- ✅ Detaylı eşleştirme bilgileri
- ✅ Backend entegrasyonu için hazır

## 📚 Dokümantasyon

- `docs/receipt_matching_system.md`: Detaylı sistem açıklaması
- `docs/receipt_matching_integration.md`: Backend entegrasyon rehberi
- `src/ocr/matching/example_usage.py`: Kullanım örnekleri

