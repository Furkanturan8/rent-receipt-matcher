"""
Transaction yönetim servisi.

Bu modül dekont işleme sonucuna göre Transaction kayıtlarını oluşturur ve yönetir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TransactionStatus(str, Enum):
    """Transaction durumları."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransactionType(str, Enum):
    """Transaction tipleri."""
    RENT_PAYMENT = "rent_payment"
    DEPOSIT_IN = "deposit_in"
    DEPOSIT_OUT = "deposit_out"
    OWNER_PAYMENT = "owner_payment"
    COMMISSION = "commission"
    OTHER = "other"


class TransactionDirection(str, Enum):
    """Transaction yönü (emlakçı açısından)."""
    IN = "in"  # Para giriyor
    OUT = "out"  # Para çıkıyor


class PaymentMethod(str, Enum):
    """Ödeme yöntemleri."""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    OTHER = "other"


@dataclass
class TransactionData:
    """Transaction oluşturmak için gerekli veriler."""
    
    # İlişkiler
    rental_contract_id: Optional[int] = None
    rental_property_id: Optional[int] = None
    account_id: Optional[int] = None
    
    # Transaction detayları
    transaction_type: str = TransactionType.RENT_PAYMENT.value
    direction: str = TransactionDirection.IN.value
    status: str = TransactionStatus.PENDING.value
    
    # Tutar
    amount: float = 0.0
    amount_currency: str = "TRY"
    
    # Tarihler
    due_date: Optional[str] = None  # YYYY-MM-DD
    payment_date: Optional[str] = None  # YYYY-MM-DD
    
    # Ödeme bilgileri
    payment_method: str = PaymentMethod.BANK_TRANSFER.value
    reference_number: str = ""
    
    # Açıklamalar
    description: str = ""
    notes: str = ""
    
    # Ek bilgiler (OCR'dan gelen)
    ocr_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Transaction verisini sözlük olarak döner."""
        return {
            "rental_contract_id": self.rental_contract_id,
            "rental_property_id": self.rental_property_id,
            "account_id": self.account_id,
            "transaction_type": self.transaction_type,
            "direction": self.direction,
            "status": self.status,
            "amount": self.amount,
            "amount_currency": self.amount_currency,
            "due_date": self.due_date,
            "payment_date": self.payment_date,
            "payment_method": self.payment_method,
            "reference_number": self.reference_number,
            "description": self.description,
            "notes": self.notes,
            "ocr_data": self.ocr_data,
        }


class TransactionManager:
    """
    Transaction yönetim sınıfı.
    
    Dekont işleme sonucuna göre Transaction kayıtları oluşturur.
    """
    
    def __init__(
        self,
        owners: List[Dict[str, Any]],
        properties: List[Dict[str, Any]],
        rental_contracts: List[Dict[str, Any]],
        accounts: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Args:
            owners: Mülk sahipleri listesi
            properties: Mülkler listesi
            rental_contracts: Kira sözleşmeleri listesi
            accounts: Cari hesaplar listesi (opsiyonel)
        """
        self.owners = owners
        self.properties = properties
        self.rental_contracts = rental_contracts
        self.accounts = accounts or []
    
    def create_transaction_from_receipt(
        self,
        extracted_fields: Dict[str, Any],
        matched_owner_id: Optional[int] = None,
        matched_customer_id: Optional[int] = None,
        matched_property_id: Optional[int] = None,
        receipt_status: str = "pending",
    ) -> TransactionData:
        """
        Dekont verisinden Transaction oluşturur.
        
        Args:
            extracted_fields: OCR'dan çıkarılan alanlar
            matched_owner_id: Eşleşen mülk sahibi ID'si
            matched_customer_id: Eşleşen müşteri ID'si
            matched_property_id: Eşleşen mülk ID'si
            receipt_status: Dekont durumu (approved, rejected, manual_review)
        
        Returns:
            TransactionData: Transaction verisi
        """
        transaction = TransactionData()
        
        # OCR verisini kaydet
        transaction.ocr_data = extracted_fields
        
        # Tutar
        amount_str = extracted_fields.get("amount", "0")
        try:
            amount_clean = str(amount_str).replace(".", "").replace(",", ".")
            transaction.amount = float(amount_clean)
        except (ValueError, AttributeError):
            transaction.amount = 0.0
        
        # Para birimi
        transaction.amount_currency = extracted_fields.get("amount_currency", "TRY")
        
        # Tarih
        payment_date_str = extracted_fields.get("date", "")
        if payment_date_str:
            # Tarih formatını normalize et (YYYY-MM-DD)
            transaction.payment_date = self._normalize_date(payment_date_str)
        
        # Açıklama
        description = extracted_fields.get("description", "")
        sender = extracted_fields.get("sender", "")
        recipient = extracted_fields.get("recipient", "")
        
        description_parts = []
        if sender:
            description_parts.append(f"Gönderen: {sender}")
        if recipient:
            description_parts.append(f"Alıcı: {recipient}")
        if description:
            description_parts.append(f"Açıklama: {description}")
        
        transaction.description = " | ".join(description_parts)
        
        # Referans numarası (dekont no)
        transaction.reference_number = f"DEKONT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Property ve Contract bilgisi
        if matched_property_id:
            transaction.rental_property_id = matched_property_id
            
            # Property için aktif contract bul
            active_contract = self._find_active_contract(matched_property_id)
            if active_contract:
                transaction.rental_contract_id = active_contract.get("id")
                
                # Due date'i contract'tan al (payment_day'e göre)
                payment_day = active_contract.get("payment_day", 1)
                now = datetime.now()
                transaction.due_date = f"{now.year}-{now.month:02d}-{payment_day:02d}"
        
        # Account bilgisi (Owner'a ait cari hesap)
        if matched_owner_id:
            owner_account = self._find_owner_account(matched_owner_id)
            if owner_account:
                transaction.account_id = owner_account.get("id")
        
        # Status
        if receipt_status == "approved":
            transaction.status = TransactionStatus.COMPLETED.value
        elif receipt_status == "rejected":
            transaction.status = TransactionStatus.REJECTED.value
        else:
            transaction.status = TransactionStatus.PENDING.value
        
        # Notlar
        notes_parts = []
        if matched_owner_id:
            notes_parts.append(f"Mülk Sahibi ID: {matched_owner_id}")
        if matched_customer_id:
            notes_parts.append(f"Müşteri ID: {matched_customer_id}")
        if matched_property_id:
            notes_parts.append(f"Mülk ID: {matched_property_id}")
        notes_parts.append(f"OCR ile otomatik oluşturuldu ({datetime.now().isoformat()})")
        
        transaction.notes = " | ".join(notes_parts)
        
        return transaction
    
    def update_transaction_status(
        self,
        transaction_id: int,
        new_status: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transaction durumunu günceller.
        
        Args:
            transaction_id: Transaction ID
            new_status: Yeni durum
            reason: Durum değişikliği nedeni (opsiyonel)
        
        Returns:
            Dict: Güncelleme sonucu
        """
        # Gerçek uygulamada database güncelleme yapılacak
        # Şu an sadece bir dict döndürüyoruz (simulasyon)
        
        result = {
            "transaction_id": transaction_id,
            "old_status": "pending",  # Gerçek uygulamada mevcut durum alınacak
            "new_status": new_status,
            "reason": reason,
            "updated_at": datetime.now().isoformat(),
        }
        
        return result
    
    def approve_transaction(
        self,
        transaction_id: int,
        approved_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transaction'ı onaylar.
        
        Args:
            transaction_id: Transaction ID
            approved_by: Onaylayan kişi (opsiyonel)
        
        Returns:
            Dict: Onaylama sonucu
        """
        reason = f"Manuel onay: {approved_by}" if approved_by else "Otomatik onay"
        return self.update_transaction_status(
            transaction_id=transaction_id,
            new_status=TransactionStatus.COMPLETED.value,
            reason=reason,
        )
    
    def reject_transaction(
        self,
        transaction_id: int,
        rejection_reason: str,
        rejected_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transaction'ı reddeder.
        
        Args:
            transaction_id: Transaction ID
            rejection_reason: Red nedeni
            rejected_by: Reddeden kişi (opsiyonel)
        
        Returns:
            Dict: Reddetme sonucu
        """
        reason = f"{rejection_reason}"
        if rejected_by:
            reason += f" (Reddeden: {rejected_by})"
        
        return self.update_transaction_status(
            transaction_id=transaction_id,
            new_status=TransactionStatus.REJECTED.value,
            reason=reason,
        )
    
    def _find_active_contract(self, property_id: int) -> Optional[Dict[str, Any]]:
        """Property için aktif kira sözleşmesi bulur."""
        for contract in self.rental_contracts:
            if (
                contract.get("rental_property_id") == property_id
                and contract.get("status") == "active"
            ):
                return contract
        return None
    
    def _find_owner_account(self, owner_id: int) -> Optional[Dict[str, Any]]:
        """Owner için cari hesap bulur."""
        for account in self.accounts:
            # Account'un content_type'ı Owner ve object_id eşleşiyorsa
            if (
                account.get("content_type") == "owner"
                and account.get("object_id") == owner_id
            ):
                return account
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """
        Tarih string'ini YYYY-MM-DD formatına çevirir.
        
        Args:
            date_str: Tarih string'i (farklı formatlarda olabilir)
        
        Returns:
            str: YYYY-MM-DD formatında tarih
        """
        date_formats = [
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # Parse edilemezse bugünün tarihini döndür
        return datetime.now().strftime("%Y-%m-%d")


__all__ = [
    "TransactionManager",
    "TransactionData",
    "TransactionStatus",
    "TransactionType",
    "TransactionDirection",
    "PaymentMethod",
]

