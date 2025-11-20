# 🏠 **Kira Takip Otomasyon Sistemi (OCR) Ön Hazırlık Raporu**

## 🎯 Giriş ve Proje Özeti

Bu proje, emlak yönetim süreçlerini dijitalleştirmeyi ve otomatikleştirmeyi hedeflemektedir. **Optik Karakter Tanıma (OCR)** teknolojisini kullanarak kiracılar tarafından gönderilen banka dekontlarındaki temel ödeme verilerini (ad, soyad, miktar, tarih, IBAN) otomatik olarak çıkarır. Bu temel işlevselliğe ek olarak, projeye iki yenilikçi modül eklenmiştir: **Akıllı Veri Uyumluluğu Kontrolü** ve **Kural Tabanlı Akıllı Geri Bildirim Sistemi**. Bu entegrasyonlar sayesinde, emlakçıların hem zamandan tasarruf etmesi hem de hukuki ve finansal riskleri azaltması sağlanacaktır.

## 1. Amaç ve Hedefler

### 1.1 Amaç
Emlakçıların kira tahsilat ve takip süreçlerini otomatikleştirmek, manuel veri girişinden kaynaklanan hataları minimize etmek ve ödeme verilerini akıllı sistemlerle analiz ederek karar destek mekanizması sunmaktır.

### 1.2 Hedefler
* OCR kullanarak banka dekontlarından gerekli verileri ($\ge 90\%$ doğrulukla) otomatik olarak çıkarmak.
* Çıkarılan veriyi, sistemdeki sözleşme verileriyle (Ad/Soyad, IBAN, Beklenen Miktar) karşılaştırarak **veri uyumluluğunu** kontrol etmek.
* Uyumsuzluk (eksik ödeme, yanlış hesap vb.) durumlarında emlakçıya anlık, eyleme geçirilebilir **akıllı geri bildirim** ve çözüm önerileri sunmak.
* Onaylanan her ödeme için otomatik olarak dijital bir **makbuz veya takip belgesi** oluşturmak.
* Projenin temelinde OCR teknolojisine ek olarak, **kural tabanlı karar destek sistemi** literatürüne katkıda bulunmak.

## 2. Uygulama Aşamaları

| Aşama | Süreç Adı | Açıklama |
| :--- | :--- | :--- |
| **Aşama 1** | **Veri Hazırlama ve OCR Temeli** | Örnek banka dekontları (görüntü/PDF) toplanması. Python/Tesseract (veya benzeri) kullanılarak temel OCR motorunun kurulması ve veri (ad, IBAN, miktar) çıkarma akışının oluşturulması. |
| **Aşama 2** | **Veri Temizleme ve Eşleştirme** | OCR çıktısındaki **gürültülü veriyi** (hata, format farklılığı) temizleme. Basit string benzerlik algoritmaları (Jaccard, Levenshtein Distance) kullanarak Kiracı Adı/IBAN eşleştirme mekanizmasının geliştirilmesi. |
| **Aşama 3** | **Akıllı Uyumluluk Modülü (Yenilik)** | Sözleşmedeki beklenen kira miktarı, tarihi ve kayıtlı IBAN ile OCR'dan gelen verinin karşılaştırılması için iş kurallarının yazılması. |
| **Aşama 4** | **Akıllı Geri Bildirim Sistemi (Yenilik)** | Kural tabanlı mantık (IF/ELSE) kullanarak **Durum Raporu** ve **Eylem Önerisi** (Eksik Ödeme Talep Et, Farklı Hesabı Onayla vb.) mekanizmasının kodlanması. |
| **Aşama 5** | **Sonuç ve Belgeleme** | Başarılı ödemeler için otomatik PDF makbuz oluşturma. Kullanıcı arayüzü (Basit Web Arayüzü) entegrasyonu ve tüm projenin test edilmesi/dokümantasyonu. |

## 3. Beklenen Problemler ve Çözüm Önerileri

| Problem | Açıklama | Çözüm Önerisi (Literatür Katkısı) |
| :--- | :--- | :--- |
| **OCR Doğruluğu** | Düşük çözünürlüklü veya farklı banka formatlarındaki dekontlarda OCR hataları. | **Ön İşleme (Pre-processing):** Görüntüleri gri tonlamaya çevirme, kontrast artırma ve keskinleştirme algoritmalarının kullanılması. OCR Motoru ayarlarının banka bazında optimize edilmesi. |
| **Gürültülü Eşleştirme** | OCR çıktısındaki "M. Yılmaz" ile veritabanındaki "Mehmet Yılmaz"ı eşleştirememe. | **Basit Benzerlik Ölçütleri:** Tam eşleşme yerine **Levenstein Mesafesi** veya **Jaccard Benzerliği** gibi algoritmalarla kısmi eşleşmeyi kabul eden bir mekanizma geliştirilmesi. |
| **Kural Karmaşıklığı** | Akıllı Geri Bildirim sistemindeki iş kurallarının zamanla yönetilemez hale gelmesi. | Kuralları bir konfigürasyon dosyasında tutmak (JSON/YAML) ve yeni kuralları kod değiştirmeden eklemeyi sağlayacak esnek bir yapı kurmak. |

---
