# Backend Simulation

Bu klasör, emlak yönetim sisteminin backend modellerini ve OCR entegrasyon servislerini içerir.

## 📁 Klasör Yapısı

```
backend-simulation/
├── backend-models/          # Django model kodları (simulasyon)
│   ├── customers.txt        # Customer modeli
│   ├── finances.txt         # Transaction ve Account modelleri
│   ├── owners.txt           # Owner modeli
│   ├── properties.txt       # Property modeli
│   ├── reservations.txt     # Appointment modeli
│   └── tenants.txt          # Tenant ve RentalContract modelleri
│
└── services/                # OCR-Backend entegrasyon servisleri
    ├── __init__.py
    ├── receipt_processor.py      # Dekont işleme servisi
    ├── validators.py             # Validasyon servisi
    ├── transaction_manager.py    # Transaction yönetim servisi
    ├── data_loader.py            # Model verisi yükleme
    ├── example_usage.py          # Örnek kullanım senaryoları
    └── README.md                 # Servis dokümantasyonu
```

## 🎯 Amaç

Bu klasörün amacı:

1. **Backend Modellerini Simüle Etmek**: Gerçek Django backend'i olmadan modelleri test etmek
2. **OCR Entegrasyonu**: OCR servisleri ile backend arasında köprü kurmak
3. **İş Akışı Testi**: Dekont işleme → Validasyon → Transaction oluşturma akışını test etmek

## 🔧 Backend Modelleri

### 1. Customer (Müşteri)
- Bireysel ve kurumsal müşteri desteği
- İletişim bilgileri
- Kullanıcı hesabı ilişkisi

### 2. Owner (Mülk Sahibi)
- Mülk sahiplerinin bilgileri
- IBAN bilgisi (kira ödemeleri için)
- Konum ve iletişim bilgileri

### 3. Property (Mülk)
- Kiralık/Satılık mülkler
- Konum ve özellikler
- Fiyatlandırma

### 4. Tenant (Kiracı)
- Kiracı profilleri
- Sözleşme ilişkileri

### 5. RentalContract (Kira Sözleşmesi)
- Kiracı-Mülk ilişkisi
- Kira tutarı ve ödeme günü
- Sözleşme tarihleri

### 6. Transaction (Finansal İşlem)
- Kira ödemeleri
- Depozito işlemleri
- Komisyon kayıtları

### 7. Account (Cari Hesap)
- Borç/alacak takibi
- Bakiye yönetimi

## 🚀 OCR-Backend Entegrasyonu

### Servis Katmanı

`services/` klasörü, OCR teknolojisi ile backend modelleri arasında köprü görevi görür.

#### Ana Özellikler:

1. **Dekont İşleme** (`receipt_processor.py`)
   - PDF okuma ve metin çıkarma
   - Banka tespiti (metin + logo tabanlı)
   - Alan çıkarma (tutar, IBAN, ad, tarih)
   - Database eşleştirme

2. **Validasyon** (`validators.py`)
   - IBAN formatı kontrolü
   - Tutar doğrulama (±%5 tolerans)
   - Tarih kontrolü
   - İlişki doğrulama

3. **Transaction Yönetimi** (`transaction_manager.py`)
   - Otomatik Transaction oluşturma
   - Onay/Red işlemleri
   - Durum yönetimi

### İş Akışı

```
┌─────────────┐
│ Kira        │
│ Dekontu PDF │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ OCR İşleme      │ ← receipt_processor.py
│ - Banka Tespit  │
│ - Alan Çıkarma  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Database        │ ← matcher.py (ocr/matching)
│ Eşleştirme      │
│ - Owner         │
│ - Customer      │
│ - Property      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Validasyon      │ ← validators.py
│ - IBAN          │
│ - Tutar         │
│ - Tarih         │
└──────┬──────────┘
       │
       ├─────────────┬─────────────┐
       │             │             │
       ▼             ▼             ▼
┌──────────┐  ┌─────────────┐  ┌──────────┐
│ ONAY     │  │ MANUELİNCELE│  │ RED      │
│ (≥90%)   │  │ (70-89%)    │  │ (<70%)   │
└────┬─────┘  └──────┬──────┘  └────┬─────┘
     │               │               │
     ▼               ▼               ▼
┌──────────────────────────────────────┐
│ Transaction Oluştur                  │ ← transaction_manager.py
│ - Status: COMPLETED/PENDING/REJECTED │
└──────────────────────────────────────┘
```

## 📖 Kullanım

### Hızlı Başlangıç

```python
# 1. Servisleri import et
from services.receipt_processor import ReceiptProcessor
from services.data_loader import DataLoader

# 2. Verileri yükle
data_loader = DataLoader("backend-models")
data = data_loader.load_all()

# 3. Processor oluştur
processor = ReceiptProcessor(
    owners=data["owners"],
    customers=data["customers"],
    properties=data["properties"],
    rental_contracts=data["rental_contracts"],
)

# 4. Dekontu işle
result = processor.process_receipt(
    pdf_path="../../data/halkbank.pdf",
    expected_amount=15000.0,
    expected_owner_id=1,
)

# 5. Sonucu kontrol et
print(f"Durum: {result.status}")
print(f"Güven: {result.match_confidence}%")
```

### Örnek Senaryolar

```bash
# Tüm örnek senaryoları çalıştır
cd services
python example_usage.py
```

Örnekler:
- ✅ Tek dekont işleme
- ✅ Transaction oluşturma
- ✅ Toplu dekont işleme
- ✅ Manuel validasyon
- ✅ Onay/Red akışı

Detaylı dokümantasyon için: `services/README.md`

## 🎨 Onay/Red Senaryoları

### Senaryo 1: Otomatik Onay ✅

**Koşullar:**
- Eşleşme güveni ≥ 90%
- Validasyon başarılı
- Beklenen owner ile eşleşti

**Sonuç:**
- Status: `approved`
- Transaction: `COMPLETED`
- Eylem: Otomatik onay

**Örnek:**
```
Dekont: Halkbank, 15.000 TL
Owner IBAN: TR33...1326 ✓
Tutar: 15.000 TL ✓
Tarih: 21.11.2024 ✓
→ Otomatik onaylandı
```

### Senaryo 2: Manuel İnceleme ⚠️

**Koşullar:**
- Eşleşme güveni 70-89%
- Validasyon uyarıları var
- Farklı owner tespit edildi

**Sonuç:**
- Status: `manual_review`
- Transaction: `PENDING`
- Eylem: Emlakçı incelemesi gerekiyor

**Örnek:**
```
Dekont: Yapı Kredi, 14.500 TL
Owner IBAN: TR33...1326 ✓
Tutar: 14.500 TL ⚠ (Beklenen: 15.000 TL)
Tarih: 21.11.2024 ✓
→ Manuel inceleme gerekli
```

### Senaryo 3: Otomatik Red ✗

**Koşullar:**
- Eşleşme güveni < 70%
- Validasyon hatası
- Kritik bilgi eksik

**Sonuç:**
- Status: `rejected`
- Transaction: `REJECTED`
- Eylem: Otomatik red

**Örnek:**
```
Dekont: Kuveyt Türk, 8.000 TL
Owner IBAN: TR21...8634 ✗ (Beklenen: TR33...1326)
Tutar: 8.000 TL ✗ (Beklenen: 15.000 TL)
→ Otomatik reddedildi
```

## 📊 Eşleştirme Kriterleri

| Kriter | Ağırlık | Eşik | Açıklama |
|--------|---------|------|----------|
| **IBAN** | %95 | 0.95 | En yüksek öncelik |
| **Tutar** | %85 | 0.80 | ±%5 tolerans |
| **İsim** | %75 | 0.70 | Fuzzy matching |
| **Adres** | %70 | 0.60 | Açıklama alanı |
| **Gönderen** | %60 | 0.60 | Customer eşleşmesi |

**Toplam Güven Skoru:** Ağırlıklı ortalama (0-100)

## 🔗 Diğer Modüllerle İlişki

### OCR Modülü (`src/ocr/`)

Servis katmanı, OCR modülünü kullanır:

```python
from ocr.extraction.bank_detector import detect_bank_hybrid
from ocr.extraction.extractor import extract_fields
from ocr.matching.matcher import match_receipt
```

- `bank_detector`: Banka tespiti
- `extractor`: Alan çıkarma
- `matcher`: Database eşleştirme

### Backend Modelleri

Model verileri `backend-models/` klasöründe `.txt` dosyaları olarak saklanır.

Gerçek uygulamada:
- Django ORM ile değiştirilecek
- PostgreSQL/MySQL database kullanılacak
- API endpoint'leri eklenecek

## 🧪 Test

### Unit Test (Gelecek)

```bash
# Test klasörü oluşturulacak
cd services
pytest tests/
```

### Manuel Test

```bash
# Örnek kullanım senaryolarını çalıştır
python example_usage.py
```

## 📝 Notlar

- Bu klasör development/testing amaçlıdır
- Gerçek production'da Django backend kullanılmalıdır
- Transaction kayıtları şu an simülasyondur
- Model verileri örnek/test verileridir

## 🚧 Gelecek Geliştirmeler

- [ ] Django ORM entegrasyonu
- [ ] REST API endpoint'leri
- [ ] Authentication/Authorization
- [ ] Email bildirimleri (onay/red)
- [ ] Dashboard/Admin panel
- [ ] Raporlama modülü
- [ ] Toplu işlem desteği
- [ ] Webhook entegrasyonu

## 📚 Referanslar

- Backend modelleri: `backend-models/*.txt`
- Servis dokümantasyonu: `services/README.md`
- OCR dokümantasyonu: `../ocr/README.md`
- Ana proje: `../../readme.md`

