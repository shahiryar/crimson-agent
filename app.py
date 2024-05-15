import streamlit as st
from streamlit_chat import message
from utils import *
from agent import Agent

@st.cache_resource
def create_agent():
    intents_classifier = load_intent_classifier( model="shahiryar/crimson-agent", revision="29c3aeb9544b8ba8132bd06347a28a5acb5ba43c")
    sentiment_analyser = load_sentiment_analyser()

    agent = Agent(intents_classifier, sentiment_analyser)
    return agent

st.session_state["messages"] = [] if not ("messages" in st.session_state.keys()) else st.session_state["messages"]
agent = create_agent()

user_input = st.chat_input("Your Message", key="1234") #TODO generate clock bound random key instead
if user_input:
    
    agent_reply = agent.process_input(user_input)["reply"]


    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "agent", "content": agent_reply})
    
for i, msg in enumerate(st.session_state.messages):
    is_user = msg["role"] == "user"
    message(msg["content"], is_user=is_user, key=f"{i}2")