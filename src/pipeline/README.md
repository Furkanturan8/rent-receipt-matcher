# Full Receipt Processing Pipeline

**OCR Output → Intent Classification → NER Extraction → Structured JSON**

---

## Ne Yapar?

Banka dekontundan çıkarılan OCR verisini alır, NLP modelleri ile işleyip yapılandırılmış JSON output üretir.

```
PDF Dekont → OCR → Intent + NER → Structured JSON
```

---

## Özellikler

- PDF Processing - Direkt PDF'den OCR çıkarımı
- Auto Bank Detection - Banka otomatik tespiti (metin/logo bazlı)
- Intent Classification - 4 ödeme tipi (v4 Production)
- Multi-Intent Detection - Karışık ödemeler (kira + depozito)
- NER Extraction - 11 entity (v4 Hybrid: REGEX-first + BERT fallback)
- Smart Merging - OCR + NER sonuçlarını akıllıca birleştirir
- Human-Readable Summary - Anlaşılır özet üretir
- Confidence Scores - Her entity için confidence gösterimi

---

## Kullanım

### 1. PDF Processing (Direkt)

```bash
# PDF'i direkt işle (otomatik banka tespiti)
python src/pipeline/cli.py --pdf data/halkbank.pdf --pretty

# Banka adını elle belirt
python src/pipeline/cli.py --pdf data/halkbank.pdf --bank halkbank --pretty

# Logo bazlı tespit de kullan (hibrit)
python src/pipeline/cli.py --pdf data/ziraatbank.pdf --use-logo-detection --pretty

# Matching ile
python src/pipeline/cli.py --pdf data/ziraatbank2.pdf --enable-matching --pretty
```

### 2. OCR JSON Dosyasından

```bash
# OCR JSON'ı işle
python src/pipeline/cli.py --ocr-json results/ocr_output.json --pretty
```

---

## Input Format (OCR Output)

**Örnek (v4 dataset'ten):**

```json
{
  "sender": "ALI ÇELIK",
  "sender_iban": "TR19002056213337325455501",
  "description": "Daire A2 çiçek2 şubat 31bintl kira ücreti",
  "amount": "31000.00",
  "amount_currency": "TRY",
  "date": "08.11.2025 - 20:21:07",
  "recipient": "Emlak Ofisi",
  "receiver_iban": "TR20000672890134496665106"
}
```

**Kritik Alan:** `description` - Bu alan Intent + NER için kullanılır.

---

## Output Format (Structured JSON)

```json
{
  "status": "success",
  "timestamp": "2024-12-17T20:56:37",
  
  "ocr_data": { ... },
  
  "intent": {
    "primary": "kira_odemesi",
    "confidence": 0.9234,
    "all_intents": [
      {"intent": "kira_odemesi", "confidence": 0.9234},
      {"intent": "aidat_odemesi", "confidence": 0.0521},
      {"intent": "depozito_odemesi", "confidence": 0.0156},
      {"intent": "kapora_odemesi", "confidence": 0.0089}
    ],
    "is_multi_intent": false,
    "detected_intents": ["kira_odemesi"]
  },
  
  "ner": {
    "entities": {
      "sender": "Ali Çelik",
      "amount": "31000",
      "apt_no": "A2",
      "period": "Şubat",
      "title": "Çiçek2"
    },
    "extraction_method": {
      "sender": "regex",
      "amount": "regex",
      "apt_no": "regex",
      "period": "regex",
      "title": "regex"
    },
    "confidence_scores": {
      "sender": 0.9,
      "amount": 1.0,
      "apt_no": 0.9,
      "period": 1.0,
      "title": 0.9
    },
    "bert_entities": {},
    "regex_entities": {
      "sender": "Ali Çelik",
      "apt_no": "A2",
      "amount": "31000",
      "period": "Şubat",
      "title": "Çiçek2"
    }
  },
  
  "final_entities": {
    "sender": "ALI ÇELIK",
    "sender_iban": "TR19002056213337325455501",
    "receiver": "Emlak Ofisi",
    "receiver_iban": "TR20000672890134496665106",
    "amount": "31000.00",
    "amount_currency": "TRY",
    "date": "08.11.2025 - 20:21:07",
    "apt_no": "A2",
    "period": "Şubat",
    "title": "Çiçek2"
  },
  
  "summary": "Kira Ödemesi | Gönderen: ALI ÇELIK | Alıcı: Emlak Ofisi | Tutar: 31000.00 TRY | Mülk: Çiçek2 | Daire: A2 | Dönem: Şubat | Tarih: 08.11.2025 - 20:21:07",
  
  "matching": {
    "status": "matched",
    "confidence": 87.5,
    "owner_id": 1,
    "customer_id": 1,
    "property_id": 1,
    "scores": {
      "iban": 1.0,
      "amount": 1.0,
      "name": 0.85,
      "address": 0.72,
      "sender": 1.0
    }
  }
}
```

---

## Performance

### Intent Classification (v4 Production)
- Test Set: 73.33% accuracy
- Gerçek Dekont: 95.74% confidence (keyword boosting ile)
- Multi-Intent Detection: Destekleniyor

### NER Extraction (v4 Production)
- Test Set: 99.28% F1-score
- Gerçek Dekont: Başarılı (REGEX-first extraction)
- Entity Types: 11 (TITLE dahil)

### Processing Time
- ~2-3 seconds per receipt (CPU)
- Model loading: ~5 seconds (first time)

---

## V4 Production Özellikleri

### Yeni Entity'ler
- TITLE: Mülk/apartman adı (çalık-2, ada-3)
- FEE entity kaldırıldı

### Multi-Month Support
- Birden fazla aylık ödeme desteği
- Örnek: "kasım aralık ocak 24bin tl"

### OCR Error Correction
- Runtime düzeltme: I→1, O→0
- Örnek: "I4O TL" → "140 TL"

### Confidence-Based Selection
- REGEX ve BERT confidence karşılaştırması
- Yüksek confidence'a sahip olan seçilir

### Keyword & Context Boosting
- Keyword-based confidence boosting
- Context-based inference (apartmanı + ay → kira)

---

## Integration

Pipeline output'u şu modüllerle entegre edilebilir:

1. Receipt Matching - Kiracı database ile eşleştirme
2. Validation - Tutar, tarih, IBAN kontrolü
3. Chatbot - Otomatik response üretme
4. Dashboard - Web UI görselleştirme
5. API - REST endpoint

---

## Related Modules

- OCR Extraction: `src/ocr/extraction/`
- Intent Classification: `src/nlp/v4/train_intent_classifier.py`
- NER Extraction: `src/nlp/v4/train_ner.py`
- Hybrid Inference: `src/nlp/v4/inference_v4.py`

---

**Son Güncelleme:** 17 Aralık 2024  
**Versiyon:** v4 Production
