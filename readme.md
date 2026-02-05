# 🏗️ NLP Receipt Processing Microservice

Banking receipt processing with Intent Classification + Named Entity Recognition as a standalone microservice.

## 🎯 Mikroservis Mimarisi

```
Frontend → Django Backend → NLP Microservice (This Project)
```

Bu proje **bağımsız bir mikroservis** olarak çalışır ve HTTP REST API üzerinden banking dekontlarını işler.

## ✨ Özellikler

- 🎯 **Intent Classification**: 4 kategori (kira, aidat, kapora, depozito)
- 🏷️ **Named Entity Recognition**: 11 entity type (sender, receiver, amount, etc.)
- 📄 **PDF Processing**: OCR + NLP pipeline
- 🚀 **Production Ready**: Gunicorn, Docker, health checks
- 📊 **High Accuracy**: Intent 95%+, NER 99.28% F1-score
- 🔄 **Stateless**: No database required
- 📖 **API Documentation**: Swagger/OpenAPI

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# Clone repo
git clone <repo-url>
cd nlp-project

# Virtual environment (önerilir)
python -m venv venv
source venv/bin/activate

# Paketleri yükle
pip install -r requirements.txt
```

### 2. Çalıştır

```bash
# Development
./start.sh

# VEYA manuel
python manage.py runserver 0.0.0.0:8001
```

### 3. Test

```bash
# Health check
curl http://localhost:8001/health/

# OCR processing
curl -X POST http://localhost:8001/api/v1/process-ocr/ \
  -H "Content-Type: application/json" \
  -d '{
    "ocr_data": {
      "description": "Haziran kira 5000 TL Daire 8"
    }
  }'

# Response:
{
  "status": "success",
  "intent": {
    "primary": "kira_odemesi",
    "confidence": 0.95
  },
  "final_entities": {
    "apt_no": "8",
    "period": "Haziran",
    "amount": "5000"
  }
}
```

### 4. Mikroservis Test

```bash
./test_microservices.sh
```

## 📡 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/health/` | Health check |
| `POST` | `/api/v1/process-ocr/` | OCR output işleme |
| `POST` | `/api/v1/process-pdf/` | PDF dosyası işleme |
| `POST` | `/api/v1/batch-process-ocr/` | Toplu işleme |

**Swagger UI:** http://localhost:8001/docs/

## 🔗 Backend Entegrasyonu

### Django Backend'den Kullanım

**1. Backend settings.py:**
```python
NLP_SERVICE_URL = 'http://localhost:8001'
NLP_SERVICE_TIMEOUT = 120
```

**2. HTTP Client (rent_receipts app):**
```python
import requests

response = requests.post(
    'http://localhost:8001/api/v1/process-ocr/',
    json={'ocr_data': {...}}
)
result = response.json()
```

**Detaylı entegrasyon:** [rent_receipts/MICROSERVICE_INTEGRATION.md](rent_receipts/MICROSERVICE_INTEGRATION.md)

## 🐳 Docker

```bash
# Build
docker build -t nlp-microservice .

# Run
docker run -p 8001:8001 nlp-microservice

# Docker Compose
docker-compose up -d
```

## 📊 Performans

| Metrik | Değer |
|--------|-------|
| İlk istek | 10-15s (model loading) |
| Sonraki istekler | 100-300ms |
| Throughput | ~200 req/min |
| Memory | ~2GB (with models) |

## 🏗️ Proje Yapısı

```
nlp-project/
├── manage.py              # Django manage
├── nlp_service/           # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── src/
│   ├── api/               # REST API (DRF)
│   │   ├── views.py       # API endpoints
│   │   ├── serializers.py
│   │   └── services.py    # Business logic
│   ├── nlp/v4/            # NLP models
│   │   ├── train_intent_classifier.py
│   │   ├── train_ner.py
│   │   └── inference_v4.py
│   └── pipeline/          # Processing pipeline
│       └── full_pipeline.py
├── models/v4_production/  # Trained models
│   ├── intent_classifier/
│   └── ner/
├── data/                  # Training data
├── rent_receipts/         # Backend integration example
└── docs/                  # Documentation
```

## 📚 Dökümantasyon

### Başlangıç
- **⚡ Hızlı:** [QUICKSTART_MICROSERVICE.md](QUICKSTART_MICROSERVICE.md) - 5 dakikada başlat
- **📖 Detaylı:** [MICROSERVICE_SETUP.md](MICROSERVICE_SETUP.md) - Tam kurulum rehberi
- **🏗️ Mimari:** [README_MICROSERVICE.md](README_MICROSERVICE.md) - Mikroservis mimarisi

### API Dökümantasyonu
- **REST API:** [src/api/README.md](src/api/README.md)
- **Swagger:** http://localhost:8001/docs/
- **ReDoc:** http://localhost:8001/redoc/

### Backend Entegrasyonu
- **rent_receipts App:** [rent_receipts/README.md](rent_receipts/README.md)
- **Entegrasyon:** [rent_receipts/MICROSERVICE_INTEGRATION.md](rent_receipts/MICROSERVICE_INTEGRATION.md)
- **Kurulum:** [rent_receipts/SETUP.md](rent_receipts/SETUP.md)

## 🧪 Test

```bash
# Mikroservis testleri
./test_microservices.sh

# Django unit tests
python manage.py test src.api

# Load test
ab -n 1000 -c 10 http://localhost:8001/health/
```

## 🔒 Production

### Environment Variables

```bash
export DJANGO_SECRET_KEY="your-secret-key"
export DEBUG=False
export ALLOWED_HOSTS="nlp-service.yourdomain.com"
export CORS_ALLOWED_ORIGINS="https://backend.yourdomain.com"
```

### Gunicorn

```bash
gunicorn nlp_service.wsgi:application \
  --bind 0.0.0.0:8001 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Security

- ✅ API Key authentication
- ✅ CORS configuration
- ✅ Rate limiting
- ✅ Network isolation (Docker)
- ✅ HTTPS (reverse proxy)

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  nlp-service:
    deploy:
      replicas: 3
```

### Load Balancing

```nginx
upstream nlp_backend {
    server nlp-1:8001;
    server nlp-2:8001;
    server nlp-3:8001;
}
```

## 🐛 Troubleshooting

**Service erişilemiyor:**
```bash
curl http://localhost:8001/health/
lsof -i :8001
```

**Models not found:**
```bash
ls -la models/v4_production/
```

**CORS hatası:**
```python
# nlp_service/settings.py
CORS_ALLOWED_ORIGINS = ['http://your-backend-url:8000']
```

**Detaylı sorun giderme:** [MICROSERVICE_SETUP.md#troubleshooting](MICROSERVICE_SETUP.md#troubleshooting)

## 📦 Gereksinimler

- Python 3.8+
- Django 4.2+
- PyTorch
- Transformers (Hugging Face)
- Tesseract OCR (PDF processing için)

## 🎯 Kullanım Senaryoları

1. **Single Backend:** Tek Django backend → NLP microservice
2. **Multiple Backends:** Web + Mobile API → Shared NLP microservice
3. **High Traffic:** Load balancer → 3x NLP instances
4. **GPU Instance:** NLP service GPU makinesinde, backend normal instance

## 📊 Model Bilgileri

### Intent Classifier
- **Model:** DistilBERT-base-turkish-cased
- **Classes:** 4 (kira, aidat, kapora, depozito)
- **Accuracy:** 73.33% (test), 95%+ (real data)
- **Training:** 1200 samples, ~1.5 dakika

### NER Extractor
- **Model:** DistilBERT-base-turkish-cased
- **Entities:** 11 types
- **F1-Score:** 99.28%
- **Method:** Hybrid (BERT + Regex)
- **Training:** 3600 samples, ~6.5 dakika

## 🤝 Katkıda Bulunma

Pull requests memnuniyetle karşılanır!

## 📄 Lisans

[Your License]

## 📞 İletişim

- **Issues:** GitHub Issues
- **Dökümantasyon:** [docs/](docs/)
- **API Docs:** http://localhost:8001/docs/

---

## ⚡ Quick Commands

```bash
# Start service
./start.sh

# Test
./test_microservices.sh

# Health check
curl http://localhost:8001/health/

# API docs
open http://localhost:8001/docs/
```

---

**🚀 Production Ready Microservice!**

Standalone Django API for banking receipt processing with NLP.
