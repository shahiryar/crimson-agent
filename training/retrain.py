#Loading variables from dotenv
import os
from dotenv import load_dotenv

load_dotenv()

from huggingface_hub import login

login(token=os.getenv("HF-TOKEN"))

import json

with open("../intents.json", 'r') as intents_file:
    intents = json.load(intents_file)

with open("../entities.json", 'r') as entities_file:
    entities = json.load(entities_file)

import sys
sys.path.insert(1, '../')

from tensorflow import keras

from datasets import Dataset

class_intents = []
label_col = []
text_col = []

for el in intents.items():
  if (el[1]["trainable"]):
    class_intents.append(el[0])
    for doc in el[1]["training_phrases"]:
      text_col.append(doc)
      label_col.append(el[0])

import pandas as pd
df = pd.DataFrame({"text": text_col, "label": label_col})

id2label = {i: intent for i, intent in enumerate(class_intents)}
label2id = {intent: i for i, intent in enumerate(class_intents)}

df.replace(label2id, inplace=True)

train_dataset = Dataset.from_pandas(df, preserve_index=False)

from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

#preprocessing function to tokenize text and truncate sequences to be no longer than DistilBERT’s maximum input length:
def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True)

#Apply the preprocessing function over the entire dataset, use 🤗 Datasets map function
tokenized_papers = train_dataset.map(preprocess_function)


from transformers import DataCollatorWithPadding

data_collator = DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="tf")

import evaluate

accuracy = evaluate.load("accuracy")

#create a function that passes your predictions and labels to compute to calculate the accuracy:
import numpy as np


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return accuracy.compute(predictions=predictions, references=labels)

from transformers import create_optimizer
import tensorflow as tf

batch_size = 7
num_epochs = 15
batches_per_epoch = len(tokenized_papers) // batch_size
total_train_steps = int(batches_per_epoch * num_epochs)
optimizer, schedule = create_optimizer(init_lr=2e-5, num_warmup_steps=0, num_train_steps=total_train_steps)


from transformers import TFAutoModelForSequenceClassification
num_intents = len(class_intents)
model = TFAutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", num_labels=num_intents, id2label=id2label, label2id=label2id
)

tf_train_set = model.prepare_tf_dataset(
    tokenized_papers,
    shuffle=True,
    batch_size=batch_size,
    collate_fn=data_collator,
)

import tensorflow as tf
#==============================
#Compile Text Classifier Model
#==============================
model.compile(optimizer=optimizer)  # No loss argument!

from transformers.keras_callbacks import PushToHubCallback

push_to_hub_callback = PushToHubCallback(
    output_dir="crimson-agent",
    tokenizer=tokenizer,
)

from transformers.keras_callbacks import KerasMetricCallback

metric_callback = KerasMetricCallback(metric_fn=compute_metrics, eval_dataset=tf_train_set)

callbacks = [metric_callback, push_to_hub_callback]

model.fit(x=tf_train_set, epochs=num_epochs, callbacks=callbacks)


