"""
NER Model Evaluation Only
Sadece test evaluation yapar, eğitim yapmaz
"""

import json
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    Trainer,
    TrainingArguments,
    DataCollatorForTokenClassification
)
from datasets import Dataset
from seqeval.metrics import classification_report

from train_ner import NERDataProcessor, ID2LABEL, LABEL2ID


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


def main():
    print("🔄 Re-evaluating NER model...")
    
    model_path = "models/ner/final"
    data_path = "data/synthetic/ner_synthetic.json"
    
    # Load data
    processor = NERDataProcessor()
    bio_data = processor.load_and_convert_data(data_path)
    
    # Split (same seed as training)
    train_data, temp_data = train_test_split(
        bio_data, test_size=0.3, random_state=42
    )
    _, test_data = train_test_split(
        temp_data, test_size=0.5, random_state=42
    )
    
    test_dataset = Dataset.from_list(test_data)
    
    print(f"\n📊 Test set: {len(test_data)} samples")
    
    # Load model
    print(f"\n🔧 Loading model from: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForTokenClassification.from_pretrained(model_path)
    
    # Tokenize function
    def tokenize_and_align_labels(examples):
        tokenized_inputs = tokenizer(
            examples['tokens'],
            truncation=True,
            is_split_into_words=True,
            max_length=128,
            padding=False
        )
        
        labels = []
        for i, label in enumerate(examples['ner_tags']):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []
            
            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    label_ids.append(label[word_idx])
                else:
                    label_ids.append(-100)
                previous_word_idx = word_idx
            
            labels.append(label_ids)
        
        tokenized_inputs["labels"] = labels
        return tokenized_inputs
    
    # Tokenize test dataset
    print("🔤 Tokenizing test dataset...")
    test_dataset = test_dataset.map(
        tokenize_and_align_labels,
        batched=True,
        remove_columns=test_dataset.column_names
    )
    
    # Data collator
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    
    # Compute metrics function
    def compute_metrics(p):
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)
        
        # Remove ignored index (special tokens)
        true_predictions = [
            [ID2LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [ID2LABEL[l] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        
        from seqeval.metrics import precision_score, recall_score, f1_score, accuracy_score
        
        return {
            "precision": precision_score(true_labels, true_predictions),
            "recall": recall_score(true_labels, true_predictions),
            "f1": f1_score(true_labels, true_predictions),
            "accuracy": accuracy_score(true_labels, true_predictions),
        }
    
    # Trainer for evaluation only
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir="models/ner",
            per_device_eval_batch_size=16,
            report_to="none"
        ),
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )
    
    # Evaluate
    print("\n📊 Evaluating...")
    predictions, labels, metrics = trainer.predict(test_dataset)
    predictions = np.argmax(predictions, axis=2)
    
    # Remove ignored index
    true_predictions = [
        [ID2LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [ID2LABEL[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    
    # Classification report
    print("\n📈 Classification Report:")
    report = classification_report(true_labels, true_predictions, digits=4)
    print(report)
    
    report_dict = classification_report(
        true_labels,
        true_predictions,
        output_dict=True
    )
    
    # Save results
    results = {
        "test_metrics": convert_numpy_types(metrics),
        "classification_report": convert_numpy_types(report_dict)
    }
    
    output_path = Path("models/ner/test_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Results saved to: {output_path}")


if __name__ == "__main__":
    main()
