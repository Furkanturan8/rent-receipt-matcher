# Kira Dekontu OCR Eşleştirme Sistemi

## Genel Bakış

Bu sistem, banka dekontlarından OCR ile bilgi çıkararak otomatik olarak mülk sahipleri, kiracılar ve mülklerle eşleştirme yapan bir kira takip çözümüdür.

## Model Yapısı

### RentReceipt Modeli

Dekonttan çıkarılan tüm bilgileri saklayan ana model.

#### Ana Alanlar

**Dekont Verisi:**
- `receipt_image`: Dekont görseli
- `ocr_raw_data`: OCR'dan gelen ham JSON verisi

**Banka İşlem Bilgileri:**
- `bank_name`: Banka adı (Ziraat, Akbank, vb.)
- `transaction_type`: İşlem türü (Havale, EFT)
- `transaction_date`: İşlem tarihi
- `transaction_time`: İşlem saati
- `reference_number`: Referans numarası
- `receipt_number`: Dekont numarası

**Taraf Bilgileri:**
- `sender_name`: Gönderen adı (Kiracı)
- `sender_account`: Gönderen IBAN
- `receiver_name`: Alıcı adı (Mülk Sahibi)
- `receiver_account`: Alıcı IBAN

**Tutar:**
- `amount`: Parse edilmiş tutar (MoneyField)
- `amount_text`: Ham tutar metni

**Açıklama:**
- `description`: Dekont açıklama metni (genelde adres, daire no, ay bilgisi içerir)

**Eşleştirme:**
- `match_status`: Eşleştirme durumu (pending/matched/manual_review/rejected)
- `match_confidence`: Güven skoru (0-100)
- `matched_owner`: Eşleşen mülk sahibi
- `matched_customer`: Eşleşen kiracı
- `matched_property`: Eşleşen mülk
- `matched_payment`: Oluşturulan ödeme kaydı
- `matching_details`: Eşleştirme algoritması detayları

## Test Verileri

### Veritabanı Kayıtları

`ocr_test_data.json` dosyasında 3 mülk sahibi, 3 kiracı ve 3 mülk kaydı bulunmaktadır.

#### Mülk Sahipleri
1. **Ahmet Yılmaz** - MS20251100001
   - IBAN: TR33 0006 1005 1978 6457 8413 26
   - Mülk: Beşiktaş 3+1 Daire (45.000 TL/ay)

2. **Ayşe Demir** - MS20251100002
   - IBAN: TR12 0001 0002 3456 7890 1234 56
   - Mülk: Kadıköy 2+1 Daire (35.000 TL/ay)

3. **Mehmet Kaya** - MS20251100003
   - IBAN: TR45 0004 6000 8888 8000 0123 45
   - Mülk: Şişli Ofis (75.000 TL/ay)

#### Kiracılar
1. **Zeynep Şahin** (Bireysel)
2. **Can Öztürk** (Bireysel)
3. **Teknoloji A.Ş.** (Kurumsal)

### Örnek Dekontlar

`ocr_test_data.json` dosyasında 5 farklı dekont örneği bulunmaktadır:

#### DEKONT_001 - İdeal Durum
- Tüm bilgiler eksiksiz ve doğru
- IBAN, tutar ve açıklama net
- Eşleştirme: Ahmet Yılmaz ← Zeynep Şahin (Beşiktaş Dairesi)

#### DEKONT_002 - İsim Farklılıkları
- Türkçe karakter hataları (Ö → O, İ → I)
- Eşleştirme: Ayşe Demir ← Can Öztürk (Kadıköy Dairesi)

#### DEKONT_003 - Kurumsal Ödeme
- Gönderen kurumsal hesap
- Ofis kirası
- Eşleştirme: Mehmet Kaya ← Teknoloji A.Ş. (Şişli Ofis)

#### DEKONT_004 - Eksik Bilgi
- İsimler kısaltılmış (A.YILMAZ, Z.SAHIN)
- Açıklama çok kısa ("kira")
- IBAN ana eşleştirme kriteri olmalı

#### DEKONT_005 - OCR Hataları
- Sayı-harf karışımı (0 ↔ O, 1 ↔ I/l, 5 ↔ S)
- Türkçe karakter sorunları
- Normalizasyon ve düzeltme gerekli

## Eşleştirme Algoritması

### Öncelik Sırası

1. **IBAN Eşleşmesi**
   - Alıcı IBAN → Owner IBAN
   - Tam eşleşme gerekli (normalize edilmiş)

2. **Tutar Eşleşmesi**
   - Dekont tutarı → Property price
   - ±%5 tolerans

3. **İsim Benzerliği**
   - Fuzzy matching (Levenshtein distance)
   - Alıcı adı → Owner full_name
   - Gönderen adı → Customer full_name

4. **Adres Bilgisi**
   - Açıklama içinde property address parçaları
   - Mahalle, sokak, daire numarası

5. **Gönderen Bilgisi**
   - Gönderen adı → Customer ismi

### Normalizasyon Kuralları

#### IBAN
```python
- Tüm boşlukları kaldır
- Büyük harfe çevir
- O harfi yerine 0 (sıfır) dene
- I/l harfi yerine 1 dene
```

#### İsim
```python
- Büyük harfe çevir
- Türkçe karakterleri normalize et
  ı → I, ş → S, ğ → G, ü → U, ö → O, ç → C
- Çift boşlukları tek boşluğa indir
- Başta/sonda boşlukları temizle
```

#### Tutar
```python
- Nokta/virgül işaretlerini standardize et
- TL/TRY/₺ ifadelerini temizle
- Decimal olarak parse et
- O harflerini 0'a çevir
```

#### Tarih
```python
- DD.MM.YYYY veya DD/MM/YYYY
- O/0 kontrolü
```

