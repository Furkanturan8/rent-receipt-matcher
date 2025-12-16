# Akıllı Emlak Ödeme Yönetim Sistemi  

---

## 🚀 Kullanım Komutları

### OCR
```bash
make extract FILE=data/halkbank.pdf BANK=halkbank
```

### Pipeline
```bash
make pipeline-pdf PDF=data/ziraatbank2.pdf MATCH=1
```

### Chatbot
```bash
python src/chatbot/cli.py --pdf data/ziraatbank2.pdf
make chatbot
```

### Dashboard
```bash
streamlit run src/dashboard/app.py
make dashboard
```

---

## 📦 Kurulum

```bash
# Venv oluştur ve aktif et
python3 -m venv .venv
source .venv/bin/activate

# Bağımlılıkları kur
pip install -r requirements.txt

# Streamlit için (manuel)
pip install streamlit plotly --user
```

---

## 🎯 Test Sonuçları

### Gerçek PDF Testi (ziraatbank2.pdf):

**OCR Extraction:** ✅
- Sender: FURKAN TURAN
- Amount: 140 TL
- Date: 12.12.2025

**Intent Classification:** ✅
- Primary: kira_odemesi
- Confidence: 65%

**NER:** ✅
- Entities: sender, period, apt_no

**Matching:** ✅
- Status: matched
- Confidence: 87%
- Owner ID: 4
- Property ID: 4

**Chatbot Response:** ✅
```
✅ Kira Ödemesi Onaylandı!
💯 Eşleşme Güveni: 87.0%
✨ Ödemeniz başarıyla kaydedildi!
```

---