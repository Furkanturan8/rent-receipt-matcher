# NLP Models v2 - OCR Aware

## Özellikler
- **Entity Sayısı:** 11 (SENDER, RECEIVER, AMOUNT, DATE, SENDER_IBAN, RECEIVER_IBAN, BANK, TRANSACTION_TYPE, FEE, PERIOD, APT_NO)
- **Dataset:** data/synthetic_ocr_aware/ (600 intent, 2000 NER)
- **Yenilikler:**
  - OCR çıktısı + Kullanıcı açıklaması ayrımı
  - Türkiye bankalarına özel (12 banka)
  - Tüm entity'ler %100 dolu (OCR'dan gelenler)

## Yapı

```json
{
  "ocr_data": {
    "sender_iban": "TR...",
    "receiver_iban": "TR...",
    "bank": "Ziraat Bankası",
    ...
  },
  "user_description": "A.Y, Kasım kira, d:5",
  "combined_text": "Dekont: ... | Açıklama: ...",
  "entities": {...}
}
```

## Scriptler

### Training
- `train_intent_classifier.py` - Intent sınıflandırma
- `train_ner.py` - Named Entity Recognition (11 entity)

### Inference
- `inference.py` - Intent tahmin
- `inference_ner.py` - NER extraction

## Kullanım

### Training
```bash
# Intent Classifier
python src/nlp/v2/train_intent_classifier.py

# NER (11 entity)
python src/nlp/v2/train_ner.py
```

### Inference
```bash
# Intent
python src/nlp/v2/inference.py --model_path models/v2_ocr_aware/intent_classifier/final

# NER
python src/nlp/v2/inference_ner.py --model_path models/v2_ocr_aware/ner/final
```

