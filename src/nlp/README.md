# NLP Scripts

Bu klasör projenin NLP model eğitim ve inference scriptlerini içerir.
ŞU AN V3 son versiyon. Adım adım ilerleme görülmesi için v1-v2 duruyor.
---

## 📁 Versiyon Yapısı

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
├── v3/                    # Robust + Hybrid (11 entity) 🔥
│   ├── train_intent_classifier.py
│   ├── train_ner.py
│   └── inference_robust.py     # ⭐ Şuanki durum
│
└── README.md              # Bu dosya
```

---

## 📊 Versiyonlar

### v1 - Original (Archived)

**Durum:** ✅ Arşivlendi (models/v1_archived/)

- **Dataset:** v1_synthetic (600 intent + 1600 NER)
- **Entity Tipi:** 6 (PER, AMOUNT, DATE, IBAN, PERIOD, APT_NO)
- **Performans:** 
  - Intent: 95% accuracy
  - NER: 95% F1-score
- **Kullanım:** Baseline/benchmark için

---

### v2 - OCR Aware (Superseded)

**Durum:** ⚠️ Geçildi (v3 kullan)

- **Dataset:** v2_ocr_aware (600 intent + 2000 NER)
- **Entity Tipi:** 11 (SENDER, RECEIVER, AMOUNT, DATE, SENDER_IBAN, RECEIVER_IBAN, BANK, TRANSACTION_TYPE, FEE, PERIOD, APT_NO)
- **Performans (Sentetik Test):**
  - Intent: 100% accuracy
  - NER: 99.50% F1-score
- **Problem:** 
  - ❌ Gerçek data'da başarısız (NER %15)
  - ❌ AMOUNT bug (0% support)
  - ❌ Overfit riski
- **Kullanım:** v3 ile karşılaştırma için

---

### v3 - Robust + Hybrid (Current) 🔥

**Durum:** ✅ PRODUCTION-READY

- **Dataset:** v3_robust (800 intent + 2500 NER)
- **Entity Tipi:** 11 (v2 ile aynı)
- **Özellikler:**
  - ✅ Noise injection (typo, random word, spacing)
  - ✅ Synonym replacement (kira → aylık ödeme)
  - ✅ OCR error simulation (k1ra, kir a)
  - ✅ Ambiguous data (multi-intent)
  - ✅ AMOUNT bug FIXED (0% → 100%)
  
- **Performans (Sentetik Test):**
  - Intent: 96.67% accuracy (v2'den -3% ama daha gerçekçi)
  - NER: 99.81% F1-score (v2'den +0.31%)

- **Performans (Gerçek Data):**
  - Intent: 100% accuracy (multi-intent detection ile)
  - NER: 88% recall (Hybrid: BERT + Regex)

- **Hybrid Inference:** 🎯
  - BERT + Regex fallback
  - Multi-intent detection
  - Case-insensitive
  - Production-ready

---


## 📚 Model Eğitimi

### v3 Robust Model Eğit (Önerilen)

```bash
# 1. Robust data üret (opsiyonel, zaten mevcut)
python scripts/generate_robust_synthetic_data.py

# 2. Intent classifier eğit
python src/nlp/v3/train_intent_classifier.py

# 3. NER model eğit
python src/nlp/v3/train_ner.py
```

### v2 Model Eğit (Karşılaştırma için)

```bash
python src/nlp/v2/train_intent_classifier.py
python src/nlp/v2/train_ner.py
```

---

## 📊 Performans Karşılaştırması

### Intent Classification

| Metrik | v1 | v2 | v3 | v3 (Gerçek Data) |
|--------|----|----|----|--------------------|
| Accuracy | 95% | 100% | 96.67% | 100% |
| Multi-Intent | ❌ | ❌ | ✅ | ✅ |
| Overfit Risk | ⚠️ | 🔥 | ✅ | ✅ |

### NER Extraction

| Metrik | v1 | v2 | v3 | v3 (Gerçek Data - Hybrid) |
|--------|----|----|----|-----------------------------|
| F1-Score | 95% | 99.50% | 99.81% | ~88% |
| SENDER | ✅ | ❌ 0% | ✅ 100% | ✅ 75% |
| AMOUNT | ✅ | ❌ 0% | ✅ 100% | ✅ 75% |
| APT_NO | ✅ | ❌ 0% | ✅ 100% | ✅ 100% |

**Sonuç:** v3 Hybrid gerçek data'da **ÇOK daha iyi!**

---

## 🔑 Özellikler Karşılaştırması

| Özellik | v1 | v2 | v3 |
|---------|----|----|-----|
| Entity Sayısı | 6 | 11 | 11 |
| Dataset Size | 2200 | 2600 | 3300 |
| Noise Injection | ❌ | ❌ | ✅ |
| Synonym Replacement | ❌ | ❌ | ✅ |
| OCR Error Simulation | ❌ | ❌ | ✅ |
| Multi-Intent | ❌ | ❌ | ✅ |
| Regex Fallback | ❌ | ❌ | ✅ |
| Case-Insensitive | ❌ | ❌ | ✅ |
| UPPERCASE Support | ❌ | ❌ | ✅ |
| Real Data Ready | ⚠️ | ❌ | ✅ |


---

