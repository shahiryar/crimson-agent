from langchain_community.llms import Ollama


def generate(dynamo_identity, user_input, message_history):
    llm = Ollama(model="llama2")
    reply = llm.invoke(f"Your Identity: {dynamo_identity}\n Conversation History:{message_history}\nuser says: {user_input}\n agent says: ")
    return str(reply)

def natural_rephrase(dynamo_identity, user_input, message_history, text):
    llm = Ollama(model="llama2")
    reply = llm.invoke(f"Your Identity: {dynamo_identity}\n Conversation History:{message_history}\nphrase this: {text}\n considering the user said this {user_input} ")
    return str(reply)
