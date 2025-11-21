# Backend-OCR Entegrasyon Servisleri

Bu klasör, OCR servisleri ile backend modellerini birleştiren servis katmanını içerir. Kira dekontlarının otomatik olarak işlenmesi, doğrulanması ve Transaction kayıtlarının oluşturulması için gerekli tüm servisleri sağlar.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Modüller](#modüller)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [İş Akışı](#iş-akışı)
- [Örnek Senaryolar](#örnek-senaryolar)

## 🎯 Genel Bakış

Bu servis katmanı aşağıdaki işlevleri yerine getirir:

1. **Dekont İşleme**: PDF dekontlarını OCR ile okur ve verileri çıkarır
2. **Banka Tespiti**: Dekontun hangi bankaya ait olduğunu tespit eder
3. **Veri Eşleştirme**: OCR verilerini database kayıtları ile eşleştirir
4. **Validasyon**: Çıkarılan verilerin doğruluğunu kontrol eder
5. **Transaction Yönetimi**: İşlem kayıtlarını oluşturur ve yönetir

## 📦 Modüller

### 1. `receipt_processor.py`

Ana dekont işleme modülü. OCR servisleri ile backend arasında köprü görevi görür.

**Sınıflar:**
- `ReceiptProcessor`: Dekont işleme ana sınıfı
- `ReceiptProcessingResult`: İşlem sonucu veri yapısı

**Özellikler:**
- PDF'den metin çıkarma (PyMuPDF kullanarak)
- Banka tespiti (metin + logo tabanlı)
- Alan çıkarma (tutar, IBAN, ad, tarih, vb.)
- Database ile eşleştirme (Owner, Customer, Property)
- Otomatik validasyon
- Çoklu dekont desteği

**Kullanım:**
```python
from receipt_processor import ReceiptProcessor
from data_loader import DataLoader

# Verileri yükle
data_loader = DataLoader("backend-models")
data = data_loader.load_all()

# Processor oluştur
processor = ReceiptProcessor(
    owners=data["owners"],
    customers=data["customers"],
    properties=data["properties"],
    rental_contracts=data["rental_contracts"],
)

# Dekontu işle
result = processor.process_receipt(
    pdf_path="path/to/receipt.pdf",
    expected_amount=15000.0,
    expected_owner_id=1,
    min_confidence=70.0,
)

print(f"Durum: {result.status}")
print(f"Banka: {result.detected_bank}")
print(f"Eşleşme Güveni: {result.match_confidence}%")
```

### 2. `validators.py`

Dekont verilerinin doğruluğunu kontrol eden validasyon modülü.

**Sınıflar:**
- `ReceiptValidator`: Validasyon ana sınıfı
- `ValidationResult`: Validasyon sonucu veri yapısı

**Validasyon Kontrolleri:**
- ✅ IBAN formatı (TR + 24 rakam)
- ✅ Tutar kontrolü (±%5 tolerans)
- ✅ Tarih kontrolü (geçmiş/gelecek kontrolleri)
- ✅ Mülk sahibi-Mülk ilişkisi
- ✅ Aktif sözleşme kontrolü
- ✅ Zorunlu alan kontrolü

**Kullanım:**
```python
from validators import ReceiptValidator

validator = ReceiptValidator(
    owners=data["owners"],
    customers=data["customers"],
    properties=data["properties"],
    rental_contracts=data["rental_contracts"],
)

validation_result = validator.validate(
    extracted_fields=ocr_data,
    matched_owner_id=1,
    matched_customer_id=2,
    matched_property_id=3,
    expected_amount=15000.0,
)

if validation_result.is_valid:
    print("✓ Validasyon başarılı")
else:
    print("✗ Validasyon hatası:")
    for error in validation_result.errors:
        print(f"  - {error}")
```

### 3. `transaction_manager.py`

Transaction kayıtlarını oluşturan ve yöneten modül.

**Sınıflar:**
- `TransactionManager`: Transaction yönetim sınıfı
- `TransactionData`: Transaction verisi
- `TransactionStatus`: Durum enum'u
- `TransactionType`: Tip enum'u
- `TransactionDirection`: Yön enum'u
- `PaymentMethod`: Ödeme yöntemi enum'u

**Özellikler:**
- Dekont verisinden Transaction oluşturma
- Durum güncelleme (pending → approved/rejected)
- Onay/Red işlemleri
- Cari hesap entegrasyonu

**Kullanım:**
```python
from transaction_manager import TransactionManager, TransactionStatus

manager = TransactionManager(
    owners=data["owners"],
    properties=data["properties"],
    rental_contracts=data["rental_contracts"],
    accounts=data["accounts"],
)

# Transaction oluştur
transaction_data = manager.create_transaction_from_receipt(
    extracted_fields=ocr_data,
    matched_owner_id=1,
    matched_customer_id=2,
    matched_property_id=3,
    receipt_status="approved",
)

# Transaction'ı onayla
approve_result = manager.approve_transaction(
    transaction_id=123,
    approved_by="admin@example.com",
)
```

### 4. `data_loader.py`

Backend model verilerini yükleyen yardımcı modül.

**Sınıflar:**
- `DataLoader`: Veri yükleme sınıfı

**Yüklenen Modeller:**
- Owners (Mülk sahipleri)
- Customers (Müşteriler)
- Properties (Mülkler)
- RentalContracts (Kira sözleşmeleri)
- Tenants (Kiracılar)
- Accounts (Cari hesaplar)

**Kullanım:**
```python
from data_loader import DataLoader

loader = DataLoader("backend-models")

# Tek model yükle
owners = loader.load_owners()

# Tüm modelleri yükle
all_data = loader.load_all()
```

## 🚀 Kurulum

### Gereksinimler

```bash
# Temel gereksinimler
pip install pymupdf  # PDF okuma
pip install Pillow  # Görüntü işleme (logo tespiti için)

# OCR gereksinimleri (zaten kurulu ise atlanabilir)
# Detaylar için: src/ocr/README.md
```

### Dizin Yapısı

```
src/
├── backend-simulation/
│   ├── backend-models/         # Model verileri (.txt dosyaları)
│   │   ├── owners.txt
│   │   ├── customers.txt
│   │   ├── properties.txt
│   │   ├── tenants.txt
│   │   ├── finances.txt
│   │   └── reservations.txt
│   └── services/               # Servis katmanı (bu klasör)
│       ├── __init__.py
│       ├── receipt_processor.py
│       ├── validators.py
│       ├── transaction_manager.py
│       ├── data_loader.py
│       ├── example_usage.py
│       └── README.md
├── ocr/                        # OCR servisleri
│   ├── extraction/
│   │   ├── bank_detector.py
│   │   ├── extractor.py
│   │   └── regex_patterns.py
│   └── matching/
│       ├── matcher.py
│       ├── fuzzy.py
│       └── normalizers.py
└── data/                       # Test dekontları
    ├── halkbank.pdf
    ├── yapikredi.pdf
    ├── kuveytturk.pdf
    └── ziraatbank.pdf
```

## 📖 Kullanım

### Temel Kullanım

```python
from pathlib import Path
from receipt_processor import ReceiptProcessor
from data_loader import DataLoader

# 1. Verileri yükle
data_loader = DataLoader("../backend-models")
data = data_loader.load_all()

# 2. Processor oluştur
processor = ReceiptProcessor(
    owners=data["owners"],
    customers=data["customers"],
    properties=data["properties"],
    rental_contracts=data["rental_contracts"],
)

# 3. Dekontu işle
result = processor.process_receipt(
    pdf_path=Path("../../data/halkbank.pdf"),
    expected_amount=15000.0,
    expected_owner_id=1,
)

# 4. Sonucu kontrol et
if result.success:
    print(f"✓ Başarılı! Durum: {result.status}")
    print(f"  Banka: {result.detected_bank}")
    print(f"  Tutar: {result.extracted_fields.get('amount')}")
    print(f"  Owner: {result.matched_owner_id}")
else:
    print("✗ İşlem başarısız")
    for error in result.validation_errors:
        print(f"  - {error}")
```

## 🔄 İş Akışı

### 1. Dekont İşleme Akışı

```
┌─────────────┐
│ PDF Dekont  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Metin Çıkarma       │ (PyMuPDF)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Banka Tespiti       │ (Metin + Logo)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Alan Çıkarma        │ (Regex Patterns)
│ - Tutar             │
│ - IBAN              │
│ - İsim              │
│ - Tarih             │
│ - Açıklama          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Database Eşleştirme │ (Fuzzy Matching)
│ - Owner             │
│ - Customer          │
│ - Property          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Validasyon          │
│ - IBAN kontrolü     │
│ - Tutar kontrolü    │
│ - Tarih kontrolü    │
│ - İlişki kontrolü   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Sonuç               │
│ - approved          │
│ - manual_review     │
│ - rejected          │
└─────────────────────┘
```

### 2. Transaction Oluşturma Akışı

```
┌──────────────────┐
│ İşlem Sonucu     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ Transaction Data     │
│ Oluştur              │
└────────┬─────────────┘
         │
         ├─── approved ──────►┌──────────────┐
         │                     │ Status:      │
         │                     │ COMPLETED    │
         │                     └──────────────┘
         │
         ├─── manual_review ──►┌──────────────┐
         │                     │ Status:      │
         │                     │ PENDING      │
         │                     │              │
         │                     │ ┌──────────┐ │
         │                     │ │ Emlakçı  │ │
         │                     │ │ Onayı    │ │
         │                     │ └────┬─────┘ │
         │                     │      │       │
         │                     │      ├─approve►│
         │                     │      │       │
         │                     │      └─reject►│
         │                     └──────────────┘
         │
         └─── rejected ────────►┌──────────────┐
                                 │ Status:      │
                                 │ REJECTED     │
                                 └──────────────┘
```

### 3. Onay/Red Durumları

| Durum | Koşul | Eylem |
|-------|-------|-------|
| **approved** | - Eşleşme güveni ≥ 90%<br>- Validasyon başarılı<br>- Beklenen owner ile eşleşti | Otomatik onay<br>Transaction COMPLETED |
| **manual_review** | - Eşleşme güveni 70-89%<br>- Validasyon uyarıları var<br>- Farklı owner tespit edildi | Manuel inceleme<br>Transaction PENDING<br>Emlakçı kararı beklenir |
| **rejected** | - Eşleşme güveni < 70%<br>- Validasyon hatası<br>- Kritik bilgi eksik | Otomatik red<br>Transaction REJECTED |

## 🎨 Örnek Senaryolar

### Senaryo 1: Başarılı Dekont İşleme

```python
# Örnek: Halkbank dekontu, doğru tutar, doğru owner
result = processor.process_receipt(
    pdf_path="halkbank.pdf",
    expected_amount=15000.0,
    expected_owner_id=1,
)

# Sonuç:
# ✓ Durum: approved
# ✓ Banka: halkbank
# ✓ Eşleşme: %95.5
# ✓ Validasyon: Geçerli
# ✓ Transaction: COMPLETED
```

### Senaryo 2: Manuel İnceleme Gerekli

```python
# Örnek: Tutar farklı ama yakın
result = processor.process_receipt(
    pdf_path="yapikredi.pdf",
    expected_amount=15000.0,  # Dekont: 14500 TL
)

# Sonuç:
# ⚠ Durum: manual_review
# ⚠ Banka: yapikredi
# ⚠ Eşleşme: %82.3
# ⚠ Validasyon: Uyarı - Tutar farklı
# ⚠ Transaction: PENDING
```

### Senaryo 3: Reddedilen Dekont

```python
# Örnek: IBAN yanlış
result = processor.process_receipt(
    pdf_path="kuveytturk.pdf",
    expected_owner_id=1,
)

# Sonuç:
# ✗ Durum: rejected
# ✗ Banka: kuveytturk
# ✗ Eşleşme: %45.2
# ✗ Validasyon: Hata - IBAN eşleşmiyor
# ✗ Transaction: REJECTED
```

### Senaryo 4: Toplu İşleme

```python
# Birden fazla dekontu işle
results = processor.process_multiple_receipts(
    pdf_paths=[
        "halkbank.pdf",
        "yapikredi.pdf",
        "kuveytturk.pdf",
    ],
    expected_amounts=[15000, 12000, 8000],
)

# Özet rapor
approved = sum(1 for r in results if r.status == "approved")
print(f"Onaylanan: {approved}/{len(results)}")
```

## 📊 Veri Yapıları

### ReceiptProcessingResult

```python
@dataclass
class ReceiptProcessingResult:
    success: bool                          # İşlem başarılı mı?
    status: str                            # approved/manual_review/rejected
    detected_bank: Optional[str]           # Tespit edilen banka
    extracted_fields: Dict[str, Any]       # OCR çıktısı
    matched_owner_id: Optional[int]        # Eşleşen owner
    matched_customer_id: Optional[int]     # Eşleşen customer
    matched_property_id: Optional[int]     # Eşleşen property
    match_confidence: float                # Eşleşme güveni (0-100)
    is_valid: bool                         # Validasyon sonucu
    validation_errors: List[str]           # Hata mesajları
    validation_warnings: List[str]         # Uyarı mesajları
    messages: List[str]                    # Bilgilendirme mesajları
    details: Dict[str, Any]                # Ek detaylar
```

### TransactionData

```python
@dataclass
class TransactionData:
    rental_contract_id: Optional[int]      # İlgili sözleşme
    rental_property_id: Optional[int]      # İlgili mülk
    account_id: Optional[int]              # İlgili cari hesap
    transaction_type: str                  # rent_payment/deposit_in/etc.
    direction: str                         # in/out
    status: str                            # pending/approved/completed/etc.
    amount: float                          # Tutar
    amount_currency: str                   # Para birimi (TRY)
    due_date: Optional[str]                # Vade tarihi
    payment_date: Optional[str]            # Ödeme tarihi
    payment_method: str                    # bank_transfer/cash/etc.
    reference_number: str                  # Dekont no
    description: str                       # Açıklama
    notes: str                             # Notlar
    ocr_data: Dict[str, Any]               # Ham OCR verisi
```

## 🔧 Yapılandırma

### Eşleştirme Kriterleri

```python
MATCHING_CRITERIA = {
    "iban": {"priority": 1, "weight": 95, "threshold": 0.95},
    "amount": {"priority": 2, "weight": 85, "threshold": 0.80},
    "name": {"priority": 3, "weight": 75, "threshold": 0.70},
    "address": {"priority": 4, "weight": 70, "threshold": 0.60},
    "sender": {"priority": 5, "weight": 60, "threshold": 0.60},
}
```

### Validasyon Ayarları

```python
# IBAN formatı
IBAN_PATTERN = r'^TR\d{24}$'

# Tutar toleransı
AMOUNT_TOLERANCE = 0.05  # %5

# Minimum güven skoru
MIN_CONFIDENCE = 70.0  # 0-100
```

## 🧪 Test ve Çalıştırma

### Örnek Kullanım Dosyasını Çalıştırma

```bash
cd src/backend-simulation/services
python example_usage.py
```

Bu komut şu senaryoları çalıştırır:
1. ✅ Tek dekont işleme
2. ✅ Transaction oluşturma
3. ✅ Manuel validasyon
4. ✅ Transaction onay akışı
5. ✅ Toplu dekont işleme (opsiyonel)

## 🐛 Hata Ayıklama

### Yaygın Hatalar ve Çözümleri

**1. PDF okunamıyor**
```python
# Hata: PyMuPDF yüklü değil
# Çözüm:
pip install pymupdf
```

**2. OCR modülü bulunamıyor**
```python
# Hata: ModuleNotFoundError: No module named 'ocr'
# Çözüm: sys.path'e ekle
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
```

**3. Banka tespit edilemiyor**
```python
# Çözüm: Logo tespiti için Pillow yükle
pip install Pillow

# veya genel desen kullan (bank_hint=None)
result = processor.process_receipt(pdf_path, bank_hint=None)
```

## 📝 Notlar

- Bu servis katmanı Django ORM simulasyonu kullanır (gerçek database yerine sözlükler)
- Gerçek uygulamada `data_loader.py` yerine Django ORM sorguları kullanılmalı
- Transaction kayıtları şu an simülasyondur, gerçek kayıt için Django view'ları güncellenmelidir
- Güven skorları ve eşik değerleri ihtiyaçlara göre ayarlanabilir

## 🤝 Katkıda Bulunma

Geliştirmeler ve öneriler için:
1. Backend modellerini güncellerken `data_loader.py` dosyasını da güncelleyin
2. Yeni validasyon kuralları için `validators.py` içine ekleyin
3. Yeni transaction tipleri için `transaction_manager.py` enum'larını genişletin

## 📞 İletişim

Sorularınız için proje README.md dosyasına bakın.

