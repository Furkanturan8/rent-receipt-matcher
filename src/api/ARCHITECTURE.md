# 🏗️ NLP Service Mimarisi

## 📐 Genel Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                           │
│         (React/Vue/Angular - API Consumer)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    DJANGO BACKEND                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Views     │  │   Models     │  │   Business       │  │
│  │  (Django)   │  │  (Database)  │  │    Logic         │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │             │
│         │                 │                    │             │
│  ┌──────▼─────────────────▼────────────────────▼─────────┐ │
│  │           NLP SERVICE (src.api)                       │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │  API Layer (views.py)                           │ │ │
│  │  │  - ProcessOCRView                               │ │ │
│  │  │  - ProcessPDFView                               │ │ │
│  │  │  - BatchProcessView                             │ │ │
│  │  └────────────────┬────────────────────────────────┘ │ │
│  │                   │                                   │ │
│  │  ┌────────────────▼────────────────────────────────┐ │ │
│  │  │  Service Layer (services.py)                    │ │ │
│  │  │  - Singleton NLPService                         │ │ │
│  │  │  - Lazy Model Loading                           │ │ │
│  │  │  - Pipeline Orchestration                       │ │ │
│  │  └────────────────┬────────────────────────────────┘ │ │
│  │                   │                                   │ │
│  └───────────────────┼───────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 NLP PIPELINE (src.pipeline)                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ReceiptPipeline                                    │    │
│  │  - OCR Extraction                                   │    │
│  │  - Intent Classification                            │    │
│  │  - NER Extraction                                   │    │
│  │  - Receipt Matching                                 │    │
│  └────────┬──────────────────┬────────────────┬────────┘    │
└───────────┼──────────────────┼────────────────┼─────────────┘
            │                  │                │
┌───────────▼─────┐  ┌─────────▼──────┐  ┌─────▼──────────┐
│  Intent Model   │  │   NER Model    │  │  OCR Module    │
│  (DistilBERT)   │  │  (DistilBERT)  │  │  (Tesseract)   │
│  v4 Production  │  │  v4 Production │  │  + Patterns    │
└─────────────────┘  └────────────────┘  └────────────────┘
```

## 🔄 Request Flow

### 1. OCR Output İşleme

```
Frontend sends OCR data
    ↓
POST /api/nlp/process-ocr/
    ↓
ProcessOCRView.post()
    ↓
Serialize & Validate (ProcessOCRRequestSerializer)
    ↓
nlp_service.process_ocr_output()
    ↓
ReceiptPipeline.process_ocr_output()
    ↓
┌─────────────────────────────────┐
│ 1. Intent Classification        │
│    - Preprocess (OCR correction)│
│    - BERT inference             │
│    - Confidence boosting        │
│    - Multi-intent detection     │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│ 2. NER Extraction               │
│    - Hybrid (BERT + Regex)      │
│    - Confidence-based selection │
│    - Multi-month support        │
│    - Entity merging             │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│ 3. Receipt Matching (optional)  │
│    - Fuzzy matching             │
│    - Score calculation          │
│    - Owner/Property matching    │
└────────┬────────────────────────┘
         │
    Build Response
         ↓
    Serialize (ProcessingResponseSerializer)
         ↓
    Return JSON to Frontend
```

### 2. PDF İşleme

```
Frontend uploads PDF
    ↓
POST /api/nlp/process-pdf/
    ↓
ProcessPDFView.post()
    ↓
Save to temp file
    ↓
nlp_service.process_pdf()
    ↓
ReceiptPipeline.process_from_file()
    ↓
┌─────────────────────────────────┐
│ 1. OCR Extraction               │
│    - PDF → Text (pdfminer)      │
│    - Bank detection             │
│    - Regex field extraction     │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│ 2-4. Same as OCR flow           │
│    (Intent + NER + Matching)    │
└────────┬────────────────────────┘
         │
    Clean up temp file
         ↓
    Return JSON
```

## 🧩 Component Details

### API Layer (`src/api/views.py`)

**Responsibility:** HTTP handling, validation, serialization

**Components:**
- `HealthCheckView`: Service health check
- `ProcessOCRView`: OCR output processing
- `ProcessPDFView`: PDF file processing
- `BatchProcessOCRView`: Batch processing

**Features:**
- Request validation with DRF serializers
- File upload handling (multipart/form-data)
- Error handling & logging
- Swagger/OpenAPI documentation

### Service Layer (`src/api/services.py`)

**Responsibility:** Business logic, model lifecycle

**Pattern:** Singleton + Lazy Loading

**Class:** `NLPService`

**Methods:**
- `process_ocr_output()`: Process OCR data
- `process_pdf()`: Process PDF file
- `health_check()`: Health status

**Features:**
- Single instance per process
- Models loaded on first request
- Thread-safe
- Error handling

### Pipeline Layer (`src/pipeline/full_pipeline.py`)

**Responsibility:** Orchestration, entity merging

**Class:** `ReceiptPipeline`

**Methods:**
- `process_ocr_output()`: Main processing logic
- `process_from_file()`: PDF processing
- `_merge_entities()`: OCR + NLP merge
- `_generate_summary()`: Human-readable summary

### Model Layer (`src/nlp/v4/`)

**Intent Classifier:**
- Model: DistilBERT-base-turkish-cased
- Classes: 4 (kira, aidat, kapora, depozito)
- Features: Multi-intent, confidence boosting

**NER Extractor:**
- Model: DistilBERT-base-turkish-cased
- Entities: 11 types
- Method: Hybrid (BERT + Regex)

## 🔐 Security Architecture

```
┌─────────────────────────────────────────┐
│  1. Request Arrives                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  2. CORS Middleware                     │
│     - Check origin                      │
│     - Validate headers                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  3. Authentication (Optional)           │
│     - Token validation                  │
│     - Session check                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  4. Throttling                          │
│     - Rate limiting                     │
│     - User/IP based                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  5. Input Validation                    │
│     - Serializers                       │
│     - File type check                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  6. Process Request                     │
└─────────────────────────────────────────┘
```

## 💾 Data Flow

### OCR Data Structure

```json
{
  "sender": "FURKAN TURAN",
  "sender_iban": "TR660001200146300002247852",
  "recipient": "Mustafa Derin",
  "receiver_iban": "TR090020200008733123900001",
  "description": "Çiçek Apt. No:8, Haziran kira ödemesi, 15000 TL",
  "amount": "15000.00",
  "amount_currency": "TRY",
  "date": "20/11/2025"
}
```

### Processing Result Structure

```json
{
  "status": "success",
  "timestamp": "2024-12-17T10:30:00",
  "ocr_data": {...},
  "intent": {
    "primary": "kira_odemesi",
    "confidence": 0.9574,
    "all_intents": [...],
    "is_multi_intent": false,
    "detected_intents": ["kira_odemesi"]
  },
  "ner": {
    "entities": {...},
    "extraction_method": {...},
    "confidence_scores": {...}
  },
  "final_entities": {
    "sender": "FURKAN TURAN",
    "receiver": "Mustafa Derin",
    "amount": "15000.00",
    "apt_no": "8",
    "period": "haziran"
  },
  "summary": "📋 Kira Ödemesi | 👤 Gönderen: FURKAN TURAN | ...",
  "matching": {...}
}
```

## ⚡ Performance Optimization

### 1. Lazy Loading
- Models loaded on first request
- Cached for subsequent requests
- Reduces startup time

### 2. Singleton Pattern
- Single model instance per worker
- Memory efficient
- Fast inference

### 3. Batch Processing
- Process multiple receipts together
- Reduced overhead
- Better throughput

### 4. Caching Strategy

```
Request 1 (cold):
  - Load models: 10-15s
  - Process: 200-300ms
  - Total: ~15s

Request 2+ (warm):
  - Models cached
  - Process: 100-200ms
  - Total: ~200ms
```

## 🔧 Configuration

### Environment Variables

```bash
# Model paths
MODEL_PATH=models/v4_production

# Service config
NLP_LAZY_LOADING=true
NLP_ENABLE_MATCHING=false

# Performance
NLP_TIMEOUT=120
NLP_MAX_WORKERS=2
```

### Django Settings

```python
# src/api specific settings
NLP_SERVICE_CONFIG = {
    'model_path': 'models/v4_production',
    'lazy_loading': True,
    'enable_matching': False,
}
```

## 📊 Monitoring & Metrics

### Key Metrics

1. **Request Latency**
   - Cold start: 10-15s
   - Warm request: 100-300ms
   - Target: <500ms (warm)

2. **Model Accuracy**
   - Intent: 73.33% (test), 95%+ (real)
   - NER: 99.28% F1-score
   - Matching: 80%+ confidence

3. **Throughput**
   - OCR: ~200 req/min (single worker)
   - PDF: ~20 req/min (OCR overhead)
   - Batch: ~500 receipts/min

4. **Resource Usage**
   - Memory: ~2GB per worker (with models)
   - CPU: ~50% during inference
   - Disk: <100MB (temp files)

### Health Indicators

```python
{
  "status": "healthy",
  "models_loaded": true,
  "uptime": "2h 35m",
  "requests_processed": 1247,
  "avg_latency_ms": 156,
  "error_rate": 0.002
}
```

## 🚀 Scaling Strategy

### Vertical Scaling
- Increase worker memory
- Add more CPU cores
- Use GPU for inference (optional)

### Horizontal Scaling
- Add more Django workers
- Load balancer
- Shared Redis cache (optional)

### Optimization Tips
1. Use Celery for async processing
2. Enable model quantization
3. Batch similar requests
4. Cache frequent queries

## 📚 Technology Stack

- **Web Framework:** Django 4.2+
- **REST API:** Django REST Framework
- **NLP Models:** Transformers (DistilBERT)
- **OCR:** Tesseract + pdfminer
- **Documentation:** drf-yasg (Swagger)
- **Serialization:** DRF Serializers
- **Validation:** Pydantic-style validation

## 🎯 Design Principles

1. **Separation of Concerns**
   - API, Service, Pipeline layers
   - Each layer has single responsibility

2. **Lazy Loading**
   - Models load on demand
   - Fast startup, memory efficient

3. **Error Resilience**
   - Graceful degradation
   - Detailed error messages
   - Proper logging

4. **Stateless Design**
   - No server-side session state
   - Horizontally scalable
   - Cloud-ready

5. **API-First**
   - REST principles
   - OpenAPI documentation
   - Version control ready
