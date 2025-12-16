# 🤖 Rule-Based Chatbot Module

Template-based conversational AI for real estate payment management.

---

## 💬 Example Conversations

### 1. Receipt Processing

```
👤 Siz: data/ziraatbank2.pdf

🤖 Bot:
✅ **Kira Ödemesi Onaylandı!**

📋 Ödeme Detayları:
   • Gönderen: FURKAN TURAN
   • Alıcı: Furkan Turan
   • Tutar: 140,00 TRY
   • Tarih: 12.12.2025 - 22:17:09
   • Daire: 14
   • Dönem: kasım

🏠 Eşleşen Kayıt:
   • Mülk Sahibi: Furkan Turan
   • Kiracı: Furkan Turan
   • Adres: Çiçek Apartmanı No:14
   
💯 Eşleşme Güveni: 87.0%

✨ Ödemeniz başarıyla kaydedildi!
```

### 2. Help Menu

```
👤 Siz: yardım

🤖 Bot:
📋 Yapabilecekleriniz:

1️⃣ **Dekont İşleme**
   • Dekont PDF'i yükleyerek otomatik işlem

2️⃣ **Ödeme Sorgulama**
   • Ödeme durumu kontrol
   • Geçmiş ödemeler

3️⃣ **Kiracı Bilgileri**
   • Kişisel bilgiler
   • Kira detayları

💡 Komut örnekleri:
   • "Kiracı bilgilerimi göster"
   • "Yardım"
```

### 3. Tenant Information

```
👤 Siz: Furkan Turan bilgilerini göster

🤖 Bot:
👤 **Kiracı Bilgileri**

📋 Kişisel Bilgiler:
   • Ad Soyad: Furkan Turan
   • Email: - email - 
   • Telefon: - telefon numarası - 

🏠 Mülk Bilgileri:
   • Adres: Çiçek Apartmanı No:14
   • Kira: 14000 TL/ay

💳 Ödeme Bilgileri:
   • Mülk Sahibi: Furkan Turan
   • IBAN: - iban numarası - 
```

---

## 📂 Module Structure

```
src/chatbot/
├── __init__.py          # Module exports
├── chatbot.py           # Main chatbot class
├── templates.py         # Response templates
├── cli.py              # CLI interface
└── README.md           # This file
```

---

## 🎯 Response Templates

### Payment Confirmed
- `kira_odemesi` - Rent payment
- `aidat_odemesi` - Maintenance fee
- `kapora_odemesi` - Deposit
- `depozito_odemesi` - Security deposit

### Payment Errors
- `amount_mismatch` - Amount doesn't match
- `iban_mismatch` - IBAN doesn't match
- `name_mismatch` - Name doesn't match
- `no_match` - No matching record
- `low_confidence` - Low confidence score

### General
- `WELCOME` - Welcome message
- `HELP_MENU` - Help menu
- `GOODBYE` - Goodbye message
- `UNKNOWN` - Unknown command

---

## 📝 Notes

- This is a **rule-based** chatbot (no LLM/NLG)
- Templates are **Turkish** language
- Requires NLP models to be trained
- Database queries are **mock data** based

---
