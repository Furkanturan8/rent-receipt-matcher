# Backend-OCR Entegrasyon Dokümantasyonu

## 📋 Genel Bakış

Bu dokümantasyon, OCR teknolojisi ile backend sisteminin nasıl entegre edildiğini ve kira dekontlarının otomatik işleme akışını açıklar.

## 🎯 Entegrasyon Amacı

Emlakçılar için kira takibini otomatikleştirmek amacıyla:

1. **Kiracı** → Mülk sahibine kira ödemesi yapar
2. **Kiracı** → Banka dekontunu sisteme yükler
3. **Sistem** → OCR ile dekontu işler ve doğrular
4. **Sistem** → Owner, Customer, Property ile eşleştirir
5. **Sistem** → Transaction kaydı oluşturur
6. **Sistem** → Onay/Red/Manuel İnceleme kararı verir
7. **Emlakçı** → Manuel inceleme gerekiyorsa onaylar/reddeder

## 🏗️ Mimari

### Katmanlı Mimari

```
┌───────────────────────────────────────────────────────────┐
│                    Presentation Layer                      │
│              (Django Views / REST API)                     │
└───────────────────┬───────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────┐
│                   Service Layer                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ receipt_processor.py                              │    │
│  │  - PDF okuma                                      │    │
│  │  - OCR koordinasyonu                              │    │
│  │  - Eşleştirme                                     │    │
│  │  - Validasyon                                     │    │
│  └──────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ validators.py                                     │    │
│  │  - IBAN kontrolü                                  │    │
│  │  - Tutar kontrolü                                 │    │
│  │  - İlişki kontrolü                                │    │
│  └──────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ transaction_manager.py                            │    │
│  │  - Transaction oluşturma                          │    │
│  │  - Durum yönetimi                                 │    │
│  │  - Onay/Red                                       │    │
│  └──────────────────────────────────────────────────┘    │
└───────────────────┬───────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────┐
│                    OCR Layer                               │
│  ┌──────────────────────────────────────────────────┐    │
│  │ bank_detector.py                                  │    │
│  │  - Metin tabanlı tespit                           │    │
│  │  - Logo tabanlı tespit                            │    │
│  └──────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ extractor.py                                      │    │
│  │  - Regex pattern matching                         │    │
│  │  - Alan çıkarma (tutar, IBAN, ad, tarih)         │    │
│  └──────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ matcher.py                                        │    │
│  │  - Fuzzy matching                                 │    │
│  │  - Database eşleştirme                            │    │
│  └──────────────────────────────────────────────────┘    │
└───────────────────┬───────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────┐
│                    Data Layer                              │
│              (Django ORM / PostgreSQL)                     │
│                                                             │
│  Models: Owner, Customer, Property, RentalContract,       │
│          Transaction, Account, Tenant                      │
└───────────────────────────────────────────────────────────┘
```

## 📦 Servis Katmanı Modülleri

### 1. Receipt Processor (receipt_processor.py)

**Sorumluluklar:**
- PDF dosyasını okuma (PyMuPDF)
- Banka tespiti (metin + logo)
- OCR modüllerini koordine etme
- Validasyon tetikleme
- Sonuç birleştirme

**API:**
```python
processor = ReceiptProcessor(owners, customers, properties, rental_contracts)
result = processor.process_receipt(
    pdf_path="receipt.pdf",
    expected_amount=15000.0,
    expected_owner_id=1,
    min_confidence=70.0
)
```

**Dönen Veri:**
```python
ReceiptProcessingResult(
    success=True,
    status="approved",  # approved/manual_review/rejected
    detected_bank="halkbank",
    extracted_fields={...},
    matched_owner_id=1,
    matched_customer_id=2,
    matched_property_id=3,
    match_confidence=95.5,
    is_valid=True,
    validation_errors=[],
    validation_warnings=[],
    messages=["✓ Dekont otomatik olarak onaylandı"],
    details={...}
)
```

### 2. Validator (validators.py)

**Sorumluluklar:**
- IBAN formatı kontrolü (TR + 24 rakam)
- Tutar doğrulama (±%5 tolerans)
- Tarih kontrolü (geçmiş/gelecek)
- Mülk sahibi-Mülk ilişkisi kontrolü
- Aktif sözleşme kontrolü
- Zorunlu alan kontrolü

**API:**
```python
validator = ReceiptValidator(owners, customers, properties, rental_contracts)
result = validator.validate(
    extracted_fields={...},
    matched_owner_id=1,
    matched_customer_id=2,
    matched_property_id=3,
    expected_amount=15000.0
)
```

**Dönen Veri:**
```python
ValidationResult(
    is_valid=True,
    errors=[],
    warnings=["Tutar beklenen değerden farklı"],
    messages=["✓ Tüm validasyonlar başarılı"],
    details={...}
)
```

### 3. Transaction Manager (transaction_manager.py)

**Sorumluluklar:**
- Dekont verisinden Transaction oluşturma
- Durum yönetimi (pending → approved/rejected)
- Onay/Red işlemleri
- Cari hesap entegrasyonu

**API:**
```python
manager = TransactionManager(owners, properties, rental_contracts, accounts)

# Transaction oluştur
transaction_data = manager.create_transaction_from_receipt(
    extracted_fields={...},
    matched_owner_id=1,
    matched_customer_id=2,
    matched_property_id=3,
    receipt_status="approved"
)

# Onayla
approve_result = manager.approve_transaction(
    transaction_id=123,
    approved_by="admin@example.com"
)

# Reddet
reject_result = manager.reject_transaction(
    transaction_id=123,
    rejection_reason="IBAN uyuşmazlığı",
    rejected_by="admin@example.com"
)
```

**Dönen Veri:**
```python
TransactionData(
    rental_contract_id=1,
    rental_property_id=3,
    account_id=5,
    transaction_type="rent_payment",
    direction="in",
    status="completed",
    amount=15000.0,
    amount_currency="TRY",
    due_date="2024-11-05",
    payment_date="2024-11-21",
    payment_method="bank_transfer",
    reference_number="DEKONT-20241121120530",
    description="Gönderen: Ali Veli | Alıcı: Ahmet Yılmaz",
    notes="Mülk Sahibi ID: 1 | OCR ile otomatik oluşturuldu",
    ocr_data={...}
)
```

## 🔄 Tam İş Akışı

### Adım 1: PDF Yükleme

```python
# Kullanıcı (kiracı/emlakçı) PDF yükler
pdf_file = request.FILES['receipt']
```

### Adım 2: OCR İşleme

```python
# Processor ile işle
processor = ReceiptProcessor(...)
result = processor.process_receipt(pdf_path)
```

**Alt Adımlar:**
1. PDF'den metin çıkar (PyMuPDF)
2. Banka tespit et (bank_detector)
3. Alanları çıkar (extractor)
4. Database ile eşleştir (matcher)
5. Validasyon yap (validators)

### Adım 3: Karar Verme

```python
if result.match_confidence >= 90 and result.is_valid:
    # Otomatik onay
    status = "approved"
elif result.match_confidence >= 70:
    # Manuel inceleme
    status = "manual_review"
else:
    # Otomatik red
    status = "rejected"
```

### Adım 4: Transaction Oluşturma

```python
# Transaction manager ile kayıt oluştur
manager = TransactionManager(...)
transaction_data = manager.create_transaction_from_receipt(
    extracted_fields=result.extracted_fields,
    matched_owner_id=result.matched_owner_id,
    matched_customer_id=result.matched_customer_id,
    matched_property_id=result.matched_property_id,
    receipt_status=result.status
)

# Database'e kaydet (Django ORM)
transaction = Transaction.objects.create(**transaction_data.to_dict())
```

### Adım 5: Bildirim

```python
# Emlakçıya bildirim gönder
if result.status == "manual_review":
    send_notification(
        to=realtor_email,
        subject="Manuel İnceleme Gerekli",
        message=f"Dekont ID: {transaction.id}"
    )
```

## 🎨 Durum Diyagramı

```
                    ┌──────────────┐
                    │ PDF Yüklendi │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ OCR İşleme   │
                    └──────┬───────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
                ▼          ▼          ▼
         ┌──────────┐ ┌─────────┐ ┌──────────┐
         │ Güven≥90%│ │ 70-89%  │ │ Güven<70%│
         └─────┬────┘ └────┬────┘ └─────┬────┘
               │           │             │
               ▼           ▼             ▼
         ┌──────────┐ ┌─────────┐ ┌──────────┐
         │ ONAY     │ │ MANUEL  │ │ RED      │
         │          │ │ İNCELE  │ │          │
         └─────┬────┘ └────┬────┘ └─────┬────┘
               │           │             │
               │      ┌────┴────┐        │
               │      │         │        │
               │      ▼         ▼        │
               │  ┌────────┐ ┌────────┐ │
               │  │ ONAYLA │ │ REDDET │ │
               │  └───┬────┘ └───┬────┘ │
               │      │          │      │
               ▼      ▼          ▼      ▼
         ┌──────────────────────────────────┐
         │ Transaction Oluştur              │
         │ Status: COMPLETED/PENDING/REJECTED│
         └──────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Bildirim     │
                    │ Gönder       │
                    └──────────────┘
```

## 🔐 Güvenlik Considerations

### 1. PDF Dosya Kontrolü

```python
# Dosya boyutu kontrolü (max 10MB)
if pdf_file.size > 10 * 1024 * 1024:
    raise ValidationError("Dosya çok büyük")

# MIME type kontrolü
if pdf_file.content_type != 'application/pdf':
    raise ValidationError("Sadece PDF dosyaları kabul edilir")
```

### 2. IBAN Doğrulama

```python
# IBAN formatı
if not re.match(r'^TR\d{24}$', iban):
    raise ValidationError("Geçersiz IBAN formatı")

# IBAN owner ile eşleşiyor mu?
if iban != owner.iban:
    # Manuel inceleme gerekli
    status = "manual_review"
```

### 3. Tutar Limitleri

```python
# Maksimum tutar kontrolü
MAX_AMOUNT = 100000.0  # 100.000 TL
if amount > MAX_AMOUNT:
    # Manuel inceleme gerekli
    status = "manual_review"
```

## 📊 Performans ve Optimizasyon

### 1. Toplu İşleme

```python
# Birden fazla dekontu paralel işle
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(
        processor.process_receipt,
        pdf_paths
    ))
```

### 2. Önbellek Kullanımı

```python
# Owner/Property verilerini cache'le
from django.core.cache import cache

owners = cache.get('active_owners')
if not owners:
    owners = Owner.objects.filter(is_active=True)
    cache.set('active_owners', owners, timeout=3600)  # 1 saat
```

### 3. Asenkron İşleme

```python
# Celery task olarak işle
from celery import shared_task

@shared_task
def process_receipt_async(pdf_path, expected_amount):
    processor = ReceiptProcessor(...)
    result = processor.process_receipt(pdf_path, expected_amount)
    # Transaction oluştur ve bildirim gönder
    ...
```

## 🧪 Test Stratejisi

### 1. Unit Tests

```python
# tests/test_receipt_processor.py
def test_process_valid_receipt():
    processor = ReceiptProcessor(...)
    result = processor.process_receipt("test_receipt.pdf")
    assert result.success == True
    assert result.status == "approved"

# tests/test_validators.py
def test_iban_validation():
    validator = ReceiptValidator(...)
    result = validator.validate(
        extracted_fields={"receiver_iban": "INVALID"}
    )
    assert result.is_valid == False
    assert "IBAN" in result.errors[0]
```

### 2. Integration Tests

```python
# tests/test_integration.py
def test_full_workflow():
    # 1. PDF yükle
    # 2. OCR işle
    # 3. Transaction oluştur
    # 4. Database'de doğrula
    ...
```

### 3. E2E Tests

```python
# tests/test_e2e.py
def test_user_uploads_receipt():
    # Selenium/Playwright ile
    # Kullanıcı akışını test et
    ...
```

## 📈 Monitoring ve Logging

### 1. Logging

```python
import logging

logger = logging.getLogger(__name__)

# İşlem başlangıcı
logger.info(f"Processing receipt: {pdf_path}")

# Hata durumu
logger.error(f"OCR failed: {error}", exc_info=True)

# Başarılı işlem
logger.info(f"Receipt approved: confidence={confidence}%")
```

### 2. Metrics

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

receipt_processed = Counter('receipt_processed_total', 'Total receipts processed')
receipt_approved = Counter('receipt_approved_total', 'Total receipts approved')
receipt_rejected = Counter('receipt_rejected_total', 'Total receipts rejected')
processing_time = Histogram('receipt_processing_seconds', 'Receipt processing time')
```

## 🚀 Deployment

### Production Checklist

- [ ] PyMuPDF kurulu
- [ ] OCR modülü yapılandırıldı
- [ ] Database migration'ları uygulandı
- [ ] Celery worker çalışıyor
- [ ] Redis cache ayarlandı
- [ ] Log dosyaları yapılandırıldı
- [ ] Monitoring aktif
- [ ] Backup sistemi hazır

### Environment Variables

```bash
# .env
OCR_MIN_CONFIDENCE=70.0
OCR_AMOUNT_TOLERANCE=0.05
MAX_RECEIPT_SIZE=10485760  # 10MB
CELERY_BROKER_URL=redis://localhost:6379/0
```

## 📚 Referanslar

- [Receipt Processor API](../src/backend-simulation/services/README.md)
- [OCR Documentation](../src/ocr/README.md)
- [Backend Models](../src/backend-simulation/backend-models/)
- [Ana Proje Dokümantasyonu](../readme.md)

