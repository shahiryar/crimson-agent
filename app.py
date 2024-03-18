import streamlit as st
from streamlit_chat import message
import random
from utils import *

import json

@st.cache_data
def load_data():
    st.session_state["messages"] = []
    st.session_state["active_intent"] = None
    st.session_state["active_intent_confidence_score"] = 1.0
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
    with open("./agent-config.json") as file:
        st.session_state["agent_config"] = json.load(file)
        for key, val in st.session_state.agent_config.items():
            st.session_state[key] = val
            


load_data()
intents_classifier = load_intent_classifier()
sentiment_analyser = load_sentiment_analyser()
st.session_state["intent-match-threshold"] = st.slider('No Intent Match Threshold?', 0.0, 1.0, st.session_state["intent-match-threshold"])


print("\n\n-----------------Rendering--------------")
print("Current Status at Start ")
print("Active Intent : ", st.session_state.active_intent) #metadata
print("Active Context : ", st.session_state.active_context) #metadata
print("Required Context : ", st.session_state.required_context) #metadata
print("Active Topic : ", st.session_state.active_topic)

user_input = st.chat_input("Your Message", key="1234") #TODO generate clock bound random key instead

print("User input taken : ", user_input)
if user_input:
    customer_sentiment = sentiment_analyser(user_input)[0]
    st.session_state.customer_mood = customer_sentiment["label"]
    st.session_state.customer_mood_score = customer_sentiment["score"]
    


if user_input and not st.session_state.active_topic: 
    print("User Input : ", user_input, " and NO active topic ")
    
    intents_classifier_result = intents_classifier(str(user_input))
    current_intent, intent_score = intents_classifier_result[0]["label"] , intents_classifier_result[0]["score"]

    if intent_score < st.session_state["intent-match-threshold"]:
            current_intent = 'no-match-intent'
            intent_score = 1- intent_score
    
    st.session_state["active_intent"] = current_intent
    st.session_state["active_intent_confidence_score"] = intent_score
    
    print("Intent Activated : ", current_intent)
    intent_obj = st.session_state.intents[current_intent]
    print("Intent Object : ", intent_obj)
    reply = random.choice(intent_obj["responses"])


    if intent_obj["params"] != 'None':
        print("Intent needs Context")
        st.session_state.required_context = intent_obj["params"]
        st.session_state.active_topic = st.session_state.required_context[0] if len(st.session_state.required_context) else None
        if len(st.session_state.required_context):
            del st.session_state.required_context[0]
        st.session_state.messages.append(str(user_input))
        user_input = None
        reply = "Alright, I will need some information to do this.\n"
        entity_obj = st.session_state.entities[st.session_state.active_topic]
        reply+=random.choice(entity_obj["reprompt"])
        st.session_state.messages.append(reply)
    else:
        print("Intent does NOT need Context")
        st.session_state.required_context = None





    if not st.session_state.required_context: 
        print("Appending messages: ", user_input)
        st.session_state.messages.append(str(user_input))
        print("Appending messages: ", reply)
        st.session_state.messages.append(str(reply))


print("Before the Second If Condition") 
if user_input and st.session_state.active_topic:
    print("User Input : ", user_input, " and Active Topic : ", st.session_state.active_topic)
    st.session_state.messages.append(str(user_input))
    entity_obj = st.session_state.entities[st.session_state.active_topic]

    entity_parameter = extract_entity(entity_obj["given"], entity_obj["values"], str(user_input))
    print()
    if not entity_parameter:
        if st.session_state.fallback_count <2:     
            print("Appending Fallback Prompt for topic : ", st.session_state.active_topic )
            st.session_state.messages.append(random.choice(entity_obj["fallback_prompt"]))
            print("Context and Active Topic Remained the same")
            st.session_state.fallback_count+=1
        else:
            st.session_state.active_context["active_intent"] = st.session_state.active_intent
            st.session_state.active_context["active_topic"] = st.session_state.active_topic
            reply = graceful_shutdown(st.session_state.active_context)
            st.session_state.messages.append(reply)
    else:
        st.session_state.active_context[st.session_state.active_topic] = entity_parameter
        print(f"Param {st.session_state.active_context} added to the Context")
        print(f"Updating active topic")
        st.session_state.active_topic = st.session_state.required_context[0] if len(st.session_state.required_context) else None
        print(f"Action Topic is now {st.session_state.active_topic}")
        if len(st.session_state.required_context):
            del st.session_state.required_context[0]

        if st.session_state.active_topic:
            print("Appending Re-Prompt for topic : ", st.session_state.active_topic )
            entity_obj = st.session_state.entities[st.session_state.active_topic]

            st.session_state.messages.append(random.choice(entity_obj["reprompt"]))
            print("Active Context Updated with value for active topic ")
        print("Active Topic Changed to : ", st.session_state.active_topic)

print("Outside the Second If Condtion")
if st.session_state.active_intent:

    if st.session_state.active_topic is None and  set(st.session_state.intents[st.session_state.active_intent]["params"]).issubset(set(st.session_state.active_context.keys())):
        st.session_state.messages.append(random.choice(st.session_state.intents[st.session_state.active_intent]["responses"]))


st.write("Active Intent : ", st.session_state.active_intent, " Score : ", st.session_state["active_intent_confidence_score"]) #metadata

st.write("Customer Mood : ", st.session_state.customer_mood, " ", {"NEGATIVE": '😑', "NEUTRAL": '🤔', "POSITIVE": '😍'}[st.session_state.customer_mood], " Score : ", st.session_state.customer_mood_score)
#st.write("Active Context : ", st.session_state.active_context) #metadata
#st.write("Required Context : ", st.session_state.required_context) #metadata
#st.write("Active Topic : ", st.session_state.active_topic)

print("Statuses written: ")
print("Active Intent : ", st.session_state.active_intent) #metadata
print("Active Context : ", st.session_state.active_context) #metadata
print("Required Context : ", st.session_state.required_context) #metadata
print("Active Topic : ", st.session_state.active_topic)

print("Print Chat Starts")
for i, msg in enumerate(st.session_state.messages):
    is_user = i%2==0
    message(msg, is_user=is_user, key=f"{i}2")
print("Print Chat Ends")

print("\n----------------END of Rendering-----------------------")