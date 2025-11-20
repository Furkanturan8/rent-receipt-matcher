## OCR Projesi Yol Haritası

- **Hazırlık**
  - Proje gereksinimlerini detaylandır ve paydaş beklentilerini toparla.
  - Örnek banka dekontlarını topla ve veri erişim izinlerini netleştir.
  - Temel proje yapısını oluştur (`src/`, `data/`, `docs/`, `tests/`).

- **Aşama 1 · OCR Temeli**
  - Python ortamını ve bağımlılıkları kur (Tesseract, pytesseract, OpenCV).
  - Örnek dekontlar için görüntü ön işleme pipeline’ını tasarla.
  - OCR çıktısını yapılandırılmış formata (JSON/CSV) dönüştüren modülü geliştir.
  - Basit doğruluk ölçümü için küçük bir değerlendirme seti hazırla.

- **Aşama 2 · Veri Temizleme ve Eşleştirme**
  - OCR çıktılarındaki gürültüyü temizleme fonksiyonlarını geliştir.
  - Kiracı bilgileri için veri modeli ve saklama yapısını tasarla.
  - Ad/IBAN eşleştirmesi için Levenshtein ve Jaccard tabanlı yardımcı fonksiyonlar ekle.
  - Test senaryoları ile eşleştirme doğruluğunu ölç ve raporla.

- **Aşama 3 · Akıllı Uyumluluk Modülü**
  - Sözleşme verilerini içeren konfigürasyon dosyası veya veritabanı şemasını hazırl.
  - Beklenen miktar, tarih ve IBAN karşılaştırmalarını yapan kural setini uygula.
  - Uyumluluk sonuçlarını sınıflandıran (uygun, kısmi, uyumsuz) bir yapı tanımla.
  - Modül sonuçlarını loglayan ve izlenebilir kılan mekanizmaları ekle.

- **Aşama 4 · Akıllı Geri Bildirim Sistemi**
  - Geri bildirim kurallarını JSON/YAML konfigürasyonu üzerinden tanımla.
  - Her uyumsuzluk tipine karşılık aksiyon önerileri üreten motoru geliştir.
  - Geri bildirim mesajlarını yapılandırılmış hale getir (başlık, açıklama, önerilen aksiyon).
  - Örnek vakalarla sistem davranışını test et ve iyileştir.

- **Aşama 5 · Raporlama ve Entegrasyon**
  - Başarılı ödemeler için otomatik makbuz PDF’i oluşturan servisi hazırla.
  - Basit bir web arayüzü veya CLI üzerinden sonuçları görselleştir.
  - Uçtan uca entegrasyon testlerini yaz ve çalıştır.
  - Teknik dokümantasyon ve kullanıcı kılavuzunu güncelle.

- **Kapanış**
  - Nihai performans raporunu çıkar (OCR doğruluğu, eşleştirme başarısı, geri bildirim isabeti).
  - Kod incelemesi ve refaktör ihtiyaçlarını değerlendir.
  - Yayına hazırlık için dağıtım planı ve bakım süreçlerini tanımla.


