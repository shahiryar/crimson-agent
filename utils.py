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

def graceful_shutdown(context):
  print("I am just a bot, trying my best to give you quality service. Please don't mind, I am elevating you to a human agent. Thank you")
  print(context)

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

