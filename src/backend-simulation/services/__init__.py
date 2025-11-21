"""
Backend simulation için servis katmanı.

Bu modül OCR servisleri ile backend modelleri arasında köprü görevi görür.
Kira dekontlarının işlenmesi, doğrulanması ve Transaction oluşturulması işlemlerini yönetir.
"""

from .receipt_processor import ReceiptProcessor, ReceiptProcessingResult
from .validators import ReceiptValidator, ValidationResult
from .transaction_manager import TransactionManager, TransactionStatus

__all__ = [
    "ReceiptProcessor",
    "ReceiptProcessingResult",
    "ReceiptValidator",
    "ValidationResult",
    "TransactionManager",
    "TransactionStatus",
]

