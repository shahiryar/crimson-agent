from langchain_community.llms import Ollama


def generate(dynamo_identity, user_input, message_history):
    llm = Ollama(model="llama2")
    reply = llm.invoke(f"Your Identity: {dynamo_identity}\n Conversation History:{message_history}\nuser says: {user_input}\n agent says: ")
    return str(reply)

def natural_rephrase(dynamo_identity, message_history, text, model='gemini'):
    try:
        prompt = f"Rephrase this: {text}"
        if model== 'llama2':
            llm = Ollama(model="llama2")
            reply = llm.invoke(prompt)
        elif model == 'gemini':
            reply = gemini(prompt)
        else:
            print("Model not valid!")
            return None
    except:
        print("Given text could not be rephrased responding with echo")
        reply = text
    return str(reply)



def gemini(prompt):
    import os
    from dotenv import load_dotenv
    if load_dotenv():
      try:
        api_key = os.getenv("GOOGLE_AI_API")
      except:
         print("Google AI API not found in the environment")
         return None
    else:
        print("Environment Variables could not loaded, make sure your have the `.env` file")
        return None

    import requests
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + api_key
    headers = {"Content-Type": "application/json"}
    data = {"contents":[{"parts":[{"text":prompt}]}]}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        from pprint import pprint
        pprint(response.json())
        return response.json()["candidates"][0]["content"]["parts"][0]['text']
    else:
        print("Error:", response.status_code)
        print(response.content)
        return None