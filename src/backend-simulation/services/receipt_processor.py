"""
Dekont işleme servisi.

Bu modül:
1. PDF dekontlarını OCR ile işler
2. Banka tespiti yapar
3. Alanları çıkarır (tutar, IBAN, ad, tarih)
4. Database ile eşleştirir (Owner, Customer, Property)
5. Validasyon yapar
6. İşlem sonucunu döner
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# OCR modüllerini import et
sys.path.append(str(Path(__file__).parent.parent.parent))
from ocr.extraction.bank_detector import detect_bank_hybrid
from ocr.extraction.extractor import extract_fields
from ocr.matching.matcher import match_receipt

try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


@dataclass
class ReceiptProcessingResult:
    """Dekont işleme sonucu."""
    
    # İşlem durumu
    success: bool = False
    status: str = "pending"  # pending, approved, rejected, manual_review
    
    # OCR çıktısı
    detected_bank: Optional[str] = None
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Eşleştirme sonuçları
    matched_owner_id: Optional[int] = None
    matched_customer_id: Optional[int] = None
    matched_property_id: Optional[int] = None
    match_confidence: float = 0.0
    
    # Validasyon sonuçları
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    
    # Mesajlar ve detaylar
    messages: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Sonucu sözlük olarak döner."""
        return {
            "success": self.success,
            "status": self.status,
            "detected_bank": self.detected_bank,
            "extracted_fields": self.extracted_fields,
            "matched_owner_id": self.matched_owner_id,
            "matched_customer_id": self.matched_customer_id,
            "matched_property_id": self.matched_property_id,
            "match_confidence": self.match_confidence,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
            "messages": self.messages,
            "details": self.details,
        }


class ReceiptProcessor:
    """
    Dekont işleme ana sınıfı.
    
    OCR servisleri ile backend modellerini birleştirir.
    """
    
    def __init__(
        self,
        owners: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        properties: List[Dict[str, Any]],
        rental_contracts: List[Dict[str, Any]],
    ):
        """
        Args:
            owners: Mülk sahipleri listesi (Owner modeli verileri)
            customers: Müşteriler listesi (Customer modeli verileri)
            properties: Mülkler listesi (Property modeli verileri)
            rental_contracts: Kira sözleşmeleri listesi (RentalContract modeli verileri)
        """
        self.owners = owners
        self.customers = customers
        self.properties = properties
        self.rental_contracts = rental_contracts
    
    def process_receipt(
        self,
        pdf_path: str | Path,
        expected_amount: Optional[float] = None,
        expected_owner_id: Optional[int] = None,
        min_confidence: float = 70.0,
    ) -> ReceiptProcessingResult:
        """
        Dekont PDF'ini işler ve sonuç döner.
        
        Args:
            pdf_path: Dekont PDF dosyasının yolu
            expected_amount: Beklenen kira tutarı (opsiyonel)
            expected_owner_id: Beklenen mülk sahibi ID'si (opsiyonel)
            min_confidence: Minimum eşleştirme güven skoru (0-100)
        
        Returns:
            ReceiptProcessingResult: İşlem sonucu
        """
        result = ReceiptProcessingResult()
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            result.messages.append(f"Dosya bulunamadı: {pdf_path}")
            return result
        
        # 1. PDF'den metin çıkar
        try:
            text = self._extract_text_from_pdf(pdf_path)
            if not text:
                result.messages.append("PDF'den metin çıkarılamadı")
                return result
        except Exception as e:
            result.messages.append(f"PDF okuma hatası: {e}")
            return result
        
        # 2. Banka tespiti
        detected_bank = detect_bank_hybrid(text, pdf_path)
        result.detected_bank = detected_bank
        
        if detected_bank:
            result.messages.append(f"Banka tespit edildi: {detected_bank.upper()}")
        else:
            result.messages.append("Banka tespit edilemedi, genel desenler kullanılacak")
        
        # 3. Alanları çıkar
        extracted_fields = extract_fields(text, bank_hint=detected_bank)
        result.extracted_fields = extracted_fields
        
        if not extracted_fields:
            result.messages.append("Dekonttan alan çıkarılamadı")
            return result
        
        result.messages.append(
            f"Çıkarılan alanlar: {', '.join(extracted_fields.keys())}"
        )
        
        # 4. Database ile eşleştir
        match_result = match_receipt(
            ocr_data=extracted_fields,
            owners=self.owners,
            customers=self.customers,
            properties=self.properties,
            min_confidence=min_confidence,
        )
        
        result.matched_owner_id = match_result.owner_id
        result.matched_customer_id = match_result.customer_id
        result.matched_property_id = match_result.property_id
        result.match_confidence = match_result.confidence_score
        result.details["matching_details"] = match_result.matching_details
        
        # Eşleştirme mesajlarını ekle
        result.messages.extend(match_result.messages)
        
        # 5. Validasyon yap
        from .validators import ReceiptValidator
        
        validator = ReceiptValidator(
            owners=self.owners,
            customers=self.customers,
            properties=self.properties,
            rental_contracts=self.rental_contracts,
        )
        
        validation_result = validator.validate(
            extracted_fields=extracted_fields,
            matched_owner_id=result.matched_owner_id,
            matched_customer_id=result.matched_customer_id,
            matched_property_id=result.matched_property_id,
            expected_amount=expected_amount,
        )
        
        result.is_valid = validation_result.is_valid
        result.validation_errors = validation_result.errors
        result.validation_warnings = validation_result.warnings
        result.messages.extend(validation_result.messages)
        
        # 6. Son durumu belirle
        if match_result.match_status == "matched" and validation_result.is_valid:
            # Yüksek güven + validasyon başarılı = otomatik onay
            if result.match_confidence >= 90:
                result.status = "approved"
                result.success = True
                result.messages.append("✓ Dekont otomatik olarak onaylandı")
            else:
                result.status = "manual_review"
                result.success = True
                result.messages.append("⚠ Manuel inceleme gerekiyor (orta güven)")
        elif match_result.match_status == "manual_review":
            result.status = "manual_review"
            result.success = True
            result.messages.append("⚠ Manuel inceleme gerekiyor")
        else:
            result.status = "rejected"
            result.messages.append("✗ Dekont reddedildi (eşleştirme/validasyon hatası)")
        
        # Beklenen owner ile eşleşme kontrolü
        if expected_owner_id and result.matched_owner_id:
            if expected_owner_id == result.matched_owner_id:
                result.messages.append("✓ Beklenen mülk sahibi ile eşleşti")
            else:
                result.status = "manual_review"
                result.messages.append(
                    f"⚠ Farklı mülk sahibi tespit edildi "
                    f"(Beklenen: {expected_owner_id}, "
                    f"Tespit: {result.matched_owner_id})"
                )
        
        return result
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """PDF'den metin çıkarır."""
        if not PDF_SUPPORT:
            raise ImportError(
                "PyMuPDF (fitz) yüklü değil. "
                "Yüklemek için: pip install pymupdf"
            )
        
        text_parts = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        
        return "\n".join(text_parts)
    
    def process_multiple_receipts(
        self,
        pdf_paths: List[str | Path],
        expected_amounts: Optional[List[float]] = None,
        expected_owner_ids: Optional[List[int]] = None,
        min_confidence: float = 70.0,
    ) -> List[ReceiptProcessingResult]:
        """
        Birden fazla dekontu toplu olarak işler.
        
        Args:
            pdf_paths: Dekont PDF dosyalarının yolları
            expected_amounts: Beklenen kira tutarları (opsiyonel)
            expected_owner_ids: Beklenen mülk sahibi ID'leri (opsiyonel)
            min_confidence: Minimum eşleştirme güven skoru
        
        Returns:
            List[ReceiptProcessingResult]: İşlem sonuçları listesi
        """
        results = []
        
        for i, pdf_path in enumerate(pdf_paths):
            expected_amount = expected_amounts[i] if expected_amounts else None
            expected_owner_id = expected_owner_ids[i] if expected_owner_ids else None
            
            result = self.process_receipt(
                pdf_path=pdf_path,
                expected_amount=expected_amount,
                expected_owner_id=expected_owner_id,
                min_confidence=min_confidence,
            )
            results.append(result)
        
        return results


__all__ = ["ReceiptProcessor", "ReceiptProcessingResult"]

