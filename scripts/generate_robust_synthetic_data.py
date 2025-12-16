"""
Robust Synthetic Dataset Generator - v3
- AMOUNT bug düzeltildi
- Noise injection (random kelime, silme, harf düşürme)
- Synonym replacement
- OCR error simulation
- Ambiguous data patterns
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path
import re

# Türkiye'nin Büyük Bankaları
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
    ("TEB", "0032"),
    ("ING", "0099"),
    ("Kuveyt Türk", "0205"),
]

# İşlem Tipleri
ISLEM_TIPLERI = ["EFT", "Havale", "FAST"]

# Türkçe isimler
FULL_NAMES = [
    ("Ahmet", "Yılmaz"), ("Mehmet", "Demir"), ("Ayşe", "Kaya"), ("Fatma", "Şahin"),
    ("Ali", "Çelik"), ("Zeynep", "Arslan"), ("Mustafa", "Koç"), ("Emine", "Yıldız"),
    ("Hüseyin", "Öztürk"), ("Hatice", "Aydın"), ("İbrahim", "Özdemir"), ("Elif", "Aksoy"),
    ("Ömer", "Yılmaz"), ("Zehra", "Polat"), ("Burak", "Şimşek"), ("Merve", "Çetin"),
    ("Emre", "Kara"), ("Selin", "Akar"), ("Can", "Erdoğan"), ("Defne", "Yavuz"),
]

# Alıcı firmalar
ALICI_FIRMALAR = [
    "ABC Gayrimenkul", "XYZ Emlak Yönetim", "Güven Emlak",
    "Metropol Gayrimenkul", "Prestij Emlak", "Site Yönetimi",
    "Ev Sahibi", "Konut Yönetimi"
]

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
TUTARLAR = list(range(5000, 35000, 1000))
DAIRE_NUMS = ["1", "2", "3", "5", "8", "12", "15", "22", "A1", "A2", "B1", "B3", "C4"]

# =========================
# SYNONYM DICTIONARIES
# =========================

INTENT_SYNONYMS = {
    "kira": ["kira", "kira bedeli", "aylık ödeme", "kira ücreti", "konut kirası"],
    "aidat": ["aidat", "site aidatı", "apartman aidatı", "yönetim aidatı", "ortak gider"],
    "kapora": ["kapora", "teminat", "ön ödeme", "peşinat", "avans"],
    "depozito": ["depozito", "güvence bedeli", "teminat bedeli", "garanti bedeli"]
}

DESCRIPTIVE_SYNONYMS = {
    "ödeme": ["ödeme", "ödendi", "gönderildi", "transfer", "yatırıldı"],
    "için": ["için", "adına", "hesabına", "-", ""],
    "yapıldı": ["yapıldı", "gerçekleşti", "tamamlandı", ""],
}

# =========================
# OCR ERROR PATTERNS
# =========================

OCR_CONFUSIONS = {
    'a': ['a', 'a', 'a', 'e'],  # çoğu zaman doğru, bazen hata
    'e': ['e', 'e', 'e', 'a'],
    'i': ['i', 'i', 'i', '1', 'ı', 'l'],
    'ı': ['ı', 'ı', 'ı', 'i', '1'],
    'o': ['o', 'o', 'o', '0'],
    '0': ['0', '0', '0', 'O', 'o'],
    '1': ['1', '1', '1', 'l', 'I', 'i'],
    'l': ['l', 'l', 'l', '1', 'I'],
    'I': ['I', 'I', 'I', 'l', '1'],
    's': ['s', 's', 's', '5'],
    '5': ['5', '5', '5', 's', 'S'],
}

# =========================
# NOISE FUNCTIONS
# =========================

def add_typo(word):
    """Kelimeye typo ekle (harf düşürme)"""
    if len(word) <= 3 or random.random() > 0.15:  # %15 chance
        return word
    
    # Harf düşürme
    if random.random() < 0.7:
        idx = random.randint(1, len(word) - 2)  # İlk ve son harf değil
        return word[:idx] + word[idx+1:]
    
    # Harf tekrarlama
    else:
        idx = random.randint(0, len(word) - 1)
        return word[:idx] + word[idx] + word[idx:]


def add_ocr_error(text):
    """OCR okuma hatası ekle"""
    if random.random() > 0.25:  # %25 chance
        return text
    
    result = []
    for char in text:
        if char.lower() in OCR_CONFUSIONS and random.random() < 0.1:  # %10 per char
            result.append(random.choice(OCR_CONFUSIONS[char.lower()]))
        else:
            result.append(char)
    return ''.join(result)


def add_spacing_error(text):
    """Spacing hatası ekle"""
    if random.random() > 0.2:  # %20 chance
        return text
    
    words = text.split()
    if len(words) < 2:
        return text
    
    # Random kelime birleştir veya böl
    if random.random() < 0.5 and len(words) >= 2:
        # Birleştir
        idx = random.randint(0, len(words) - 2)
        words[idx] = words[idx] + words[idx + 1]
        words.pop(idx + 1)
    else:
        # Böl
        idx = random.randint(0, len(words) - 1)
        word = words[idx]
        if len(word) > 4:
            split_pos = len(word) // 2
            words[idx] = word[:split_pos] + " " + word[split_pos:]
    
    return ' '.join(words)


def add_random_noise(text):
    """Random noise: kelime ekleme/silme/yer değiştirme"""
    if random.random() > 0.3:  # %30 chance
        return text
    
    words = text.split()
    if len(words) < 3:
        return text
    
    noise_type = random.choice(['add', 'remove', 'swap'])
    
    if noise_type == 'add':
        # Filler words ekle
        fillers = ["işte", "yani", "böyle", "şey", "hani", "ya", "o"]
        idx = random.randint(0, len(words))
        words.insert(idx, random.choice(fillers))
    
    elif noise_type == 'remove' and len(words) > 3:
        # Random kelime sil (önemli olmayanlardan)
        removable = ["için", "adına", "ile", "de", "da"]
        for word in removable:
            if word in words:
                words.remove(word)
                break
        else:
            # Hiç yoksa random sil
            idx = random.randint(0, len(words) - 1)
            words.pop(idx)
    
    elif noise_type == 'swap' and len(words) >= 2:
        # İki kelimenin yerini değiştir
        idx1 = random.randint(0, len(words) - 2)
        idx2 = idx1 + 1
        words[idx1], words[idx2] = words[idx2], words[idx1]
    
    return ' '.join(words)


def apply_synonym_replacement(text, intent_type):
    """Synonym replacement uygula"""
    if random.random() > 0.4:  # %40 chance
        return text
    
    # Intent-specific synonyms
    for original, synonyms in INTENT_SYNONYMS.items():
        if original in text.lower():
            text = re.sub(original, random.choice(synonyms), text, flags=re.IGNORECASE)
            break
    
    # Descriptive synonyms
    for original, synonyms in DESCRIPTIVE_SYNONYMS.items():
        if original in text.lower():
            text = re.sub(original, random.choice(synonyms), text, flags=re.IGNORECASE)
    
    return text


def generate_ambiguous_description(intent1, intent2):
    """Çelişkili/ambiguous açıklama üret"""
    templates = [
        f"{random.choice(AYLAR)} {intent1} {intent2}",
        f"{intent1} ve {intent2} ödemesi",
        f"{intent1} olarak {intent2}",
        f"{intent2} gibi {intent1}",
    ]
    return random.choice(templates)


# =========================
# HELPER FUNCTIONS
# =========================

def generate_iban(banka_kodu=None):
    """Türk IBAN üret"""
    if banka_kodu is None:
        banka_kodu = random.choice(TURKIYE_BANKALARI)[1]
    
    reserved = "0"
    account_no = str(random.randint(1000000000000000, 9999999999999999))
    check_digits = random.randint(10, 99)
    
    return f"TR{check_digits}{reserved}{banka_kodu}{account_no}"


def generate_date_time():
    """Tarih ve saat üret"""
    base = datetime.now()
    random_days = random.randint(0, 180)
    date_time = base - timedelta(days=random_days)
    
    return {
        "full": date_time.strftime("%d.%m.%Y %H:%M:%S"),
        "date_only": date_time.strftime("%d.%m.%Y"),
        "with_time": date_time.strftime("%d.%m.%Y %H:%M"),
    }


def generate_islem_ucreti():
    """İşlem ücreti"""
    if random.random() < 0.7:  # %70 ücretsiz
        return "0.00"
    else:
        return str(random.choice([2.00, 2.50, 3.00, 3.50, 4.00, 5.00]))


# =========================
# MAIN GENERATION FUNCTIONS
# =========================

def generate_robust_ner_dataset(num_samples=2500):
    """
    Robust NER dataset - v3
    - AMOUNT bug düzeltildi (combined_text'e eklendi!)
    - Noise injection
    - Synonym replacement
    - OCR errors
    - Ambiguous patterns
    """
    dataset = []
    
    # Intent dağılımı
    intents = ["kira_odemesi", "aidat_odemesi", "kapora_odemesi", "depozito_odemesi"]
    samples_per_intent = num_samples // len(intents)
    
    print("🎯 Robust NER Dataset Generation (v3) - AMOUNT BUG FİXED!")
    print(f"📊 Target samples: {num_samples}")
    print(f"🔧 Features: Noise, Synonyms, OCR Errors, Ambiguous Data")
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
            ucret = generate_islem_ucreti()
            date_time = generate_date_time()
            gonderen_iban = generate_iban(banka_kodu)
            alici_iban = generate_iban()
            
            # Period/Daire (contextual)
            ay = random.choice(AYLAR) if random.random() < 0.6 else None
            daire = random.choice(DAIRE_NUMS) if random.random() < 0.7 else None
            
            # ===== OCR DATA (Always clean) =====
            ocr_data = {
                "sender_name": f"{ad} {soyad}",
                "sender_iban": gonderen_iban,
                "receiver_name": alici_firma,
                "receiver_iban": alici_iban,
                "bank": banka_adi,
                "transaction_type": islem_tipi,
                "date": date_time["full"],
                "amount": f"{tutar_raw}.00 TL",  # ✅ OCR'da her zaman var
                "fee": f"{ucret} TL",
            }
            
            # ===== USER DESCRIPTION (Noisy, incomplete) =====
            intent_word = intent.split('_')[0]  # kira, aidat, kapora, depozito
            
            # Base description
            description_parts = []
            
            # Period (opsiyonel, noisy)
            if ay:
                period_text = f"{ay} dönemi" if random.random() < 0.3 else f"{ay} ayı" if random.random() < 0.5 else ay
                description_parts.append(period_text)
            
            # Intent (synonym replacement)
            intent_text = random.choice(INTENT_SYNONYMS[intent_word])
            description_parts.append(intent_text)
            
            # "ödeme" kelimesi (synonym)
            if random.random() < 0.7:
                odeme_text = random.choice(DESCRIPTIVE_SYNONYMS["ödeme"])
                if odeme_text:
                    description_parts.append(odeme_text)
            
            # Daire (opsiyonel)
            if daire:
                daire_text = f"Daire {daire}" if random.random() < 0.5 else f"daire:{daire}" if random.random() < 0.5 else f"d:{daire}"
                description_parts.append(daire_text)
            
            # ✅ AMOUNT - Kullanıcı bazen yazar (%50 şans)
            if random.random() < 0.5:
                amount_text = f"{tutar_raw} TL" if random.random() < 0.5 else f"{tutar_raw}TL" if random.random() < 0.5 else f"{tutar_raw}"
                description_parts.append(amount_text)
            
            user_description = ' '.join(description_parts)
            
            # Apply noise (%30 ambiguous)
            if random.random() < 0.3:
                # Ambiguous pattern
                other_intent = random.choice([i for i in intents if i != intent])
                other_word = other_intent.split('_')[0]
                user_description = generate_ambiguous_description(intent_word, other_word)
            else:
                # Normal noise
                user_description = apply_synonym_replacement(user_description, intent)
                user_description = add_typo(user_description)
                user_description = add_ocr_error(user_description)
                user_description = add_spacing_error(user_description)
                user_description = add_random_noise(user_description)
            
            # ===== COMBINED TEXT =====
            # OCR data (clean) + User description (noisy)
            combined_text = (
                f"Gönderen: {ocr_data['sender_name']} "
                f"IBAN: {gonderen_iban} "
                f"Alan: {alici_firma} "
                f"IBAN: {alici_iban} "
                f"Banka: {banka_adi} "
                f"İşlem: {islem_tipi} "
                f"Tutar: {tutar_raw}.00 TL "  # ✅ OCR'dan AMOUNT her zaman var!
                f"Komisyon: {ucret} TL "
                f"Tarih: {date_time['full']} "
                f"Açıklama: {user_description}"
            )
            
            # ===== GROUND TRUTH ENTITIES =====
            entities = {
                "SENDER": [f"{ad} {soyad}"],
                "RECEIVER": [alici_firma],
                "AMOUNT": [f"{tutar_raw}.00 TL"],  # ✅ Ground truth (OCR'dan)
                "DATE": [date_time["date_only"]],
                "SENDER_IBAN": [gonderen_iban],
                "RECEIVER_IBAN": [alici_iban],
                "BANK": [banka_adi],
                "TRANSACTION_TYPE": [islem_tipi],
                "FEE": [f"{ucret} TL"],
            }
            
            if ay:
                entities["PERIOD"] = [ay]
            if daire:
                entities["APT_NO"] = [daire]
            
            dataset.append({
                "text": combined_text,
                "entities": entities,
                "intent": intent,
                "ocr_data": ocr_data,
                "user_description": user_description,
            })
    
    print(f"\n✅ Generated {len(dataset)} samples")
    return dataset


def generate_robust_intent_dataset(num_samples=800):
    """
    Robust Intent dataset - v3
    Focus on user_description (noisy, ambiguous)
    """
    dataset = []
    
    intents = ["kira_odemesi", "aidat_odemesi", "kapora_odemesi", "depozito_odemesi"]
    samples_per_intent = num_samples // len(intents)
    
    print("🎯 Robust Intent Dataset Generation (v3)")
    print(f"📊 Target samples: {num_samples}")
    print(f"🔧 Features: Noise, Synonyms, Ambiguous Data")
    print()
    
    for intent in intents:
        print(f"🔄 Generating {intent}...")
        
        for i in range(samples_per_intent):
            intent_word = intent.split('_')[0]
            
            # Base templates
            ay = random.choice(AYLAR) if random.random() < 0.5 else None
            daire = random.choice(DAIRE_NUMS) if random.random() < 0.4 else None
            
            templates = [
                f"{ay + ' ' if ay else ''}{random.choice(INTENT_SYNONYMS[intent_word])} {random.choice(DESCRIPTIVE_SYNONYMS['ödeme'])}",
                f"{random.choice(INTENT_SYNONYMS[intent_word])} - {ay if ay else ''}",
                f"{random.choice(INTENT_SYNONYMS[intent_word])} {daire + ' nolu daire' if daire else ''}",
                f"{ay + ' ayı ' if ay else ''}{random.choice(INTENT_SYNONYMS[intent_word])}",
            ]
            
            text = random.choice(templates).strip()
            
            # Apply noise (%40 ambiguous)
            if random.random() < 0.4:
                other_intent = random.choice([i for i in intents if i != intent])
                other_word = other_intent.split('_')[0]
                text = generate_ambiguous_description(intent_word, other_word)
            else:
                text = add_typo(text)
                text = add_ocr_error(text)
                text = add_spacing_error(text)
                text = add_random_noise(text)
            
            dataset.append({
                "text": text,
                "label": intent
            })
    
    print(f"\n✅ Generated {len(dataset)} samples")
    return dataset


def main():
    """Generate robust datasets"""
    output_dir = Path("data/v3_robust")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("🚀 ROBUST SYNTHETIC DATA GENERATION - v3")
    print("="*80)
    print()
    print("✅ FEATURES:")
    print("  1. AMOUNT bug FİXED - combined_text'e eklendi")
    print("  2. Noise Injection - random kelime, silme, yer değiştirme")
    print("  3. Synonym Replacement - kira→aylık ödeme, kapora→teminat")
    print("  4. OCR Error Simulation - k1ra, kir a, spacing")
    print("  5. Ambiguous Data - 'Aralık aidatı kira ödemesi'")
    print()
    print("="*80)
    print()
    
    # Generate NER dataset
    print("📋 GENERATING NER DATASET...")
    print("-"*80)
    ner_data = generate_robust_ner_dataset(num_samples=2500)
    
    ner_output = output_dir / "ner_robust.json"
    with open(ner_output, 'w', encoding='utf-8') as f:
        json.dump(ner_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 NER dataset saved: {ner_output}")
    print()
    
    # Generate Intent dataset
    print("📋 GENERATING INTENT DATASET...")
    print("-"*80)
    intent_data = generate_robust_intent_dataset(num_samples=800)
    
    intent_output = output_dir / "intent_robust.json"
    with open(intent_output, 'w', encoding='utf-8') as f:
        json.dump(intent_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Intent dataset saved: {intent_output}")
    print()
    
    # Statistics
    print("="*80)
    print("📊 DATASET STATISTICS")
    print("="*80)
    print(f"\n✅ NER Dataset: {len(ner_data)} samples")
    print(f"✅ Intent Dataset: {len(intent_data)} samples")
    print(f"✅ Total: {len(ner_data) + len(intent_data)} samples")
    print()
    
    # Entity distribution
    print("📈 Entity Distribution (NER):")
    entity_counts = {}
    for sample in ner_data:
        for entity_type in sample["entities"].keys():
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    for entity, count in sorted(entity_counts.items()):
        percentage = (count / len(ner_data)) * 100
        print(f"  {entity:18s} {count:4d} ({percentage:5.1f}%)")
    
    print()
    print("="*80)
    print("✨ DATASET GENERATION COMPLETE!")
    print("="*80)
    print()
    print("🎯 Next steps:")
    print("  1. Train v3 models: python src/nlp/v3/train_intent_classifier.py")
    print("  2. Train v3 NER: python src/nlp/v3/train_ner.py")
    print("  3. Compare with v2 results")
    print()


if __name__ == "__main__":
    main()
