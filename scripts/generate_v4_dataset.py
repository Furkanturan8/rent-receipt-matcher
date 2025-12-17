"""
v4 Dataset Generator - Production Ready
========================================

Yeni Özellikler:
1. FEE entity kaldırıldı (gereksiz)
2. TITLE entity eklendi (mülk adı: "Çalık-2 Apart")
3. Çoklu ay ödemeleri (kasım aralık ocak)
4. Tutar varyasyonları (24bin, 24bintl, 24000)
5. Mülk adı varyasyonları (çalık-2, çalık2, ÇALIK 2)
6. Daire varyasyonları (d2, daire:2, d:2)
7. Random sıralama (bilgiler karışık)
8. Boşluksuz yazım (24bintl, d2)

Entity Types (11):
- SENDER, RECEIVER, AMOUNT, DATE
- SENDER_IBAN, RECEIVER_IBAN, BANK, TRANSACTION_TYPE
- PERIOD (multi-month support)
- APT_NO
- TITLE (NEW!)
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path
import re

# Türkiye Bankaları
TURKIYE_BANKALARI = [
    ("Ziraat Bankası", "0001"),
    ("Halkbank", "0012"),
    ("Vakıfbank", "0015"),
    ("İş Bankası", "0064"),
    ("Garanti BBVA", "0062"),
    ("Yapı Kredi", "0067"),
    ("Akbank", "0046"),
    ("QNB Finansbank", "0111"),
    ("DenizBank", "0134"),
    ("Kuveyt Türk", "0205"),
]

ISLEM_TIPLERI = ["EFT", "Havale", "FAST"]

# Türkçe isimler
FULL_NAMES = [
    ("Ahmet", "Yılmaz"), ("Mehmet", "Demir"), ("Ayşe", "Kaya"), ("Fatma", "Şahin"),
    ("Ali", "Çelik"), ("Zeynep", "Arslan"), ("Mustafa", "Koç"), ("Emine", "Yıldız"),
    ("Furkan", "Turan"), ("Selin", "Aydın"), ("Can", "Öztürk"), ("Elif", "Aksoy"),
]

# Alıcı firmalar
ALICI_FIRMALAR = [
    "Ev Sahibi", "Emlak Ofisi", "Site Yönetimi", "Gayrimenkul A.Ş."
]

# Mülk isimleri (TITLE için)
MULK_ISIMLERI = [
    "Çalık", "Gül", "Lale", "Çiçek", "Yıldız", "Güneş", 
    "Aydın", "Nur", "Işık", "Bahçe", "Park", "Lotus"
]

MULK_TIPLERI = ["Apart", "Apartmanı", "Sitesi", "Rezidans", "Evleri"]

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# Gerçekçi kiralar (8.000 - 35.000 TL arası)
TUTARLAR = list(range(8000, 36000, 1000))

# Daire numaraları
DAIRE_NUMS = list(range(1, 25)) + ["A1", "A2", "B1", "B2", "C1"]

# =========================
# SYNONYM & VARIATIONS
# =========================

INTENT_SYNONYMS = {
    "kira": ["kira", "kira bedeli", "aylık ödeme", "kira ücreti", "konut kirası", "ev kirası"],
    "aidat": ["aidat", "site aidatı", "apartman aidatı", "yönetim aidatı", "ortak gider"],
    "kapora": ["kapora", "teminat", "ön ödeme", "peşinat", "avans"],
    "depozito": ["depozito", "güvence bedeli", "teminat bedeli", "garanti bedeli"]
}

# OCR Error Patterns
OCR_CONFUSIONS = {
    'i': ['i', 'i', 'i', '1', 'ı', 'l'],
    'ı': ['ı', 'ı', 'ı', 'i', '1'],
    'o': ['o', 'o', 'o', '0'],
    '0': ['0', '0', '0', 'O', 'o'],
    '1': ['1', '1', '1', 'l', 'I', 'i'],
    'l': ['l', 'l', 'l', '1', 'I'],
}

# =========================
# HELPER FUNCTIONS
# =========================

def generate_iban(banka_kodu=None):
    """IBAN üret"""
    if banka_kodu is None:
        banka_kodu = random.choice(TURKIYE_BANKALARI)[1]
    reserved = "0"
    account_no = str(random.randint(1000000000000000, 9999999999999999))
    check_digits = random.randint(10, 99)
    return f"TR{check_digits}{reserved}{banka_kodu}{account_no}"


def generate_date_time():
    """Tarih üret"""
    base = datetime.now()
    random_days = random.randint(0, 180)
    date_time = base - timedelta(days=random_days)
    return {
        "full": date_time.strftime("%d.%m.%Y %H:%M:%S"),
        "date_only": date_time.strftime("%d.%m.%Y"),
    }


def generate_title():
    """Mülk adı üret (TITLE entity)"""
    mulk_adi = random.choice(MULK_ISIMLERI)
    numara = random.choice(["", "-2", "-3", " 2", " 3", "2", "3"])
    
    # %60 tip ekle (Apart, Sitesi vb)
    if random.random() < 0.6:
        tip = random.choice(MULK_TIPLERI)
        return f"{mulk_adi}{numara} {tip}"
    else:
        return f"{mulk_adi}{numara}"


def generate_title_variations(base_title):
    """Mülk adı varyasyonları"""
    # "Çalık-2 Apart" → ["çalık-2", "çalık2", "ÇALIK 2", "çalık-2 apart"]
    
    # Temizle
    clean = base_title.replace("-", "").replace(" ", "")
    
    variations = [
        base_title,  # Original
        base_title.lower(),  # lowercase
        base_title.upper(),  # UPPERCASE
        clean.lower(),  # Boşluksuz
        base_title.replace("-", " "),  # - → space
        base_title.replace("-", ""),  # - kaldır
    ]
    
    return random.choice(variations)


def generate_apt_no_variations(apt_no):
    """Daire numarası varyasyonları"""
    # 14 → ["daire 14", "d14", "daire:14", "d:14", "14"]
    
    if isinstance(apt_no, int):
        apt_no = str(apt_no)
    
    variations = [
        f"daire {apt_no}",
        f"d{apt_no}",
        f"daire:{apt_no}",
        f"d:{apt_no}",
        f"DAİRE {apt_no}",
        f"Daire {apt_no}",
        apt_no,
    ]
    
    return random.choice(variations)


def generate_amount_variations(amount):
    """Tutar varyasyonları"""
    # 24000 → ["24 bin tl", "24bin", "24bintl", "24.000", "24000"]
    
    bin = amount // 1000  # 24000 → 24
    
    variations = [
        f"{amount:,}".replace(",", ".") + " TL",  # 24.000 TL
        f"{amount} TL",  # 24000 TL
        f"{bin} bin tl",  # 24 bin tl
        f"{bin}bin",  # 24bin
        f"{bin}bintl",  # 24bintl (boşluksuz)
        f"{bin} BİN TL",  # 24 BİN TL
        f"{amount}",  # 24000 (sadece rakam)
    ]
    
    return random.choice(variations)


def generate_multi_period():
    """
    Çoklu ay üret (1-3 ay arası)
    
    Dağılım:
    - %70 tek aylık (normal ödeme)
    - %20 iki aylık (iki ay birden)
    - %10 üç aylık (üç ay birden)
    """
    rand = random.random()
    
    if rand < 0.70:  # %70 tek ay
        num_months = 1
    elif rand < 0.90:  # %20 iki ay
        num_months = 2
    else:  # %10 üç ay
        num_months = 3
    
    start_month = random.randint(0, 11 - num_months + 1)
    months = [AYLAR[start_month + i] for i in range(num_months)]
    
    return months


def apply_ocr_error(text):
    """OCR hatası ekle"""
    if random.random() > 0.2:  # %20 chance
        return text
    
    result = []
    for char in text:
        if char.lower() in OCR_CONFUSIONS and random.random() < 0.1:
            result.append(random.choice(OCR_CONFUSIONS[char.lower()]))
        else:
            result.append(char)
    return ''.join(result)


def add_typo(word):
    """Typo ekle"""
    if len(word) <= 3 or random.random() > 0.15:
        return word
    
    # Harf düşürme
    if random.random() < 0.7:
        idx = random.randint(1, len(word) - 2)
        return word[:idx] + word[idx+1:]
    else:
        # Harf tekrarlama
        idx = random.randint(0, len(word) - 1)
        return word[:idx] + word[idx] + word[idx:]


# =========================
# DATASET GENERATION
# =========================

def generate_user_description(intent_type, title, apt_no, months, amount):
    """
    Kullanıcı açıklaması üret (serbest format, karışık sıralı)
    
    Örnek: "24bintl kasım aralık ocak çalık2 d2"
    """
    intent_word = intent_type.split('_')[0]
    
    # Parçaları hazırla
    parts = []
    
    # 1. Tutar (%80 şans)
    if random.random() < 0.8:
        parts.append(generate_amount_variations(amount))
    
    # 2. Period(lar) (%90 şans)
    if random.random() < 0.9 and months:
        # Ayları birleştir: "kasım aralık ocak"
        month_text = " ".join([m.lower() for m in months])
        parts.append(month_text)
    
    # 3. Intent kelimesi (%70 şans)
    if random.random() < 0.7:
        intent_text = random.choice(INTENT_SYNONYMS[intent_word])
        parts.append(intent_text)
    
    # 4. Title (%85 şans)
    if random.random() < 0.85 and title:
        title_var = generate_title_variations(title)
        parts.append(title_var)
    
    # 5. Apt No (%80 şans)
    if random.random() < 0.8 and apt_no:
        apt_var = generate_apt_no_variations(apt_no)
        parts.append(apt_var)
    
    # Random sırala!
    random.shuffle(parts)
    
    # Birleştir
    description = " ".join(parts)
    
    # Noise ekle
    if random.random() < 0.3:
        description = apply_ocr_error(description)
    
    if random.random() < 0.2:
        words = description.split()
        description = " ".join([add_typo(w) for w in words])
    
    return description


def generate_v4_ner_dataset(num_samples=3000):
    """v4 NER dataset üret"""
    dataset = []
    
    intents = ["kira_odemesi", "aidat_odemesi", "kapora_odemesi", "depozito_odemesi"]
    samples_per_intent = num_samples // len(intents)
    
    print("🎯 v4 NER Dataset Generation")
    print(f"📊 Target: {num_samples} samples")
    print(f"✨ Features: Multi-period, Title, Amount variations, Random order")
    print()
    
    for intent in intents:
        print(f"🔄 Generating {intent}...")
        
        for i in range(samples_per_intent):
            # Base data
            ad, soyad = random.choice(FULL_NAMES)
            alici_firma = random.choice(ALICI_FIRMALAR)
            banka_adi, banka_kodu = random.choice(TURKIYE_BANKALARI)
            islem_tipi = random.choice(ISLEM_TIPLERI)
            tutar_raw = random.choice(TUTARLAR)
            date_time = generate_date_time()
            gonderen_iban = generate_iban(banka_kodu)
            alici_iban = generate_iban()
            
            # Yeni: TITLE ve multi-period
            title = generate_title()
            months = generate_multi_period()  # ["Kasım"] veya ["Kasım", "Aralık", "Ocak"]
            apt_no = random.choice(DAIRE_NUMS) if random.random() < 0.8 else None
            
            # Çoklu ay için tutar ayarla
            monthly_amount = tutar_raw
            total_amount = tutar_raw * len(months)
            
            # OCR Data (Clean, structured)
            ocr_data = {
                "sender_name": f"{ad} {soyad}",
                "sender_iban": gonderen_iban,
                "receiver_name": alici_firma,
                "receiver_iban": alici_iban,
                "bank": banka_adi,
                "transaction_type": islem_tipi,
                "date": date_time["full"],
                "amount": f"{total_amount}.00 TL",
            }
            
            # User Description (Noisy, random order)
            user_description = generate_user_description(
                intent_type=intent,
                title=title,
                apt_no=apt_no,
                months=months,
                amount=total_amount
            )
            
            # Combined Text
            combined_text = (
                f"Gönderen: {ocr_data['sender_name']} "
                f"IBAN: {gonderen_iban} "
                f"Alan: {alici_firma} "
                f"IBAN: {alici_iban} "
                f"Banka: {banka_adi} "
                f"İşlem: {islem_tipi} "
                f"Tutar: {total_amount}.00 TL "
                f"Tarih: {date_time['full']} "
                f"Açıklama: {user_description}"
            )
            
            # Ground Truth Entities
            entities = {
                "SENDER": [f"{ad} {soyad}"],
                "RECEIVER": [alici_firma],
                "AMOUNT": [f"{total_amount}.00 TL"],
                "DATE": [date_time["date_only"]],
                "SENDER_IBAN": [gonderen_iban],
                "RECEIVER_IBAN": [alici_iban],
                "BANK": [banka_adi],
                "TRANSACTION_TYPE": [islem_tipi],
            }
            
            # Multi-period
            if months:
                entities["PERIOD"] = months  # ["Kasım", "Aralık", "Ocak"]
            
            # APT_NO
            if apt_no:
                entities["APT_NO"] = [str(apt_no)]
            
            # TITLE (NEW!)
            if title:
                entities["TITLE"] = [title]
            
            dataset.append({
                "text": combined_text,
                "entities": entities,
                "intent": intent,
                "ocr_data": ocr_data,
                "user_description": user_description,
            })
    
    print(f"\n✅ Generated {len(dataset)} samples")
    return dataset


def generate_v4_intent_dataset(num_samples=1000):
    """v4 Intent dataset üret"""
    dataset = []
    
    intents = ["kira_odemesi", "aidat_odemesi", "kapora_odemesi", "depozito_odemesi"]
    samples_per_intent = num_samples // len(intents)
    
    print("🎯 v4 Intent Dataset Generation")
    print(f"📊 Target: {num_samples} samples")
    print()
    
    for intent in intents:
        print(f"🔄 Generating {intent}...")
        
        for i in range(samples_per_intent):
            intent_word = intent.split('_')[0]
            
            # Random data
            title = generate_title()
            apt_no = random.choice(DAIRE_NUMS) if random.random() < 0.5 else None
            months = generate_multi_period()
            amount = random.choice(TUTARLAR) * len(months)
            
            # User description üret
            text = generate_user_description(
                intent_type=intent,
                title=title,
                apt_no=apt_no,
                months=months,
                amount=amount
            )
            
            dataset.append({
                "text": text,
                "label": intent
            })
    
    print(f"\n✅ Generated {len(dataset)} samples")
    return dataset


def generate_realistic_extreme_samples(num_ner=600, num_intent=200):
    """
    Daha gerçekçi/ekstrem örnekler üret
    - Eksik bilgiler
    - Daha fazla typo
    - İnformal yazım
    """
    print("\n🔥 GENERATING REALISTIC EXTREME SAMPLES")
    print("-"*80)
    
    ner_data = []
    intent_data = []
    
    intents = ["kira_odemesi", "aidat_odemesi", "kapora_odemesi", "depozito_odemesi"]
    
    # Informal intent words
    informal_intents = {
        "kira": ["kira", "kra", "kiraa", "kra"],
        "aidat": ["aidat", "aydat", "adat", "aydat odeme"],
        "kapora": ["kapora", "kapara", "kapro", "kapra"],
        "depozito": ["depozito", "depo", "depozit", "dpozit"]
    }
    
    for i in range(num_ner):
        intent = random.choice(intents)
        intent_word = intent.split('_')[0]
        
        # Base data
        ad, soyad = random.choice(FULL_NAMES)
        alici_firma = random.choice(ALICI_FIRMALAR)
        banka_adi, banka_kodu = random.choice(TURKIYE_BANKALARI)
        islem_tipi = random.choice(ISLEM_TIPLERI)
        tutar_raw = random.choice(TUTARLAR)
        date_time = generate_date_time()
        gonderen_iban = generate_iban(banka_kodu)
        alici_iban = generate_iban()
        
        title = generate_title()
        months = generate_multi_period()
        apt_no = random.choice(DAIRE_NUMS) if random.random() < 0.7 else None
        total_amount = tutar_raw * len(months)
        
        # OCR Data (clean)
        ocr_data = {
            "sender_name": f"{ad} {soyad}",
            "sender_iban": gonderen_iban,
            "receiver_name": alici_firma,
            "receiver_iban": alici_iban,
            "bank": banka_adi,
            "transaction_type": islem_tipi,
            "date": date_time["full"],
            "amount": f"{total_amount}.00 TL",
        }
        
        # Realistic extreme description
        parts = []
        
        # Eksik bilgi: %40 şans ile bazı bilgileri atla
        include_amount = random.random() < 0.6  # %60 tutar var
        include_period = random.random() < 0.8  # %80 ay var
        include_title = random.random() < 0.7   # %70 title var
        include_apt = random.random() < 0.6     # %60 daire var
        include_intent = random.random() < 0.5  # %50 intent kelimesi var
        
        if include_amount:
            # Typo in amount (%30 şans)
            if random.random() < 0.3:
                amount_text = f"{tutar_raw//1000}bni"  # "bin" → "bni"
            else:
                amount_text = generate_amount_variations(total_amount)
            parts.append(amount_text)
        
        if include_period and months:
            # Typo in months (%20 şans)
            month_texts = []
            for m in months:
                if random.random() < 0.2:
                    # Typo: kasım → kasmi, ocak → ocaj
                    m_typo = m.lower()
                    if 'ı' in m_typo:
                        m_typo = m_typo.replace('ı', 'i')
                    if 'k' in m_typo and random.random() < 0.5:
                        m_typo = m_typo.replace('k', 'j', 1)  # ocak → ocaj
                    month_texts.append(m_typo)
                else:
                    month_texts.append(m.lower())
            parts.append(" ".join(month_texts))
        
        if include_intent:
            # Informal intent word
            intent_text = random.choice(informal_intents[intent_word])
            parts.append(intent_text)
        
        if include_title and title:
            # Typo in title (%20 şans)
            title_text = generate_title_variations(title)
            if random.random() < 0.2:
                # çalık → calik, ı → i
                title_text = title_text.replace('ı', 'i').replace('ğ', 'g').replace('ş', 's')
            parts.append(title_text)
        
        if include_apt and apt_no:
            apt_text = generate_apt_no_variations(apt_no)
            parts.append(apt_text)
        
        # En az 1 bilgi olmalı
        if not parts:
            parts.append(generate_amount_variations(total_amount))
        
        # Random sırala
        random.shuffle(parts)
        user_description = " ".join(parts)
        
        # Combined text
        combined_text = (
            f"Gönderen: {ocr_data['sender_name']} "
            f"IBAN: {gonderen_iban} "
            f"Alan: {alici_firma} "
            f"IBAN: {alici_iban} "
            f"Banka: {banka_adi} "
            f"İşlem: {islem_tipi} "
            f"Tutar: {total_amount}.00 TL "
            f"Tarih: {date_time['full']} "
            f"Açıklama: {user_description}"
        )
        
        # Entities
        entities = {
            "SENDER": [f"{ad} {soyad}"],
            "RECEIVER": [alici_firma],
            "AMOUNT": [f"{total_amount}.00 TL"],
            "DATE": [date_time["date_only"]],
            "SENDER_IBAN": [gonderen_iban],
            "RECEIVER_IBAN": [alici_iban],
            "BANK": [banka_adi],
            "TRANSACTION_TYPE": [islem_tipi],
        }
        
        if months:
            entities["PERIOD"] = months
        if apt_no:
            entities["APT_NO"] = [str(apt_no)]
        if title:
            entities["TITLE"] = [title]
        
        ner_data.append({
            "text": combined_text,
            "entities": entities,
            "intent": intent,
            "ocr_data": ocr_data,
            "user_description": user_description,
        })
    
    # Intent data
    for i in range(num_intent):
        intent = random.choice(intents)
        intent_word = intent.split('_')[0]
        
        title = generate_title() if random.random() < 0.6 else None
        apt_no = random.choice(DAIRE_NUMS) if random.random() < 0.4 else None
        months = generate_multi_period() if random.random() < 0.7 else []
        amount = random.choice(TUTARLAR) * (len(months) if months else 1)
        
        parts = []
        
        if random.random() < 0.5:
            parts.append(generate_amount_variations(amount))
        if months and random.random() < 0.7:
            parts.append(" ".join([m.lower() for m in months]))
        if random.random() < 0.4:
            parts.append(random.choice(informal_intents[intent_word]))
        if title and random.random() < 0.6:
            parts.append(generate_title_variations(title))
        if apt_no and random.random() < 0.5:
            parts.append(generate_apt_no_variations(apt_no))
        
        if not parts:
            parts.append(random.choice(informal_intents[intent_word]))
        
        random.shuffle(parts)
        text = " ".join(parts)
        
        intent_data.append({
            "text": text,
            "label": intent
        })
    
    print(f"✅ Generated {len(ner_data)} NER + {len(intent_data)} Intent samples")
    return ner_data, intent_data


def main():
    """Ana fonksiyon"""
    output_dir = Path("data/v4_production")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("🚀 v4 DATASET GENERATION - PRODUCTION READY")
    print("="*80)
    print()
    print("✨ NEW FEATURES:")
    print("  1. FEE entity removed (unnecessary)")
    print("  2. TITLE entity added (property name)")
    print("  3. Multi-period support (kasım aralık ocak)")
    print("  4. Amount variations (24bin, 24bintl, 24000)")
    print("  5. Title variations (çalık-2, çalık2, ÇALIK 2)")
    print("  6. Apt variations (d2, daire:2, d:2)")
    print("  7. Random order (info shuffled)")
    print("  8. No-space format (24bintl, d2)")
    print()
    print("="*80)
    print()
    
    # Generate Base Dataset
    print("📋 GENERATING BASE DATASET...")
    print("-"*80)
    ner_data = generate_v4_ner_dataset(num_samples=3000)
    intent_data = generate_v4_intent_dataset(num_samples=1000)
    
    print(f"✅ Base: {len(ner_data)} NER + {len(intent_data)} Intent")
    print()
    
    # Generate Realistic Extreme Samples
    realistic_ner, realistic_intent = generate_realistic_extreme_samples(
        num_ner=600,
        num_intent=200
    )
    
    # Merge datasets
    print("\n🔗 MERGING DATASETS...")
    ner_data.extend(realistic_ner)
    intent_data.extend(realistic_intent)
    
    print(f"✅ Total: {len(ner_data)} NER + {len(intent_data)} Intent")
    print()
    
    # Save NER
    ner_output = output_dir / "ner_v4.json"
    with open(ner_output, 'w', encoding='utf-8') as f:
        json.dump(ner_data, f, ensure_ascii=False, indent=2)
    print(f"💾 NER saved: {ner_output}")
    
    # Save Intent
    intent_output = output_dir / "intent_v4.json"
    with open(intent_output, 'w', encoding='utf-8') as f:
        json.dump(intent_data, f, ensure_ascii=False, indent=2)
    print(f"💾 Intent saved: {intent_output}")
    print()
    
    # Statistics
    print("="*80)
    print("📊 DATASET STATISTICS")
    print("="*80)
    print(f"\n✅ NER: {len(ner_data)} samples")
    print(f"✅ Intent: {len(intent_data)} samples")
    print(f"✅ Total: {len(ner_data) + len(intent_data)} samples")
    
    # Entity distribution
    print("\n📈 Entity Distribution:")
    entity_counts = {}
    for sample in ner_data:
        for entity_type in sample["entities"].keys():
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    for entity, count in sorted(entity_counts.items()):
        percentage = (count / len(ner_data)) * 100
        print(f"  {entity:18s} {count:4d} ({percentage:5.1f}%)")
    
    # Sample examples (from realistic extreme)
    print("\n📝 Realistic Extreme Samples (son 600'den):")
    for i in range(5):
        sample = ner_data[-(600-i*100)]  # Son 600'den örnekle
        print(f"\n  [{i+1}] {sample['user_description']}")
        print(f"      Intent: {sample['intent']}")
        entities_str = ", ".join([f"{k}: {v}" for k, v in sample['entities'].items() 
                                   if k in ['TITLE', 'APT_NO', 'PERIOD', 'AMOUNT']])
        print(f"      Entities: {entities_str}")
    
    print("\n📝 Base Samples (ilk 3000'den):")
    for i in range(3):
        sample = random.choice(ner_data[:3000])
        print(f"\n  [{i+1}] {sample['user_description']}")
        print(f"      Intent: {sample['intent']}")
        entities_str = ", ".join([f"{k}: {v}" for k, v in sample['entities'].items() 
                                   if k in ['TITLE', 'APT_NO', 'PERIOD', 'AMOUNT']])
        print(f"      Entities: {entities_str}")
    
    print()
    print("="*80)
    print("✨ DATASET GENERATION COMPLETE!")
    print("="*80)
    print()
    print("🎯 Next Steps:")
    print("  1. Train v4 models:")
    print("     python src/nlp/v4/train_intent_classifier.py")
    print("     python src/nlp/v4/train_ner.py")
    print("  2. Test with real data")
    print()


if __name__ == "__main__":
    main()

