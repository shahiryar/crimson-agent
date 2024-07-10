from twilio.rest import Client
import os
from dotenv import load_dotenv

class Whatsapp:
    def __init__(self, sender_number, receiver_number):
        """
        Initializes the Whatsapp class with sender and receiver numbers.

        Args:
            sender_number (str): The sender's WhatsApp number in international format (e.g., '+14155238886').
            receiver_number (str): The receiver's WhatsApp number in international format (e.g., '+923364050797').
        """
        self.sender_number = sender_number
        self.receiver_number = receiver_number
        self.load_credentials()
        self.create_twilio_client()

    def load_credentials(self):
        """
        Loads Twilio account SID and auth token from environment variables.
        Returns True if successful, False otherwise.
        """
        if load_dotenv():
            try:
                self.account_sid = os.getenv("TWILLIO_ACCOUNT_SID")
                self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
                return True
            except:
                print("Twillio account or auth token not found in the environment")
                self.account_sid = None
                self.auth_token = None
                return False
        else:
            print("Environment Variables could not loaded, make sure your have the `.env` file")
            self.account_sid = None
            self.auth_token = None
            return False
        
    def credentials_available(self):
        """
        Checks if Twilio account SID and auth token are available.

        Returns:
            bool: True if both SID and auth token are available, False otherwise.
        """
        if self.account_sid and self.auth_token:
            return True
        else:
            return False

    def send_message(self, text):
        """
        Sends a message to the receiver.

        Args:
            text (str): The message to send.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        if self.twilioClient:
            client = self.twilioClient
            message = client.messages.create(
                from_=f'whatsapp:{self.sender_number}',
                body=text,
                to=f'whatsapp:{self.receiver_number}'
            )
            if message:
                return True
            else:
                return False
        else:
            print("Twillio credentials not found. Unable to send message.")
            return False
    
    def create_twilio_client(self):
        if self.account_sid and self.auth_token:
            client = Client(self.account_sid, self.auth_token)
            self.twilioClient = client
            return True
        else:
            self.twilioClient = None
            return False
        
    def get_twilio_client(self):
      return self.twilioClient

    def receive_message(self):
        """
        Receives a message from the receiver.

        This method is not implemented yet, as Twilio's API doesn't directly support receiving messages.
        You would need to use webhooks or a similar mechanism to receive messages.

        Returns:
            None: This method is not yet implemented.
        """
        print("Receiving messages is not yet implemented.")
        return None

# Example usage:
if __name__ == "__main__":
    sender_number = '+14155238886'
    receiver_number = '+923364050797'
    whatsapp = Whatsapp(sender_number, receiver_number)
    if whatsapp.send_message("Hello from Python!"):
        print("Message sent successfully!")
    else:
        print("Failed to send message.")

