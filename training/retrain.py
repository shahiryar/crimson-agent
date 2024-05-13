#Loading variables from dotenv
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

sys.path.insert(1, '../')
load_dotenv()

#====================================================
#  Define these Parameters before running the script
#====================================================

HF_TOKEN = os.getenv("HF-TOKEN") # Huggingface token
INTENTS_FILE_PATH = "./intents.json" # jSON file that contains the intents
ENTITIES_FILE_PATH = "./entities.json" # Entities file that contains the entities
TOKENIZER_NAME = "distilbert-base-uncased" # name of the tokenizer: for more infor check: https://huggingface.co/google-bert
HF_REPO_NAME = "crimson-agent" # Name of the repo where the model and its config will be pushed
MODEL_OUTPUT_DIR = "" # path to a local directory where the model and its config will be saved

#====================================================

login(token=HF_TOKEN)

with open(INTENTS_FILE_PATH, 'r') as intents_file:
    intents = json.load(intents_file)

with open(ENTITIES_FILE_PATH, 'r') as entities_file:
    entities = json.load(entities_file)

class_intents = []
label_col = []
text_col = []

for el in intents.items():
  if (el[1]["trainable"]):
    class_intents.append(el[0])
    for doc in el[1]["training_phrases"]:
      text_col.append(doc)
      label_col.append(el[0])

df = pd.DataFrame({"text": text_col, "label": label_col})

id2label = {i: intent for i, intent in enumerate(class_intents)}
label2id = {intent: i for i, intent in enumerate(class_intents)}

df.replace(label2id, inplace=True)

train_dataset = Dataset.from_pandas(df, preserve_index=False)

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

#preprocessing function to tokenize text and truncate sequences to be no longer than DistilBERT’s maximum input length:
def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True)

#Apply the preprocessing function over the entire dataset, use 🤗 Datasets map function
tokenized_papers = train_dataset.map(preprocess_function)

data_collator = DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="tf")

accuracy = evaluate.load("accuracy")

#create a function that passes your predictions and labels to compute to calculate the accuracy:
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return accuracy.compute(predictions=predictions, references=labels)

batch_size = 7
num_epochs = 15
batches_per_epoch = len(tokenized_papers) // batch_size
total_train_steps = int(batches_per_epoch * num_epochs)
optimizer, schedule = create_optimizer(init_lr=2e-5, num_warmup_steps=0, num_train_steps=total_train_steps)

num_intents = len(class_intents)
model = TFAutoModelForSequenceClassification.from_pretrained(
    TOKENIZER_NAME, num_labels=num_intents, id2label=id2label, label2id=label2id
)

tf_train_set = model.prepare_tf_dataset(
    tokenized_papers,
    shuffle=True,
    batch_size=batch_size,
    collate_fn=data_collator,
)

model.compile(optimizer=optimizer)
push_to_hub_callback = PushToHubCallback(
    output_dir=HF_REPO_NAME,
    tokenizer=tokenizer,
)

metric_callback = KerasMetricCallback(metric_fn=compute_metrics, eval_dataset=tf_train_set)

callbacks = [metric_callback, push_to_hub_callback]

model.fit(x=tf_train_set, epochs=num_epochs, callbacks=callbacks)
if MODEL_OUTPUT_DIR:
    model.save_pretrained(MODEL_OUTPUT_DIR)
