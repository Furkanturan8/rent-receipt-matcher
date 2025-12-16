"""
Full Receipt Processing Pipeline

OCR Output → Intent Classification → NER Extraction → Structured Output

Example OCR Input:
{
  "sender": "FURKAN TURAN",
  "sender_iban": "TR660001200146300002247852",
  "description": "Çiçek Apt. No:8, FURKAN TURAN, Haziran kira ödemesi, 15000 TL",
  "amount": "15000.00",
  "amount_currency": "TRY",
  "date": "20/11/2025 - 21:06",
  "recipient": "Mustafa Derin",
  "receiver_iban": "TR090020200008733123900001"
}
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.nlp.v3.inference_robust import (
    RobustIntentClassifier,
    RobustNERExtractor
)
from src.ocr.extraction.extractor import extract_fields
from src.ocr.extraction.bank_detector import detect_bank_hybrid, detect_bank
from src.ocr.matching.matcher import match_receipt, ReceiptMatchResult
from pdfminer.high_level import extract_text

# Import database loader
try:
    from .database_loader import load_mock_database
except ImportError:
    from src.pipeline.database_loader import load_mock_database


class ReceiptPipeline:
    """
    Full receipt processing pipeline
    
    Combines:
    1. OCR Extraction (Tesseract/PaddleOCR)
    2. Intent Classification (v3 Robust)
    3. NER Extraction (v3 Hybrid: BERT + Regex)
    """
    
    def __init__(self, enable_matching: bool = False, mock_db_path: Optional[str] = None):
        print("🚀 Initializing Receipt Pipeline...")
        print("   Loading NLP models...")
        
        # Load NLP models
        self.intent_classifier = RobustIntentClassifier()
        self.ner_extractor = RobustNERExtractor()
        
        # Load database for matching (optional)
        self.enable_matching = enable_matching
        self.database = None
        
        if enable_matching:
            print("   Loading mock database for matching...")
            try:
                self.database = load_mock_database(mock_db_path)
                print(f"   ✅ Loaded {len(self.database['owners'])} owners, "
                      f"{len(self.database['customers'])} customers, "
                      f"{len(self.database['properties'])} properties")
            except Exception as e:
                print(f"   ⚠️  Failed to load database: {e}")
                self.enable_matching = False
        
        print("   ✅ Models loaded!")
    
    def process_ocr_output(self, ocr_result: Dict) -> Dict:
        """
        Process OCR output through NLP pipeline
        
        Args:
            ocr_result: OCR extraction result (JSON)
        
        Returns:
            Complete structured output
        """
        # Extract description (main text for NLP)
        description = ocr_result.get('description', '')
        
        if not description:
            return {
                'status': 'error',
                'error': 'No description found in OCR output',
                'ocr_data': ocr_result
            }
        
        print(f"\n📝 Processing description:")
        print(f"   {description[:80]}...")
        
        # 1. Intent Classification
        print(f"\n🎯 Running Intent Classification...")
        intent_result = self.intent_classifier.predict(
            description, 
            multi_intent=True
        )
        
        print(f"   Primary Intent: {intent_result['primary_intent']}")
        print(f"   Confidence: {intent_result['confidence']:.2%}")
        
        if intent_result['is_multi_intent']:
            print(f"   🔥 Multi-Intent Detected: {intent_result['detected_intents']}")
        
        # 2. NER Extraction
        print(f"\n🏷️  Running NER Extraction (Hybrid)...")
        ner_result = self.ner_extractor.extract(
            description, 
            use_fallback=True
        )
        
        print(f"   Extracted Entities:")
        for entity_type, value in ner_result['entities_merged'].items():
            method = ner_result['extraction_method'].get(entity_type, 'unknown')
            print(f"      {entity_type:15s}: {value} [{method}]")
        
        # 3. Merge with OCR data
        merged_entities = self._merge_entities(ocr_result, ner_result['entities_merged'])
        
        # 4. Receipt Matching (if enabled)
        matching_result = None
        if self.enable_matching and self.database:
            print(f"\n🔗 Running Receipt Matching...")
            try:
                matching_result = match_receipt(
                    ocr_data=ocr_result,
                    owners=self.database['owners'],
                    customers=self.database['customers'],
                    properties=self.database['properties'],
                    min_confidence=70.0
                )
                
                print(f"   Match Status: {matching_result.match_status}")
                print(f"   Confidence: {matching_result.confidence_score:.1f}%")
                if matching_result.owner_id:
                    print(f"   Matched Owner ID: {matching_result.owner_id}")
                    print(f"   Property ID: {matching_result.property_id}")
                    print(f"   Customer ID: {matching_result.customer_id}")
                
            except Exception as e:
                print(f"   ⚠️  Matching failed: {e}")
        
        # 5. Build structured output
        output = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            
            # OCR Data (original)
            'ocr_data': ocr_result,
            
            # Intent Classification
            'intent': {
                'primary': intent_result['primary_intent'],
                'confidence': round(intent_result['confidence'], 4),
                'all_intents': [
                    {
                        'intent': intent,
                        'confidence': round(conf, 4)
                    }
                    for intent, conf in intent_result['all_intents']
                ],
                'is_multi_intent': intent_result['is_multi_intent'],
                'detected_intents': intent_result['detected_intents']
            },
            
            # NER Extraction
            'ner': {
                'entities': ner_result['entities_merged'],
                'extraction_method': ner_result['extraction_method'],
                'bert_entities': ner_result['entities_bert'],
                'regex_entities': ner_result['entities_regex']
            },
            
            # Merged/Final Entities
            'final_entities': merged_entities,
            
            # Summary
            'summary': self._generate_summary(
                intent_result,
                merged_entities,
                ocr_result
            )
        }
        
        # Add matching result if available
        if matching_result:
            output['matching'] = {
                'status': matching_result.match_status,
                'confidence': round(matching_result.confidence_score, 2),
                'owner_id': matching_result.owner_id,
                'customer_id': matching_result.customer_id,
                'property_id': matching_result.property_id,
                'scores': {
                    'iban': round(matching_result.iban_match_score, 2),
                    'amount': round(matching_result.amount_match_score, 2),
                    'name': round(matching_result.name_match_score, 2),
                    'address': round(matching_result.address_match_score, 2),
                    'sender': round(matching_result.sender_match_score, 2)
                },
                'messages': matching_result.messages
            }
        
        return output
    
    def _merge_entities(self, ocr_data: Dict, ner_entities: Dict) -> Dict:
        """
        Merge OCR data with NER entities
        
        Priority: OCR > NER (OCR more reliable for structured fields)
        """
        merged = {}
        
        # From OCR (high confidence)
        if ocr_data.get('sender'):
            merged['sender'] = ocr_data['sender']
        elif 'sender' in ner_entities:
            merged['sender'] = ner_entities['sender']
        
        if ocr_data.get('sender_iban'):
            merged['sender_iban'] = ocr_data['sender_iban']
        elif 'sender_iban' in ner_entities:
            merged['sender_iban'] = ner_entities['sender_iban']
        
        if ocr_data.get('recipient'):
            merged['receiver'] = ocr_data['recipient']
        elif 'receiver' in ner_entities:
            merged['receiver'] = ner_entities['receiver']
        
        if ocr_data.get('receiver_iban'):
            merged['receiver_iban'] = ocr_data['receiver_iban']
        elif 'receiver_iban' in ner_entities:
            merged['receiver_iban'] = ner_entities['receiver_iban']
        
        if ocr_data.get('amount'):
            merged['amount'] = ocr_data['amount']
            merged['amount_currency'] = ocr_data.get('amount_currency', 'TRY')
        elif 'amount' in ner_entities:
            merged['amount'] = ner_entities['amount']
        
        if ocr_data.get('date'):
            merged['date'] = ocr_data['date']
        elif 'date' in ner_entities:
            merged['date'] = ner_entities['date']
        
        # From NER only (not in OCR)
        ner_only_fields = ['apt_no', 'period', 'bank', 'transaction_type', 'fee']
        for field in ner_only_fields:
            if field in ner_entities:
                merged[field] = ner_entities[field]
        
        return merged
    
    def _generate_summary(self, intent_result: Dict, entities: Dict, ocr_data: Dict) -> str:
        """
        Generate human-readable summary
        """
        intent = intent_result['primary_intent']
        
        intent_names = {
            'kira_odemesi': 'Kira Ödemesi',
            'aidat_odemesi': 'Aidat Ödemesi',
            'kapora_odemesi': 'Kapora Ödemesi',
            'depozito_odemesi': 'Depozito Ödemesi'
        }
        
        summary_parts = [f"📋 {intent_names.get(intent, intent.upper())}"]
        
        if entities.get('sender'):
            summary_parts.append(f"👤 Gönderen: {entities['sender']}")
        
        if entities.get('receiver'):
            summary_parts.append(f"👤 Alıcı: {entities['receiver']}")
        
        if entities.get('amount'):
            currency = entities.get('amount_currency', 'TRY')
            summary_parts.append(f"💰 Tutar: {entities['amount']} {currency}")
        
        if entities.get('apt_no'):
            summary_parts.append(f"🏠 Daire: {entities['apt_no']}")
        
        if entities.get('period'):
            summary_parts.append(f"📅 Dönem: {entities['period']}")
        
        if entities.get('date'):
            summary_parts.append(f"📆 Tarih: {entities['date']}")
        
        if intent_result['is_multi_intent']:
            summary_parts.append(f"🔥 Karışık Ödeme: {', '.join(intent_result['detected_intents'])}")
        
        return " | ".join(summary_parts)
    
    def process_from_file(self, pdf_path: str, bank: str = None, output_path: Optional[str] = None, use_logo_detection: bool = False) -> Dict:
        """
        Full pipeline from PDF file
        
        Args:
            pdf_path: Path to PDF receipt
            bank: Bank name hint (halkbank, kuveytturk, yapikredi, ziraatbank). If None, auto-detect.
            output_path: Optional output JSON path
            use_logo_detection: Use hybrid bank detection (text + logo)
        
        Returns:
            Structured output
        """
        print(f"📄 Processing receipt: {pdf_path}")
        
        # 1. OCR Extraction
        print(f"\n🔍 Step 1/3: OCR Text Extraction...")
        try:
            # Extract text from PDF
            text = extract_text(pdf_path)
            
            if not text or not text.strip():
                raise ValueError("PDF'den metin çıkarılamadı. Dosya boş veya okunamaz olabilir.")
            
            print(f"   ✅ Text extracted ({len(text)} characters)")
            
            # Auto-detect bank if not provided
            if not bank:
                print(f"\n🔍 Auto-detecting bank...")
                if use_logo_detection:
                    bank = detect_bank_hybrid(text, pdf_path=pdf_path)
                    print(f"   ℹ️  Method: Hybrid (text + logo)")
                else:
                    bank = detect_bank(text)
                    print(f"   ℹ️  Method: Text-based")
                
                if bank:
                    print(f"   ✅ Detected bank: {bank}")
                else:
                    print(f"   ⚠️  Bank could not be detected, using generic patterns")
            else:
                print(f"🏦 Bank (provided): {bank}")
            
            # Extract structured fields using regex patterns
            print(f"\n🔍 Step 2/3: Field Extraction...")
            ocr_result = extract_fields(text, bank_hint=bank)
            
            if not ocr_result:
                raise ValueError("OCR'dan hiçbir alan çıkarılamadı.")
            
            print(f"   ✅ Extracted {len(ocr_result)} fields")
            for field, value in ocr_result.items():
                if value:
                    print(f"      • {field}: {value[:50]}..." if len(str(value)) > 50 else f"      • {field}: {value}")
            
        except Exception as e:
            print(f"\n❌ OCR Extraction failed: {e}")
            raise
        
        # 2. NLP Processing (Intent + NER)
        print(f"\n🔍 Step 3/3: NLP Processing...")
        result = self.process_ocr_output(ocr_result)
        
        # 3. Save output
        if output_path:
            print(f"\n💾 Saving to: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"   ✅ Saved successfully")
        
        return result
    
    def process_from_ocr_json(self, ocr_json_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Process from OCR JSON output file
        
        Args:
            ocr_json_path: Path to OCR output JSON
            output_path: Optional output path
        
        Returns:
            Structured output
        """
        print(f"📂 Loading OCR output: {ocr_json_path}")
        
        with open(ocr_json_path, 'r', encoding='utf-8') as f:
            ocr_result = json.load(f)
        
        # Process
        result = self.process_ocr_output(ocr_result)
        
        # Save if output path provided
        if output_path:
            print(f"\n💾 Saving result to: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"   ✅ Saved!")
        
        return result


def demo():
    """Demo with example OCR output"""
    
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     🚀 FULL RECEIPT PROCESSING PIPELINE - DEMO           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    # Example OCR outputs
    test_cases = [
        {
            "name": "Kira Ödemesi - Çiçek Apt",
            "ocr_output": {
                "sender": "FURKAN TURAN",
                "sender_iban": "TR660001200146300002247852",
                "description": "Çiçek Apt. No:8, FURKAN TURAN, Haziran kira ödemesi, 15000 TL",
                "amount": "15000.00",
                "amount_currency": "TRY",
                "date": "20/11/2025 - 21:06",
                "recipient": "Mustafa Derin",
                "receiver_iban": "TR090020200008733123900001"
            }
        },
        {
            "name": "Aidat Ödemesi",
            "ocr_output": {
                "sender": "FATİH DİNDAR",
                "sender_iban": "TR540001200146300001147858",
                "description": "ÇALIK-2 APART DAİRE 9 Haziran ayı aidat ödemesi",
                "amount": "500.00",
                "amount_currency": "TRY",
                "date": "01/06/2025",
                "recipient": "SITE YÖNETİMİ",
                "receiver_iban": "TR290070500000609138100006"
            }
        },
        {
            "name": "Karışık Ödeme (Kira + Depozito)",
            "ocr_output": {
                "sender": "ALİ YILMAZ",
                "sender_iban": "TR110001200146300001147858",
                "description": "Daire 5 Ağustos kira, yarım depozito 8000, 4000 toplam 12BIN TL",
                "amount": "12000.00",
                "amount_currency": "TRY",
                "date": "01/08/2024",
                "recipient": "MEHMET DEMİR",
                "receiver_iban": "TR330020200008733123900001"
            }
        }
    ]
    
    # Initialize pipeline
    pipeline = ReceiptPipeline()
    
    # Process each test case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"[TEST {i}] {test_case['name']}")
        print(f"{'='*70}")
        
        result = pipeline.process_ocr_output(test_case['ocr_output'])
        
        if result['status'] == 'success':
            print(f"\n✅ PROCESSING SUCCESSFUL")
            print(f"\n📋 SUMMARY:")
            print(f"   {result['summary']}")
            
            print(f"\n🎯 INTENT:")
            print(f"   Primary: {result['intent']['primary']} ({result['intent']['confidence']:.2%})")
            
            if result['intent']['is_multi_intent']:
                print(f"   🔥 Multi-Intent: {result['intent']['detected_intents']}")
            
            print(f"\n🏷️  FINAL ENTITIES:")
            for key, value in result['final_entities'].items():
                print(f"      {key:15s}: {value}")
        else:
            print(f"\n❌ ERROR: {result.get('error')}")
        
        print(f"\n{'─'*70}")


if __name__ == "__main__":
    demo()
