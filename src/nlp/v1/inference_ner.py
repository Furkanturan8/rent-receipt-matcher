"""
NER Model Inference
Eğitilmiş NER modelini kullanarak entity extraction
"""

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np


# Entity label mapping
ENTITY_LABELS = {
    "O": 0,
    "B-PER": 1,
    "I-PER": 2,
    "B-AMOUNT": 3,
    "I-AMOUNT": 4,
    "B-DATE": 5,
    "I-DATE": 6,
    "B-IBAN": 7,
    "I-IBAN": 8,
    "B-PERIOD": 9,
    "I-PERIOD": 10,
    "B-APT_NO": 11,
    "I-APT_NO": 12,
}

ID2LABEL = {v: k for k, v in ENTITY_LABELS.items()}


class NERExtractor:
    """Eğitilmiş NER modelini kullanarak entity extraction"""
    
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
        print(f"📋 Entity types: PER, AMOUNT, DATE, IBAN, PERIOD, APT_NO")
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Metinden entity'leri çıkar
        
        Args:
            text: Input metin
        
        Returns:
            Dict with entity types as keys and list of entities as values
            {"PER": ["Ahmet Yılmaz"], "AMOUNT": ["14000 TL"], ...}
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
            "PER": [],
            "AMOUNT": [],
            "DATE": [],
            "IBAN": [],
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
            List of dicts: [{"text": "Ahmet Yılmaz", "type": "PER", "start": 0, "end": 12}, ...]
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
    """Demo kullanımı"""
    model_path = "models/ner/final"
    
    # Check if model exists
    if not Path(model_path).exists():
        print(f"❌ Model not found at: {model_path}")
        print("⚠️  First train the model using: python src/nlp/train_ner.py")
        return
    
    # Initialize extractor
    extractor = NERExtractor(model_path)
    
    # Test examples
    test_examples = [
        "Ahmet Yılmaz tarafından 14000 TL 15.12.2024 tarihinde TR1234567890123456789012 hesabına gönderilmiştir.",
        "Kasım 2024 dönemi kira ödemesi 12000 TL - Daire A5",
        "Gönderen: Mehmet Demir, Tutar: 15000 TL, IBAN: TR9876543210987654321098",
        "24.11.2024 tarihli ödeme Ayşe Kaya tarafından yapılmıştır. Tutar: 10000 TL",
        "Daire 12 için Aralık 2024 aidatı - 3000 TL",
    ]
    
    print("\n" + "=" * 80)
    print("🎯 NER Extraction Demo")
    print("=" * 80 + "\n")
    
    for text in test_examples:
        print(f"📝 Text: {text}")
        
        entities = extractor.extract_entities(text)
        
        if entities:
            print("🔍 Extracted Entities:")
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    print(f"  {entity_type:10s} → {entity}")
        else:
            print("  (No entities found)")
        
        print("-" * 80 + "\n")


def pipeline_demo():
    """Intent + NER birlikte kullanım örneği"""
    from src.nlp.inference import IntentClassifier
    
    intent_model = "models/intent_classifier/final"
    ner_model = "models/ner/final"
    
    # Check models
    if not Path(intent_model).exists() or not Path(ner_model).exists():
        print("❌ Models not found. Please train them first.")
        return
    
    # Initialize classifiers
    intent_clf = IntentClassifier(intent_model)
    ner_extractor = NERExtractor(ner_model)
    
    # Test text
    text = "Ahmet Yılmaz tarafından Kasım 2024 dönemi kira ödemesi yapılmıştır. Tutar: 14000 TL"
    
    print("\n" + "=" * 80)
    print("🚀 Full Pipeline Demo (Intent + NER)")
    print("=" * 80 + "\n")
    
    print(f"📝 Input: {text}\n")
    
    # Intent classification
    intent_result = intent_clf.predict(text)
    print(f"🎯 Intent: {intent_result['predicted_label']}")
    print(f"💯 Confidence: {intent_result['confidence']:.2%}\n")
    
    # NER extraction
    entities = ner_extractor.extract_entities(text)
    print("🔍 Entities:")
    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            print(f"  {entity_type:10s} → {entity}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo()
    
    # Uncomment for pipeline demo
    # pipeline_demo()
