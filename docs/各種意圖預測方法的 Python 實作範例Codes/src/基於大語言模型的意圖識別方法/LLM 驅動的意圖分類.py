'''
1.1 LLM 驅動的意圖分類（Fine-tune BERT）
'''

from transformers import BertTokenizerFast, BertForSequenceClassification, Trainer, TrainingArguments
import torch
from datasets import load_dataset

# 1. 載入數據集（範例：CSV 包含 text, intent_label）
ds = load_dataset("csv", data_files="intent_data.csv")
tokenizer = BertTokenizerFast.from_pretrained("bert-base-chinese")

def preprocess(examples):
    return tokenizer(examples["text"], truncation=True, padding=True)
ds = ds.map(preprocess, batched=True)
ds = ds.rename_column("intent_label", "labels")
ds.set_format(type="torch", columns=["input_ids","attention_mask","labels"])

# 2. 載入預訓練模型
model = BertForSequenceClassification.from_pretrained("bert-base-chinese", num_labels=ds["train"].features["labels"].num_classes)

# 3. 訓練設定
args = TrainingArguments(
    output_dir="out_llm_intent",
    evaluation_strategy="epoch",
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    logging_dir="logs"
)
trainer = Trainer(model=model, args=args, train_dataset=ds["train"], eval_dataset=ds["validation"])
trainer.train()
