# Modular function to train a classification model
from transformers.keras_callbacks import KerasMetricCallback
import os
from dotenv import load_dotenv
import json
from huggingface_hub import login
import sys
from datasets import Dataset
import pandas as pd
from transformers import DataCollatorWithPadding
import evaluate
from transformers import TFAutoModelForSequenceClassification
import numpy as np
from transformers import create_optimizer
import tensorflow as tf
from transformers import AutoTokenizer
from transformers.keras_callbacks import PushToHubCallback

sys.path.insert(1, '../')  # Adjust path as needed
load_dotenv()

# Function to load and prepare intent data
def load_intent_data(intents_file_path, entities_file_path):
    with open(intents_file_path, 'r') as intents_file:
        intents = json.load(intents_file)
    
    # Entities aren't directly used in this script but are loaded for potential future use
    with open(entities_file_path, 'r') as entities_file:
        entities = json.load(entities_file)  
    
    class_intents, label_col, text_col = [], [], []
    for intent, data in intents.items():
        if data["trainable"]:
            class_intents.append(intent)
            for phrase in data["training_phrases"]:
                text_col.append(phrase)
                label_col.append(intent)

    df = pd.DataFrame({"text": text_col, "label": label_col})
    id2label = {i: intent for i, intent in enumerate(class_intents)}
    label2id = {intent: i for i, intent in enumerate(class_intents)}
    df.replace(label2id, inplace=True)

    return Dataset.from_pandas(df, preserve_index=False), id2label, label2id

# Function to preprocess the dataset
def preprocess_dataset(dataset, tokenizer_name):
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    def preprocess_function(examples):
        return tokenizer(examples["text"], truncation=True)
    return dataset.map(preprocess_function), tokenizer

# Function to compute evaluation metrics
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    accuracy = evaluate.load("accuracy")
    return accuracy.compute(predictions=predictions, references=labels)

# Main training function
def train_classification_model(hf_token,intents_file_path, entities_file_path, tokenizer_name, hf_repo_name, model_output_dir=""):
    login(hf_token)
    dataset, id2label, label2id = load_intent_data(intents_file_path, entities_file_path)
    tokenized_dataset, tokenizer = preprocess_dataset(dataset, tokenizer_name)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="tf")

    batch_size = 7
    num_epochs = 15
    batches_per_epoch = len(tokenized_dataset) // batch_size
    total_train_steps = int(batches_per_epoch * num_epochs)
    optimizer, schedule = create_optimizer(init_lr=2e-5, num_warmup_steps=0, num_train_steps=total_train_steps)

    num_intents = len(id2label)
    model = TFAutoModelForSequenceClassification.from_pretrained(
        tokenizer_name, num_labels=num_intents, id2label=id2label, label2id=label2id
    )

    tf_train_set = model.prepare_tf_dataset(
        tokenized_dataset,
        shuffle=True,
        batch_size=batch_size,
        collate_fn=data_collator,
    )

    model.compile(optimizer=optimizer)

    push_to_hub_callback = PushToHubCallback(
        output_dir=hf_repo_name,
        tokenizer=tokenizer,
    )

    metric_callback = KerasMetricCallback(metric_fn=compute_metrics, eval_dataset=tf_train_set)

    callbacks = [metric_callback, push_to_hub_callback]

    model.fit(x=tf_train_set, epochs=num_epochs, callbacks=callbacks)

    if model_output_dir:
        model.save_pretrained(model_output_dir)
    
    

# Example usage:
if __name__ == "__main__":
    # Define these parameters before running
    HF_TOKEN = os.getenv("HF-TOKEN") # Huggingface token
    INTENTS_FILE_PATH = "./intents.json"  # Path to your intents.json
    ENTITIES_FILE_PATH = "./entities.json"  # Path to your entities.json
    TOKENIZER_NAME = "distilbert-base-uncased" 
    HF_REPO_NAME = "your-repo-name"  # Replace with your actual Hugging Face repo name
    MODEL_OUTPUT_DIR = ""  # Set to desired output directory if saving locally

    train_classification_model(HF_TOKEN, INTENTS_FILE_PATH, ENTITIES_FILE_PATH, 
                              TOKENIZER_NAME, HF_REPO_NAME, MODEL_OUTPUT_DIR)
    
