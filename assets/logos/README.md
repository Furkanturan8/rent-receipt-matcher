# Banka Logoları Dizini

Bu dizin, banka tespiti için referans logo görsellerini içerir.

## Logo Dosyaları

Her banka için logo dosyaları şu isimlerde olmalıdır:

- **Halkbank**: `halkbank_logo.png` veya `halkbank_logo.jpg`
- **YapıKredi**: `yapikredi_logo.png` veya `yapikredi_logo.jpg`
- **KuveytTürk**: `kuveytturk_logo.png` veya `kuveytturk_logo.jpg`
- **Ziraat Bankası**: `ziraatbank_logo.png` veya `ziraatbank_logo.jpg`
- **VakıfBank**: `vakifbank_logo.png` veya `vakifbank_logo.jpg`

## Logo Ekleme

1. PDF'lerden veya banka web sitelerinden temiz logo görsellerini alın
2. Logo dosyalarını yukarıdaki isimlendirme formatına göre kaydedin
3. PNG veya JPG formatında olabilir
4. İdeal boyut: 200-500 piksel genişlik (çok büyük olmasına gerek yok)

## Kullanım

Logo tabanlı tespit otomatik olarak çalışır. CLI'de `--use-logo-detection` parametresi ile aktif edilebilir:

```bash
make extract FILE=data/halkbank.pdf --use-logo-detection
```

veya doğrudan:

```bash
python -m ocr.extraction.cli data/halkbank.pdf --use-logo-detection
```

## Notlar

- Logo tabanlı tespit, metin tabanlı tespite ek olarak kullanılabilir (hibrit mod)
- OpenCV ve PyMuPDF kurulu olmalıdır (opsiyonel bağımlılıklar)
- Logo dosyaları yoksa sistem sadece metin tabanlı tespit kullanır

