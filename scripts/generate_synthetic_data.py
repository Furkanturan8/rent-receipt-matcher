"""
Synthetic Dataset Generator for Intent Classification and NER
Emlak Ödeme Sistemi için template-based veri üretimi
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path

# Türkçe isim listesi
ISIMLER = [
    "Ahmet Yılmaz", "Mehmet Demir", "Ayşe Kaya", "Fatma Şahin",
    "Ali Çelik", "Zeynep Arslan", "Mustafa Koç", "Emine Yıldız",
    "Hüseyin Öztürk", "Hatice Aydın", "İbrahim Özdemir", "Elif Aksoy",
    "Ömer Yılmaz", "Zehra Polat", "Burak Şimşek", "Merve Çetin",
    "Emre Kara", "Selin Akar", "Can Erdoğan", "Defne Yavuz"
]

# Daire numaraları
DAIRELER = [
    "A1", "A2", "A3", "A4", "A5",
    "B1", "B2", "B3", "B4", "B5",
    "C1", "C2", "C3", "D1", "D2",
    "1", "2", "3", "12", "24", "35"
]

# Aylar
AYLAR = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]

# Tutarlar (TL)
TUTARLAR = [
    8000, 9000, 10000, 11000, 12000, 13000, 14000, 15000,
    16000, 17000, 18000, 20000, 22000, 25000, 30000
]

# Intent kategorileri ve template'ler
INTENT_TEMPLATES = {
    "kira_odemesi": [
        "{ay} ayı kira bedeli - {daire}",
        "{ay}/{yil} dönemi kira ödemesi - Daire: {daire}",
        "Kira - {ay} {yil} - {daire} nolu daire",
        "{daire} dairesi {ay} {yil} kira ödemesi",
        "{ay} ayı kira bedeli {daire}",
        "Daire {daire} - {ay} kira ödemesi",
        "{ay}/{yil} kira - {daire}",
        "{daire} numaralı daire {ay} ayı kirası",
        "Kira bedeli {ay} {yil} dönem {daire}",
        "{ay} {yil} kira ödemesi daire {daire}",
    ],
    "aidat_odemesi": [
        "Site aidatı - {ay} {yil}",
        "{ay} ayı apartman aidatı",
        "Aidat ödemesi {daire}",
        "{ay}/{yil} aidat - {daire}",
        "Apartman aidatı {ay} {yil}",
        "{daire} dairesi aidat ödemesi {ay}",
        "Site yönetim aidatı {ay} {yil}",
        "{ay} ayı aidat bedeli",
        "Aidat - {ay} {yil} - {daire}",
        "{daire} aidat {ay}/{yil}",
    ],
    "kapora_odemesi": [
        "Yeni kiralama kapora bedeli",
        "Daire {daire} kapora ödemesi",
        "Kapora - {daire}",
        "{daire} numaralı daire kapora bedeli",
        "Kapora ödemesi {daire}",
        "Yeni kiracı kapora {daire}",
        "{daire} dairesi için kapora",
        "Kapora bedeli daire {daire}",
        "Ön ödeme kapora {daire}",
        "{daire} kapora {ay} {yil}",
    ],
    "depozito_odemesi": [
        "Güvence bedeli - {daire}",
        "Depozito ödemesi",
        "Teminat bedeli {ay} {yil}",
        "{daire} dairesi depozito",
        "Güvence bedeli {daire}",
        "Depozito - {daire}",
        "{daire} teminat ödemesi",
        "Güvence depozito {daire}",
        "Depozito bedeli daire {daire}",
        "{daire} depozito {ay} {yil}",
    ]
}

# NER template'leri
NER_TEMPLATES = [
    "{isim} tarafından {tutar} TL {tarih} tarihinde {iban} hesabına gönderilmiştir.",
    "{tarih} - {isim} - {tutar} TL - {donem} dönemi - IBAN: {iban}",
    "{donem} kira bedeli {tutar} TL olarak {isim} tarafından ödenmiştir.",
    "{isim} adlı kiracı {tutar} TL tutarında ödeme yapmıştır. Tarih: {tarih}",
    "Ödeme: {tutar} TL, Gönderen: {isim}, Hesap: {iban}, Tarih: {tarih}",
    "{donem} için {isim} tarafından {tutar} TL ödeme yapılmıştır.",
    "IBAN: {iban} hesabından {isim} tarafından {tarih} tarihinde {tutar} TL gönderilmiştir.",
    "{isim} - {tutar} TL - {donem} - Daire: {daire}",
    "Gönderen: {isim}, Tutar: {tutar} TL, Dönem: {donem}, IBAN: {iban}",
    "{tarih} tarihli {tutar} TL tutarındaki ödeme {isim} tarafından yapılmıştır.",
]


def generate_iban():
    """Rastgele Türk IBAN üret"""
    return f"TR{random.randint(10, 99)}{random.randint(1000, 9999)}{random.randint(1000000000000000, 9999999999999999)}"


def generate_date():
    """Rastgele tarih üret (son 6 ay)"""
    base = datetime.now()
    random_days = random.randint(0, 180)
    date = base - timedelta(days=random_days)
    return date.strftime("%d.%m.%Y")


def generate_intent_dataset(samples_per_class=75):
    """Intent classification dataset üret"""
    dataset = []
    idx = 0
    
    for intent, templates in INTENT_TEMPLATES.items():
        for _ in range(samples_per_class):
            template = random.choice(templates)
            
            text = template.format(
                ay=random.choice(AYLAR),
                yil=random.choice([2023, 2024]),
                daire=random.choice(DAIRELER)
            )
            
            dataset.append({
                "id": idx,
                "text": text,
                "label": intent
            })
            idx += 1
    
    random.shuffle(dataset)
    return dataset


def generate_ner_dataset(num_samples=500):
    """NER dataset üret (BIO formatında)"""
    dataset = []
    
    for _ in range(num_samples):
        template = random.choice(NER_TEMPLATES)
        
        isim = random.choice(ISIMLER)
        tutar = random.choice(TUTARLAR)
        tarih = generate_date()
        iban = generate_iban()
        donem = f"{random.choice(AYLAR)} {random.choice([2023, 2024])}"
        daire = random.choice(DAIRELER)
        
        text = template.format(
            isim=isim,
            tutar=tutar,
            tarih=tarih,
            iban=iban,
            donem=donem,
            daire=daire
        )
        
        # BIO etiketleme (basitleştirilmiş)
        # Gerçek projedе bu kısmı Label Studio ile manuel yapacaksın
        tokens = text.split()
        
        dataset.append({
            "text": text,
            "entities": {
                "PER": [isim],
                "AMOUNT": [f"{tutar} TL"],
                "DATE": [tarih],
                "IBAN": [iban],
                "PERIOD": [donem],
                "APT_NO": [daire]
            }
        })
    
    return dataset


def save_dataset(data, filename):
    """Dataset'i JSON olarak kaydet"""
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {filename} kaydedildi: {len(data)} örnek")


def main():
    print("🚀 Synthetic Dataset Generation Başlıyor...\n")
    
    # Intent Classification Dataset
    print("📊 Intent Classification Dataset üretiliyor...")
    intent_data = generate_intent_dataset(samples_per_class=75)
    save_dataset(intent_data, "intent_classification_synthetic.json")
    
    # İstatistikler
    intent_counts = {}
    for item in intent_data:
        label = item['label']
        intent_counts[label] = intent_counts.get(label, 0) + 1
    
    print("\nIntent dağılımı:")
    for intent, count in intent_counts.items():
        print(f"  - {intent}: {count} örnek")
    
    # NER Dataset
    print("\n📊 NER Dataset üretiliyor...")
    ner_data = generate_ner_dataset(num_samples=500)
    save_dataset(ner_data, "ner_synthetic.json")
    
    print(f"\n✨ Toplam {len(intent_data)} intent + {len(ner_data)} NER örneği oluşturuldu!")
    print(f"📁 Dosyalar: data/synthetic/ klasöründe")
    
    # Örnek göster
    print("\n📝 Örnek Intent Data:")
    for i in range(3):
        print(f"  {intent_data[i]['text']} → {intent_data[i]['label']}")
    
    print("\n📝 Örnek NER Data:")
    for i in range(2):
        print(f"  {ner_data[i]['text']}")


if __name__ == "__main__":
    main()
