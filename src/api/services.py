"""
Business Logic for NLP Processing
Singleton pattern for model management
"""
import json
import logging
from typing import Dict, Optional
from pathlib import Path

# Pipeline import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.full_pipeline import ReceiptPipeline

logger = logging.getLogger(__name__)


class NLPService:
    """
    Singleton NLP Service
    Manages model lifecycle and provides processing methods
    """
    _instance = None
    _pipeline = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLPService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize service (models loaded lazily)"""
        if self._pipeline is None:
            logger.info("NLP Service initialized (models will load on first request)")
    
    def _ensure_pipeline(self, enable_matching: bool = False):
        """Lazy load pipeline on first use"""
        if self._pipeline is None:
            logger.info("🚀 Loading NLP models...")
            self._pipeline = ReceiptPipeline(enable_matching=enable_matching)
            logger.info("✅ NLP models loaded successfully")
    
    def process_pdf(
        self, 
        pdf_path: str, 
        bank: Optional[str] = None,
        enable_matching: bool = False,
        use_logo_detection: bool = False
    ) -> Dict:
        """
        Process PDF receipt
        
        Args:
            pdf_path: Path to PDF file
            bank: Bank name hint (optional)
            enable_matching: Enable receipt matching
            use_logo_detection: Use logo detection for bank
        
        Returns:
            Processing result dict
        """
        try:
            self._ensure_pipeline(enable_matching)
            
            result = self._pipeline.process_from_file(
                pdf_path=pdf_path,
                bank=bank,
                use_logo_detection=use_logo_detection
            )
            
            return result
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}", exc_info=True)
            raise
    
    def process_ocr_output(
        self, 
        ocr_data: Dict,
        enable_matching: bool = False
    ) -> Dict:
        """
        Process OCR output directly
        
        Args:
            ocr_data: OCR extraction result (JSON)
            enable_matching: Enable receipt matching
        
        Returns:
            Processing result dict
        """
        try:
            self._ensure_pipeline(enable_matching)
            
            result = self._pipeline.process_ocr_output(ocr_data)
            
            return result
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}", exc_info=True)
            raise
    
    def health_check(self) -> Dict:
        """Service health check"""
        return {
            'status': 'healthy',
            'models_loaded': self._pipeline is not None,
            'service': 'nlp-receipt-processing',
            'version': '1.0.0'
        }


# Global service instance
nlp_service = NLPService()
