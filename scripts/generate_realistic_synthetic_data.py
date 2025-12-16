"""
Realistic Synthetic Dataset Generator with Variations
Gerçek dünya senaryolarını yansıtan, kısaltmalar ve hatalar içeren dataset
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path

# Türkçe isimler (Tam hali)
FULL_NAMES = [
    ("Ahmet", "Yılmaz"), ("Mehmet", "Demir"), ("Ayşe", "Kaya"), ("Fatma", "Şahin"),
    ("Ali", "Çelik"), ("Zeynep", "Arslan"), ("Mustafa", "Koç"), ("Emine", "Yıldız"),
    ("Hüseyin", "Öztürk"), ("Hatice", "Aydın"), ("İbrahim", "Özdemir"), ("Elif", "Aksoy"),
    ("Ömer", "Yılmaz"), ("Zehra", "Polat"), ("Burak", "Şimşek"), ("Merve", "Çetin"),
    ("Emre", "Kara"), ("Selin", "Akar"), ("Can", "Erdoğan"), ("Defne", "Yavuz"),
    ("Oğuz", "Koçak"), ("Gizem", "Baltacı"), ("Cem", "Güneş"), ("Nazlı", "Özkan"),
    ("Kerem", "Yıldırım"), ("Ebru", "Tekin"), ("Onur", "Kaplan"), ("Deniz", "Aslan")
]

# Mahalle isimleri
MAHALLELER = [
    "Fethiye", "Çiçek", "Bahçelievler", "Yıldıztepe", "Atatürk", 
    "Cumhuriyet", "Güzelyalı", "Yeşiltepe", "Merkez", "Kültür",
    "Sakarya", "Bağlar", "Çamlık", "Gültepe", "Yenimahalle"
]

# Apartman isimleri
APARTMANLAR = [
    "Çiçek", "Gül", "Lale", "Papatya", "Zambak", "Orkide",
    "Mimoza", "Menekşe", "Yasemin", "Nergis", "Kardelen",
    "Modern", "Lüks", "Panorama", "Vista", "Park", "Green"
]

# Daire numaraları (çeşitli formatlar)
DAIRE_NUMS = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "12", "15", "18", "22", "24", "31", "35", "42",
    "A1", "A2", "A3", "B1", "B2", "C1", "D2"
]

# Aylar
AYLAR = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]

# Tutarlar
TUTARLAR = list(range(5000, 35000, 1000))


def apply_name_abbreviation(ad, soyad):
    """İsim kısaltmaları uygula (gerçekçi varyasyonlar)"""
    variations = [
        # Tam hali
        f"{ad} {soyad}",
        # Ad kısaltma
        f"{ad[0]}. {soyad}",
        f"{ad[0]}.{soyad}",
        f"{ad[:3]}. {soyad}",
        # Soyad kısaltma
        f"{ad} {soyad[0]}.",
        # Her ikisi kısaltma
        f"{ad[0]}. {soyad[0]}.",
        f"{ad[0]}.{soyad[0]}.",
        # Sadece soyad
        soyad,
        # Titiz versiyonlar
        f"{ad.upper()} {soyad.upper()}",
        f"{ad.lower()} {soyad.lower()}",
    ]
    return random.choice(variations)


def apply_location_abbreviation(mahalle, apartman):
    """Mahalle/apartman kısaltmaları"""
    mah_variations = [
        f"{mahalle} Mahallesi",
        f"{mahalle} Mah.",
        f"{mahalle} mah.",
        f"{mahalle}",
        f"{mahalle[:4]}. Mah.",  # İlk 4 harf
    ]
    
    apt_variations = [
        f"{apartman} Apartmanı",
        f"{apartman} Apt.",
        f"{apartman} apt.",
        f"{apartman}",
        f"{apartman} Ap.",
    ]
    
    return random.choice(mah_variations), random.choice(apt_variations)


def apply_apartment_number_variation(daire):
    """Daire numarası varyasyonları"""
    variations = [
        f"Daire: {daire}",
        f"daire: {daire}",
        f"Daire {daire}",
        f"daire {daire}",
        f"D:{daire}",
        f"d:{daire}",
        f"No: {daire}",
        f"no: {daire}",
        f"{daire}",
        f"Kat {daire}",
    ]
    return random.choice(variations)


def apply_amount_variation(tutar):
    """Tutar formatı varyasyonları"""
    variations = [
        f"{tutar} TL",
        f"{tutar} tl",
        f"{tutar} Tl",
        f"{tutar}TL",
        f"{tutar:,} TL".replace(",", "."),  # 15.000 TL
        f"{tutar:,} TL".replace(",", ","),  # 15,000 TL
        f"{tutar} ₺",
        f"{tutar}₺",
    ]
    return random.choice(variations)


def apply_month_variation(ay):
    """Ay varyasyonları"""
    variations = [
        ay,
        ay.lower(),
        ay.upper(),
        ay[:3],  # İlk 3 harf (Oca, Şub, vb.)
        ay[:4],  # İlk 4 harf
    ]
    return random.choice(variations)


def generate_iban():
    """Rastgele Türk IBAN üret"""
    return f"TR{random.randint(10, 99)}{random.randint(1000, 9999)}{random.randint(1000000000000000, 9999999999999999)}"


def generate_date(format_variation=True):
    """Rastgele tarih üret (çeşitli formatlar)"""
    base = datetime.now()
    random_days = random.randint(0, 180)
    date = base - timedelta(days=random_days)
    
    if not format_variation:
        return date.strftime("%d.%m.%Y")
    
    # Farklı tarih formatları
    formats = [
        "%d.%m.%Y",  # 20.11.2025
        "%d/%m/%Y",  # 20/11/2025
        "%d-%m-%Y",  # 20-11-2025
        "%d.%m.%y",  # 20.11.25
    ]
    return date.strftime(random.choice(formats))


def add_typos(text, probability=0.1):
    """Küçük typo'lar ekle (gerçekçi hatalar)"""
    if random.random() > probability:
        return text
    
    # Yaygın typo'lar
    typos = {
        "Çiçek": "Çicek",
        "ğ": "g",
        "ş": "s",
        "ı": "i",
        "ö": "o",
        "ü": "u",
        "ç": "c",
    }
    
    for original, replacement in typos.items():
        if original in text and random.random() < 0.3:
            text = text.replace(original, replacement, 1)  # Sadece birini değiştir
    
    return text


def generate_realistic_ner_samples(num_samples=1000):
    """Gerçekçi NER dataset üret"""
    dataset = []
    
    templates = [
        # Template 1: Tam bilgili
        "{isim}, {ay} ayı kira ödemesi, {mahalle} {apartman}, {daire}, {tutar}",
        
        # Template 2: Kısa format
        "{isim}, {ay} kira, {mahalle} {apartman} {daire}, {tutar}",
        
        # Template 3: Çok kısa
        "{isim}, {ay}, {apartman} {daire}, {tutar}",
        
        # Template 4: Detaylı
        "Gönderen: {isim} | Açıklama: {ay} {yil} kira - {mahalle} {apartman} {daire} | Tutar: {tutar}",
        
        # Template 5: Basit
        "{isim} - {ay} kira - {daire} - {tutar}",
        
        # Template 6: IBAN dahil
        "{isim} tarafından {tutar} {tarih} tarihinde {iban} hesabına gönderildi. {ay} kira {daire}",
        
        # Template 7: Farklı sıra
        "{ay} {yil} - {mahalle} {apartman} {daire} - {isim} - {tutar}",
        
        # Template 8: Aidat formatı
        "{apartman} {daire} - {ay} aidat - {isim} - {tutar}",
        
        # Template 9: Kapora formatı
        "Kapora: {isim}, {apartman} {daire}, {tutar}, {tarih}",
        
        # Template 10: Depozito formatı
        "{isim} - Depozito {daire} - {tutar} - {tarih}",
    ]
    
    for _ in range(num_samples):
        # Rastgele veri seç
        ad, soyad = random.choice(FULL_NAMES)
        mahalle = random.choice(MAHALLELER)
        apartman = random.choice(APARTMANLAR)
        daire_num = random.choice(DAIRE_NUMS)
        ay = random.choice(AYLAR)
        yil = random.choice([2023, 2024, 2025])
        tutar_raw = random.choice(TUTARLAR)
        tarih = generate_date()
        iban = generate_iban()
        
        # Varyasyonlar uygula
        isim_var = apply_name_abbreviation(ad, soyad)
        mah_var, apt_var = apply_location_abbreviation(mahalle, apartman)
        daire_var = apply_apartment_number_variation(daire_num)
        tutar_var = apply_amount_variation(tutar_raw)
        ay_var = apply_month_variation(ay)
        
        # Template seç ve doldur
        template = random.choice(templates)
        text = template.format(
            isim=isim_var,
            mahalle=mah_var,
            apartman=apt_var,
            daire=daire_var,
            ay=ay_var,
            yil=yil,
            tutar=tutar_var,
            tarih=tarih,
            iban=iban
        )
        
        # Typo ekle (%10 olasılık)
        text = add_typos(text)
        
        # Entity'leri kaydet (tam halleri)
        entities = {
            "PER": [f"{ad} {soyad}"],
            "AMOUNT": [f"{tutar_raw} TL"],
            "DATE": [tarih],
            "IBAN": [iban] if "{iban}" in template else [],
            "PERIOD": [f"{ay} {yil}"],
            "APT_NO": [daire_num]
        }
        
        dataset.append({
            "text": text,
            "entities": entities
        })
    
    return dataset


def generate_realistic_intent_samples(samples_per_class=100):
    """Gerçekçi Intent classification dataset üret"""
    dataset = []
    idx = 0
    
    intent_templates = {
        "kira_odemesi": [
            "{ay} kira",
            "{ay} kira {daire}",
            "{ay} {yil} kira",
            "kira {ay}",
            "{ay} ayı kira bedeli",
            "{daire} kira {ay}",
            "Kira - {ay}",
            "{ay}/{yil} kira",
        ],
        "aidat_odemesi": [
            "{ay} aidat",
            "aidat {ay}",
            "{ay} {yil} aidat",
            "Site aidatı {ay}",
            "{ay} apartman aidatı",
            "Aidat - {ay}",
            "{daire} aidat",
        ],
        "kapora_odemesi": [
            "kapora",
            "Kapora {daire}",
            "kapora ödemesi",
            "yeni kiracı kapora",
            "{daire} kapora",
            "Kapora bedeli",
        ],
        "depozito_odemesi": [
            "depozito",
            "Depozito {daire}",
            "güvence bedeli",
            "teminat",
            "{daire} depozito",
            "Depozito ödemesi",
        ]
    }
    
    for intent, templates in intent_templates.items():
        for _ in range(samples_per_class):
            template = random.choice(templates)
            
            # Varyasyonlar
            ay = apply_month_variation(random.choice(AYLAR))
            yil = random.choice([2023, 2024, 2025])
            daire = apply_apartment_number_variation(random.choice(DAIRE_NUMS))
            
            text = template.format(ay=ay, yil=yil, daire=daire)
            
            # Küçük/büyük harf varyasyonları
            if random.random() < 0.3:
                text = text.lower()
            elif random.random() < 0.1:
                text = text.upper()
            
            # Typo ekle
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
    """Dataset'i JSON olarak kaydet"""
    output_dir = Path("data/synthetic_realistic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {filename} kaydedildi: {len(data)} örnek")
    return filepath


def main():
    print("🚀 Realistic Synthetic Dataset Generation Başlıyor...\n")
    print("📌 Özellikler:")
    print("  - Kısaltmalar (A.Bay, Mah., Apt., d:2)")
    print("  - Farklı formatlar (15.000 TL, 15000TL)")
    print("  - Küçük/büyük harf karışımları")
    print("  - Typo'lar (%10 olasılık)")
    print("  - Eksik bilgiler\n")
    
    # Intent Classification Dataset
    print("📊 Realistic Intent Classification Dataset üretiliyor...")
    intent_data = generate_realistic_intent_samples(samples_per_class=100)
    intent_file = save_dataset(intent_data, "intent_realistic.json")
    
    # İstatistikler
    intent_counts = {}
    for item in intent_data:
        label = item['label']
        intent_counts[label] = intent_counts.get(label, 0) + 1
    
    print("\nIntent dağılımı:")
    for intent, count in intent_counts.items():
        print(f"  - {intent}: {count} örnek")
    
    # NER Dataset
    print("\n📊 Realistic NER Dataset üretiliyor...")
    ner_data = generate_realistic_ner_samples(num_samples=1000)
    ner_file = save_dataset(ner_data, "ner_realistic.json")
    
    print(f"\n✨ Toplam {len(intent_data)} intent + {len(ner_data)} NER örneği oluşturuldu!")
    print(f"📁 Dosyalar: data/synthetic_realistic/ klasöründe")
    
    # Örnekler göster
    print("\n" + "="*70)
    print("📝 Realistic Intent Örnekleri:")
    print("="*70)
    for i in range(10):
        print(f"  {i+1}. '{intent_data[i]['text']}' → {intent_data[i]['label']}")
    
    print("\n" + "="*70)
    print("📝 Realistic NER Örnekleri:")
    print("="*70)
    for i in range(5):
        print(f"\n  {i+1}. Text: {ner_data[i]['text']}")
        print(f"     Entities:")
        for entity_type, values in ner_data[i]['entities'].items():
            if values:
                print(f"       - {entity_type}: {values}")
    
    print("\n" + "="*70)
    print("✅ Dataset generation tamamlandı!")
    print("="*70)


if __name__ == "__main__":
    main()
