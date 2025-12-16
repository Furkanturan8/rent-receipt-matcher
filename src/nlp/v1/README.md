# NLP Models v1

## Özellikler
- **Entity Sayısı:** 6 (PER, AMOUNT, DATE, IBAN, PERIOD, APT_NO)
- **Dataset:** data/synthetic/ (300 intent, 500 NER)
- **Performans:**
  - Intent: %86.7 accuracy
  - NER: %99.6 F1-score

## Kullanım

### Training
```bash
# Intent Classifier
python src/nlp/v1/train_intent_classifier.py

# NER
python src/nlp/v1/train_ner.py
```

### Inference
```bash
# Intent
python src/nlp/v1/inference.py

# NER
python src/nlp/v1/inference_ner.py
```

## Durum
✅ Tamamlandı ve archived (models/v1_archived/)
📦 Benchmark için saklanıyor
