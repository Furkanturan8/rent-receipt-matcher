"""
Response Templates for Chatbot

Intent-based template responses for real estate payment management.
"""

from typing import Dict, Any


class ResponseTemplates:
    """Template-based response generator."""
    
    # Payment confirmation templates
    PAYMENT_CONFIRMED = {
        "kira_odemesi": """
✅ **Kira Ödemesi Onaylandı!**

📋 Ödeme Detayları:
   • Gönderen: {sender}
   • Alıcı: {receiver}
   • Tutar: {amount} {currency}
   • Tarih: {date}
   • Daire: {apt_no}
   • Dönem: {period}

🏠 Eşleşen Kayıt:
   • Mülk Sahibi: {owner_name}
   • Kiracı: {customer_name}
   • Adres: {property_address}
   
💯 Eşleşme Güveni: {confidence}%

✨ Ödemeniz başarıyla kaydedildi!
""",
        
        "aidat_odemesi": """
✅ **Aidat Ödemesi Onaylandı!**

📋 Ödeme Detayları:
   • Gönderen: {sender}
   • Tutar: {amount} {currency}
   • Dönem: {period}
   • Tarih: {date}

💯 Eşleşme Güveni: {confidence}%

✨ Aidat ödemeniz başarıyla kaydedildi!
""",
        
        "kapora_odemesi": """
✅ **Kapora Ödemesi Onaylandı!**

📋 Ödeme Detayları:
   • Gönderen: {sender}
   • Alıcı: {receiver}
   • Tutar: {amount} {currency}
   • Tarih: {date}

🏠 Mülk: {property_address}

✨ Kapora ödemeniz başarıyla kaydedildi!
""",
        
        "depozito_odemesi": """
✅ **Depozito Ödemesi Onaylandı!**

📋 Ödeme Detayları:
   • Gönderen: {sender}
   • Alıcı: {receiver}
   • Tutar: {amount} {currency}
   • Tarih: {date}

🏠 Mülk: {property_address}

✨ Depozito ödemeniz başarıyla kaydedildi!
"""
    }
    
    # Payment error templates
    PAYMENT_ERRORS = {
        "amount_mismatch": """
⚠️ **Tutar Uyuşmazlığı!**

❌ Sorun:
   • Beklenen Tutar: {expected_amount} {currency}
   • Gelen Tutar: {actual_amount} {currency}
   • Fark: {difference} {currency}

💡 Öneri:
   Lütfen eksik/fazla ödeme tutarını kontrol edin.
   Eğer tutar doğruysa, kira artışı varsa bilgi verin.
""",
        
        "iban_mismatch": """
⚠️ **IBAN Uyuşmazlığı!**

❌ Sorun:
   • Gelen IBAN: {actual_iban}
   • Beklenen IBAN: {expected_iban}

💡 Öneri:
   Lütfen doğru IBAN'a ödeme yapın.
   Farklı bir hesap kullanıyorsanız bilgi verin.
""",
        
        "name_mismatch": """
⚠️ **İsim Uyuşmazlığı!**

❌ Sorun:
   • Gelen İsim: {actual_name}
   • Beklenen İsim: {expected_name}

💡 Öneri:
   Lütfen kayıtlı isminizle ödeme yapın.
   Farklı bir kişi adına ödeme yapıyorsanız bilgi verin.
""",
        
        "no_match": """
❌ **Eşleşen Kayıt Bulunamadı!**

📋 Çıkarılan Bilgiler:
   • Gönderen: {sender}
   • Alıcı: {receiver}
   • Tutar: {amount} {currency}
   • Tarih: {date}

💡 Öneri:
   • Dekont bilgilerini kontrol edin
   • Mülk sahibi IBAN'ı doğru mu?
   • Kira tutarı değişti mi?
   
📞 Manuel inceleme gerekiyor.
""",
        
        "low_confidence": """
⚠️ **Düşük Güven Skoru!**

📊 Eşleşme Güveni: {confidence}%

Olası eşleşme bulundu ama kesin değil:
   • Mülk Sahibi: {owner_name}
   • Mülk: {property_address}
   • Beklenen Tutar: {expected_amount} {currency}

💡 Öneri:
   Manuel inceleme yapılması önerilir.
"""
    }
    
    # Manual review template
    MANUAL_REVIEW = """
⚠️ **Manuel İnceleme Gerekiyor**

📋 Durum:
   • Otomatik eşleştirme yapılamadı
   • Güven skoru: {confidence}%

📝 Çıkarılan Bilgiler:
{extracted_info}

🔍 Sorun:
{issues}

💡 Sonraki Adım:
   Yönetici incelemesi gerekiyor.
   Lütfen dekont bilgilerini manuel kontrol edin.
"""
    
    # Query responses
    TENANT_INFO = """
👤 **Kiracı Bilgileri**

📋 Kişisel Bilgiler:
   • Ad Soyad: {full_name}
   • Email: {email}
   • Telefon: {phone}

🏠 Mülk Bilgileri:
   • Adres: {property_address}
   • Daire No: {apt_no}
   • Kira: {rent_amount} TL/ay

💳 Ödeme Bilgileri:
   • Mülk Sahibi: {owner_name}
   • IBAN: {owner_iban}
   • Ödeme Günü: Her ayın {payment_day}. günü
"""
    
    PAYMENT_STATUS = """
💰 **Ödeme Durumu**

📅 {period} Dönemi:
   • Durum: {status}
   • Tutar: {amount} TL
   • Son Ödeme Tarihi: {due_date}
   • Ödeme Tarihi: {payment_date}

{additional_info}
"""
    
    # Help menu
    HELP_MENU = """
🤖 **Yardım Menüsü**

📋 Yapabilecekleriniz:

1️⃣ **Dekont İşleme**
   • Dekont PDF'i yükleyerek otomatik işlem

2️⃣ **Ödeme Sorgulama**
   • Ödeme durumu kontrol
   • Geçmiş ödemeler

3️⃣ **Kiracı Bilgileri**
   • Kişisel bilgiler
   • Kira detayları

4️⃣ **İletişim**
   • Destek talebi
   • Soru sorma

💡 Komut örnekleri:
   • "Kiracı bilgilerimi göster"
   • "Kasım ayı ödeme durumu"
   • "Son ödeme tarihi ne zaman?"
   • "Yardım"
"""
    
    WELCOME = """
👋 **Hoş Geldiniz!**

🏢 Akıllı Emlak Ödeme Yönetim Sistemi

Bu sistemle:
✅ Dekont yükleme ve otomatik işleme
✅ Ödeme takibi ve doğrulama
✅ Kiracı bilgisi sorgulama
✅ 7/24 destek

💡 Yardım için "yardım" yazın
"""
    
    GOODBYE = """
👋 **Görüşmek Üzere!**

✨ Bizi kullandığınız için teşekkürler!

📞 Sorularınız için:
   Email: destek@emlakodeme.com
   Tel: 0850 123 4567
"""
    
    UNKNOWN = """
❓ **Anlayamadım**

Üzgünüm, ne demek istediğinizi anlayamadım.

💡 Şunları deneyebilirsiniz:
   • "Yardım" yazarak menüyü görebilirsiniz
   • Dekont PDF'i yükleyebilirsiniz
   • Ödeme durumu sorgulayabilirsiniz

Nasıl yardımcı olabilirim?
"""
    
    @staticmethod
    def format_payment_confirmed(intent: str, data: Dict[str, Any]) -> str:
        """Format payment confirmation message."""
        template = ResponseTemplates.PAYMENT_CONFIRMED.get(intent, "")
        if not template:
            return "✅ Ödeme onaylandı!"
        
        return template.format(
            sender=data.get('sender', 'Bilinmiyor'),
            receiver=data.get('receiver', 'Bilinmiyor'),
            amount=data.get('amount', '0'),
            currency=data.get('currency', 'TRY'),
            date=data.get('date', 'Bilinmiyor'),
            apt_no=data.get('apt_no', 'Bilinmiyor'),
            period=data.get('period', 'Bilinmiyor'),
            owner_name=data.get('owner_name', 'Bilinmiyor'),
            customer_name=data.get('customer_name', 'Bilinmiyor'),
            property_address=data.get('property_address', 'Bilinmiyor'),
            confidence=data.get('confidence', 0)
        )
    
    @staticmethod
    def format_payment_error(error_type: str, data: Dict[str, Any]) -> str:
        """Format payment error message."""
        template = ResponseTemplates.PAYMENT_ERRORS.get(error_type, "")
        if not template:
            return "❌ Ödeme hatası!"
        
        return template.format(**data)
    
    @staticmethod
    def format_manual_review(data: Dict[str, Any]) -> str:
        """Format manual review message."""
        return ResponseTemplates.MANUAL_REVIEW.format(
            confidence=data.get('confidence', 0),
            extracted_info=data.get('extracted_info', 'Bilgi yok'),
            issues=data.get('issues', 'Bilinmiyor')
        )
    
    # Payment history template
    PAYMENT_HISTORY = """
📊 **{tenant_name} - Ödeme Geçmişi**

💳 **Kiracı Bilgileri:**
   • Ad Soyad: {full_name}
   • Mülk: {property_address}
   • Aylık Kira: {rent_amount} TRY

📅 **Geçmiş Ödemeler:**
{payment_records}

📈 **Özet:**
   • Toplam Ödeme: {total_payments} kez
   • Son Ödeme: {last_payment_date}
   • Durum: {payment_status}
"""
    
    # Payment status template
    PAYMENT_STATUS = """
💰 **{tenant_name} - Ödeme Durumu**

👤 **Kiracı:**
   • Ad Soyad: {full_name}
   • Mülk: {property_address}
   • Kira Bedeli: {rent_amount} TRY

📅 **{period} Ödeme Durumu:**
   • Durum: {status}
   • Ödeme Tarihi: {payment_date}
   • Tutar: {amount} TRY

{notes}
"""
    
    # Tenant not found template
    TENANT_NOT_FOUND = """
❌ **Kiracı Bulunamadı**

"{search_term}" için veritabanında kayıt bulunamadı.

💡 **Öneriler:**
   • İsmi tam ve doğru yazdığınızdan emin olun
   • "Furkan Turan" gibi ad soyad şeklinde deneyin
   • Kiracı listesini görmek için "kiracı listesi" yazın
"""


__all__ = ["ResponseTemplates"]
