import streamlit as st
from streamlit_chat import message
from utils import *
from agent import Agent
from session import Session

# This decorator caches the result of the function call, so that it is only executed once per session.
# This is useful for functions that are expensive to execute, such as loading large models.
@st.cache_resource
def create_agent():
    """
    Creates an instance of the Agent class.

    This function loads the intent classifier and sentiment analyser models
    and initializes an Agent object with them.

    Returns:
        Agent: An instance of the Agent class.
    """
    intents_classifier = load_intent_classifier( model="shahiryar/crimson-agent", revision="29c3aeb9544b8ba8132bd06347a28a5acb5ba43c")
    sentiment_analyser = load_sentiment_analyser()

    agent = Agent(intents_classifier, sentiment_analyser)
    return agent

# This decorator caches the result of the function call, so that it is only executed once per session.
# This is useful for functions that are expensive to execute, such as loading large models.
@st.cache_resource
def create_session():
    """
    Creates an instance of the Session class.

    This function initializes a Session object with an Agent instance.

    Returns:
        Session: An instance of the Session class.
    """
    return Session(create_agent())



# Create a Session object and store it in the current_session variable.
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
            # Call the integrate_whatsapp method of the Agent object to integrate with WhatsApp.
            if current_session.agent.integrate_whatsapp(sender_number, receiver_number):
                st.success("WhatsApp integration successful!")
            else:
                st.error("Failed to integrate with WhatsApp. Please check your credentials.")


# Initialize the messages list in the session state.
st.session_state["messages"] = [] if not ("messages" in st.session_state.keys()) else st.session_state["messages"]
# Set the messages list in the session state to the messages list in the session object.
current_session.set_state("messages", st.session_state["messages"])
#agent = create_agent()

# Get the user input from the chat input field.
user_input = st.chat_input("Your Message", key="1234") #TODO generate clock bound random key instead
if user_input:
    
    # Interact with the agent using the current session and get the agent's reply.
    agent_reply = current_session.interact(user_input)["reply"]


    # Append the user input and the agent's reply to the messages list in the session state.
    st.session_state.messages.append({"role": "user", "content": user_input})
    #current_session.session_state["messages"].append({"role": "user", "content": user_input})

    st.session_state.messages.append({"role": "agent", "content": agent_reply})
    #current_session.session_state["messages"].append({"role": "agent", "content": agent_reply})
    
# Iterate over the messages list in the session state and display them in the chat interface.
for i, msg in enumerate(st.session_state.messages):
    is_user = msg["role"] == "user"
    message(msg["content"], is_user=is_user, key=f"{i}2")

