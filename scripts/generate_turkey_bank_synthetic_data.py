"""
Turkey Bank-Specific Realistic Synthetic Dataset Generator
Türkiye bankalarına özel, detaylı dekont bilgileri içeren dataset
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
ISLEM_TIPLERI = [
    "EFT", "Havale", "Fast", "FAST", "Havale/EFT", "Para Transferi"
]

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

# Alıcı firma/kişiler (Emlak şirketleri)
ALICILAR = [
    "ABC Gayrimenkul A.Ş.",
    "XYZ Emlak Yönetim Ltd.",
    "Güven Emlak",
    "Metropol Gayrimenkul",
    "Prestij Emlak Danışmanlık",
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

# Daire numaraları
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


def generate_iban(banka_kodu=None):
    """Türk IBAN üret (gerçek banka kodları ile)"""
    if banka_kodu is None:
        banka_kodu = random.choice(TURKIYE_BANKALARI)[1]
    
    # TR + 2 digit check + 5 digit (0+banka_kodu) + 1 digit + 16 digit account
    reserved = "0"
    account_no = str(random.randint(1000000000000000, 9999999999999999))
    check_digits = random.randint(10, 99)
    
    return f"TR{check_digits}{reserved}{banka_kodu}{account_no}"


def generate_date_time():
    """Rastgele tarih ve saat üret"""
    base = datetime.now()
    random_days = random.randint(0, 180)
    date = base - timedelta(days=random_days)
    
    # Farklı format varyasyonları
    date_formats = [
        date.strftime("%d.%m.%Y"),
        date.strftime("%d/%m/%Y"),
        date.strftime("%d-%m-%Y"),
        date.strftime("%d.%m.%Y %H:%M"),
        date.strftime("%d.%m.%Y %H:%M:%S"),
    ]
    
    return random.choice(date_formats)


def apply_name_abbreviation(ad, soyad):
    """İsim kısaltmaları"""
    variations = [
        f"{ad} {soyad}",
        f"{ad[0]}. {soyad}",
        f"{ad[0]}.{soyad}",
        f"{ad[:3]}. {soyad}",
        f"{ad} {soyad[0]}.",
        f"{ad[0]}. {soyad[0]}.",
        soyad,
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
        f"{mahalle[:4]}. Mah.",
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
        f"{tutar:,} TL".replace(",", "."),
        f"{tutar:,} TL".replace(",", ","),
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
        ay[:3],
        ay[:4],
    ]
    return random.choice(variations)


def generate_islem_ucreti(tutar):
    """İşlem ücreti hesapla (gerçekçi)"""
    if random.random() < 0.7:  # %70 ücretsiz
        return 0
    else:
        # Genelde 2-5 TL arası
        return random.choice([2, 2.5, 3, 3.5, 4, 5])


def add_typos(text, probability=0.1):
    """Küçük typo'lar ekle"""
    if random.random() > probability:
        return text
    
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
            text = text.replace(original, replacement, 1)
    
    return text


def generate_extended_ner_samples(num_samples=1500):
    """Genişletilmiş NER dataset (banka bilgileri dahil)"""
    dataset = []
    
    # Template'ler (daha detaylı)
    templates = [
        # Template 1: Basit kullanıcı açıklaması
        "{isim}, {ay} kira, {mahalle} {apartman} {daire}, {tutar}",
        
        # Template 2: Detaylı açıklama
        "Gönderen: {isim} | {ay} {yil} kira - {mahalle} {apartman} {daire} | {tutar}",
        
        # Template 3: IBAN ile
        "{gonderen_iban} hesabından {alici_iban} hesabına {tutar} gönderildi. Açıklama: {isim}, {ay} kira, {daire}",
        
        # Template 4: İşlem tipi ile
        "{islem_tipi}: {gonderen_isim} → {alici_isim} | {tutar} | {tarih} | {ay} kira {daire}",
        
        # Template 5: Banka bilgisi ile
        "{banka} - {islem_tipi} | Gönderen: {gonderen_isim} ({gonderen_iban}) | Alıcı: {alici_isim} | Tutar: {tutar} | Açıklama: {ay} {yil} kira - {daire}",
        
        # Template 6: Çok kısa
        "{isim}, {ay}, {daire}, {tutar}",
        
        # Template 7: İşlem ücreti ile
        "Transfer: {tutar} (Ücret: {ucret} TL) | {gonderen_isim} → {alici_isim} | {ay} kira {daire} | {tarih}",
        
        # Template 8: Tarih ve saat ile
        "{tarih} - {gonderen_isim} - {tutar} - {ay} {yil} kira - {mahalle} {apartman} {daire}",
    ]
    
    for _ in range(num_samples):
        # Rastgele veriler
        ad, soyad = random.choice(FULL_NAMES)
        alici_firma = random.choice(ALICILAR)
        banka_adi, banka_kodu = random.choice(TURKIYE_BANKALARI)
        islem_tipi = random.choice(ISLEM_TIPLERI)
        mahalle = random.choice(MAHALLELER)
        apartman = random.choice(APARTMANLAR)
        daire_num = random.choice(DAIRE_NUMS)
        ay = random.choice(AYLAR)
        yil = random.choice([2023, 2024, 2025])
        tutar_raw = random.choice(TUTARLAR)
        ucret = generate_islem_ucreti(tutar_raw)
        tarih = generate_date_time()
        gonderen_iban = generate_iban(banka_kodu)
        alici_iban = generate_iban()
        
        # Varyasyonlar uygula
        gonderen_isim_var = apply_name_abbreviation(ad, soyad)
        alici_isim_var = alici_firma if random.random() < 0.8 else apply_name_abbreviation(*random.choice(FULL_NAMES))
        mah_var, apt_var = apply_location_abbreviation(mahalle, apartman)
        daire_var = apply_apartment_number_variation(daire_num)
        tutar_var = apply_amount_variation(tutar_raw)
        ay_var = apply_month_variation(ay)
        
        # Template seç
        template = random.choice(templates)
        
        text = template.format(
            isim=gonderen_isim_var,
            gonderen_isim=gonderen_isim_var,
            alici_isim=alici_isim_var,
            mahalle=mah_var,
            apartman=apt_var,
            daire=daire_var,
            ay=ay_var,
            yil=yil,
            tutar=tutar_var,
            ucret=ucret,
            tarih=tarih,
            gonderen_iban=gonderen_iban,
            alici_iban=alici_iban,
            banka=banka_adi,
            islem_tipi=islem_tipi
        )
        
        # Typo ekle
        text = add_typos(text)
        
        # Entity'leri kaydet
        entities = {
            "SENDER": [f"{ad} {soyad}"],  # Gönderen (tam isim)
            "RECEIVER": [alici_firma if alici_isim_var == alici_firma else alici_isim_var],  # Alıcı
            "AMOUNT": [f"{tutar_raw} TL"],
            "FEE": [f"{ucret} TL"] if ucret > 0 and "{ucret}" in template else [],
            "DATE": [tarih],
            "SENDER_IBAN": [gonderen_iban] if "{gonderen_iban}" in template else [],
            "RECEIVER_IBAN": [alici_iban] if "{alici_iban}" in template else [],
            "BANK": [banka_adi] if "{banka}" in template else [],
            "TRANSACTION_TYPE": [islem_tipi] if "{islem_tipi}" in template else [],
            "PERIOD": [f"{ay} {yil}"],
            "APT_NO": [daire_num]
        }
        
        dataset.append({
            "text": text,
            "entities": entities
        })
    
    return dataset


def generate_extended_intent_samples(samples_per_class=125):
    """Genişletilmiş Intent dataset"""
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
            "{islem_tipi} kira {ay}",
            "Kira ödemesi {ay} {yil}",
        ],
        "aidat_odemesi": [
            "{ay} aidat",
            "aidat {ay}",
            "{ay} {yil} aidat",
            "Site aidatı {ay}",
            "{ay} apartman aidatı",
            "Aidat - {ay}",
            "{daire} aidat",
            "Apartman gideri {ay}",
        ],
        "kapora_odemesi": [
            "kapora",
            "Kapora {daire}",
            "kapora ödemesi",
            "yeni kiracı kapora",
            "{daire} kapora",
            "Kapora bedeli",
            "Ön ödeme",
        ],
        "depozito_odemesi": [
            "depozito",
            "Depozito {daire}",
            "güvence bedeli",
            "teminat",
            "{daire} depozito",
            "Depozito ödemesi",
            "Güvence",
        ]
    }
    
    for intent, templates in intent_templates.items():
        for _ in range(samples_per_class):
            template = random.choice(templates)
            
            ay = apply_month_variation(random.choice(AYLAR))
            yil = random.choice([2023, 2024, 2025])
            daire = apply_apartment_number_variation(random.choice(DAIRE_NUMS))
            islem_tipi = random.choice(ISLEM_TIPLERI)
            
            text = template.format(ay=ay, yil=yil, daire=daire, islem_tipi=islem_tipi)
            
            # Küçük/büyük harf
            if random.random() < 0.3:
                text = text.lower()
            elif random.random() < 0.1:
                text = text.upper()
            
            # Typo
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
    """Dataset'i kaydet"""
    output_dir = Path("data/synthetic_turkey_banks")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {filename} kaydedildi: {len(data)} örnek")
    return filepath


def main():
    print("🇹🇷 Türkiye Bankaları Özel Synthetic Dataset Generation Başlıyor...\n")
    print("📌 Yeni Özellikler:")
    print("  - Türkiye'nin 12 büyük bankası")
    print("  - Gerçek banka kodları ile IBAN")
    print("  - İşlem tipleri (EFT, Havale, FAST)")
    print("  - Gönderen ve Alıcı bilgileri")
    print("  - İşlem ücretleri")
    print("  - Tarih + Saat bilgisi")
    print("  - 10+ entity tipi\n")
    
    # Intent Dataset
    print("📊 Extended Intent Classification Dataset üretiliyor...")
    intent_data = generate_extended_intent_samples(samples_per_class=125)
    save_dataset(intent_data, "intent_extended.json")
    
    intent_counts = {}
    for item in intent_data:
        label = item['label']
        intent_counts[label] = intent_counts.get(label, 0) + 1
    
    print("\nIntent dağılımı:")
    for intent, count in intent_counts.items():
        print(f"  - {intent}: {count} örnek")
    
    # NER Dataset
    print("\n📊 Extended NER Dataset üretiliyor...")
    ner_data = generate_extended_ner_samples(num_samples=1500)
    save_dataset(ner_data, "ner_extended.json")
    
    print(f"\n✨ Toplam {len(intent_data)} intent + {len(ner_data)} NER örneği!")
    print(f"📁 Dosyalar: data/synthetic_turkey_banks/ klasöründe")
    
    # Örnekler
    print("\n" + "="*80)
    print("📝 Extended Intent Örnekleri:")
    print("="*80)
    for i in range(8):
        print(f"  {i+1}. '{intent_data[i]['text']}' → {intent_data[i]['label']}")
    
    print("\n" + "="*80)
    print("📝 Extended NER Örnekleri (Banka Bilgileri ile):")
    print("="*80)
    for i in range(5):
        print(f"\n  {i+1}. Text: {ner_data[i]['text'][:120]}...")
        print(f"     Entities:")
        for entity_type, values in ner_data[i]['entities'].items():
            if values:
                print(f"       - {entity_type}: {values}")
    
    print("\n" + "="*80)
    print("✅ Türkiye Bankaları Dataset Tamamlandı!")
    print("="*80)
    
    # Entity istatistikleri
    print("\n📊 Entity İstatistikleri:")
    entity_counts = {}
    for sample in ner_data:
        for entity_type, values in sample['entities'].items():
            if values:
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    for entity, count in sorted(entity_counts.items()):
        percentage = (count / len(ner_data)) * 100
        print(f"  - {entity}: {count}/{len(ner_data)} ({percentage:.1f}%)")


if __name__ == "__main__":
    main()
