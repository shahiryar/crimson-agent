import streamlit as st
from streamlit_chat import message
import json
import random
import uuid

from utils import *



@st.cache_data
def load_data():
    with open("./entities.json") as file:
        st.session_state["entities"] = json.load(file)
    with open("./intents.json") as file:
        st.session_state["intents"] = json.load(file)
    
    st.session_state["activate_context"] = {}
    
    st.session_state["messages"] = {"user":[], "agent":[]}

def on_send_message():
    user_input = st.session_state.user_message
    user_intent = classifier(user_input)[0]['label']
    user_intent = st.session_state.intents[user_intent]
    required_params = user_intent["params"]
    #check if the active_context has the values in the params
    agent_reply = random.choice(user_intent["responses"])


    st.session_state.messages["user"].append(user_input)
    st.session_state.messages["agent"].append(agent_reply)

def comb_concat(a, b):
    """Combines two input lists by alternating elements with labels 'a' and 'b'.

    Args:
        a: The first list.
        b: The second list.

    Returns:
        A new list of tuples where elements from 'a' and 'b' are 
        interleaved and labeled with 'a' or 'b'.
    """

    result = []  # Initialize result list 

    # Use zip to pair elements, ensuring we handle lists of different lengths
    for x, y in zip(a, b):
        result.append((x, "user"))
        result.append((y, "agent"))

    # Add any remaining elements from the longer list with their label
    for item in a[len(b):]:
        result.append((item, "user"))
    for item in b[len(a):]:
        result.append((item, "agent"))
    
    return result

@st.cache_resource
def load_model():
    from transformers import pipeline
    return pipeline("sentiment-analysis", model="shahiryar/crimson-agent")

classifier = load_model()
load_data()

with st.container():
    conversation = comb_concat(st.session_state.messages["user"], st.session_state.messages["agent"])
    for msg in conversation:
        if msg[1] == "user": message(msg[0], is_user=True)
        else: message(msg[0], is_user=False, key=str(uuid.uuid4()) )

with st.container():
    st.chat_input("Your message", on_submit=on_send_message ,key="user_message")
