# 🏢 Akıllı Emlak Ödeme Yönetim Sistemi

**OCR + NLP + AI Chatbot + Dashboard** - Tam Entegre Dekont İşleme Sistemi

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-brightgreen.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🚀 **Hızlı Başlangıç:** [QUICK_START.md](QUICK_START.md)  
> 📄 **Final Rapor:** [FINAL_SUMMARY.md](FINAL_SUMMARY.md)

---

## 🎯 Proje Özeti

Emlak sektörü için **tam otomatik dekont işleme sistemi**. PDF dekontları yükleyin, sistem otomatik olarak:
- 📄 OCR ile metin çıkarır (4 banka desteği)
- 🎯 Ödeme tipini belirler (Intent Classification)
- 🏷️ Önemli bilgileri çıkarır (NER)
- 🔗 Veritabanı ile eşleştirir (Fuzzy Matching)
- 🤖 AI ile konuşarak sorgu yaparsınız
- 📊 Web dashboard'da sonuçları görürsünüz

### ✅ Tamamlanan Özellikler

**7 Ana Modül:**
- ✅ **OCR Extraction** - 4 banka desteği (Ziraat, Halkbank, Yapı Kredi, Kuveyt Türk)
- ✅ **Intent Classification** - DistilBERT-based, %100 accuracy (real data)
- ✅ **Named Entity Recognition** - Hybrid BERT+Regex, %99.8 F1-score
- ✅ **Full Pipeline** - PDF → JSON tek komutla
- ✅ **Receipt Matching** - Fuzzy matching, %87 confidence (real PDF)
- ✅ **Rule-based Chatbot** - Template-based + NLP entegrasyonu
- ✅ **Streamlit Dashboard** - Modern web UI + PDF upload + AI chat

---

## 📊 Performans Metrikleri

### Intent Classification (v3 Robust)
```
Synthetic Data:   96.67% accuracy
Real Data:       100.00% accuracy 🔥
Training:         800 samples
Inference:        <100ms/query

Kategoriler:
├─ kira_odemesi     (F1: 100%) 💯
├─ aidat_odemesi    (F1: 100%) 💯
├─ kapora_odemesi   (F1: 100%) 💯
└─ depozito_odemesi (F1: 100%) 💯
```

### Named Entity Recognition (Hybrid BERT+Regex)
```
Synthetic Data:  99.81% F1-score 🔥
Real Data:       88.00% recall
Training:        2500 samples
Method:          Hybrid (BERT + Regex fallback)

Entity Types (11 tip):
├─ sender, recipient    (Regex-based)
├─ amount, currency     (Hybrid)
├─ date, period         (Hybrid)
├─ iban, apt_no         (Hybrid)
└─ 3 more types         (NER-based)
```

### Receipt Matching
```
Real PDF Test:   87% confidence ✅
Auto-match:      83% success rate
Criteria:        5 (IBAN, amount, name, address, sender)
Performance:     <200ms/match
```

---

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# Repo'yu klonla
git clone https://github.com/Furkanturan8/rent-receipt-matcher
cd nlp-project

# Virtual environment oluştur ve aktif et
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. ⚠️ Model Dosyalarını İndir

**Model dosyaları GitHub'da YOK (7.6 GB)** - İki seçenek:


#### Eğitme Komutu: ⭐
```bash
# Intent Classification model eğit (~5-10 dakika)
python src/nlp/v3/train_intent_classifier.py

# NER model eğit (~5-10 dakika)
python src/nlp/v3/train_ner.py

# Modeller models/v3_robust/ klasörüne kaydedilir
```

**Not:** Eğitilmiş modeller olmadan sadece OCR çalışır. NLP özellikleri için model eğitimi gerekli.

### 3. Dashboard Başlat

```bash
# Streamlit dashboard (Web UI)
streamlit run src/dashboard/app.py

# Tarayıcıda otomatik açılır: http://localhost:8501
```

### 4. Komut Satırından Kullan

```bash
# Full pipeline - PDF işle
python src/pipeline/cli.py --pdf data/ziraatbank2.pdf --enable-matching --pretty

# Chatbot - İnteraktif sohbet
python src/chatbot/cli.py

# OCR - Sadece dekont çıkarma
python src/ocr/extraction/cli.py data/halkbank.pdf halkbank

# Makefile ile (daha kolay)
make pipeline-pdf PDF=data/ziraatbank2.pdf MATCH=1
make chatbot
make dashboard
```

### 5. Python'dan Kullan

```python
# Full Pipeline
from src.pipeline.full_pipeline import ReceiptPipeline

pipeline = ReceiptPipeline(enable_matching=True)
result = pipeline.process_from_file("data/ziraatbank2.pdf")
print(result['summary'])  # → Özet bilgi
print(result['matching']['confidence'])  # → %87

# Chatbot
from src.chatbot import RealEstateChatbot

chatbot = RealEstateChatbot()
response = chatbot.handle_message("Furkan Turan kimdir?")
print(response)  # → Kiracı bilgileri
```

---

## 📁 Proje Yapısı

```
nlp-project/
├── src/                              # Kaynak kodlar
│   ├── ocr/                          # OCR & Extraction
│   │   ├── extraction/               # Bank detection, regex patterns
│   │   └── matching/                 # Fuzzy matching, normalizers
│   ├── nlp/                          # NLP Models
│   │   ├── v1/                       # İlk versiyon (synthetic)
│   │   ├── v2/                       # OCR-aware versiyon
│   │   └── v3/                       # Robust versiyon (final)
│   ├── pipeline/                     # Full Pipeline
│   │   ├── full_pipeline.py          # Ana pipeline
│   │   └── cli.py                    # Komut satırı arayüzü
│   ├── chatbot/                      # AI Chatbot
│   │   ├── chatbot.py                # Ana chatbot mantığı
│   │   ├── templates.py              # Yanıt şablonları
│   │   └── cli.py                    # İnteraktif CLI
│   ├── dashboard/                    # Web Dashboard
│   │   └── app.py                    # Streamlit app
│   └── backend-simulation/           # Backend servisleri
│
├── data/                             # Veri setleri
│   ├── v1_synthetic/                 # Synthetic data (800 sample)
│   ├── v2_ocr_aware/                 # OCR-aware data
│   ├── v3_robust/                    # Robust data (2500 sample)
│   └── *.pdf                         # Test dekontları (ignore edildi)
│
├── models/                           # ⚠️ GitHub'da YOK (7.6 GB)
│   ├── v3_robust/                    # En son modeller
│   │   ├── intent_classifier/        # Intent model
│   │   └── ner/                      # NER model
│   └── ...                           # (Kendin eğitmelisin)
│
├── tests/                            # Test dosyaları
│   ├── mock-data.json                # Mock database
│   └── test_receipt_*.json           # Test case'ler
│
├── docs/                             # Dokümantasyon
│   ├── reports/                      # Raporlar
│   └── *.md                          # Teknik dokümanlar
│
├── scripts/                          # Data generation scriptleri
├── Makefile                          # Komut kısayolları
├── run.sh                            # Wrapper script
├── requirements.txt                  # Python bağımlılıkları
├── QUICK_START.md                    # Hızlı başlangıç rehberi
├── FINAL_SUMMARY.md                  # Final rapor
└── README.md                         # Bu dosya
```

**Not:** `.gitignore` ile `models/`, `*.pdf`, `.venv/`, `__pycache__/` ignore edilmiştir.

---

## 🛠️ Teknoloji Stack

### NLP & ML
- **Model:** DistilBERT-base-turkish-cased (Hugging Face)
- **Framework:** PyTorch 2.0+, Transformers 4.57+
- **Training:** 2500+ samples, Stratified split
- **Inference:** Hybrid (BERT + Regex) for robustness

### OCR & Processing
- **OCR:** Tesseract 4.x / PaddleOCR
- **Image Processing:** OpenCV, PIL
- **Logo Detection:** Template matching
- **Fuzzy Matching:** Levenshtein distance, Jaccard similarity

### Web & UI
- **Dashboard:** Streamlit 1.28+
- **Visualization:** Plotly (gauge & bar charts)
- **API:** Python-based (FastAPI-ready)

### Database & Matching
- **Mock DB:** JSON-based (tests/mock-data.json)
- **Matching:** Multi-criteria fuzzy matching
- **Normalization:** OCR error correction, Turkish chars

---

## 📚 Dokümantasyon

### Kullanıcı Rehberleri
- **README.md** - Bu dosya (Hızlı başlangıç)
- **docs/reports/README_TRAINING.md** - Detaylı model eğitim rehberi

### Geliştirici Raporları
- **docs/reports/PROGRESS_REPORT.md** - Detaylı ilerleme raporu
- **docs/reports/FINAL_SUMMARY.md** - Bugünün özet raporu
- **docs/reports/NER_RESULTS.md** - NER model sonuçları
- **docs/dataset-strategy.md** - Dataset toplama stratejisi

### Dokümantasyon Ana Sayfası
- **docs/README.md** - Tüm dokümantasyon rehberi

---

## 🎓 Akademik Değer

### Kullanılan NLP Teknikleri
✅ Transfer Learning (Pre-trained BERT)  
✅ Fine-tuning (Domain adaptation)  
✅ Text Classification (Supervised learning)  
✅ Model Evaluation (Precision, Recall, F1, Confusion Matrix)  
✅ Stratified Train/Val/Test Split

### Kapsam
- Dataset: 300+ örnek (synthetic + real karışık olacak)
- Model: Türkçe BERT fine-tuning
- Pipeline: OCR → Intent → NER → Chatbot → Dashboard
- Metrikler: %86.7 accuracy (synthetic data ile)

---

## 🎯 Özellikler ve Kullanım

### 📊 Web Dashboard
```bash
streamlit run src/dashboard/app.py
```
- **Tab 1 - Dekont İşleme:** PDF yükle, OCR, NLP, matching sonuçları
- **Tab 2 - AI Asistan:** ChatGPT benzeri interface, PDF yükleme + sohbet
- **Visualizations:** Gauge charts (confidence), bar charts (scores)
- **Export:** JSON download

### 🤖 AI Chatbot (CLI)
```bash
python src/chatbot/cli.py
```
**Özellikler:**
- Kiracı sorguları: "Furkan Turan kimdir?"
- Ödeme geçmişi: "geçmiş ödemelerini göster"
- Ödeme durumu: "Kasım ayı ödeme durumu"
- PDF işleme: `--pdf data/ziraatbank2.pdf`
- Template-based responses + NLP entegrasyonu

### 📄 Pipeline (CLI)
```bash
python src/pipeline/cli.py --pdf data/ziraatbank2.pdf --enable-matching --pretty
```
**İşlemler:**
1. Bank detection (logo-based)
2. OCR extraction (Tesseract/PaddleOCR)
3. Intent classification (BERT)
4. NER extraction (Hybrid BERT+Regex)
5. Database matching (Fuzzy matching)
6. JSON output (formatted)

### 🔍 OCR Only
```bash
python src/ocr/extraction/cli.py data/halkbank.pdf halkbank
```

## 🎓 Akademik Değer

### NLP Teknikleri
- ✅ **Transfer Learning** - Pre-trained BERT fine-tuning
- ✅ **Domain Adaptation** - Real estate domain specialization
- ✅ **Multi-task Learning** - Intent + NER jointly
- ✅ **Hybrid Approach** - BERT + Regex fallback for robustness
- ✅ **Data Augmentation** - Synthetic data generation
- ✅ **Evaluation Metrics** - Precision, Recall, F1, Confusion Matrix

## 📚 Dokümantasyon

### Ana Dokümanlar
- 📖 [README.md](README.md) - Bu dosya
- 🚀 [QUICK_START.md](QUICK_START.md) - Hızlı başlangıç rehberi
- 📄 [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - Final rapor

### Modül Dokümantasyonu
- [src/dashboard/README.md](src/dashboard/README.md) - Dashboard rehberi
- [src/chatbot/README.md](src/chatbot/README.md) - Chatbot rehberi
- [src/pipeline/README.md](src/pipeline/README.md) - Pipeline rehberi

### Teknik Dokümanlar
- [docs/](docs/) - Tüm teknik dokümanlar
- [docs/reports/](docs/reports/) - Detaylı raporlar

---




