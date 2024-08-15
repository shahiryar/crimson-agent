import random
import json
from utils import *
from string import Template
from nlp import dynamo
from integrations import Whatsapp, Webhook

class Agent:
    """
    Represents a conversational agent that interacts with users, understands their intents, and fulfills their requests.

    Attributes:
        active_intent (str): The currently identified intent of the user.
        active_intent_confidence_score (float): The confidence score of the identified intent.
        active_context (dict): A dictionary containing the current context of the conversation, including user input and extracted entities.
        required_context (list): A list of entities that are required to fulfill the active intent.
        active_topic (str): The current entity being extracted from user input.
        fallback_count (int): The number of times the agent has failed to extract an entity from user input.
        held_fulfilment (str): The name of the fulfilment that is currently being held.
        customer_mood_score (float): The sentiment score of the user's last message.
        customer_mood (str): The sentiment label of the user's last message (e.g., "POSITIVE", "NEGATIVE", "NEUTRAL").
        intent_match_threshold (float): The minimum confidence score required for an intent to be considered a match.
        messages (list): A list of messages exchanged between the agent and the user.
        dynamo_identity (str): A description of the agent's persona and role in the conversation.
        context_history (list): A list of entities that have been extracted from user input.
        use_dynamo (bool): Whether to use the Dynamo natural language processing library for response generation.
        whatsappClient (Whatsapp): The WhatsApp client object for sending messages.
        whatsappIntegrated (bool): Whether the agent is integrated with WhatsApp.
        fulfilment_path (str): The path to the JSON file containing fulfilment configurations.
        fulfilments (dict): A dictionary of fulfilment objects, keyed by their names.
        entities (dict): A dictionary of entities, keyed by their names.
        intents (dict): A dictionary of intents, keyed by their names.
        agent_config (dict): A dictionary containing agent configuration settings.
        intents_classifier (object): The intent classification model.
        sentiment_analyser (object): The sentiment analysis model.

    Methods:
        process_input(user_input): Processes user input, identifies intent, extracts entities, and generates a response.
        cancel_slot_filling(): Cancels the current slot filling process.
        process_no_topic(user_input): Processes user input when there is no active topic to fill.
        prompt_for_next_param(): Prompts the user for the next required entity.
        has_context_for_fullfilment(): Checks if the agent has all the required context to fulfill the active intent.
        fullfil_active_intent(): Fulfills the active intent using the available context.
        process_with_topic(user_input): Processes user input when there is an active topic to fill.
        integrate_whatsapp(sender_number, receiver_number): Integrates the agent with WhatsApp using Twilio.
        send_whatsapp_message(message): Sends a message to the WhatsApp receiver.
        load_integrations(): Loads fulfilment configurations from a JSON file.
    """
    def __init__(self, intent_classifier, sentiment_analyser, intents_path="./intents.json", entities_path= "./entities.json", agent_config_path="./agent-config.json" , fulfilments_path = "./fulfilments.json"):
        """
        Initializes the Agent object.

        Args:
            intent_classifier (object): The intent classification model.
            sentiment_analyser (object): The sentiment analysis model.
            intents_path (str): The path to the JSON file containing intent configurations.
            entities_path (str): The path to the JSON file containing entity configurations.
            agent_config_path (str): The path to the JSON file containing agent configuration settings.
            fulfilments_path (str): The path to the JSON file containing fulfilment configurations.
        """
        self.active_intent = None
        self.active_intent_confidence_score = 1.0
        self.active_context = {"__context__": get_blank_context()}
        self.required_context = []
        self.active_topic = None
        self.fallback_count = 0
        self.held_fulfilment = None
        self.customer_mood_score = 0.0
        self.customer_mood = 'NEUTRAL'
        self.intent_match_threshold = 0.3
        self.messages = []
        self.dynamo_identity= "You are a helpful assistent name Crimson. You help users manage their subscriptions. You can help them signup or signff. You consider the conversation history to respond to the user. In the conversation your role is as agent. "
        self.context_history = []
        self.use_dynamo = False
        self.whatsappClient = None
        self.whatsappIntegrated = False

        self.fulfilment_path = fulfilments_path
        self.fulfilments = {}
        self.load_integrations()
        #self.agent_name
        #self.agent_uid

        with open(entities_path) as file:
            self.entities = json.load(file)
        with open(intents_path) as file:
            self.intents = json.load(file)
        with open(agent_config_path) as file:
            self.agent_config = json.load(file)
            for key, val in self.agent_config.items():
                setattr(self, key, val)

        self.intents_classifier = intent_classifier
        self.sentiment_analyser = sentiment_analyser

    def process_input(self, user_input):
        """
        Processes user input, identifies intent, extracts entities, and generates a response.

        Args:
            user_input (str): The user's input message.

        Returns:
            dict: A dictionary containing the agent's response and other information.
        """
        self.messages.append({"role": "user", "content": str(user_input)})
        response = {}

        # determine user sentiment
        if user_input:
            customer_sentiment = self.sentiment_analyser(user_input)[0]
            self.customer_mood = customer_sentiment["label"]
            self.customer_mood_score = customer_sentiment["score"]
        
        # determine if the the user wants to cancel slot filling 
        if all([user_input, self.active_topic, is_cancel_intent(str(user_input))]):
            self.cancel_slot_filling()
            agent_reply = "Alright, I understand that you want to cancel this request. What else can I do for you?"

            if self.use_dynamo:
                agent_reply = dynamo.natural_rephrase(self.dynamo_identity, self.messages, self.messages)

            self.messages.append({"role": "agent", "content": agent_reply})
            response["reply"] = agent_reply
       
        # determine intent given no topic to fill
        elif user_input and not self.active_topic:
            response["reply"] = self.process_no_topic(user_input)
        
        # if there is an active topic to fill
        elif user_input and self.active_topic:
            response["reply"] = self.process_with_topic(user_input)
                

        response["active_intent"] = self.active_intent
        response["active_intent_confidence_score"] = self.active_intent_confidence_score
        response["customer_mood"] = self.customer_mood
        response["customer_mood_score"] = self.customer_mood_score

        return response

    def cancel_slot_filling(self):
        """
        Cancels the current slot filling process.
        """
        self.active_topic = None
        self.active_intent = None
        self.required_context = []

    def process_no_topic(self, user_input):
        """
        Processes user input when there is no active topic to fill.

        Args:
            user_input (str): The user's input message.

        Returns:
            str: The agent's response.
        """
        self.active_context["__context__"]["max_count"] -= 1 if self.active_context["__context__"]["max_count"] > 0 else 0
        intents_classifier_result = determine_intent(self.active_context["__context__"]["context_label"], str(user_input), self.intent_match_threshold, self.intents_classifier, self.intents)
        current_intent, intent_score = intents_classifier_result["label"], intents_classifier_result["score"]
        self.active_intent = current_intent
        self.active_intent_confidence_score = intent_score
        self.required_context = get_missing_context(self.active_context, self.intents[current_intent]["params"]) if self.intents[current_intent]["params"] != 'None' else []
        print("Determined Intent : ", current_intent, " : ", self.active_intent)
        if len(self.required_context):
            agent_reply = "Alright, I will need some information to do this.\n" + self.prompt_for_next_param()
            self.messages.append({"role": "agent", "content": agent_reply})
        else:
            agent_reply = self.fullfil_active_intent()
            self.messages.append({"role": "agent", "content": agent_reply})
        return agent_reply
            
    def prompt_for_next_param(self):
        """
        Prompts the user for the next required entity.

        Returns:
            str: The prompt message.
        """
        if len(self.required_context):
            self.active_topic = self.required_context.pop(0)
            self.context_history.append(self.active_topic)

            entity_obj = self.entities[self.active_topic]
            agent_reply =  random.choice(entity_obj["reprompt"])

            self.use_dynamo = self.intents[self.active_intent]["use_dynamo"]
            if self.use_dynamo:
                agent_reply = dynamo.natural_rephrase(self.dynamo_identity, self.messages, Template(agent_reply).safe_substitute(self.active_context))
                #self.messages.append({"role": "agent", "content": agent_reply})

            return agent_reply
        else:
            self.active_topic=None
        return None
    
    def has_context_for_fullfilment(self):
        """
        Checks if the agent has all the required context to fulfill the active intent.

        Returns:
            bool: True if the agent has all the required context, False otherwise.
        """
        return ((len(self.required_context)==0)
                 or (self.active_topic is None 
                     and set(self.intents[self.active_intent]["params"]).issubset(set(self.active_context.keys()))))
    
    def fullfil_active_intent(self):
        """
        Fulfills the active intent using the available context.

        Returns:
            str: The agent's response.
        """
        #TODO: assert here and on other places with error handling
        print(self.active_intent)
        if self.has_context_for_fullfilment():
            agent_reply = random.choice(self.intents[self.active_intent]["responses"])
            agent_reply = Template(str(agent_reply)).safe_substitute(self.active_context)
            self.active_context["__context__"] = self.intents[self.active_intent]['output_context']
            #TODO: Check if there is anyother fulfilment
            print(self.active_intent, ": Notification : " ,self.intents[self.active_intent]["notify"])
            if self.whatsappIntegrated and self.intents[self.active_intent]["notify"]:
                self.send_whatsapp_message(agent_reply)
            
            for fulfilment in self.intents[self.active_intent]['fulfilements']:
                webhook = self.fulfilments[fulfilment] #self.fulfilments contain a dictionary of webhooks
                webhook.call(self.active_context)

            self.active_intent = None
            return agent_reply
        
        return None


    def process_with_topic(self, user_input):
        """
        Processes user input when there is an active topic to fill.

        Args:
            user_input (str): The user's input message.

        Returns:
            str: The agent's response.
        """
        #self.messages.append({"role": "user", "content": str(user_input)})
        entity_obj = self.entities[self.active_topic]
        entity_parameter = extract_entity(entity_obj["given"], entity_obj["values"], str(user_input))
        
        if not entity_parameter: # Couldn't find the entity from the given text
            if self.fallback_count < 2: #TODO: MAKE THIS NUMBER CONFIGURABLE VARIABLE
                agent_reply = Template(random.choice(entity_obj["fallback_prompt"])).safe_substitute(self.active_context)
                if self.use_dynamo:
                    agent_reply = dynamo.natural_rephrase(self.dynamo_identity, self.messages, agent_reply)
                    #self.messages.append({"role": "agent", "content": agent_reply})
                self.fallback_count += 1
            else:
                self.active_context["active_intent"] = self.active_intent
                self.active_context["active_topic"] = self.active_topic
                agent_reply = graceful_shutdown(self.active_context)
                #self.messages.append({"role": "agent", "content": dynamo.natural_rephrase(self.dynamo_identity, self.messages, Template(reply).safe_substitute(self.active_context))})
        else:
            self.active_context[self.active_topic] = entity_parameter
            agent_reply = self.prompt_for_next_param()
            if not agent_reply:
                agent_reply = self.fullfil_active_intent()
        return agent_reply
    
    def integrate_whatsapp(self, sender_number="+14155238886", receiver_number="+923364050797"):
        """
        Integrates the agent with WhatsApp using Twilio.

        Args:
            sender_number (str): The sender's phone number.
            receiver_number (str): The receiver's phone number.

        Returns:
            bool: True if integration is successful, False otherwise.
        """
        wa = Whatsapp(sender_number, receiver_number)
        if wa.credentials_available():
            self.whatsappClient = wa
            self.whatsappIntegrated = True
            return True
        else:
            return False
    
    def send_whatsapp_message(self, message):
        """
        Sends a message to the WhatsApp receiver.

        Args:
            message (str): The message to send.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        if self.whatsappIntegrated:
            self.whatsappClient.send_message(message)
            return True
        else:
            print("Whatsapp not integrated")
            return False
        
    def load_integrations(self):
        """
        Loads fulfilment configurations from a JSON file.
        """
        with open(self.fulfilment_path) as file:
            fulfilments = file.read()
            fulfilments = json.loads(fulfilments)
        
        for fulfilment in fulfilments:
            self.fulfilments[fulfilment] = Webhook(fulfilment, self.fulfilment_path)
            ## Make sure that the params required in the intents file for an intent match the entities needed for the fulfilment in the fulfilments file
        




