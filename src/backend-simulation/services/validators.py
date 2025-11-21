"""
Dekont validasyon servisi.

Bu modül dekonttan çıkarılan verilerin doğruluğunu kontrol eder:
- IBAN formatı kontrolü
- Tutar kontrolü (beklenen tutar ile karşılaştırma)
- Tarih kontrolü
- Mülk sahibi ve kiracı eşleşme kontrolü
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """Validasyon sonucu."""
    
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, message: str):
        """Hata mesajı ekler ve is_valid'i False yapar."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Uyarı mesajı ekler."""
        self.warnings.append(message)
    
    def add_message(self, message: str):
        """Bilgilendirme mesajı ekler."""
        self.messages.append(message)


class ReceiptValidator:
    """
    Dekont validasyon sınıfı.
    
    Dekonttan çıkarılan verilerin doğruluğunu kontrol eder.
    """
    
    # Türk IBAN formatı: TR + 24 rakam
    IBAN_PATTERN = re.compile(r'^TR\d{24}$')
    
    # Tutar için tolerans (%)
    AMOUNT_TOLERANCE = 0.05  # %5
    
    def __init__(
        self,
        owners: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        properties: List[Dict[str, Any]],
        rental_contracts: List[Dict[str, Any]],
    ):
        """
        Args:
            owners: Mülk sahipleri listesi
            customers: Müşteriler listesi
            properties: Mülkler listesi
            rental_contracts: Kira sözleşmeleri listesi
        """
        self.owners = owners
        self.customers = customers
        self.properties = properties
        self.rental_contracts = rental_contracts
    
    def validate(
        self,
        extracted_fields: Dict[str, Any],
        matched_owner_id: Optional[int] = None,
        matched_customer_id: Optional[int] = None,
        matched_property_id: Optional[int] = None,
        expected_amount: Optional[float] = None,
    ) -> ValidationResult:
        """
        Dekont verilerini doğrular.
        
        Args:
            extracted_fields: OCR'dan çıkarılan alanlar
            matched_owner_id: Eşleşen mülk sahibi ID'si
            matched_customer_id: Eşleşen müşteri ID'si
            matched_property_id: Eşleşen mülk ID'si
            expected_amount: Beklenen tutar
        
        Returns:
            ValidationResult: Validasyon sonucu
        """
        result = ValidationResult()
        
        # 1. IBAN kontrolü
        self._validate_iban(extracted_fields, result)
        
        # 2. Tutar kontrolü
        self._validate_amount(extracted_fields, expected_amount, matched_property_id, result)
        
        # 3. Tarih kontrolü
        self._validate_date(extracted_fields, result)
        
        # 4. Mülk sahibi-Müşteri ilişki kontrolü
        self._validate_relationships(
            matched_owner_id,
            matched_customer_id,
            matched_property_id,
            result
        )
        
        # 5. Aktif sözleşme kontrolü
        self._validate_active_contract(
            matched_owner_id,
            matched_property_id,
            result
        )
        
        # 6. Zorunlu alanlar kontrolü
        self._validate_required_fields(extracted_fields, result)
        
        # Sonuç mesajı
        if result.is_valid and not result.warnings:
            result.add_message("✓ Tüm validasyonlar başarılı")
        elif result.is_valid and result.warnings:
            result.add_message("✓ Validasyon başarılı (uyarılar var)")
        else:
            result.add_message("✗ Validasyon başarısız")
        
        return result
    
    def _validate_iban(self, extracted_fields: Dict[str, Any], result: ValidationResult):
        """IBAN formatını kontrol eder."""
        receiver_iban = extracted_fields.get("receiver_iban", "").strip().upper()
        sender_iban = extracted_fields.get("sender_iban", "").strip().upper()
        
        # Alıcı IBAN kontrolü
        if receiver_iban:
            # Boşlukları temizle
            receiver_iban_clean = receiver_iban.replace(" ", "")
            if not self.IBAN_PATTERN.match(receiver_iban_clean):
                result.add_error(
                    f"Geçersiz alıcı IBAN formatı: {receiver_iban} "
                    "(TR + 24 rakam olmalı)"
                )
            else:
                result.add_message(f"✓ Alıcı IBAN formatı geçerli: {receiver_iban_clean}")
        else:
            result.add_warning("Alıcı IBAN bilgisi eksik")
        
        # Gönderen IBAN kontrolü (opsiyonel)
        if sender_iban:
            sender_iban_clean = sender_iban.replace(" ", "")
            if not self.IBAN_PATTERN.match(sender_iban_clean):
                result.add_warning(
                    f"Geçersiz gönderen IBAN formatı: {sender_iban}"
                )
            else:
                result.add_message(f"✓ Gönderen IBAN formatı geçerli: {sender_iban_clean}")
    
    def _validate_amount(
        self,
        extracted_fields: Dict[str, Any],
        expected_amount: Optional[float],
        matched_property_id: Optional[int],
        result: ValidationResult
    ):
        """Tutar kontrolü yapar."""
        amount_str = extracted_fields.get("amount", "")
        
        if not amount_str:
            result.add_error("Tutar bilgisi eksik")
            return
        
        # Tutarı sayıya çevir
        try:
            # Nokta ve virgül işaretlerini temizle
            amount_clean = amount_str.replace(".", "").replace(",", ".")
            amount = float(amount_clean)
        except (ValueError, AttributeError):
            result.add_error(f"Geçersiz tutar formatı: {amount_str}")
            return
        
        if amount <= 0:
            result.add_error(f"Tutar sıfır veya negatif olamaz: {amount}")
            return
        
        result.add_message(f"✓ Tutar: {amount:.2f} TL")
        result.details["parsed_amount"] = amount
        
        # Beklenen tutar ile karşılaştır
        comparison_amount = expected_amount
        
        # Eğer beklenen tutar yoksa, property'den al
        if not comparison_amount and matched_property_id:
            property_obj = next(
                (p for p in self.properties if p.get("id") == matched_property_id),
                None
            )
            if property_obj:
                comparison_amount = property_obj.get("price")
        
        if comparison_amount:
            tolerance = comparison_amount * self.AMOUNT_TOLERANCE
            diff = abs(amount - comparison_amount)
            
            if diff <= tolerance:
                result.add_message(
                    f"✓ Tutar beklenen değere yakın "
                    f"(Beklenen: {comparison_amount:.2f} TL, "
                    f"Fark: {diff:.2f} TL)"
                )
            elif diff <= tolerance * 2:
                result.add_warning(
                    f"Tutar beklenen değerden farklı "
                    f"(Beklenen: {comparison_amount:.2f} TL, "
                    f"Gerçek: {amount:.2f} TL, "
                    f"Fark: {diff:.2f} TL)"
                )
            else:
                result.add_error(
                    f"Tutar beklenen değerden çok farklı "
                    f"(Beklenen: {comparison_amount:.2f} TL, "
                    f"Gerçek: {amount:.2f} TL, "
                    f"Fark: {diff:.2f} TL)"
                )
    
    def _validate_date(self, extracted_fields: Dict[str, Any], result: ValidationResult):
        """Tarih kontrolü yapar."""
        date_str = extracted_fields.get("date", "")
        
        if not date_str:
            result.add_warning("Tarih bilgisi eksik")
            return
        
        # Tarih formatını parse et (farklı formatlar dene)
        date_formats = [
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            result.add_warning(f"Tarih formatı tanınamadı: {date_str}")
            return
        
        result.add_message(f"✓ Tarih: {parsed_date.strftime('%d.%m.%Y')}")
        result.details["parsed_date"] = parsed_date.isoformat()
        
        # Gelecek tarih kontrolü
        now = datetime.now()
        if parsed_date > now:
            result.add_error(
                f"Dekont tarihi gelecekte olamaz: {parsed_date.strftime('%d.%m.%Y')}"
            )
        
        # Çok eski tarih kontrolü (1 yıldan eski)
        one_year_ago = datetime(now.year - 1, now.month, now.day)
        if parsed_date < one_year_ago:
            result.add_warning(
                f"Dekont tarihi 1 yıldan eski: {parsed_date.strftime('%d.%m.%Y')}"
            )
    
    def _validate_relationships(
        self,
        matched_owner_id: Optional[int],
        matched_customer_id: Optional[int],
        matched_property_id: Optional[int],
        result: ValidationResult
    ):
        """Mülk sahibi-Mülk-Müşteri ilişkilerini kontrol eder."""
        if not matched_owner_id:
            result.add_error("Mülk sahibi eşleştirilemedi")
            return
        
        result.add_message(f"✓ Mülk sahibi eşleştirildi (ID: {matched_owner_id})")
        
        # Property kontrolü
        if matched_property_id:
            property_obj = next(
                (p for p in self.properties if p.get("id") == matched_property_id),
                None
            )
            if property_obj:
                # Property'nin owner'ı ile eşleşen owner'ı karşılaştır
                property_owner_id = property_obj.get("owner_id")
                if property_owner_id and property_owner_id != matched_owner_id:
                    result.add_error(
                        f"Mülk sahibi uyuşmazlığı "
                        f"(Mülk sahibi: {property_owner_id}, "
                        f"Eşleşen: {matched_owner_id})"
                    )
                else:
                    result.add_message(f"✓ Mülk eşleştirildi (ID: {matched_property_id})")
        
        # Customer kontrolü
        if matched_customer_id:
            result.add_message(f"✓ Müşteri eşleştirildi (ID: {matched_customer_id})")
    
    def _validate_active_contract(
        self,
        matched_owner_id: Optional[int],
        matched_property_id: Optional[int],
        result: ValidationResult
    ):
        """Aktif kira sözleşmesi kontrolü yapar."""
        if not matched_property_id:
            return
        
        # Property için aktif sözleşme ara
        active_contracts = [
            c for c in self.rental_contracts
            if c.get("rental_property_id") == matched_property_id
            and c.get("status") == "active"
        ]
        
        if not active_contracts:
            result.add_warning(
                f"Mülk için aktif kira sözleşmesi bulunamadı (Property ID: {matched_property_id})"
            )
            return
        
        result.add_message(
            f"✓ Aktif kira sözleşmesi mevcut "
            f"(Sözleşme sayısı: {len(active_contracts)})"
        )
        
        # Sözleşme detaylarını kaydet
        result.details["active_contracts"] = [
            {
                "contract_id": c.get("id"),
                "contract_number": c.get("contract_number"),
                "tenant_id": c.get("tenant_id"),
                "monthly_rent": c.get("monthly_rent"),
            }
            for c in active_contracts
        ]
    
    def _validate_required_fields(
        self,
        extracted_fields: Dict[str, Any],
        result: ValidationResult
    ):
        """Zorunlu alanların varlığını kontrol eder."""
        required_fields = ["amount"]
        
        for field in required_fields:
            if not extracted_fields.get(field):
                result.add_error(f"Zorunlu alan eksik: {field}")
        
        # Alıcı bilgisi kontrolü (IBAN veya İsim)
        if not extracted_fields.get("receiver_iban") and not extracted_fields.get("recipient"):
            result.add_warning(
                "Alıcı bilgisi eksik (IBAN veya İsim olmalı)"
            )


__all__ = ["ReceiptValidator", "ValidationResult"]

