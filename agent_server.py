from flask import Flask, request
from flask import session as FlaskSession
from utils import *
from agent import Agent
from session import Session as AgentSession
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

def create_agent():
    intents_classifier = load_intent_classifier( model="shahiryar/crimson-agent", revision="29c3aeb9544b8ba8132bd06347a28a5acb5ba43c")
    sentiment_analyser = load_sentiment_analyser()

    agent = Agent(intents_classifier, sentiment_analyser)
    return agent


agent = create_agent()



@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Get the incoming message
    incoming_msg = request.values.get('Body', '').strip()
    sender_number = request.values.get('From', '').strip()
    sender_profile_name = request.values.get('ProfileName', '')
    waID = request.values.get('WaId', '')

    print(request.values)
    agent_reply = agent.process_input(incoming_msg)
    agent_reply = agent_reply["reply"]

    

    # Start our TwiML response
    resp = MessagingResponse()

    # Add a message that echoes the incoming message
    resp.message(f"{agent_reply}")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)


