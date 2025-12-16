"""
Named Entity Recognition (NER) Model Training - V2 (OCR-Aware)
Türkçe BERT ile finansal entity tanıma (11 entity tipi)

Entity Types (v2):
- SENDER: Gönderen kişi adı
- RECEIVER: Alıcı firma/kişi adı  
- AMOUNT: Tutar
- DATE: Tarih
- SENDER_IBAN: Gönderen IBAN
- RECEIVER_IBAN: Alıcı IBAN
- BANK: Banka adı
- TRANSACTION_TYPE: İşlem tipi (EFT/Havale/FAST)
- FEE: İşlem ücreti
- PERIOD: Ödeme dönemi (Ocak 2024)
- APT_NO: Daire numarası

Version: 3.0 - ROBUST
Dataset: data/v3_robust/ner_robust.json (2500 samples)
Features: Noise injection, synonyms, OCR errors, ambiguous data
✅ AMOUNT BUG FIXED - Now 100% coverage!
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


# Entity label mapping (BIO format) - 11 entity types
ENTITY_LABELS = {
    "O": 0,
    # SENDER (Gönderen)
    "B-SENDER": 1,
    "I-SENDER": 2,
    # RECEIVER (Alıcı)
    "B-RECEIVER": 3,
    "I-RECEIVER": 4,
    # AMOUNT (Tutar)
    "B-AMOUNT": 5,
    "I-AMOUNT": 6,
    # DATE (Tarih)
    "B-DATE": 7,
    "I-DATE": 8,
    # SENDER_IBAN
    "B-SENDER_IBAN": 9,
    "I-SENDER_IBAN": 10,
    # RECEIVER_IBAN
    "B-RECEIVER_IBAN": 11,
    "I-RECEIVER_IBAN": 12,
    # BANK (Banka adı)
    "B-BANK": 13,
    "I-BANK": 14,
    # TRANSACTION_TYPE (İşlem tipi)
    "B-TRANSACTION_TYPE": 15,
    "I-TRANSACTION_TYPE": 16,
    # FEE (İşlem ücreti)
    "B-FEE": 17,
    "I-FEE": 18,
    # PERIOD (Dönem)
    "B-PERIOD": 19,
    "I-PERIOD": 20,
    # APT_NO (Daire no)
    "B-APT_NO": 21,
    "I-APT_NO": 22,
}

ID2LABEL = {v: k for k, v in ENTITY_LABELS.items()}
LABEL2ID = ENTITY_LABELS


class NERDataProcessor:
    """NER dataset işleme ve BIO formatına çevirme"""
    
    def __init__(self):
        self.entity_types = [
            "SENDER", "RECEIVER", "AMOUNT", "DATE",
            "SENDER_IBAN", "RECEIVER_IBAN", "BANK",
            "TRANSACTION_TYPE", "FEE", "PERIOD", "APT_NO"
        ]
    
    def convert_to_bio(self, text: str, entities: Dict[str, List[str]]) -> Tuple[List[str], List[str]]:
        """
        Text ve entity dict'ini BIO formatına çevir
        
        Args:
            text: Input text (combined_text)
            entities: Entity dictionary
            
        Returns:
            (tokens, labels): Token listesi ve BIO label'ları
        """
        tokens = text.split()
        labels = ["O"] * len(tokens)
        
        # Her entity tipi için
        for entity_type in self.entity_types:
            if entity_type not in entities or not entities[entity_type]:
                continue
            
            for entity_value in entities[entity_type]:
                if not entity_value:
                    continue
                
                entity_tokens = entity_value.split()
                
                # Text içinde entity'yi bul
                for i in range(len(tokens) - len(entity_tokens) + 1):
                    # Token eşleşmesi kontrol et
                    match = True
                    for j, entity_token in enumerate(entity_tokens):
                        # Normalize edilmiş karşılaştırma
                        if not self._token_match(tokens[i + j], entity_token):
                            match = False
                            break
                    
                    if match:
                        # BIO etiketleme
                        labels[i] = f"B-{entity_type}"
                        for j in range(1, len(entity_tokens)):
                            if i + j < len(labels):
                                labels[i + j] = f"I-{entity_type}"
                        break
        
        return tokens, labels
    
    def _token_match(self, token1: str, token2: str) -> bool:
        """İki token'ın eşleşip eşleşmediğini kontrol et (normalize edilmiş)"""
        # Noktalama işaretlerini temizle ve küçük harfe çevir
        clean1 = re.sub(r'[^\w\s]', '', token1.lower())
        clean2 = re.sub(r'[^\w\s]', '', token2.lower())
        return clean1 == clean2 or token1 == token2
    
    def load_and_convert_data(self, json_path: str) -> List[Dict]:
        """
        JSON dataset'i yükle ve BIO formatına çevir
        
        Args:
            json_path: Dataset path
            
        Returns:
            List of dictionaries with 'tokens' and 'ner_tags'
        """
        print(f"\n📂 Loading data from: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Total samples: {len(data)}")
        
        # Convert to BIO format
        bio_data = []
        skipped = 0
        
        for idx, item in enumerate(data):
            try:
                # v3 dataset'te "text" field'ı var
                text = item["text"]
                entities = item["entities"]
                
                tokens, labels = self.convert_to_bio(text, entities)
                
                # Label ID'lerine çevir
                label_ids = [LABEL2ID.get(label, 0) for label in labels]
                
                bio_data.append({
                    "tokens": tokens,
                    "ner_tags": label_ids
                })
                
            except Exception as e:
                skipped += 1
                if skipped <= 5:
                    print(f"⚠️  Skipped sample {idx}: {str(e)}")
        
        print(f"✅ Converted: {len(bio_data)} samples")
        if skipped > 0:
            print(f"⚠️  Skipped: {skipped} samples")
        
        # Entity istatistikleri
        self._print_entity_stats(bio_data)
        
        return bio_data
    
    def _print_entity_stats(self, bio_data: List[Dict]):
        """Entity istatistiklerini yazdır"""
        entity_counts = {entity_type: 0 for entity_type in self.entity_types}
        
        for item in bio_data:
            labels = [ID2LABEL[label_id] for label_id in item["ner_tags"]]
            for label in labels:
                if label.startswith("B-"):
                    entity_type = label[2:]
                    if entity_type in entity_counts:
                        entity_counts[entity_type] += 1
        
        print("\n📈 Entity Statistics:")
        for entity_type, count in sorted(entity_counts.items()):
            percentage = (count / len(bio_data)) * 100
            print(f"  {entity_type:<20} {count:>5} ({percentage:>5.1f}%)")


class NERTrainer:
    """NER model eğitim sınıfı"""
    
    def __init__(
        self,
        model_name: str = "dbmdz/distilbert-base-turkish-cased",
        output_dir: str = "models/v2_ocr_aware/ner",
        max_length: int = 256
    ):
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.max_length = max_length
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔧 Loading tokenizer: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        print(f"🤖 Loading model: {model_name}")
        self.model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=len(ENTITY_LABELS),
            id2label=ID2LABEL,
            label2id=LABEL2ID
        )
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"💻 Device: {self.device}")
    
    def prepare_datasets(self, bio_data: List[Dict]) -> Tuple[Dataset, Dataset, Dataset]:
        """Dataset'i train/val/test olarak böl"""
        print("\n📊 Splitting dataset...")
        
        # Stratified split yapmak için entity yoğunluğunu kullan
        train_data, temp_data = train_test_split(
            bio_data,
            test_size=0.3,
            random_state=42
        )
        
        val_data, test_data = train_test_split(
            temp_data,
            test_size=0.5,
            random_state=42
        )
        
        print(f"  Train: {len(train_data)} samples")
        print(f"  Val: {len(val_data)} samples")
        print(f"  Test: {len(test_data)} samples")
        
        # Convert to HuggingFace datasets
        train_dataset = Dataset.from_list(train_data)
        val_dataset = Dataset.from_list(val_data)
        test_dataset = Dataset.from_list(test_data)
        
        return train_dataset, val_dataset, test_dataset
    
    def tokenize_and_align_labels(self, examples):
        """Tokenize ve label'ları hizala"""
        tokenized_inputs = self.tokenizer(
            examples["tokens"],
            truncation=True,
            is_split_into_words=True,
            max_length=self.max_length,
            padding=False
        )
        
        labels = []
        for i, label in enumerate(examples["ner_tags"]):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            label_ids = []
            previous_word_idx = None
            
            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    label_ids.append(label[word_idx])
                else:
                    # Subword için -100 (ignore)
                    label_ids.append(-100)
                previous_word_idx = word_idx
            
            labels.append(label_ids)
        
        tokenized_inputs["labels"] = labels
        return tokenized_inputs
    
    def compute_metrics(self, p):
        """Evaluation metrics hesapla"""
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)
        
        true_labels = [[ID2LABEL[l] for l in label if l != -100] for label in labels]
        true_predictions = [
            [ID2LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        
        results = {
            "precision": precision_score(true_labels, true_predictions),
            "recall": recall_score(true_labels, true_predictions),
            "f1": f1_score(true_labels, true_predictions),
            "accuracy": accuracy_score(true_labels, true_predictions),
        }
        
        return results
    
    def train(
        self,
        train_dataset: Dataset,
        val_dataset: Dataset,
        num_epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5
    ):
        """Model eğitimi"""
        print(f"\n🚀 Starting training...")
        print(f"   Epochs: {num_epochs}")
        print(f"   Batch size: {batch_size}")
        print(f"   Learning rate: {learning_rate}")
        
        # Tokenize
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
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            eval_strategy="epoch",
            save_strategy="epoch",
            learning_rate=learning_rate,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            num_train_epochs=num_epochs,
            weight_decay=0.01,
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=50,
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            save_total_limit=2,
        )
        
        # Data collator
        data_collator = DataCollatorForTokenClassification(self.tokenizer)
        
        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            compute_metrics=self.compute_metrics,
        )
        
        # Train
        trainer.train()
        
        # Save final model
        final_dir = self.output_dir / "final"
        trainer.save_model(str(final_dir))
        print(f"\n💾 Model saved to: {final_dir}")
        
        return trainer
    
    def evaluate(self, test_dataset: Dataset, trainer: Trainer):
        """Test set evaluation"""
        print("\n📊 Evaluating on test set...")
        
        # Tokenize test set
        test_dataset = test_dataset.map(
            self.tokenize_and_align_labels,
            batched=True,
            remove_columns=test_dataset.column_names
        )
        
        # Evaluate
        results = trainer.evaluate(test_dataset)
        
        print("\n✅ Test Results:")
        print(f"   Accuracy: {results['eval_accuracy']:.4f}")
        print(f"   Precision: {results['eval_precision']:.4f}")
        print(f"   Recall: {results['eval_recall']:.4f}")
        print(f"   F1-Score: {results['eval_f1']:.4f}")
        
        # Detailed classification report
        predictions = trainer.predict(test_dataset)
        preds = np.argmax(predictions.predictions, axis=2)
        labels = predictions.label_ids
        
        true_labels = [[ID2LABEL[l] for l in label if l != -100] for label in labels]
        true_predictions = [
            [ID2LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(preds, labels)
        ]
        
        print("\n📋 Detailed Classification Report:")
        report = classification_report(true_labels, true_predictions, digits=4)
        print(report)
        
        # Save results
        def convert_numpy_types(obj):
            """Convert numpy types to native Python types"""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        results_file = self.output_dir / "test_results.json"
        results_data = {
            "test_accuracy": float(results['eval_accuracy']),
            "test_precision": float(results['eval_precision']),
            "test_recall": float(results['eval_recall']),
            "test_f1": float(results['eval_f1']),
            "classification_report": report,
            "num_test_samples": len(test_dataset),
            "entity_types": ["SENDER", "RECEIVER", "AMOUNT", "DATE", "SENDER_IBAN", "RECEIVER_IBAN", "BANK", "TRANSACTION_TYPE", "FEE", "PERIOD", "APT_NO"]
        }
        
        results_data = convert_numpy_types(results_data)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {results_file}")


def main():
    """Ana eğitim fonksiyonu"""
    print("="*80)
    print("🎯 NER Model Training - v2 (OCR-Aware)")
    print("="*80)
    print("\n📌 Entity Types (11):")
    print("   SENDER, RECEIVER, AMOUNT, DATE, SENDER_IBAN, RECEIVER_IBAN,")
    print("   BANK, TRANSACTION_TYPE, FEE, PERIOD, APT_NO")
    print()
    
    # Paths (v3 - Robust)
    data_path = "data/v3_robust/ner_robust.json"
    output_dir = "models/v3_robust/ner"
    
    # Process data
    processor = NERDataProcessor()
    bio_data = processor.load_and_convert_data(data_path)
    
    # Initialize trainer
    trainer_obj = NERTrainer(
        model_name="dbmdz/distilbert-base-turkish-cased",
        output_dir=output_dir,
        max_length=256
    )
    
    # Prepare datasets
    train_dataset, val_dataset, test_dataset = trainer_obj.prepare_datasets(bio_data)
    
    # Train
    trainer = trainer_obj.train(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        num_epochs=3,
        batch_size=16,
        learning_rate=2e-5
    )
    
    # Evaluate
    trainer_obj.evaluate(test_dataset, trainer)
    
    print("\n" + "="*80)
    print("✅ Training completed successfully!")
    print("="*80)
    print(f"\n📁 Model location: {output_dir}/final")
    print(f"📊 Results: {output_dir}/test_results.json")


if __name__ == "__main__":
    # Set HuggingFace cache
    os.environ['HF_HOME'] = './.cache/huggingface'
    main()
