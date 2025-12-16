"""
Intent Classification Inference
Eğitilmiş modeli kullanarak tahmin yapma
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path
from typing import Dict, List


class IntentClassifier:
    """Eğitilmiş intent classification modelini kullan"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise ValueError(f"Model path not found: {model_path}")
        
        print(f"🔧 Loading model from: {model_path}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_path))
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        # Label mapping
        self.id2label = self.model.config.id2label
        
        print(f"✅ Model loaded successfully!")
        print(f"📋 Labels: {list(self.id2label.values())}")
    
    def predict(self, text: str, return_probabilities: bool = False) -> Dict:
        """Tek bir metin için tahmin yap"""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
        
        # Get prediction
        pred_id = torch.argmax(probabilities, dim=-1).item()
        pred_label = self.id2label[pred_id]
        confidence = probabilities[0][pred_id].item()
        
        result = {
            "text": text,
            "predicted_label": pred_label,
            "confidence": confidence
        }
        
        if return_probabilities:
            all_probs = {
                self.id2label[i]: probabilities[0][i].item()
                for i in range(len(self.id2label))
            }
            result["probabilities"] = all_probs
        
        return result
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """Birden fazla metin için tahmin yap"""
        return [self.predict(text) for text in texts]


def demo():
    """Demo kullanımı"""
    model_path = "models/intent_classifier/final"
    
    # Check if model exists
    if not Path(model_path).exists():
        print(f"❌ Model not found at: {model_path}")
        print("⚠️  First train the model using: python src/nlp/train_intent_classifier.py")
        return
    
    # Initialize classifier
    classifier = IntentClassifier(model_path)
    
    # Test examples
    test_examples = [
        "Kasım ayı kira bedeli - Daire A2",
        "Site aidatı - Aralık 2024",
        "Yeni kiralama kapora ödemesi",
        "Depozito bedeli - Daire B5",
        "Ocak kira ödemesi - 12 nolu daire",
        "Apartman aidat ödemesi",
    ]
    
    print("\n" + "=" * 60)
    print("🎯 Intent Classification Demo")
    print("=" * 60 + "\n")
    
    for text in test_examples:
        result = classifier.predict(text, return_probabilities=True)
        
        print(f"📝 Text: {result['text']}")
        print(f"🎯 Predicted: {result['predicted_label']}")
        print(f"💯 Confidence: {result['confidence']:.4f}")
        print("\n📊 All probabilities:")
        for label, prob in result['probabilities'].items():
            bar = "█" * int(prob * 40)
            print(f"  {label:20s} {prob:6.4f} {bar}")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    demo()
