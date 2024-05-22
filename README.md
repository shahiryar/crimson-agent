# Crimson Agent
<img src="./assets/Crimson Agent Avatar.jpeg" alt="A powerful crimson horse showing Crimson Agent's Avatar" width=300>

Crimson Agent is a python-based framework built that can be used to build custom chatbots for privacy critical applications such as for banking and finance.
# How to test it out?
Note: _Before starting make sure you have `python3` and `pip` installed on your system_
1. Clone this repo:
```bash
git clone https://github.com/shahiryar/crimson-agent.git
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Run the app
```bash
streamlit run app.py
```
-------------------

# TODOs
## Develop POC
- [X] Demo Intent Classifier Training
- [X] Intent Classification
- [x] Follow up entity reprompt
- [X] Sentiment Analysis

## Make Robust
- [X] Add No-Match Intent (threshold based)
- [X] Redirect conversation amdist of active context (Cancel Slot Filling)
- [X] Reponse formating from context
- [X] Design Context Lifecycle Management
- [X] Handle Input and Output contexts for Intents
- [X] Modulate the code for reusablity

## Make Configurable
- [ ] Configurations Page to add new Intents and Entities and a Configuration Page to add new agents
- [X] Train and Retrain Script
- [X] Session Lifecycle Management

## Make Integrated
- [ ] Communication Channels Integration
- [X] Enable Whatsapp Message Sending
- [X] Enable Webhook Integrations
- [ ] Plan Deployment

## Make Better
- [ ] Option for Rule-based Intent Matching
- [X] Implement open-source LLM to generate Natural Language Responses
- [ ] Manage Knowledge Base Creation and Connection
