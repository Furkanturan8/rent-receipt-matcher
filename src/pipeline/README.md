# 🚀 Full Receipt Processing Pipeline

**OCR Output → Intent Classification → NER Extraction → Structured JSON**

---

## 📋 Ne Yapar?

Banka dekontundan çıkarılan OCR verisini alır, NLP modelleri ile işleyip yapılandırılmış JSON output üretir.

```
PDF Dekont → OCR → Intent + NER → Structured JSON
```

---

## 🎯 Özellikler

- ✅ **PDF Processing** - Direkt PDF'den OCR çıkarımı
- ✅ **Auto Bank Detection** - Banka otomatik tespiti (metin/logo bazlı)
- ✅ **Intent Classification** - 4 ödeme tipi (v3 Robust)
- ✅ **Multi-Intent Detection** - Karışık ödemeler (kira + depozito)
- ✅ **NER Extraction** - 11 entity (v3 Hybrid: BERT + Regex)
- ✅ **Smart Merging** - OCR + NER sonuçlarını akıllıca birleştirir
- ✅ **Human-Readable Summary** - Anlaşılır özet üretir

---

## 🚀 Kullanım

### 1. PDF Processing (Direkt - ÖNERİLEN)

```bash
# PDF'i direkt işle (otomatik banka tespiti)
python src/pipeline/cli.py --pdf data/halkbank.pdf --pretty

# Banka adını elle belirt
python src/pipeline/cli.py --pdf data/halkbank.pdf --bank halkbank --pretty

# Logo bazlı tespit de kullan (hibrit)
python src/pipeline/cli.py --pdf data/ziraatbank.pdf --use-logo-detection --pretty

# Makefile ile
make pipeline-pdf PDF=data/halkbank.pdf
make pipeline-pdf PDF=data/halkbank.pdf BANK=halkbank

# run.sh ile
./run.sh pipeline-pdf data/halkbank.pdf
./run.sh pipeline-pdf data/halkbank.pdf halkbank
```

### 2. OCR JSON Dosyasından

```bash
# OCR JSON'ı işle
python src/pipeline/cli.py --ocr-json results/ocr_output.json --pretty

# veya Makefile ile
make pipeline-json OCR=results/ocr_output.json

# veya run.sh ile
./run.sh pipeline-json results/ocr_output.json
```

---

## 📊 Input Format (OCR Output)

```json
{
  "sender": "FURKAN TURAN",
  "sender_iban": "TR660001200146300002247852",
  "description": "Çiçek Apt. No:8, FURKAN TURAN, Haziran kira ödemesi, 15000 TL",
  "amount": "15000.00",
  "amount_currency": "TRY",
  "date": "20/11/2025 - 21:06",
  "recipient": "Mustafa Derin",
  "receiver_iban": "TR090020200008193122900001"
}
```

**Kritik Alan:** `description` - Bu alan Intent + NER için kullanılır.

---

## 📦 Output Format (Structured JSON)

```json
{
  "status": "success",
  "timestamp": "2024-12-12T22:00:00",
  
  "ocr_data": { ... },                    // Original OCR output
  
  "intent": {
    "primary": "kira_odemesi",
    "confidence": 0.8924,
    "all_intents": [...],
    "is_multi_intent": false,
    "detected_intents": ["kira_odemesi"]
  },
  
  "ner": {
    "entities": {
      "sender": "...",
      "apt_no": "8",
      "period": "Haziran",
      ...
    },
    "extraction_method": {
      "sender": "regex",
      "apt_no": "regex",
      "period": "bert",
      ...
    },
    "bert_entities": {...},               // Raw BERT output
    "regex_entities": {...}               // Raw Regex output
  },
  
  "final_entities": {
    "sender": "FURKAN TURAN",
    "sender_iban": "TR660001200146300002247852",
    "receiver": "Mustafa Derin",
    "receiver_iban": "TR090020200008193122900001",
    "amount": "15000.00",
    "amount_currency": "TRY",
    "date": "20/11/2025 - 21:06",
    "apt_no": "8",
    "period": "Haziran"
  },
  
  "summary": "📋 Kira Ödemesi | 👤 Gönderen: FURKAN TURAN | 👤 Alıcı: Mustafa Derin | 💰 Tutar: 15000.00 TRY | 🏠 Daire: 8 | 📅 Dönem: Haziran | 📆 Tarih: 20/11/2025 - 21:06"
}
```
---

## 📈 Performance

### Intent Classification (v3 Robust)
- Sentetik Test: 96.67% accuracy
- Gerçek Data: 100% accuracy
- Multi-Intent Detection: ✅ Yes

### NER Extraction (v3 Hybrid)
- Sentetik Test: 99.81% F1
- Gerçek Data: 88% recall (Hybrid: BERT + Regex)
- Entity Types: 11

### Processing Time
- ~2-3 seconds per receipt (CPU)
- Model loading: ~5 seconds (first time)

---

## 🔗 Integration

### Next Steps

Pipeline output'u şu modüllerle entegre edilebilir:

1. **Receipt Matching** - Kiracı database ile eşleştirme
2. **Validation** - Tutar, tarih, IBAN kontrolü
3. **Chatbot** - Otomatik response üretme
4. **Dashboard** - Web UI görselleştirme
5. **API** - REST endpoint


## 📚 Related Modules

- **OCR Extraction:** `src/ocr/extraction/`
- **Intent Classification:** `src/nlp/v3/train_intent_classifier.py`
- **NER Extraction:** `src/nlp/v3/train_ner.py`
- **Hybrid Inference:** `src/nlp/v3/inference_robust.py`

---
