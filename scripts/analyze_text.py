#!/usr/bin/env python3
"""
Quick text analysis script - v3 Robust Inference
Usage: python scripts/analyze_text.py "TEXT HERE"
"""

import sys
from src.nlp.v3.inference_robust import RobustIntentClassifier, RobustNERExtractor


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/analyze_text.py 'TEXT HERE'")
        print("")
        print("Örnek:")
        print("  python scripts/analyze_text.py 'FATİH DİNDAR DAİRE 9 KİRA ÖDEME'")
        sys.exit(1)
    
    text = sys.argv[1]
    
    print(f"🔍 Analyzing: {text}")
    print()
    
    # Init models
    intent_clf = RobustIntentClassifier()
    ner = RobustNERExtractor()
    
    # Intent classification
    intent_result = intent_clf.predict(text, multi_intent=True)
    
    print("🎯 INTENT:")
    print(f"  Primary: {intent_result['primary_intent']} ({intent_result['confidence']:.2%})")
    
    if intent_result['is_multi_intent']:
        print(f"  🔥 Multi-Intent: {intent_result['detected_intents']}")
    
    # NER extraction
    ner_result = ner.extract(text, use_fallback=True)
    
    print()
    print("🏷️  ENTITIES:")
    
    if ner_result['entities_merged']:
        for entity, value in ner_result['entities_merged'].items():
            method = ner_result['extraction_method'].get(entity, 'unknown')
            print(f"  {entity:15s}: {value} [{method}]")
    else:
        print("  ⚠️  Hiç entity bulunamadı")
    
    print()
    print("📊 EXTRACTION STATS:")
    print(f"  BERT entities: {len(ner_result['entities_bert'])}")
    print(f"  Regex entities: {len(ner_result['entities_regex'])}")
    print(f"  Merged entities: {len(ner_result['entities_merged'])}")


if __name__ == "__main__":
    main()
