import streamlit as st
from streamlit_chat import message
from utils import *
from agent import Agent
from session import Session

@st.cache_resource
def create_agent():
    intents_classifier = load_intent_classifier( model="shahiryar/crimson-agent", revision="29c3aeb9544b8ba8132bd06347a28a5acb5ba43c")
    sentiment_analyser = load_sentiment_analyser()

    agent = Agent(intents_classifier, sentiment_analyser)
    return agent

@st.cache_resource
def create_session():
    return Session(create_agent())



current_session = create_session()

# Sidebar
with st.sidebar:
    # Chat interface
    st.title("Integrations")
    #check box to Integrate Whatsapp
    whatsapp_integration = st.checkbox("Integrate with WhatsApp")
    if whatsapp_integration:
        sender_number = st.text_input("Your WhatsApp number (international format):", value="+14155238886")
        receiver_number = st.text_input("Receiver's WhatsApp number (international format):", value="+923364050797")
        if st.button("Integrate"):
            if current_session.agent.integrate_whatsapp(sender_number, receiver_number):
                st.success("WhatsApp integration successful!")
            else:
                st.error("Failed to integrate with WhatsApp. Please check your credentials.")


st.session_state["messages"] = [] if not ("messages" in st.session_state.keys()) else st.session_state["messages"]
current_session.set_state("messages", st.session_state["messages"])
#agent = create_agent()

user_input = st.chat_input("Your Message", key="1234") #TODO generate clock bound random key instead
if user_input:
    
    agent_reply = current_session.interact(user_input)["reply"]


    st.session_state.messages.append({"role": "user", "content": user_input})
    #current_session.session_state["messages"].append({"role": "user", "content": user_input})

    st.session_state.messages.append({"role": "agent", "content": agent_reply})
    #current_session.session_state["messages"].append({"role": "agent", "content": agent_reply})
    
for i, msg in enumerate(st.session_state.messages):
    is_user = msg["role"] == "user"
    message(msg["content"], is_user=is_user, key=f"{i}2")

