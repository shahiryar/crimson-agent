import streamlit as st
from streamlit_chat import message
import random
from utils import *


load_data()
intents_classifier = load_intent_classifier()
print("\n\n-----------------Rendering--------------")
print("Current Status at Start ")
print("Active Intent : ", st.session_state.active_intent) #metadata
print("Active Context : ", st.session_state.active_context) #metadata
print("Required Context : ", st.session_state.required_context) #metadata
print("Active Topic : ", st.session_state.active_topic)

user_input = st.chat_input("Your Message", key="1234") #TODO generate clock bound random key instead

print("User input taken : ", user_input)
    


if user_input and not st.session_state.active_topic: 
    print("User Input : ", user_input, " and NO active topic ")
    

    current_intent = intents_classifier(str(user_input))[0]["label"]
    intent_obj = st.session_state.intents[current_intent]
    reply = random.choice(intent_obj["responses"])
    st.session_state["active_intent"] = current_intent
    print("Intent Activated : ", current_intent)

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


st.write("Active Intent : ", st.session_state.active_intent) #metadata
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