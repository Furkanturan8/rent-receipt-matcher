"""
Intent Classification Model Training - V2 (OCR-Aware)
Türkçe BERT ile emlak ödeme tipi sınıflandırması

Kategoriler:
- kira_odemesi
- aidat_odemesi
- kapora_odemesi
- depozito_odemesi

Version: 2.0
Dataset: data/synthetic_ocr_aware/intent_ocr_aware.json (600 samples)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from datasets import Dataset
import matplotlib.pyplot as plt
import seaborn as sns


# Model seçenekleri
TURKISH_BERT_MODELS = {
    "dbmdz": "dbmdz/bert-base-turkish-cased",
    "distilbert": "dbmdz/distilbert-base-turkish-cased",
    "berturk": "savasy/bert-base-turkish-sentiment-cased",
}

# Label mapping
LABEL2ID = {
    "kira_odemesi": 0,
    "aidat_odemesi": 1,
    "kapora_odemesi": 2,
    "depozito_odemesi": 3
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


class IntentClassifierTrainer:
    def __init__(
        self,
        model_name: str = "dbmdz/distilbert-base-turkish-cased",
        output_dir: str = "models/v2_ocr_aware/intent_classifier",
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
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=len(LABEL2ID),
            id2label=ID2LABEL,
            label2id=LABEL2ID
        )
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"💻 Device: {self.device}")
    
    def load_data(self, data_path: str) -> Tuple[Dataset, Dataset, Dataset]:
        """JSON dataset'i yükle ve train/val/test split yap"""
        print(f"\n📂 Loading data from: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Total samples: {len(data)}")
        
        # Label dağılımını göster
        label_counts = {}
        for item in data:
            label = item['label']
            label_counts[label] = label_counts.get(label, 0) + 1
        
        print("\n📈 Label distribution:")
        for label, count in label_counts.items():
            print(f"  {label}: {count} samples")
        
        # Convert labels to IDs
        for item in data:
            item['label_id'] = LABEL2ID[item['label']]
        
        # Train/Val/Test split (70/15/15)
        train_data, temp_data = train_test_split(
            data, test_size=0.3, random_state=42, stratify=[d['label'] for d in data]
        )
        val_data, test_data = train_test_split(
            temp_data, test_size=0.5, random_state=42, stratify=[d['label'] for d in temp_data]
        )
        
        print(f"\n✂️ Split:")
        print(f"  Train: {len(train_data)} samples")
        print(f"  Val: {len(val_data)} samples")
        print(f"  Test: {len(test_data)} samples")
        
        # Convert to HuggingFace Dataset
        train_dataset = Dataset.from_list(train_data)
        val_dataset = Dataset.from_list(val_data)
        test_dataset = Dataset.from_list(test_data)
        
        return train_dataset, val_dataset, test_dataset
    
    def preprocess_function(self, examples):
        """Tokenization"""
        return self.tokenizer(
            examples['text'],
            truncation=True,
            max_length=self.max_length,
            padding=False  # Dynamic padding will be handled by DataCollator
        )
    
    def compute_metrics(self, eval_pred):
        """Evaluation metrics"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        
        accuracy = accuracy_score(labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='weighted', zero_division=0
        )
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
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
            self.preprocess_function,
            batched=True,
            remove_columns=['id', 'text', 'label']
        )
        val_dataset = val_dataset.map(
            self.preprocess_function,
            batched=True,
            remove_columns=['id', 'text', 'label']
        )
        
        # Rename label_id to labels for Trainer
        train_dataset = train_dataset.rename_column("label_id", "labels")
        val_dataset = val_dataset.rename_column("label_id", "labels")
        
        # Data collator for dynamic padding
        data_collator = DataCollatorWithPadding(tokenizer=self.tokenizer)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=0.01,
            eval_strategy="epoch",  # updated from evaluation_strategy
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=10,
            warmup_steps=100,
            save_total_limit=2,
            report_to="none",  # Disable wandb/tensorboard
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
            self.preprocess_function,
            batched=True,
            remove_columns=['id', 'text', 'label']
        )
        test_dataset = test_dataset.rename_column("label_id", "labels")
        
        # Predict
        predictions = trainer.predict(test_dataset)
        pred_labels = np.argmax(predictions.predictions, axis=1)
        true_labels = predictions.label_ids
        
        # Classification report
        print("📈 Classification Report:")
        print(classification_report(
            true_labels,
            pred_labels,
            target_names=list(LABEL2ID.keys()),
            digits=4
        ))
        
        # Confusion matrix
        cm = confusion_matrix(true_labels, pred_labels)
        self.plot_confusion_matrix(cm)
        
        # Save results
        results = {
            "test_metrics": predictions.metrics,
            "classification_report": classification_report(
                true_labels,
                pred_labels,
                target_names=list(LABEL2ID.keys()),
                output_dict=True
            )
        }
        
        with open(self.output_dir / "test_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Results saved to: {self.output_dir / 'test_results.json'}")
    
    def plot_confusion_matrix(self, cm: np.ndarray):
        """Confusion matrix görselleştirme"""
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=list(LABEL2ID.keys()),
            yticklabels=list(LABEL2ID.keys())
        )
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        
        save_path = self.output_dir / "confusion_matrix.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Confusion matrix saved to: {save_path}")
        plt.close()


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("🎯 Intent Classification Model Training")
    print("=" * 60)
    
    # Paths (v2 - OCR Aware)
    data_path = "data/v2_ocr_aware/intent_ocr_aware.json"
    output_dir = "models/v2_ocr_aware/intent_classifier"
    
    # Initialize trainer
    trainer_obj = IntentClassifierTrainer(
        model_name="dbmdz/distilbert-base-turkish-cased",  # Daha hızlı
        output_dir=output_dir,
        max_length=128
    )
    
    # Load data
    train_dataset, val_dataset, test_dataset = trainer_obj.load_data(data_path)
    
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
