"""
NER Model Inference - v2 (OCR-Aware)
Eğitilmiş NER modelini kullanarak entity extraction
11 Entity Types: SENDER, RECEIVER, AMOUNT, DATE, SENDER_IBAN, RECEIVER_IBAN, 
                 BANK, TRANSACTION_TYPE, FEE, PERIOD, APT_NO
"""

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np


# Entity label mapping - v2 (11 entities)
ENTITY_LABELS = {
    "O": 0,
    "B-SENDER": 1,
    "I-SENDER": 2,
    "B-RECEIVER": 3,
    "I-RECEIVER": 4,
    "B-AMOUNT": 5,
    "I-AMOUNT": 6,
    "B-DATE": 7,
    "I-DATE": 8,
    "B-SENDER_IBAN": 9,
    "I-SENDER_IBAN": 10,
    "B-RECEIVER_IBAN": 11,
    "I-RECEIVER_IBAN": 12,
    "B-BANK": 13,
    "I-BANK": 14,
    "B-TRANSACTION_TYPE": 15,
    "I-TRANSACTION_TYPE": 16,
    "B-FEE": 17,
    "I-FEE": 18,
    "B-PERIOD": 19,
    "I-PERIOD": 20,
    "B-APT_NO": 21,
    "I-APT_NO": 22,
}

ID2LABEL = {v: k for k, v in ENTITY_LABELS.items()}


class NERExtractor:
    """Eğitilmiş NER modelini kullanarak entity extraction - v2 (11 entities)"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise ValueError(f"Model path not found: {model_path}")
        
        print(f"🔧 Loading NER model from: {model_path}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        self.model = AutoModelForTokenClassification.from_pretrained(str(self.model_path))
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        # Label mapping
        self.id2label = self.model.config.id2label
        
        print(f"✅ Model loaded successfully!")
        print(f"📋 Entity types (11): SENDER, RECEIVER, AMOUNT, DATE, SENDER_IBAN, RECEIVER_IBAN,")
        print(f"                     BANK, TRANSACTION_TYPE, FEE, PERIOD, APT_NO")
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Metinden entity'leri çıkar
        
        Args:
            text: Input metin
        
        Returns:
            Dict with entity types as keys and list of entities as values
            {"SENDER": ["Ahmet Yılmaz"], "AMOUNT": ["14000 TL"], ...}
        """
        # Tokenize
        tokens = text.split()
        encoded = self.tokenizer(
            tokens,
            return_tensors="pt",
            truncation=True,
            is_split_into_words=True,
            max_length=128,
            padding=True
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in encoded.items()}
        
        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)
        
        # Get word_ids for alignment
        word_ids = encoded.word_ids(batch_index=0)
        
        # Align predictions with original tokens
        token_predictions = []
        previous_word_idx = None
        
        for idx, word_idx in enumerate(word_ids):
            if word_idx is None:
                continue
            if word_idx != previous_word_idx:
                pred_label_id = predictions[0][idx].item()
                pred_label = self.id2label.get(pred_label_id, "O")
                token_predictions.append((tokens[word_idx], pred_label))
            previous_word_idx = word_idx
        
        # Group entities
        entities = self._group_entities(token_predictions)
        
        return entities
    
    def _group_entities(self, token_predictions: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """BIO tagged tokens'ları entity'lere grupla"""
        entities = {
            "SENDER": [],
            "RECEIVER": [],
            "AMOUNT": [],
            "DATE": [],
            "SENDER_IBAN": [],
            "RECEIVER_IBAN": [],
            "BANK": [],
            "TRANSACTION_TYPE": [],
            "FEE": [],
            "PERIOD": [],
            "APT_NO": []
        }
        
        current_entity = []
        current_type = None
        
        for token, label in token_predictions:
            if label.startswith("B-"):
                # New entity starts
                if current_entity and current_type:
                    entities[current_type].append(" ".join(current_entity))
                
                current_type = label[2:]  # Remove "B-"
                current_entity = [token]
            
            elif label.startswith("I-"):
                # Continue entity
                entity_type = label[2:]  # Remove "I-"
                if entity_type == current_type:
                    current_entity.append(token)
                else:
                    # Type mismatch, treat as new entity
                    if current_entity and current_type:
                        entities[current_type].append(" ".join(current_entity))
                    current_type = entity_type
                    current_entity = [token]
            
            else:
                # "O" label - end of entity
                if current_entity and current_type:
                    entities[current_type].append(" ".join(current_entity))
                current_entity = []
                current_type = None
        
        # Add last entity if exists
        if current_entity and current_type:
            entities[current_type].append(" ".join(current_entity))
        
        # Remove empty lists
        entities = {k: v for k, v in entities.items() if v}
        
        return entities
    
    def extract_with_positions(self, text: str) -> List[Dict]:
        """
        Entity'leri pozisyonlarıyla birlikte çıkar
        
        Returns:
            List of dicts: [{"text": "Ahmet Yılmaz", "type": "SENDER", "start": 0, "end": 12}, ...]
        """
        entities = self.extract_entities(text)
        
        result = []
        for entity_type, entity_list in entities.items():
            for entity_text in entity_list:
                # Find position in original text
                start = text.find(entity_text)
                if start != -1:
                    result.append({
                        "text": entity_text,
                        "type": entity_type,
                        "start": start,
                        "end": start + len(entity_text)
                    })
        
        return result


def demo():
    """Demo kullanımı - v2 (OCR-Aware)"""
    model_path = "models/v2_ocr_aware/ner/final"
    
    # Check if model exists
    if not Path(model_path).exists():
        print(f"❌ Model not found at: {model_path}")
        print("⚠️  First train the model using: python src/nlp/v2/train_ner.py")
        return
    
    # Initialize extractor
    extractor = NERExtractor(model_path)
    
    # Test examples - OCR-aware format
    test_examples = [
        "Gönderen: Ahmet Yılmaz IBAN: TR1234567890123456789012 Alan: Mehmet Demir IBAN: TR9876543210987654321098 Banka: Ziraat Bankası İşlem: EFT Tutar: 15000 TL Komisyon: 2.50 TL Tarih: 15.11.2024 Açıklama: Kasım ayı kira ödemesi Daire: 12",
        
        "Gönderen: Ayşe Kaya IBAN: TR1111222233334444555566 Alan: Site Yönetimi IBAN: TR6666555544443333222211 Banka: İş Bankası İşlem: Havale Tutar: 3000 TL Komisyon: 1.00 TL Tarih: 20.11.2024 Açıklama: Aralık dönemi aidat ödemesi Daire: A5",
        
        "Gönderen: Fatma Yıldız IBAN: TR7777888899990000111122 Alan: Ev Sahibi IBAN: TR2222111100009999888877 Banka: Garanti Bankası İşlem: FAST Tutar: 50000 TL Komisyon: 5.00 TL Tarih: 01.12.2024 Açıklama: Yeni kiralama kapora ödemesi",
        
        "Gönderen: Ali Öztürk IBAN: TR3333444455556666777788 Alan: Konut Yönetimi IBAN: TR8888777766665555444433 Banka: Akbank İşlem: EFT Tutar: 10000 TL Komisyon: 1.50 TL Tarih: 25.11.2024 Açıklama: Depozito bedeli Daire: B3",
    ]
    
    print("\n" + "=" * 100)
    print("🎯 NER Extraction Demo - v2 (OCR-Aware, 11 Entities)")
    print("=" * 100 + "\n")
    
    for i, text in enumerate(test_examples, 1):
        print(f"📝 Example {i}:")
        print(f"   {text[:80]}..." if len(text) > 80 else f"   {text}")
        
        entities = extractor.extract_entities(text)
        
        if entities:
            print("\n🔍 Extracted Entities:")
            # Order by importance
            entity_order = ["SENDER", "RECEIVER", "AMOUNT", "DATE", "SENDER_IBAN", 
                          "RECEIVER_IBAN", "BANK", "TRANSACTION_TYPE", "FEE", "PERIOD", "APT_NO"]
            
            for entity_type in entity_order:
                if entity_type in entities:
                    for entity in entities[entity_type]:
                        print(f"  {entity_type:18s} → {entity}")
        else:
            print("  (No entities found)")
        
        print("-" * 100 + "\n")


def pipeline_demo():
    """Intent + NER birlikte kullanım örneği - v2"""
    from src.nlp.v2.inference import IntentClassifier
    
    intent_model = "models/v2_ocr_aware/intent_classifier/final"
    ner_model = "models/v2_ocr_aware/ner/final"
    
    # Check models
    if not Path(intent_model).exists() or not Path(ner_model).exists():
        print("❌ Models not found. Please train them first.")
        return
    
    # Initialize classifiers
    intent_clf = IntentClassifier(intent_model)
    ner_extractor = NERExtractor(ner_model)
    
    # Test text - OCR-aware format
    text = "Gönderen: Ahmet Yılmaz IBAN: TR1234567890123456789012 Alan: Ev Sahibi IBAN: TR9876543210987654321098 Banka: Ziraat Bankası İşlem: EFT Tutar: 15000 TL Komisyon: 2.50 TL Tarih: 20.11.2024 Açıklama: Kasım 2024 dönemi kira ödemesi Daire: 12"
    
    print("\n" + "=" * 100)
    print("🚀 Full Pipeline Demo (Intent + NER) - v2 (OCR-Aware)")
    print("=" * 100 + "\n")
    
    print(f"📝 Input:\n{text}\n")
    
    # Intent classification
    intent_result = intent_clf.predict(text)
    print(f"🎯 Intent: {intent_result['predicted_label']}")
    print(f"💯 Confidence: {intent_result['confidence']:.2%}\n")
    
    # NER extraction
    entities = ner_extractor.extract_entities(text)
    print("🔍 Entities:")
    
    entity_order = ["SENDER", "RECEIVER", "AMOUNT", "DATE", "SENDER_IBAN", 
                   "RECEIVER_IBAN", "BANK", "TRANSACTION_TYPE", "FEE", "PERIOD", "APT_NO"]
    
    for entity_type in entity_order:
        if entity_type in entities:
            for entity in entities[entity_type]:
                print(f"  {entity_type:18s} → {entity}")
    
    print("\n" + "=" * 100)
    
    # Structured output
    print("\n📦 Structured Output (JSON-like):\n")
    structured = {
        "intent": intent_result['predicted_label'],
        "confidence": intent_result['confidence'],
        "entities": entities
    }
    
    import json
    print(json.dumps(structured, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    demo()
    
    print("\n" + "=" * 100)
    print("💡 Tip: For full pipeline demo (Intent + NER), run:")
    print("   python -c 'from src.nlp.v2.inference_ner import pipeline_demo; pipeline_demo()'")
    print("=" * 100 + "\n")
