# Logo Tabanlı Banka Tespiti Kurulumu

Bu dokümantasyon, logo ve görsel tabanlı banka tespitinin nasıl kurulacağını açıklar.

## Gereksinimler

Logo tabanlı tespit için aşağıdaki Python paketlerinin kurulu olması gerekir:

```bash
pip install opencv-python pillow pymupdf
```

veya `requirements.txt` dosyasına ekleyin:

```
opencv-python>=4.5.0
pillow>=9.0.0
pymupdf>=1.20.0
```

## Yapı

```
nlp-project/
├── assets/
│   └── logos/              # Referans logo görselleri
│       ├── halkbank_logo.png
│       ├── yapikredi_logo.png
│       ├── kuveytturk_logo.png
│       └── ...
└── src/ocr/extraction/
    ├── bank_detector.py    # Metin tabanlı tespit
    └── logo_detector.py    # Logo tabanlı tespit
```

## Nasıl Çalışır?

1. **PDF'den Görsel Çıkarma**: PyMuPDF kullanarak PDF'den tüm görseller çıkarılır
2. **Logo Yükleme**: Referans logolar `assets/logos/` dizininden yüklenir
3. **Template Matching**: OpenCV kullanarak görseller karşılaştırılır
4. **Skorlama**: En yüksek benzerlik skoruna sahip banka seçilir

## Kullanım

### 1. Referans Logoları Ekle

Bankalardan temiz logo görsellerini `assets/logos/` dizinine ekleyin:

```bash
# Örnek
assets/logos/halkbank_logo.png
assets/logos/yapikredi_logo.png
```

### 2. Hibrit Tespit Kullan

```bash
# Logo tespitini de kullan
python -m ocr.extraction.cli data/halkbank.pdf --use-logo-detection
```

### 3. Sadece Metin Tespiti (Varsayılan)

```bash
# Logo tespiti olmadan (sadece metin)
python -m ocr.extraction.cli data/halkbank.pdf
```

## Avantajlar

- ✅ Metin tabanlı tespite ek doğrulama sağlar
- ✅ Logo bulunan PDF'lerde daha güvenilir sonuçlar
- ✅ Hibrit yaklaşım ile en iyi sonuç

## Dezavantajlar

- ⚠️ Ek bağımlılıklar gerektirir (OpenCV, PyMuPDF)
- ⚠️ Referans logoların hazırlanması gerekir
- ⚠️ Logo yoksa veya kalitesizse tespit edemez

## Alternatif Yaklaşımlar

İleride eklenebilecek gelişmiş yöntemler:

1. **Feature Matching (SIFT/ORB)**: Daha esnek logo tespiti
2. **Deep Learning**: CNN ile logo sınıflandırma
3. **Color Histogram Matching**: Renk dağılımına göre tespit
4. **OCR on Images**: Logo içindeki metinleri OCR ile okuma

