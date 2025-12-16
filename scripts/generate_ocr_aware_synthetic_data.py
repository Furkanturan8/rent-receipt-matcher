"""
OCR-Aware Realistic Synthetic Dataset Generator
Dekont OCR çıktısı + Kullanıcı açıklaması ayrımını yapan gerçekçi dataset
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path

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

# İşlem Durumu
ISLEM_DURUMLARI = ["Başarılı", "Gerçekleşti", "Tamamlandı"]

# Türkçe isimler
FULL_NAMES = [
    ("Ahmet", "Yılmaz"), ("Mehmet", "Demir"), ("Ayşe", "Kaya"), ("Fatma", "Şahin"),
    ("Ali", "Çelik"), ("Zeynep", "Arslan"), ("Mustafa", "Koç"), ("Emine", "Yıldız"),
    ("Hüseyin", "Öztürk"), ("Hatice", "Aydın"), ("İbrahim", "Özdemir"), ("Elif", "Aksoy"),
    ("Ömer", "Yılmaz"), ("Zehra", "Polat"), ("Burak", "Şimşek"), ("Merve", "Çetin"),
    ("Emre", "Kara"), ("Selin", "Akar"), ("Can", "Erdoğan"), ("Defne", "Yavuz"),
    ("Oğuz", "Koçak"), ("Gizem", "Baltacı"), ("Cem", "Güneş"), ("Nazlı", "Özkan"),
]

# Alıcı firmalar
ALICI_FIRMALAR = [
    "ABC Gayrimenkul A.Ş.",
    "XYZ Emlak Yönetim Ltd.",
    "Güven Emlak",
    "Metropol Gayrimenkul",
    "Prestij Emlak Danışmanlık",
]

# Mahalle/Apartman
MAHALLELER = [
    "Fethiye", "Çiçek", "Bahçelievler", "Yıldıztepe", "Atatürk", 
    "Cumhuriyet", "Güzelyalı", "Yeşiltepe"
]

APARTMANLAR = [
    "Çiçek", "Gül", "Lale", "Papatya", "Modern", "Lüks", "Panorama"
]

DAIRE_NUMS = ["1", "2", "3", "5", "8", "12", "15", "22", "A1", "A2", "B1"]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
TUTARLAR = list(range(5000, 35000, 1000))


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
    if random.random() < 0.8:  # %80 ücretsiz
        return "0.00"
    else:
        return str(random.choice([2.00, 2.50, 3.00, 3.50, 4.00, 5.00]))


def apply_name_abbreviation(ad, soyad):
    """İsim kısaltmaları (kullanıcı açıklaması için)"""
    variations = [
        f"{ad} {soyad}",
        f"{ad[0]}. {soyad}",
        f"{ad[0]}.{soyad}",
        f"{ad} {soyad[0]}.",
        soyad,
        f"{ad.lower()} {soyad.lower()}",
    ]
    return random.choice(variations)


def apply_location_abbreviation(mahalle, apartman):
    """Mahalle/apartman kısaltmaları"""
    mah_var = random.choice([
        f"{mahalle} Mahallesi",
        f"{mahalle} Mah.",
        f"{mahalle}",
        f"{mahalle[:4]}. Mah.",
    ])
    
    apt_var = random.choice([
        f"{apartman} Apartmanı",
        f"{apartman} Apt.",
        f"{apartman}",
    ])
    
    return mah_var, apt_var


def apply_daire_variation(daire):
    """Daire varyasyonları"""
    variations = [
        f"Daire: {daire}",
        f"daire: {daire}",
        f"D:{daire}",
        f"d:{daire}",
        f"No: {daire}",
        f"{daire}",
    ]
    return random.choice(variations)


def apply_month_variation(ay):
    """Ay varyasyonları"""
    variations = [ay, ay.lower(), ay[:3], ay[:4]]
    return random.choice(variations)


def add_typos(text, probability=0.1):
    """Typo ekle"""
    if random.random() > probability:
        return text
    
    typos = {"Çiçek": "Çicek", "ğ": "g", "ş": "s", "ı": "i"}
    for original, replacement in typos.items():
        if original in text and random.random() < 0.3:
            text = text.replace(original, replacement, 1)
    
    return text


def generate_ocr_aware_ner_dataset(num_samples=2000):
    """OCR + Kullanıcı açıklaması ayrımını yapan NER dataset"""
    dataset = []
    
    # Kullanıcı açıklama template'leri (sadece kullanıcının yazdığı kısım)
    user_description_templates = [
        "{isim}, {ay} kira, {daire}",
        "{isim}, {ay} kira, {mahalle} {apartman} {daire}",
        "{isim}, {ay} {yil} kira, {daire}",
        "{isim} - {ay} kira - {daire}",
        "{ay} kira {daire}",
        "{ay} {yil} kira - {mahalle} {apartman} {daire}",
        "Kira {ay} - {isim} - {daire}",
        "{daire} - {ay} kira - {isim}",
    ]
    
    for _ in range(num_samples):
        # === OCR ÇIKTISI (Dekonttan - HER ZAMAN TAM) ===
        ad, soyad = random.choice(FULL_NAMES)
        alici_firma = random.choice(ALICI_FIRMALAR)
        banka_adi, banka_kodu = random.choice(TURKIYE_BANKALARI)
        islem_tipi = random.choice(ISLEM_TIPLERI)
        islem_durumu = random.choice(ISLEM_DURUMLARI)
        tutar_raw = random.choice(TUTARLAR)
        ucret = generate_islem_ucreti()
        date_time = generate_date_time()
        gonderen_iban = generate_iban(banka_kodu)
        alici_iban = generate_iban()
        
        ocr_data = {
            "sender_name": f"{ad.upper()} {soyad.upper()}",  # Dekontlarda büyük harf
            "sender_iban": gonderen_iban,
            "receiver_name": alici_firma.upper(),
            "receiver_iban": alici_iban,
            "bank": banka_adi,
            "transaction_type": islem_tipi,
            "date": date_time["full"],
            "amount": f"{tutar_raw}.00 TL",
            "fee": f"{ucret} TL",
            "status": islem_durumu
        }
        
        # === KULLANICI AÇIKLAMASI (Kullanıcının yazdığı kısım) ===
        mahalle = random.choice(MAHALLELER)
        apartman = random.choice(APARTMANLAR)
        daire_num = random.choice(DAIRE_NUMS)
        ay = random.choice(AYLAR)
        yil = random.choice([2023, 2024, 2025])
        
        # Varyasyonlar uygula (kullanıcı kısaltır)
        isim_var = apply_name_abbreviation(ad, soyad)
        mah_var, apt_var = apply_location_abbreviation(mahalle, apartman)
        daire_var = apply_daire_variation(daire_num)
        ay_var = apply_month_variation(ay)
        
        # Kullanıcı açıklaması template'i seç
        template = random.choice(user_description_templates)
        user_description = template.format(
            isim=isim_var,
            mahalle=mah_var,
            apartman=apt_var,
            daire=daire_var,
            ay=ay_var,
            yil=yil
        )
        
        # Typo ekle
        user_description = add_typos(user_description)
        
        # === BİRLEŞİK METİN (NLP modeline giden input) ===
        # Format: OCR bilgileri + Kullanıcı açıklaması
        combined_text = (
            f"Dekont: {banka_adi} | {islem_tipi} | "
            f"Gönderen: {ocr_data['sender_name']} ({gonderen_iban}) | "
            f"Alıcı: {alici_firma.upper()} ({alici_iban}) | "
            f"Tutar: {tutar_raw}.00 TL | Ücret: {ucret} TL | "
            f"Tarih: {date_time['full']} | "
            f"Açıklama: {user_description}"
        )
        
        # === ENTITY'LER (Ground Truth) ===
        entities = {
            "SENDER": [f"{ad} {soyad}"],  # Tam isim (ground truth)
            "RECEIVER": [alici_firma],
            "AMOUNT": [f"{tutar_raw} TL"],
            "DATE": [date_time["date_only"]],
            "SENDER_IBAN": [gonderen_iban],  # OCR'dan gelir - HER ZAMAN VAR
            "RECEIVER_IBAN": [alici_iban],  # OCR'dan gelir - HER ZAMAN VAR
            "BANK": [banka_adi],  # OCR'dan gelir - HER ZAMAN VAR
            "TRANSACTION_TYPE": [islem_tipi],  # OCR'dan gelir - HER ZAMAN VAR
            "FEE": [f"{ucret} TL"],  # OCR'dan gelir - HER ZAMAN VAR
            "PERIOD": [f"{ay} {yil}"],  # Kullanıcı açıklamasından
            "APT_NO": [daire_num]  # Kullanıcı açıklamasından
        }
        
        dataset.append({
            "ocr_data": ocr_data,
            "user_description": user_description,
            "combined_text": combined_text,
            "entities": entities
        })
    
    return dataset


def generate_ocr_aware_intent_dataset(samples_per_class=150):
    """Intent classification dataset (kullanıcı açıklaması odaklı)"""
    dataset = []
    idx = 0
    
    # Kullanıcı sadece açıklama field'ına yazar
    intent_templates = {
        "kira_odemesi": [
            "{ay} kira",
            "{ay} kira {daire}",
            "{ay} {yil} kira",
            "Kira {ay}",
        ],
        "aidat_odemesi": [
            "{ay} aidat",
            "Aidat {ay}",
            "Site aidatı {ay}",
        ],
        "kapora_odemesi": [
            "kapora",
            "Kapora {daire}",
            "Ön ödeme",
        ],
        "depozito_odemesi": [
            "depozito",
            "Depozito {daire}",
            "Güvence bedeli",
        ]
    }
    
    for intent, templates in intent_templates.items():
        for _ in range(samples_per_class):
            template = random.choice(templates)
            
            ay = apply_month_variation(random.choice(AYLAR))
            yil = random.choice([2023, 2024, 2025])
            daire = apply_daire_variation(random.choice(DAIRE_NUMS))
            
            text = template.format(ay=ay, yil=yil, daire=daire)
            
            if random.random() < 0.3:
                text = text.lower()
            
            text = add_typos(text, probability=0.05)
            
            dataset.append({
                "id": idx,
                "text": text,
                "label": intent
            })
            idx += 1
    
    random.shuffle(dataset)
    return dataset


def save_dataset(data, filename):
    """Dataset kaydet"""
    output_dir = Path("data/synthetic_ocr_aware")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {filename} kaydedildi: {len(data)} örnek")
    return filepath


def main():
    print("🎯 OCR-Aware Synthetic Dataset Generation\n")
    print("📌 Yeni Yapı:")
    print("  - OCR Çıktısı (Dekonttan - TAM bilgi)")
    print("  - Kullanıcı Açıklaması (Description field - KISMİ bilgi)")
    print("  - Birleşik Metin (NLP modeline input)")
    print("  - Entity'ler (Ground truth)\n")
    
    # Intent Dataset
    print("📊 Intent Classification Dataset...")
    intent_data = generate_ocr_aware_intent_dataset(samples_per_class=150)
    save_dataset(intent_data, "intent_ocr_aware.json")
    
    # NER Dataset
    print("\n📊 NER Dataset (OCR + User Description)...")
    ner_data = generate_ocr_aware_ner_dataset(num_samples=2000)
    save_dataset(ner_data, "ner_ocr_aware.json")
    
    print(f"\n✨ Toplam: {len(intent_data)} intent + {len(ner_data)} NER")
    print(f"📁 Klasör: data/synthetic_ocr_aware/")
    
    # Örnekler göster
    print("\n" + "="*80)
    print("📝 NER ÖRNEK YAPISI:")
    print("="*80)
    sample = ner_data[0]
    
    print("\n1️⃣ OCR Çıktısı (Dekonttan):")
    for key, value in sample['ocr_data'].items():
        print(f"   {key}: {value}")
    
    print(f"\n2️⃣ Kullanıcı Açıklaması:")
    print(f"   {sample['user_description']}")
    
    print(f"\n3️⃣ Birleşik Metin (Model input):")
    print(f"   {sample['combined_text'][:150]}...")
    
    print(f"\n4️⃣ Entity'ler (Ground truth):")
    for entity_type, values in sample['entities'].items():
        print(f"   {entity_type}: {values}")
    
    # Entity istatistikleri
    print("\n" + "="*80)
    print("📊 ENTITY İSTATİSTİKLERİ:")
    print("="*80)
    entity_counts = {}
    for sample in ner_data:
        for entity_type, values in sample['entities'].items():
            if values and values[0]:  # Boş değilse
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    for entity, count in sorted(entity_counts.items()):
        percentage = (count / len(ner_data)) * 100
        source = "OCR (Dekont)" if entity in ["SENDER_IBAN", "RECEIVER_IBAN", "BANK", "TRANSACTION_TYPE", "FEE"] else "User Desc"
        print(f"   {entity:<20} {count:>4}/{len(ner_data)} ({percentage:>5.1f}%) - {source}")
    
    print("\n" + "="*80)
    print("✅ OCR-Aware Dataset Tamamlandı!")
    print("="*80)


if __name__ == "__main__":
    main()
