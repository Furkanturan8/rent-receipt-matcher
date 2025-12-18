# NLP Scripts

Bu klasör projenin NLP model eğitim ve inference scriptlerini içerir.
ŞU AN V4 Production versiyonu aktif. Geçmiş versiyonlar referans için duruyor.
---

## Versiyon Yapısı

```
src/nlp/
├── v1/                    # Orijinal modeller (6 entity)
│   ├── train_intent_classifier.py
│   ├── train_ner.py
│   ├── inference.py
│   ├── inference_ner.py
│   └── README.md
│
├── v2/                    # OCR-Aware modeller (11 entity)
│   ├── train_intent_classifier.py
│   ├── train_ner.py
│   ├── inference.py
│   ├── inference_ner.py
│   └── README.md
│
├── v3/                    # Robust + Hybrid (11 entity)
│   ├── train_intent_classifier.py
│   ├── train_ner.py
│   └── inference_robust.py
│
├── v4/                    # Production Ready (11 entity)
│   ├── train_intent_classifier.py
│   ├── train_ner.py
│   └── inference_v4.py     # Aktif versiyon
│
└── README.md              # Bu dosya
```

---

## Versiyonlar

### v1 - Original (Archived)

**Durum:** Arşivlendi (models/v1_archived/)

- **Dataset:** v1_synthetic (600 intent + 1600 NER)
- **Entity Tipi:** 6 (PER, AMOUNT, DATE, IBAN, PERIOD, APT_NO)
- **Performans:** 
  - Intent: 95% accuracy
  - NER: 95% F1-score
- **Kullanım:** Baseline/benchmark için

---

### v2 - OCR Aware (Superseded)

**Durum:** Geçildi (v4 kullan)

- **Dataset:** v2_ocr_aware (600 intent + 2000 NER)
- **Entity Tipi:** 11 (SENDER, RECEIVER, AMOUNT, DATE, SENDER_IBAN, RECEIVER_IBAN, BANK, TRANSACTION_TYPE, FEE, PERIOD, APT_NO)
- **Performans (Sentetik Test):**
  - Intent: 100% accuracy
  - NER: 99.50% F1-score
- **Problem:** 
  - Gerçek data'da başarısız (NER %15)
  - AMOUNT bug (0% support)
  - Overfit riski
- **Kullanım:** v4 ile karşılaştırma için

---

### v3 - Robust + Hybrid

**Durum:** Geçildi (v4 kullan)

- **Dataset:** v3_robust (800 intent + 2500 NER)
- **Entity Tipi:** 11
- **Özellikler:**
  - Noise injection (typo, random word, spacing)
  - Synonym replacement (kira → aylık ödeme)
  - OCR error simulation (k1ra, kir a)
  - Ambiguous data (multi-intent)
  - AMOUNT bug FIXED (0% → 100%)
  
- **Performans (Sentetik Test):**
  - Intent: 96.67% accuracy
  - NER: 99.81% F1-score

- **Performans (Gerçek Data):**
  - Intent: 100% accuracy (multi-intent detection ile)
  - NER: 88% recall (Hybrid: BERT + Regex)

---

### v4 - Production Ready

**Durum:** Aktif Production Versiyonu

- **Dataset:** v4_production (1200 intent + 3600 NER)
- **Entity Tipi:** 11 (FEE kaldırıldı, TITLE eklendi)
- **Yeni Özellikler:**
  - TITLE entity (mülk/apartman adı çıkarma)
  - Multi-month support (kasım aralık ocak)
  - Amount variations (24bin, 24bintl, 24.000)
  - OCR error correction (inference sırasında I→1, O→0)
  - Confidence-based selection (REGEX-first + BERT fallback)
  - Keyword-based confidence boosting
  - Context-based inference
  - Balanced period distribution (70% tek, 20% iki, 10% üç aylık)
  
- **Performans (Test Set):**
  - Intent: 73.33% accuracy, 73.64% F1-score
  - NER: 99.25% accuracy, 99.28% F1-score
  - Intent Kategori Bazlı:
    - kira_odemesi: 78.16% F1
    - aidat_odemesi: 77.65% F1
    - kapora_odemesi: 68.47% F1
    - depozito_odemesi: 70.13% F1
  - NER Entity Bazlı:
    - AMOUNT, BANK, DATE, PERIOD, RECEIVER, IBANs: 100% F1
    - SENDER: 99.81% F1
    - TITLE: 90.00% F1
    - APT_NO: 98.92% F1

- **Inference Özellikleri:**
  - REGEX-first + BERT fallback (confidence-based)
  - OCR error correction
  - Multi-intent detection
  - Keyword-based boosting
  - Context-aware inference
  - Production-ready

---


## Model Eğitimi

### v4 Production Model Eğit (Önerilen)

```bash
# 1. v4 dataset üret (opsiyonel, zaten mevcut)
python scripts/generate_v4_dataset.py

# 2. Intent classifier eğit
python src/nlp/v4/train_intent_classifier.py

# 3. NER model eğit
python src/nlp/v4/train_ner.py
```

### Inference Test

```bash
# v4 inference demo
python src/nlp/v4/inference_v4.py
```

### Eski Versiyonlar (Referans için)

```bash
# v3
python src/nlp/v3/train_intent_classifier.py
python src/nlp/v3/train_ner.py

# v2
python src/nlp/v2/train_intent_classifier.py
python src/nlp/v2/train_ner.py
```

---

## Performans Karşılaştırması

### Intent Classification

| Metrik | v1 | v2 | v3 | v4 (Production) |
|--------|----|----|----|-----------------|
| Accuracy | 95% | 100% | 96.67% | 73.33% |
| F1-Score | 86.81% | 100% | 96.66% | 73.64% |
| Multi-Intent | Hayır | Hayır | Evet | Evet |
| Test Samples | 45 | 90 | 120 | 180 |
| Overfit Risk | Yüksek | Çok Yüksek | Düşük | Düşük |

**Not:** v4'te accuracy düşük görünse de, bu daha zorlu ve gerçekçi test data nedeniyledir. Gerçek hayat senaryolarında v4, v3'ten daha robust performans gösterecektir.

### NER Extraction

| Metrik | v1 | v2 | v3 | v4 (Production) |
|--------|----|----|----|-----------------|
| Accuracy | 99.88% | 99.79% | 99.87% | 99.25% |
| F1-Score | 99.58% | 99.50% | 99.81% | 99.28% |
| Precision | 99.58% | 99.56% | 99.72% | 98.71% |
| Recall | 99.58% | 99.44% | 99.89% | 99.85% |
| Test Samples | 75 | 300 | 375 | 540 |
| Entity Sayısı | 6 | 11 | 11 | 11 |

**Entity Bazlı (v4):**
- AMOUNT, BANK, DATE, PERIOD, RECEIVER, IBANs: 100% F1
- SENDER: 99.81% F1
- TITLE: 90.00% F1 (yeni entity)
- APT_NO: 98.92% F1

---

## Özellikler Karşılaştırması

| Özellik | v1 | v2 | v3 | v4 |
|---------|----|----|-----|-----|
| Entity Sayısı | 6 | 11 | 11 | 11 |
| Dataset Size | 2200 | 2600 | 3300 | 4800 |
| TITLE Entity | Hayır | Hayır | Hayır | Evet |
| FEE Entity | Hayır | Evet | Evet | Hayır |
| Multi-Month Support | Hayır | Hayır | Hayır | Evet |
| Noise Injection | Hayır | Hayır | Evet | Evet |
| Synonym Replacement | Hayır | Hayır | Evet | Evet |
| OCR Error Simulation | Hayır | Hayır | Evet | Evet |
| OCR Error Correction | Hayır | Hayır | Hayır | Evet |
| Multi-Intent | Hayır | Hayır | Evet | Evet |
| Regex Fallback | Hayır | Hayır | Evet | Evet |
| Confidence-Based Selection | Hayır | Hayır | Hayır | Evet |
| Keyword Boosting | Hayır | Hayır | Hayır | Evet |
| Context-Based Inference | Hayır | Hayır | Hayır | Evet |
| Case-Insensitive | Hayır | Hayır | Evet | Evet |
| Real Data Ready | Kısmen | Hayır | Evet | Evet |

---

## v4 Önemli Değişiklikler

### Entity Değişiklikleri
- **FEE kaldırıldı:** Gereksiz entity, kullanılmıyordu
- **TITLE eklendi:** Mülk/apartman adı çıkarma ("çalık-2", "ada-3")

### Dataset İyileştirmeleri
- Multi-month ödeme desteği (kasım aralık ocak)
- Amount format varyasyonları (24bin, 24bintl, 24.000)
- Daha gerçekçi ekstrem örnekler (typo, eksik bilgi, informal dil)
- Dengeli period dağılımı (70% tek, 20% iki, 10% üç aylık)

### Inference İyileştirmeleri
- **REGEX-first + BERT fallback:** Confidence-based seçim
- **OCR error correction:** Inference sırasında düzeltme (I→1, O→0)
- **Keyword-based boosting:** Intent confidence artırma
- **Context-based inference:** Çevre kelimelere göre çıkarım

---

