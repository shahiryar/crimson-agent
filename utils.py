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
    if given=="values": entity = extract_entity_given_values(label, utterance)
    if given=="regex": entity = extract_entity_given_regex(label, utterance)
    if given=="nlp": entity = extract_entity_given_nlp(label, utterance)
    return entity




def get_missing_context(active_intent: dict, keys: list) -> list:
  """
  Returns the keys in the 'keys' list that are not present in the 'active_intent' dictionary.

  Args:
      active_intent: A dictionary.
      keys: A list of keys.

  Returns:
      A list of missing keys.
  """
  return [key for key in keys if key not in active_intent]

import streamlit as st
import json

@st.cache_data
def load_data():
    st.session_state["messages"] = []
    st.session_state["active_intent"] = None
    st.session_state["active_context"] = {}
    st.session_state["required_context"] = []
    st.session_state["active_topic"] = None
    st.session_state["fallback_count"] = 0
    st.session_state["held_fulfilment"] = None
    st.session_state["customer_mood_score"] = 0.0
    st.session_state["customer_mood"] = 'NEUTRAL'

    with open("./entities.json") as file:
        st.session_state["entities"] = json.load(file)
    with open("./intents.json") as file:
        st.session_state["intents"] = json.load(file)

@st.cache_resource
def load_intent_classifier():
    from transformers import pipeline
    return pipeline("text-classification", model="shahiryar/crimson-agent")

@st.cache_resource
def load_sentiment_analyser():
  from transformers import pipeline
  return pipeline("sentiment-analysis")
