"""
v4 Inference - Production Ready with OCR Correction
====================================================

Yeni Özellikler:
1. OCR Post-processing (I→1, O→0 düzeltme)
2. Token birleştirme düzeltmesi
3. TITLE entity desteği
4. Multi-period support
5. Hybrid NER (BERT + Regex)

Fixes:
- ✅ Subword token birleştirme sorunu çözüldü
- ✅ OCR hatalarını düzelt (description'da I→1, O→0)
- ✅ TITLE entity eklendi (FEE kaldırıldı)
"""

import re
import json
import torch
from typing import Dict, List, Tuple, Optional
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification
)


def correct_ocr_errors(text: str) -> str:
    """
    OCR hatalarını düzelt
    
    Düzeltmeler:
    - Sayı context'inde: I→1, O→0, l→1
    - Harf context'inde: 1→I, 0→O
    """
    # Pattern: Sayılarla çevrili I, O, l karakterleri
    
    # "I4" → "14", "2O25" → "2025"
    text = re.sub(r'I(\d)', r'1\1', text)  # I4 → 14
    text = re.sub(r'(\d)I', r'\g<1>1', text)  # 4I → 41
    text = re.sub(r'O(\d)', r'0\1', text)  # O5 → 05
    text = re.sub(r'(\d)O', r'\g<1>0', text)  # 5O → 50
    text = re.sub(r'l(\d)', r'1\1', text)  # l4 → 14
    
    # "I4O" → "140"
    text = re.sub(r'I(\d+)O', r'1\g<1>0', text)  # I40 → 140
    
    # Tarih format: "I2.I2.2O25" → "12.12.2025"
    text = re.sub(r'I(\d)\.I(\d)\.2O(\d{2})', r'1\1.1\2.20\3', text)
    
    return text


class RobustIntentClassifier:
    """
    v4 Intent Classifier with OCR correction
    """
    
    def __init__(self, model_path: str = "models/v4_production/intent_classifier/final"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        self.id_to_label = {
            0: "kira_odemesi",
            1: "aidat_odemesi",
            2: "kapora_odemesi",
            3: "depozito_odemesi"
        }
        
        # Multi-intent keywords (expanded for better coverage)
        self.intent_keywords = {
            'kira_odemesi': [
                'kira', 'konut', 'mesken', 'ev', 'kra',
                'aylık ödeme', 'kira bedeli', 'kira ödemesi',
                'aylık', 'kira tutarı'
            ],
            'aidat_odemesi': [
                'aidat', 'site', 'yönetim', 'aydat', 'adat',
                'ortak gider', 'apartman aidatı', 'site aidatı',
                'yönetim gideri', 'ortak gider ödemesi'
            ],
            'kapora_odemesi': ['kapora', 'avans', 'teminat', 'kapara', 'kapro'],
            'depozito_odemesi': ['depozito', 'güvence', 'depo', 'dpozit', 'depozit']
        }
        
        # Context patterns (for cases without explicit keywords)
        self.context_patterns = {
            'kira_odemesi': [
                r'(apartmanı|rezidans|sitesi).*?(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)',
                r'(daire|d:?\d+).*?(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)',
            ],
            'aidat_odemesi': [
                r'(apartman|site|rezidans).*?(aidat|ortak gider)',
            ]
        }
    
    def preprocess(self, text: str) -> str:
        """Text preprocessing with OCR correction and noise removal"""
        # 1. OCR correction
        text = correct_ocr_errors(text)
        
        # 2. Remove noise that confuses intent classification
        # Remove dates (e.g., "12.12.2025 :")
        text = re.sub(r'\d{1,2}\.\d{1,2}\.\d{4}\s*:?\s*', '', text)
        # Remove IBAN-like patterns
        text = re.sub(r'TR\d{24}', '', text)
        # Remove standalone numbers (amounts, dates)
        # But keep numbers that are part of intent keywords (e.g., "No:14")
        text = re.sub(r'\b\d{4,}\b', '', text)  # Remove long numbers (years, amounts)
        
        # 3. Lowercase
        text = text.lower()
        
        # 4. Clean up extra spaces
        text = ' '.join(text.split())
        
        return text
    
    def predict(self, text: str, multi_intent: bool = True) -> Dict:
        """
        Intent classification
        
        Returns:
            {
                'primary_intent': str,
                'confidence': float,
                'all_intents': List[Tuple[str, float]],
                'detected_intents': List[str],
                'is_multi_intent': bool
            }
        """
        # Preprocess
        text_processed = self.preprocess(text)
        
        # Tokenize
        inputs = self.tokenizer(
            text_processed,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128
        )
        
        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
        
        # Primary intent
        predicted_class = torch.argmax(probs).item()
        primary_intent = self.id_to_label[predicted_class]
        confidence = probs[predicted_class].item()
        
        # All intents
        all_intents = [
            (self.id_to_label[i], probs[i].item())
            for i in range(len(probs))
        ]
        all_intents.sort(key=lambda x: x[1], reverse=True)
        
        # Keyword-based confidence boosting
        # If primary intent has strong keyword match, boost confidence
        if confidence < 0.7:  # Only boost if confidence is low
            for intent, keywords in self.intent_keywords.items():
                if intent == primary_intent:
                    # Check if strong keywords exist
                    strong_keywords = [kw for kw in keywords if kw in text_processed]
                    if strong_keywords:
                        # Boost confidence by 10-20% (capped at 0.95)
                        boost = min(0.2, len(strong_keywords) * 0.1)
                        confidence = min(0.95, confidence + boost)
                        # Update in all_intents list
                        for i, (intent_name, conf) in enumerate(all_intents):
                            if intent_name == primary_intent:
                                all_intents[i] = (intent_name, confidence)
                                break
                        break
        
        # Context-based boosting (if no strong keywords found)
        # Special case: "apartmanı" + month but no "aidat" → likely kira
        months = ['ocak', 'şubat', 'mart', 'nisan', 'mayıs', 'haziran', 
                  'temmuz', 'ağustos', 'eylül', 'ekim', 'kasım', 'aralık']
        has_month = any(month in text_processed for month in months)
        has_apartman = 'apartman' in text_processed or 'rezidans' in text_processed
        has_aidat_keyword = any(kw in text_processed for kw in ['aidat', 'ortak gider', 'yönetim'])
        
        if has_apartman and has_month and not has_aidat_keyword:
            # Strong pattern: apartman + month but no aidat keyword → likely kira
            # Find kira_odemesi in all_intents
            kira_idx = None
            for i, (intent_name, conf) in enumerate(all_intents):
                if intent_name == 'kira_odemesi':
                    kira_idx = i
                    break
            
            if kira_idx is not None:
                # Aggressively boost kira to be primary
                kira_conf = all_intents[kira_idx][1]
                boosted_conf = min(0.95, max(0.80, kira_conf + 0.30))  # Strong boost, capped at 0.95
                all_intents[kira_idx] = ('kira_odemesi', boosted_conf)
                
                # Re-sort and update primary
                all_intents.sort(key=lambda x: x[1], reverse=True)
                if all_intents[0][0] == 'kira_odemesi':
                    primary_intent = 'kira_odemesi'
                    confidence = boosted_conf
        
        # Check if context patterns match but confidence is still low
        if confidence < 0.6:
            for intent, patterns in self.context_patterns.items():
                if intent == primary_intent:
                    # Check if context patterns match
                    for pattern in patterns:
                        if re.search(pattern, text_processed, re.IGNORECASE):
                            # Boost confidence by 15% (context match)
                            confidence = min(0.90, confidence + 0.15)
                            # Update in all_intents list
                            for i, (intent_name, conf) in enumerate(all_intents):
                                if intent_name == primary_intent:
                                    all_intents[i] = (intent_name, confidence)
                                    break
                            break
                    break
        
        # Final cap: ensure confidence never exceeds 1.0
        confidence = min(1.0, confidence)
        # Update primary intent confidence in all_intents
        for i, (intent_name, conf) in enumerate(all_intents):
            if intent_name == primary_intent:
                all_intents[i] = (intent_name, confidence)
                break
        
        # Multi-intent detection
        detected_intents = [primary_intent]
        
        if multi_intent and confidence < 0.75:
            for intent, keywords in self.intent_keywords.items():
                if intent != primary_intent:
                    for keyword in keywords:
                        if keyword in text_processed:
                            detected_intents.append(intent)
                            break
        
        return {
            'primary_intent': primary_intent,
            'confidence': confidence,
            'all_intents': all_intents,
            'detected_intents': list(set(detected_intents)),
            'is_multi_intent': len(detected_intents) > 1
        }


class RobustNERExtractor:
    """
    v4 NER Extractor with:
    - OCR correction
    - Proper token merging (FIX for subword issue)
    - TITLE entity support
    - Multi-period support
    """
    
    def __init__(self, model_path: str = "models/v4_production/ner/final"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        
        # v4 Label mapping (11 entities: FEE removed, TITLE added)
        self.id2label = {
            0: 'O',
            1: 'B-SENDER', 2: 'I-SENDER',
            3: 'B-RECEIVER', 4: 'I-RECEIVER',
            5: 'B-AMOUNT', 6: 'I-AMOUNT',
            7: 'B-DATE', 8: 'I-DATE',
            9: 'B-SENDER_IBAN', 10: 'I-SENDER_IBAN',
            11: 'B-RECEIVER_IBAN', 12: 'I-RECEIVER_IBAN',
            13: 'B-BANK', 14: 'I-BANK',
            15: 'B-TRANSACTION_TYPE', 16: 'I-TRANSACTION_TYPE',
            17: 'B-PERIOD', 18: 'I-PERIOD',
            19: 'B-APT_NO', 20: 'I-APT_NO',
            21: 'B-TITLE', 22: 'I-TITLE',  # NEW!
        }
        
        # Regex patterns for fallback
        self.patterns = {
            'sender': [
                r'Gönderen:\s*([A-ZĞÜŞİÖÇ][A-ZĞÜŞİÖÇa-zğüşiöç\s]+)',
                r'([A-ZĞÜŞİÖÇ]{2,}\s+[A-ZĞÜŞİÖÇ]{2,})',
            ],
            'receiver': [
                r'Alıcı:\s*([A-ZĞÜŞİÖÇ\*\s]+)',
                r'([A-Z]{2,}\*+\s*[A-Z]{2,}\*+)',
            ],
            'apt_no': [
                r'(?:DAİRE|daire|DAYRE|dayre|NO\.?|no\.?|d:|d)\s*[:-]?\s*(\d+)',
                r'daire(\d+)',
            ],
            'amount': [
                r'(\d+[\.,]?\d*)\s*(?:TL|TRY|tl|try)',
                r'(\d+)\s*(?:bin|BİN|BIN)\s*(?:tl|TL)',
                r'(\d+)(?:bin|BİN)(?:tl|TL)',
                r'(\d{3,}(?:[.,]\d{2})?)',
            ],
            'period': [
                r'(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)',
                r'(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|agustos|eylül|ekim|kasım|aralık)',
            ],
            'title': [
                r'([A-ZĞÜŞİÖÇ][a-zğüşiöç]+[-\s]?\d*\s+(?:Apart|Apartmanı|Sitesi|Rezidans|Evleri))',
                r'([A-ZĞÜŞİÖÇ]+[-\s]?\d+\s+(?:APART|SİTE|REZIDANS))',
            ],
            'iban': [
                r'(TR\d{24})',
            ]
        }
    
    def preprocess(self, text: str) -> str:
        """Preprocess with OCR correction"""
        return correct_ocr_errors(text)
    
    def extract_bert(self, text: str) -> Dict[str, List[tuple]]:
        """
        BERT entity extraction with PROPER token merging + CONFIDENCE
        
        Returns: {entity_type: [(value, confidence), ...]}
        """
        import torch.nn.functional as F
        
        # Preprocess
        text = self.preprocess(text)
        text_lower = text.lower()
        
        inputs = self.tokenizer(
            text_lower,
            return_tensors="pt",
            truncation=True,
            max_length=256
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Get probabilities (confidence scores)
            probabilities = F.softmax(outputs.logits, dim=-1)[0]
            predictions = torch.argmax(outputs.logits, dim=-1)[0]
        
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        entities = {}
        current_entity = None
        current_tokens = []
        current_confidences = []
        
        for idx, (token, pred_id) in enumerate(zip(tokens, predictions)):
            if token in ['[CLS]', '[SEP]', '[PAD]']:
                continue
            
            label = self.id2label[pred_id.item()]
            # Get confidence for this prediction
            token_confidence = probabilities[idx][pred_id.item()].item()
            
            if label.startswith('B-'):
                # Save previous entity
                if current_entity and current_tokens:
                    entity_type = current_entity.replace('B-', '')
                    entity_value = self.tokenizer.convert_tokens_to_string(current_tokens).strip()
                    # Average confidence for multi-token entities
                    avg_confidence = sum(current_confidences) / len(current_confidences) if current_confidences else token_confidence
                    
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].append((entity_value, avg_confidence))
                
                # Start new entity
                current_entity = label
                current_tokens = [token]
                current_confidences = [token_confidence]
            
            elif label.startswith('I-') and current_entity:
                if label.replace('I-', '') == current_entity.replace('B-', ''):
                    current_tokens.append(token)
                    current_confidences.append(token_confidence)
            
            else:  # 'O'
                if current_entity and current_tokens:
                    entity_type = current_entity.replace('B-', '')
                    entity_value = self.tokenizer.convert_tokens_to_string(current_tokens).strip()
                    avg_confidence = sum(current_confidences) / len(current_confidences) if current_confidences else 0.0
                    
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].append((entity_value, avg_confidence))
                
                current_entity = None
                current_tokens = []
                current_confidences = []
        
        # Save last entity
        if current_entity and current_tokens:
            entity_type = current_entity.replace('B-', '')
            entity_value = self.tokenizer.convert_tokens_to_string(current_tokens).strip()
            avg_confidence = sum(current_confidences) / len(current_confidences) if current_confidences else 0.0
            
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].append((entity_value, avg_confidence))
        
        return entities
    
    def extract_regex(self, text: str) -> Dict[str, tuple]:
        """
        Regex extraction with CONFIDENCE scoring
        
        Returns: {entity_type: (value, confidence)}
        Confidence based on:
        - Exact case match: 1.0
        - Case-insensitive match: 0.9
        - Pattern specificity: 0.8-0.95
        """
        text = self.preprocess(text)
        entities = {}
        
        for entity_type, patterns in self.patterns.items():
            best_match = None
            best_confidence = 0.0
            
            for pattern in patterns:
                # Try exact case first (higher confidence)
                match_exact = re.search(pattern, text)
                if match_exact:
                    confidence = 1.0  # Exact match
                    if entity_type == 'period':
                        value = match_exact.group(1)
                    else:
                        value = match_exact.group(1)
                    
                    if confidence > best_confidence:
                        best_match = value
                        best_confidence = confidence
                    break  # Exact match found, use it
                
                # Try case-insensitive (lower confidence)
                match_ci = re.search(pattern, text, re.IGNORECASE)
                if match_ci:
                    confidence = 0.9  # Case-insensitive match
                    if entity_type == 'period':
                        value = match_ci.group(1)
                    else:
                        value = match_ci.group(1)
                    
                    if confidence > best_confidence:
                        best_match = value
                        best_confidence = confidence
            
            if best_match:
                entities[entity_type] = (best_match, best_confidence)
        
        return entities
    
    def extract(self, text: str, use_fallback: bool = True) -> Dict:
        """
        Hybrid extraction: BERT + Regex with CONFIDENCE-BASED selection
        
        Returns:
            {
                'entities_bert': Dict,
                'entities_regex': Dict,
                'entities_merged': Dict,
                'extraction_method': Dict,
                'confidence_scores': Dict
            }
        """
        # BERT extraction (with confidence)
        entities_bert_raw = self.extract_bert(text)
        
        # Convert BERT format: {type: [(value, conf), ...]} -> {type: (value, conf)}
        entities_bert = {}
        for entity_type, values in entities_bert_raw.items():
            if values:
                # Take the first (best) result
                value, confidence = values[0]
                # Filter invalid values
                if isinstance(value, str) and len(value) > 1 and not value.startswith('##'):
                    entities_bert[entity_type] = (value, confidence)
        
        # Regex extraction (with confidence)
        entities_regex = self.extract_regex(text) if use_fallback else {}
        
        # Merge with CONFIDENCE-BASED selection
        entities_merged = {}
        extraction_method = {}
        confidence_scores = {}
        
        # Critical entities: Choose based on confidence
        critical_entities = ['SENDER', 'AMOUNT', 'APT_NO', 'PERIOD', 'TITLE']
        
        for entity_type in critical_entities:
            entity_lower = entity_type.lower()
            
            regex_result = entities_regex.get(entity_lower)
            bert_result = entities_bert.get(entity_type)
            
            # Both found: Compare confidence
            if regex_result and bert_result:
                regex_value, regex_conf = regex_result
                bert_value, bert_conf = bert_result
                
                if regex_conf >= bert_conf:
                    # REGEX has higher or equal confidence
                    entities_merged[entity_lower] = regex_value
                    extraction_method[entity_lower] = 'regex'
                    confidence_scores[entity_lower] = regex_conf
                else:
                    # BERT has higher confidence
                    entities_merged[entity_lower] = bert_value
                    extraction_method[entity_lower] = 'bert'
                    confidence_scores[entity_lower] = bert_conf
            
            # Only REGEX found
            elif regex_result:
                regex_value, regex_conf = regex_result
                entities_merged[entity_lower] = regex_value
                extraction_method[entity_lower] = 'regex'
                confidence_scores[entity_lower] = regex_conf
            
            # Only BERT found
            elif bert_result:
                bert_value, bert_conf = bert_result
                entities_merged[entity_lower] = bert_value
                extraction_method[entity_lower] = 'bert'
                confidence_scores[entity_lower] = bert_conf
        
        # Other entities (BERT only, or REGEX if available)
        for entity_type, bert_result in entities_bert.items():
            entity_lower = entity_type.lower()
            if entity_lower not in entities_merged:
                bert_value, bert_conf = bert_result
                entities_merged[entity_lower] = bert_value
                extraction_method[entity_lower] = 'bert'
                confidence_scores[entity_lower] = bert_conf
        
        # IBAN from regex (if not already set)
        if 'iban' in entities_regex and 'receiver_iban' not in entities_merged:
            iban_value, iban_conf = entities_regex['iban']
            entities_merged['receiver_iban'] = iban_value
            extraction_method['receiver_iban'] = 'regex'
            confidence_scores['receiver_iban'] = iban_conf
        
        # Filter out unwanted entities (no need to retrain model!)
        excluded_entities = ['transaction_type', 'bank']
        for entity in excluded_entities:
            entities_merged.pop(entity, None)
            extraction_method.pop(entity, None)
            confidence_scores.pop(entity, None)
        
        return {
            'entities_bert': {k: v[0] if isinstance(v, tuple) else v for k, v in entities_bert.items() if k.lower() not in excluded_entities},
            'entities_regex': {k: v[0] if isinstance(v, tuple) else v for k, v in entities_regex.items() if k.lower() not in excluded_entities},
            'entities_merged': entities_merged,
            'extraction_method': extraction_method,
            'confidence_scores': confidence_scores
        }


def demo():
    """Demo with OCR errors"""
    
    print("🚀 v4 INFERENCE - OCR CORRECTION DEMO\n")
    print("=" * 70)
    
    # Test cases with OCR errors
    test_cases = [
        {
            "description": "I2.I2.2O25 : Furkan Turan, Çiçek Apartmanı No:I4, Kasım ayı Kirası, I4O TL",
            "note": "OCR hatası: I→1, O→0"
        },
        {
            "description": "24bintl kasım aralık çalık2 d2",
            "note": "Boşluksuz, çoklu ay"
        },
        {
            "description": "dpozit 20bin gül 3 apartmanı jasim",
            "note": "Typo: dpozit, jasim"
        },
    ]
    
    print("📥 Modeller yükleniyor...")
    intent_clf = RobustIntentClassifier()
    ner = RobustNERExtractor()
    print("✅ Hazır!\n")
    print("=" * 70)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test['note']}")
        print(f"📝 Original: {test['description']}")
        
        # OCR correction preview
        corrected = correct_ocr_errors(test['description'])
        if corrected != test['description']:
            print(f"✅ Corrected: {corrected}")
        
        # Intent
        intent_result = intent_clf.predict(test['description'])
        print(f"\n🎯 INTENT:")
        print(f"   {intent_result['primary_intent']} ({intent_result['confidence']:.2%})")
        if intent_result['is_multi_intent']:
            print(f"   Multi: {intent_result['detected_intents']}")
        
        # NER
        ner_result = ner.extract(test['description'])
        print(f"\n🏷️  ENTITIES:")
        for entity, value in ner_result['entities_merged'].items():
            method = ner_result['extraction_method'].get(entity, 'unknown')
            # ✅ Value artık string olmalı (liste değil)
            print(f"   {entity:15s}: {value} [{method}]")
        
        print("\n" + "-" * 70)


if __name__ == "__main__":
    demo()

