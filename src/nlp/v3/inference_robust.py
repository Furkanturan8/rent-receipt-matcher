"""
v3 Robust Inference - Gerçek Data için İyileştirilmiş

Bu script:
- Case-insensitive preprocessing
- Rule-based fallback extraction
- Multi-intent detection
- Hybrid NER (BERT + Regex)
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


class RobustIntentClassifier:
    """
    Gerçek data için geliştirilmiş Intent Classifier
    """
    
    def __init__(self, model_path: str = "models/v3_robust/intent_classifier/final"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        self.id_to_label = {
            0: "kira_odemesi",
            1: "aidat_odemesi",
            2: "kapora_odemesi",
            3: "depozito_odemesi"
        }
        
        # Multi-intent detection için keywords
        self.intent_keywords = {
            'kira_odemesi': ['kira', 'konut', 'mesken', 'ev'],
            'aidat_odemesi': ['aidat', 'site', 'yönetim'],
            'kapora_odemesi': ['kapora', 'avans', 'teminat'],
            'depozito_odemesi': ['depozito', 'güvence', 'yarım depozito', 'yarim depozito']
        }
    
    def preprocess(self, text: str) -> str:
        """Text'i normalize et - case insensitive"""
        # Lowercase'e çevir (model büyük/küçük harf farkını görmez)
        return text.lower()
    
    def predict(self, text: str, multi_intent: bool = True) -> Dict:
        """
        Intent classification
        
        Args:
            text: Dekont açıklaması
            multi_intent: Birden fazla intent tespit et
        
        Returns:
            {
                'primary_intent': str,
                'confidence': float,
                'all_intents': List[Tuple[str, float]],
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
        
        # Multi-intent detection (düşük güven + keyword var)
        detected_intents = [primary_intent]
        
        if multi_intent and confidence < 0.75:
            # Keyword-based detection
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
    Gerçek data için geliştirilmiş NER Extractor (Hybrid: BERT + Regex)
    """
    
    def __init__(self, model_path: str = "models/v3_robust/ner/final"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        
        # Label mapping (11 entities, BIO format = 23 labels)
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
            17: 'B-FEE', 18: 'I-FEE',
            19: 'B-PERIOD', 20: 'I-PERIOD',
            21: 'B-APT_NO', 22: 'I-APT_NO'
        }
        
        # Regex patterns for fallback
        self.patterns = {
            'sender': [
                r'Gönderen:\s*([A-ZĞÜŞİÖÇ][A-ZĞÜŞİÖÇa-zğüşiöç\s]+)',
                r'([A-ZĞÜŞİÖÇ]{2,}\s+[A-ZĞÜŞİÖÇ]{2,})',  # "FATİH DİNDAR"
                r'([A-ZĞÜŞİÖÇa-zğüşiöç]+\s+[A-ZĞÜŞİÖÇa-zğüşiöç]+)(?=\s+DAİRE|\s+daire)',
            ],
            'receiver': [
                r'Alıcı:\s*([A-ZĞÜŞİÖÇ\*\s]+)',
                r'([A-Z]{2,}\*+\s*[A-Z]{2,}\*+)',
            ],
            'apt_no': [
                r'(?:DAİRE|daire|DAYRE|dayre|NO\.?|no\.?)\s*[:-]?\s*(\d+)',
                r'daire(\d+)',
            ],
            'amount': [
                r'(\d+[\.,]?\d*)\s*(?:TL|TRY|tl|try)',
                r'(\d+)\s*(?:bin|BİN|BIN)\s*(?:tl|TL)',
                r'(\d+)(?:bin|BİN)(?:tl|TL)',
                r'(\d{3,}(?:[.,]\d{2})?)',
            ],
            'period': [
                r'(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s*(\d{4})?',
                r'(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|agustos|eylül|ekim|kasım|aralık)\s*(\d{4})?',
            ],
            'iban': [
                r'(TR\d{24})',
            ]
        }
    
    def extract_bert(self, text: str) -> Dict[str, List[str]]:
        """BERT modeli ile entity extraction"""
        # Lowercase for consistency
        text_lower = text.lower()
        
        inputs = self.tokenizer(
            text_lower,
            return_tensors="pt",
            truncation=True,
            max_length=128
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)[0]
        
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        entities = {}
        current_entity = None
        current_text = []
        
        for token, pred_id in zip(tokens, predictions):
            if token in ['[CLS]', '[SEP]', '[PAD]']:
                continue
            
            label = self.id2label[pred_id.item()]
            
            if label.startswith('B-'):
                # Save previous entity
                if current_entity and current_text:
                    entity_type = current_entity.replace('B-', '')
                    entity_value = self.tokenizer.convert_tokens_to_string(current_text).strip()
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].append(entity_value)
                
                # Start new entity
                current_entity = label
                current_text = [token]
            
            elif label.startswith('I-') and current_entity:
                if label.replace('I-', '') == current_entity.replace('B-', ''):
                    current_text.append(token)
            
            else:  # 'O'
                if current_entity and current_text:
                    entity_type = current_entity.replace('B-', '')
                    entity_value = self.tokenizer.convert_tokens_to_string(current_text).strip()
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].append(entity_value)
                
                current_entity = None
                current_text = []
        
        # Save last entity
        if current_entity and current_text:
            entity_type = current_entity.replace('B-', '')
            entity_value = self.tokenizer.convert_tokens_to_string(current_text).strip()
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].append(entity_value)
        
        return entities
    
    def extract_regex(self, text: str) -> Dict[str, Optional[str]]:
        """Regex ile entity extraction (fallback)"""
        entities = {}
        
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if entity_type == 'period' and len(match.groups()) > 1:
                        # Combine month + year
                        period = match.group(1)
                        if match.group(2):
                            period += f" {match.group(2)}"
                        entities[entity_type] = period
                    else:
                        entities[entity_type] = match.group(1)
                    break
        
        return entities
    
    def extract(self, text: str, use_fallback: bool = True) -> Dict[str, any]:
        """
        Hybrid extraction: BERT + Regex fallback
        
        Args:
            text: Dekont açıklaması
            use_fallback: Regex fallback kullan
        
        Returns:
            {
                'entities_bert': Dict[str, List[str]],
                'entities_regex': Dict[str, str],
                'entities_merged': Dict[str, str],
                'extraction_method': Dict[str, str]
            }
        """
        # BERT extraction
        entities_bert = self.extract_bert(text)
        
        # Regex extraction (fallback)
        entities_regex = self.extract_regex(text) if use_fallback else {}
        
        # Merge: BERT first, then regex fallback
        entities_merged = {}
        extraction_method = {}
        
        # Critical entities için fallback
        critical_entities = ['SENDER', 'AMOUNT', 'APT_NO', 'PERIOD']
        
        for entity_type in critical_entities:
            entity_lower = entity_type.lower()
            
            # BERT'ten al
            if entity_type in entities_bert and entities_bert[entity_type]:
                entities_merged[entity_lower] = entities_bert[entity_type][0]
                extraction_method[entity_lower] = 'bert'
            # Regex fallback
            elif entity_lower in entities_regex:
                entities_merged[entity_lower] = entities_regex[entity_lower]
                extraction_method[entity_lower] = 'regex'
        
        # Other entities (BERT only)
        for entity_type, values in entities_bert.items():
            entity_lower = entity_type.lower()
            if entity_lower not in entities_merged and values:
                entities_merged[entity_lower] = values[0] if len(values) == 1 else values
                extraction_method[entity_lower] = 'bert'
        
        # IBAN from regex (BERT genelde iyi değil)
        if 'iban' in entities_regex and 'receiver_iban' not in entities_merged:
            entities_merged['receiver_iban'] = entities_regex['iban']
            extraction_method['receiver_iban'] = 'regex'
        
        return {
            'entities_bert': entities_bert,
            'entities_regex': entities_regex,
            'entities_merged': entities_merged,
            'extraction_method': extraction_method
        }


def demo():
    """Gerçek data ile demo"""
    
    print("🚀 ROBUST INFERENCE - Gerçek Data Testi\n")
    print("=" * 70)
    
    # Real examples
    test_cases = [
        {
            "description": "Mayıs-Haziran Kira Gönderen: FATİH DİNDAR , Alıcı: ME**** TU*** , IBAN'a Para",
            "amount": "16.000,00",
            "date": "03.10.2025",
            "receiver_iban": "TR290070500000609138100006"
        },
        {
            "description": "ÇALIK-2 APART DAİRE 9 FATİH DİNDAR KİRA ÖDEME",
            "amount": "16.000,00",
            "date": "01.12.2024",
            "receiver_iban": "TR290070500000609138100006"
        },
        {
            "description": "calik-2daire9 FATİH DİNDAR şubat 2025 kira 8bin tl",
            "amount": "8.000,00",
            "date": "01.02.2025",
            "receiver_iban": "TR290070500000609138100006"
        },
        {
            "description": "calik-2daire9 FATİH DİNDAR agustos KİRA, YARIM DEPOZITO 8000, 4000 12BIN TL GONDERILDI",
            "amount": "12.000,00",
            "date": "01.08.2024",
            "receiver_iban": "TR290070500000609138100006"
        }
    ]
    
    # Load models
    print("📥 Modeller yükleniyor...\n")
    intent_clf = RobustIntentClassifier()
    ner_extractor = RobustNERExtractor()
    
    print("✅ Modeller hazır!\n")
    print("=" * 70)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[TEST {i}]")
        print(f"📝 Açıklama: {test['description']}")
        print(f"💰 Tutar: {test['amount']} TRY")
        print(f"📅 Tarih: {test['date']}")
        print()
        
        # Intent classification
        intent_result = intent_clf.predict(test['description'])
        print(f"🎯 INTENT:")
        print(f"   Primary: {intent_result['primary_intent']} ({intent_result['confidence']:.2%})")
        if intent_result['is_multi_intent']:
            print(f"   🔥 Multi-Intent: {intent_result['detected_intents']}")
        print()
        
        # NER extraction
        ner_result = ner_extractor.extract(test['description'])
        print(f"🏷️  NER EXTRACTION:")
        print(f"   Merged Entities:")
        for entity, value in ner_result['entities_merged'].items():
            method = ner_result['extraction_method'].get(entity, 'unknown')
            print(f"      {entity:15s}: {value} [{method}]")
        
        if not ner_result['entities_merged']:
            print(f"      ⚠️  Hiç entity çıkarılamadı!")
        
        print()
        print(f"   Extraction Methods:")
        print(f"      BERT entities: {len(ner_result['entities_bert'])}")
        print(f"      Regex entities: {len(ner_result['entities_regex'])}")
        
        print()
        print("-" * 70)


if __name__ == "__main__":
    demo()
