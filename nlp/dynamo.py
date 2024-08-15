from langchain_community.llms import Ollama


def generate(dynamo_identity, user_input, message_history):
    """
    Generates a response using the Ollama LLM.

    Args:
        dynamo_identity (str): The identity of the Dynamo agent.
        user_input (str): The user's input message.
        message_history (str): The history of the conversation.

    Returns:
        str: The generated response from the LLM.
    """
    llm = Ollama(model="llama2")  # Initialize Ollama LLM with "llama2" model
    reply = llm.invoke(f"Your Identity: {dynamo_identity}\n Conversation History:{message_history}\nuser says: {user_input}\n agent says: ")  # Invoke the LLM with the provided context
    return str(reply)  # Return the LLM's response as a string


def natural_rephrase(dynamo_identity, message_history, text, model='gemini'):
    """
    Rephrases a given text using either the Ollama or Gemini LLM.

    Args:
        dynamo_identity (str): The identity of the Dynamo agent.
        message_history (str): The history of the conversation.
        text (str): The text to be rephrased.
        model (str, optional): The LLM model to use for rephrasing. Defaults to 'gemini'.

    Returns:
        str: The rephrased text, or the original text if rephrasing fails.
    """
    try:
        prompt = f"Rephrase this: {text}"  # Construct the prompt for rephrasing
        if model == 'llama2':
            llm = Ollama(model="llama2")  # Initialize Ollama LLM with "llama2" model
            reply = llm.invoke(prompt)  # Invoke the LLM with the prompt
        elif model == 'gemini':
            reply = gemini(prompt)  # Call the gemini function to use the Gemini LLM
        else:
            print("Model not valid!")  # Print an error message if the model is invalid
            return None
    except:
        print("Given text could not be rephrased responding with echo")  # Print an error message if rephrasing fails
        reply = text  # Return the original text if rephrasing fails
    return str(reply)  # Return the rephrased text as a string


def gemini(prompt):
    """
    Uses the Gemini LLM to generate text.

    Args:
        prompt (str): The prompt for the Gemini LLM.

    Returns:
        str: The generated text from the Gemini LLM, or None if an error occurs.
    """
    import os
    from dotenv import load_dotenv
    if load_dotenv():
      try:
        api_key = os.getenv("GOOGLE_AI_API")  # Load the Google AI API key from environment variables
      except:
         print("Google AI API not found in the environment")  # Print an error message if the API key is not found
         return None
    else:
        print("Environment Variables could not loaded, make sure your have the `.env` file")  # Print an error message if environment variables cannot be loaded
        return None

    import requests
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + api_key  # Construct the URL for the Gemini API
    headers = {"Content-Type": "application/json"}  # Set the content type header
    data = {"contents":[{"parts":[{"text":prompt}]}]}  # Prepare the request data with the prompt
    
    response = requests.post(url, headers=headers, json=data)  # Send the POST request to the Gemini API
    if response.status_code == 200:
        from pprint import pprint
        pprint(response.json())  # Print the response JSON if the request is successful
        return response.json()["candidates"][0]["content"]["parts"][0]['text']  # Extract the generated text from the response
    else:
        print("Error:", response.status_code)  # Print an error message if the request fails
        print(response.content)
        return None
