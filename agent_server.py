from flask import Flask, request
from flask import session as FlaskSession
from utils import *
from agent import Agent
from session import Session as AgentSession
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Function to create an instance of the Agent class
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


# Create an instance of the Agent class
agent = create_agent()

# Import the Webhook class from the integrations module
from integrations import Webhook

# Create an instance of the Webhook class for checking balance
check_balance = Webhook("check_balance")

# Sample data for the webhook call
data = {
    "name": "Shahiryar",
}

# Define the route for handling SMS messages
@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """
    Handles incoming SMS messages and generates a response.

    This function retrieves the incoming message, sender information, and WaId from the request.
    It then processes the message using the Agent object and generates a response.
    If the message contains "balance", it calls the check_balance webhook to retrieve the balance.
    Finally, it constructs a TwiML response with the generated reply and returns it.

    Returns:
        str: A TwiML response containing the agent's reply.
    """
    # Get the incoming message
    incoming_msg = request.values.get('Body', '').strip()
    sender_number = request.values.get('From', '').strip()
    sender_profile_name = request.values.get('ProfileName', '')
    waID = request.values.get('WaId', '')

    print(request.values)  # Print the request values for debugging
    agent_reply = agent.process_input(incoming_msg)  # Process the message using the Agent

    # Temporary fix: If the message contains "balance", call the webhook
    if "balance" in incoming_msg:
        agent_reply["reply"] = f"Your Balance is {check_balance.call(data)}"

    agent_reply = agent_reply["reply"]  # Extract the reply from the agent's response

    # Start the TwiML response
    resp = MessagingResponse()

    # Add a message to the response with the agent's reply
    resp.message(f"{agent_reply}")

    return str(resp)  # Return the TwiML response as a string

# Run the Flask app in debug mode
if __name__ == "__main__":
    app.run(debug=True)

