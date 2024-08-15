# Modular function to train a classification model
from transformers.keras_callbacks import KerasMetricCallback
import os
from dotenv import load_dotenv
import sys
import json
from huggingface_hub import login
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

# Function to load and prepare intent data
def load_intent_data(intents_file_path, entities_file_path):
    """
    Loads intent and entity data from JSON files and prepares it for training.

    Args:
        intents_file_path (str): Path to the JSON file containing intents data.
        entities_file_path (str): Path to the JSON file containing entities data.

    Returns:
        tuple: A tuple containing the dataset, id2label mapping, and label2id mapping.

    Example usage:
        >>> dataset, id2label, label2id = load_intent_data("./intents.json", "./entities.json")

    Steps:
        1. Loads intents and entities data from the specified JSON files.
        2. Filters intents based on the "trainable" flag.
        3. Creates a Pandas DataFrame with "text" and "label" columns.
        4. Converts labels to numerical IDs using label2id mapping.
        5. Creates a Hugging Face Dataset from the DataFrame.

    Notes:
        - The intents file should be a valid JSON containing training phrases and labels.
        - Entities file is currently not utilized but is loaded for potential future use.
    """
    sys.path.insert(1, '../')  # Adjust path as needed
    load_dotenv()
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
    """
    Preprocesses the dataset using the specified tokenizer.

    Args:
        dataset (Dataset): The Hugging Face Dataset to preprocess.
        tokenizer_name (str): Name of the pre-trained tokenizer to use (e.g., 'distilbert-base-uncased').

    Returns:
        tuple: A tuple containing the preprocessed dataset and the tokenizer.

    Example usage:
        >>> preprocessed_dataset, tokenizer = preprocess_dataset(dataset, "distilbert-base-uncased")

    Steps:
        1. Loads the tokenizer from the specified name.
        2. Applies tokenization and truncation to the dataset.
    """
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    def preprocess_function(examples):
        return tokenizer(examples["text"], truncation=True)
    return dataset.map(preprocess_function), tokenizer

# Function to compute evaluation metrics
def compute_metrics(eval_pred):
    """
    Computes accuracy metric for model evaluation.

    Args:
        eval_pred (tuple): A tuple containing predictions and labels.

    Returns:
        dict: A dictionary containing the accuracy score.

    Example usage:
        >>> metrics = compute_metrics(eval_pred)
        >>> print(metrics)
    """
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    accuracy = evaluate.load("accuracy")
    return accuracy.compute(predictions=predictions, references=labels)

# Main training function
def train_classification_model(hf_token,intents_file_path, entities_file_path, tokenizer_name, hf_repo_name, model_output_dir=""):
    """
    Trains a sequence classification model using the provided dataset and uploads the trained model to Hugging Face Hub.

    Args:
        hf_token (str): The Hugging Face authentication token.
        intents_file_path (str): Path to the JSON file containing intents data.
        entities_file_path (str): Path to the JSON file containing entities data.
        tokenizer_name (str): Name of the pre-trained tokenizer to use (e.g., 'distilbert-base-uncased').
        hf_repo_name (str): Name of the Hugging Face repository to push the trained model to.
        model_output_dir (str, optional): Directory to save the trained model locally. Default is "" (do not save locally).

    Returns:
        None

    Example usage:
        >>> HF_TOKEN = os.getenv("HF-TOKEN")
        >>> INTENTS_FILE_PATH = "./intents.json"
        >>> ENTITIES_FILE_PATH = "./entities.json"
        >>> TOKENIZER_NAME = "distilbert-base-uncased"
        >>> HF_REPO_NAME = "your-repo-name"
        >>> MODEL_OUTPUT_DIR = "./model_output"
        >>> train_classification_model(HF_TOKEN, INTENTS_FILE_PATH, ENTITIES_FILE_PATH, 
                                      TOKENIZER_NAME, HF_REPO_NAME, MODEL_OUTPUT_DIR)

    Steps:
        1. Authenticates with Hugging Face Hub using the provided token.
        2. Loads and processes the intents and entities data from the provided file paths.
        3. Preprocesses the dataset using the specified tokenizer.
        4. Initializes the model and optimizer.
        5. Converts the dataset into a TensorFlow dataset.
        6. Compiles and trains the model, with evaluation and push-to-hub callbacks.
        7. Optionally saves the trained model to a local directory if specified.

    Notes:
        - Ensure the intents file is a valid JSON containing the training phrases and labels.
        - Entities file is currently not utilized but is loaded for potential future use.
        - The tokenizer and model name should correspond to a model available on Hugging Face Model Hub.
    """
    
    
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
    
    save_agent_config(hf_repo_name, hf_repo_name, model_output_dir, intents_file_path, entities_file_path )
    

import json
def save_agent_config(repo,model_name,intents_path, entities_path,local_model_path=""):
    """
    Saves the agent configuration to a JSON file.

    Args:
        repo (str): The Hugging Face repository name.
        model_name (str): The model name.
        intents_path (str): The path to the intents file.
        entities_path (str): The path to the entities file.
        local_model_path (str, optional): The path to the local model directory. Defaults to "".

    Returns:
        None

    Example usage:
        >>> save_agent_config("your-repo-name", "your-model-name", "./intents.json", "./entities.json", "./model_output")
    """
    with open("../artefacts/agent-config.json", 'w') as config_file:
        data = {
            "hf_repo_name": repo,
            "model_name": model_name,
            "intents_path": intents_path,
            "entities_path": entities_path,
        }
        if local_model_path:
            data["local_model"] = local_model_path
        json.dump(data, config_file)


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
    
