def extract_entity_given_values(values, utterance):
  for val in values:
    if val in utterance:
      return val
  return None

def extract_entity_given_regex(regex, utterance):
  import re
  from typing import Pattern
  pattern = regex  # Regex pattern to match exactly 4 consecutive digits
  match = re.search(pattern, utterance)

  if match:
      return match.group(0)  # Extract the matched PIN
  else:
      return None
def extract_entity_given_nlp(label, utterance):
  import spacy
  nlp=spacy.load("en_core_web_sm")
  doc = nlp(utterance)
  for ent in doc.ents:
    if ent.label_ == label:
      return ent.text
  return None

def graceful_shutdown(context=None):
  message = "I am trying my best to give you quality service. However, currently, I am not in the best position to help you with this.\nPlease don't mind, I am elevating you to a human agent. Thank you!"
  #send context on to the Human Agent
  if context: pass
  return message

def extract_entity(given, label, utterance):
    if given=="values": entity = extract_entity_given_values(label, utterance.lower())
    if given=="regex": entity = extract_entity_given_regex(label, utterance)
    if given=="nlp": entity = extract_entity_given_nlp(label, utterance)
    return entity




def get_missing_context(active_context: dict, keys: list) -> list:
  """
  Returns the keys in the 'keys' list that are not present in the 'active_context' dictionary.

  Args:
      active_context: A dictionary.
      keys: A list of keys.

  Returns:
      A list of missing keys.
  """
  return [key for key in keys if key not in active_context]

import streamlit as st


@st.cache_resource
def load_intent_classifier(model, revision):
    from transformers import pipeline
    return pipeline("text-classification", model=model, revision=revision)

@st.cache_resource
def load_sentiment_analyser():
  from transformers import pipeline
  return pipeline("sentiment-analysis")

def is_cancel_intent(text):
    """Detects whether the given text indicates a desire to cancel the current process.

    Args:
        text (str): The user's input text.

    Returns:
        bool: True if cancellation intent is detected, False otherwise.
    """
    import spacy

    nlp = spacy.load('en_core_web_sm')  # Load the language model
    from spacy.matcher import Matcher
    
    doc = nlp(text)

    # Explicit keyword matching
    cancel_words = ["cancel", "stop","n't","not", "nevermind", "forget", "leave"]
    if any(token.text.lower() in cancel_words for token in doc):
        return True

    print("Rule based")

    # Rule-based patterns (customize these further)
    patterns = [
        [{"POS": "VERB"}, {"LOWER": "cancel"}],  
        [{"DEP": "ROOT"}, {"LOWER": "forget"}, {"LOWER": "it"}],
        [{"TEXT": "Ugh"}, {"LOWER": "nevermind"}], 
        [{"DEP": "neg"}, {"POS": "VERB"}, {"OP": "?"}, {"LOWER": "continue"}],
        [{"LOWER": "i"}, {"POS": "VERB"},{"DEP": "neg"}, {"LOWER": "want"}, {"LOWER": "to"}, 
           {"LOWER": "do"}, {"LOWER": "this"}],
        [{"LOWER": {"REGEX": "^(i|do)n't"}}, {"LOWER": "want"}, {"LOWER": "to"}, 
           {"LOWER": "do"}, {"LOWER": "this"}] ,
        [{"LOWER": "i"}, {"DEP": "neg"}, {"LOWER": "want"}, {"LOWER": "to"}, 
           {"POS": "VERB"}, {"LOWER": "this"}],
        [{"LOWER": "actually"}, {"OP": "?"}, {"LOWER": "i"}, {"LOWER": "want"}, 
           {"LOWER": "to"}, {"ENT_TYPE": "intent_name"}],
        [{"TEXT": {"REGEX": "^ugh|argh|grr"}}, {"OP": "?"},  
           {"LOWER": "just"}, {"LOWER": "cancel"}],
        [{"LOWER": "this"}, {"LOWER": "is"}, {"LOWER": "not"}, {"POS": "VERB"}, 
           {"OP": "?"}, {"LOWER": "forget"}, {"LOWER": "it"}],
        [{"LOWER": "actually"}, {"OP": "?"}, {"LOWER": "never"}, {"LOWER": "mind"}],
        [{"LOWER": "never"}, {"LOWER": "mind"}, 
           {"OP": "?"}, {"LOWER": "forget"}, {"LOWER": "it"}],
        [{"LOWER": "i"}, {"POS": "VERB"}, {"DEP": "neg"}, {"LOWER": "want"}, {"LOWER": "to"}, 
           {"POS": "VERB"}, {"LOWER": "this"}]   
    ]

    matcher = Matcher(nlp.vocab)
    for pattern in patterns:
        matcher.add(f"pattern_{pattern}", [pattern]) 

    matches = matcher(doc)
    return len(matches) > 0


def determine_intent(active_context_label, utterance, no_match_threshold, classifier, intents):
  print(f"Determining Intent with Active Context : {active_context_label}")

  classes = classifier(utterance, top_k=None)
  determined_intent = None
  probable_classes = []

  for el in classes:
    input_context = intents[el["label"]]["input_context"]
    if not(input_context and input_context != active_context_label):
      probable_classes.append(el)

  most_probable_intent = max(probable_classes, key=lambda item: item['score'])
  if most_probable_intent["score"] > no_match_threshold:
    determined_intent = most_probable_intent
  else:
    determined_intent = {"label": "no-match-intent", "score":1-most_probable_intent["score"]}

  return determined_intent

def get_blank_context():
   return { "context_label":"", "max_count":0}


def send_whatsapp_message(text):
  from twilio.rest import Client

  import os
  from dotenv import load_dotenv
  if load_dotenv():
      try:
        account_sid = os.getenv("TWILLIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
      except:
         print("Twillio account or auth token not found in the environment")
         return False
  else:
     print("Environment Variables could not loaded, make sure your have the `.env` file")
     return False

  client = Client(account_sid, auth_token)

  message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=text,
    to='whatsapp:+923364050797'
  )

  if message: return True
  else: return False
