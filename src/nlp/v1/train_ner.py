"""
Named Entity Recognition (NER) Model Training
Türkçe BERT ile finansal entity tanıma (person, amount, date, IBAN, etc.)

Entity Types:
- PER: Kişi adı
- AMOUNT: Tutar
- DATE: Tarih
- IBAN: Banka hesap numarası
- PERIOD: Ödeme dönemi
- APT_NO: Daire numarası
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import re

import torch
import numpy as np
from sklearn.model_selection import train_test_split
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification
)
from datasets import Dataset
from seqeval.metrics import (
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    accuracy_score
)
import matplotlib.pyplot as plt
import seaborn as sns


# Entity label mapping (BIO format)
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
LABEL2ID = ENTITY_LABELS


class NERDataProcessor:
    """NER data'yı BIO formatına çevirme ve işleme"""
    
    def __init__(self):
        self.label2id = LABEL2ID
        self.id2label = ID2LABEL
    
    def convert_to_bio(self, text: str, entities: Dict[str, List[str]]) -> Tuple[List[str], List[str]]:
        """
        Entity dictionary'yi BIO formatına çevir
        
        Args:
            text: Input cümle
            entities: {"PER": ["Ahmet Yılmaz"], "AMOUNT": ["14000 TL"], ...}
        
        Returns:
            tokens: Token listesi
            labels: BIO label listesi
        """
        # Tokenize (whitespace-based for alignment)
        tokens = text.split()
        labels = ["O"] * len(tokens)
        
        # Her entity type için işle
        for entity_type, entity_list in entities.items():
            for entity_text in entity_list:
                # Entity'yi metinde bul
                entity_tokens = entity_text.split()
                
                # Sliding window ile entity'yi tokens içinde bul
                for i in range(len(tokens) - len(entity_tokens) + 1):
                    # Tokens match ediyor mu?
                    match = True
                    for j, entity_token in enumerate(entity_tokens):
                        if tokens[i + j].lower() != entity_token.lower():
                            match = False
                            break
                    
                    if match:
                        # BIO tagging
                        labels[i] = f"B-{entity_type}"
                        for j in range(1, len(entity_tokens)):
                            labels[i + j] = f"I-{entity_type}"
                        break
        
        return tokens, labels
    
    def load_and_convert_data(self, json_path: str) -> List[Dict]:
        """JSON formatındaki NER data'yı BIO formatına çevir"""
        print(f"📂 Loading NER data from: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Total samples: {len(data)}")
        
        bio_data = []
        skipped = 0
        
        for idx, item in enumerate(data):
            try:
                text = item['text']
                entities = item['entities']
                
                tokens, labels = self.convert_to_bio(text, entities)
                
                # Validation
                if len(tokens) != len(labels):
                    skipped += 1
                    continue
                
                bio_data.append({
                    'id': idx,
                    'tokens': tokens,
                    'ner_tags': [self.label2id[label] for label in labels],
                    'ner_tags_str': labels  # For debugging
                })
            except Exception as e:
                print(f"⚠️  Sample {idx} skipped: {e}")
                skipped += 1
                continue
        
        print(f"✅ Converted: {len(bio_data)} samples")
        if skipped > 0:
            print(f"⚠️  Skipped: {skipped} samples")
        
        # Label distribution
        label_counts = {}
        for item in bio_data:
            for label in item['ner_tags_str']:
                label_counts[label] = label_counts.get(label, 0) + 1
        
        print("\n📈 Label distribution:")
        for label, count in sorted(label_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {label:15s}: {count:5d}")
        
        return bio_data


class NERTrainer:
    def __init__(
        self,
        model_name: str = "dbmdz/distilbert-base-turkish-cased",
        output_dir: str = "models/ner",
        max_length: int = 128
    ):
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.max_length = max_length
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tokenizer
        print(f"🔧 Loading tokenizer: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Initialize model
        print(f"🤖 Loading model: {model_name}")
        self.model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=len(LABEL2ID),
            id2label=ID2LABEL,
            label2id=LABEL2ID
        )
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"💻 Device: {self.device}")
    
    def tokenize_and_align_labels(self, examples):
        """Tokenize ve label'ları align et"""
        tokenized_inputs = self.tokenizer(
            examples['tokens'],
            truncation=True,
            is_split_into_words=True,
            max_length=self.max_length,
            padding=False
        )
        
        labels = []
        for i, label in enumerate(examples['ner_tags']):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []
            
            for word_idx in word_ids:
                # Special tokens have a word id that is None
                if word_idx is None:
                    label_ids.append(-100)
                # We set the label for the first token of each word
                elif word_idx != previous_word_idx:
                    label_ids.append(label[word_idx])
                # For other tokens in a word, we set the label to -100
                else:
                    label_ids.append(-100)
                previous_word_idx = word_idx
            
            labels.append(label_ids)
        
        tokenized_inputs["labels"] = labels
        return tokenized_inputs
    
    def compute_metrics(self, p):
        """seqeval metrics"""
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
        
        return {
            "precision": precision_score(true_labels, true_predictions),
            "recall": recall_score(true_labels, true_predictions),
            "f1": f1_score(true_labels, true_predictions),
            "accuracy": accuracy_score(true_labels, true_predictions),
        }
    
    def train(
        self,
        train_dataset: Dataset,
        val_dataset: Dataset,
        num_epochs: int = 5,
        batch_size: int = 16,
        learning_rate: float = 2e-5
    ):
        """Model eğitimi"""
        print("\n🚀 Starting training...\n")
        
        # Tokenize datasets
        print("🔤 Tokenizing datasets...")
        train_dataset = train_dataset.map(
            self.tokenize_and_align_labels,
            batched=True,
            remove_columns=train_dataset.column_names
        )
        val_dataset = val_dataset.map(
            self.tokenize_and_align_labels,
            batched=True,
            remove_columns=val_dataset.column_names
        )
        
        # Data collator
        data_collator = DataCollatorForTokenClassification(
            tokenizer=self.tokenizer
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=0.01,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=10,
            warmup_steps=100,
            save_total_limit=2,
            report_to="none",
            seed=42
        )
        
        # Initialize Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            compute_metrics=self.compute_metrics
        )
        
        # Train!
        trainer.train()
        
        # Save final model
        print("\n💾 Saving model...")
        trainer.save_model(str(self.output_dir / "final"))
        self.tokenizer.save_pretrained(str(self.output_dir / "final"))
        
        print(f"✅ Model saved to: {self.output_dir / 'final'}")
        
        return trainer
    
    def evaluate(self, test_dataset: Dataset, trainer: Trainer):
        """Test set üzerinde değerlendirme"""
        print("\n📊 Evaluating on test set...\n")
        
        # Tokenize test dataset
        test_dataset = test_dataset.map(
            self.tokenize_and_align_labels,
            batched=True,
            remove_columns=test_dataset.column_names
        )
        
        # Predict
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
        print("📈 Classification Report:")
        print(classification_report(true_labels, true_predictions, digits=4))
        
        # Save results (convert numpy types to Python types)
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
        
        report_dict = classification_report(
            true_labels,
            true_predictions,
            output_dict=True
        )
        
        results = {
            "test_metrics": convert_numpy_types(metrics),
            "classification_report": convert_numpy_types(report_dict)
        }
        
        with open(self.output_dir / "test_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Results saved to: {self.output_dir / 'test_results.json'}")


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("🎯 NER Model Training")
    print("=" * 60)
    
    # Paths (v1)
    data_path = "data/v1_synthetic/ner_synthetic.json"
    output_dir = "models/v1_archived/ner"
    
    # Process data
    processor = NERDataProcessor()
    bio_data = processor.load_and_convert_data(data_path)
    
    # Train/Val/Test split
    train_data, temp_data = train_test_split(
        bio_data, test_size=0.3, random_state=42
    )
    val_data, test_data = train_test_split(
        temp_data, test_size=0.5, random_state=42
    )
    
    print(f"\n✂️ Split:")
    print(f"  Train: {len(train_data)} samples")
    print(f"  Val: {len(val_data)} samples")
    print(f"  Test: {len(test_data)} samples")
    
    # Convert to HuggingFace Dataset
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)
    test_dataset = Dataset.from_list(test_data)
    
    # Initialize trainer
    trainer_obj = NERTrainer(
        model_name="dbmdz/distilbert-base-turkish-cased",
        output_dir=output_dir,
        max_length=128
    )
    
    # Train
    trainer = trainer_obj.train(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        num_epochs=5,
        batch_size=16,
        learning_rate=2e-5
    )
    
    # Evaluate
    trainer_obj.evaluate(test_dataset, trainer)
    
    print("\n" + "=" * 60)
    print("✨ Training completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
