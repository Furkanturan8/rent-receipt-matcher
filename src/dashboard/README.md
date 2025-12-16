# 📊 Streamlit Dashboard

Modern web-based interface for real estate payment management.

---

## 🚀 Installation

### 1. Install Dependencies

```bash
pip install streamlit plotly
```

Or from requirements:

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
streamlit --version
```

---

## 💻 Usage

### Start Dashboard

```bash
# From project root
streamlit run src/dashboard/app.py

# Or with make
make dashboard

# Or with run.sh
./run.sh dashboard
```

### Access Dashboard

Open browser at: `http://localhost:8501`

---

## 📋 User Guide

### Step 1: Load Models
1. Click **"🚀 Modelleri Yükle"** button in sidebar
2. Wait for models to load (~10 seconds)
3. See success message

### Step 2: Upload PDF
1. Click **"Browse files"** or drag-and-drop PDF
2. Supported format: PDF only
3. File appears in upload area

### Step 3: Process Receipt
1. Click **"🔄 İşle"** button
2. Wait for processing (~2-5 seconds)
3. View results automatically

### Step 4: Explore Results

**Tab 1 - Özet (Summary):**
- Sender/Receiver information
- Amount and date
- Description
- Matching status

**Tab 2 - Intent & NER:**
- Intent classification results
- Confidence scores
- Extracted entities (NER)
- All intent probabilities

**Tab 3 - Eşleşme (Matching):**
- Overall confidence gauge
- Criteria scores bar chart
- Detailed score metrics
- Matching messages

**Tab 4 - Ham Veri (Raw Data):**
- Complete JSON output
- Copy-paste ready
- Debugging information

---

## 🎯 Screenshots

### Main Interface
```
┌─────────────────────────────────────────┐
│  🏢 Emlak Ödeme Yönetim Sistemi        │
├─────────────────────────────────────────┤
│                                         │
│  📤 Dekont Yükleme                      │
│  ┌───────────────────────────────────┐ │
│  │   Drag & Drop PDF here...         │ │
│  └───────────────────────────────────┘ │
│                                         │
│         [🔄 İşle]                       │
│                                         │
└─────────────────────────────────────────┘
```

### Results Display
```
┌─────────────────────────────────────────┐
│  📊 İşlem Sonuçları                     │
├─────────────────────────────────────────┤
│  [📋 Özet] [🎯 Intent & NER]           │
│  [🔗 Eşleşme] [📄 Ham Veri]            │
├─────────────────────────────────────────┤
│  👤 Gönderen    👤 Alıcı    💰 Tutar    │
│  FURKAN TURAN   FURKAN     140 TRY     │
│  TR98...        TURAN                   │
│                 TR54...                 │
├─────────────────────────────────────────┤
│  ✅ Eşleşme Bulundu!                    │
│  Güven Skoru: 87.0%                     │
└─────────────────────────────────────────┘
```
---