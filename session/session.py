import uuid
import time
import threading


class Session:
    """
    Represents a user session with an agent.

    This class manages the lifecycle of a user session, including session ID generation,
    expiration tracking, and interaction with the agent.

    Attributes:
        session_id (uuid.UUID): A unique identifier for the session.
        start_time (float): The POSIX timestamp when the session was created.
        agent (Agent): The agent associated with the session.
        lifespan (int): The duration in seconds for which the session remains active.
        expired (bool): A flag indicating whether the session has expired.
        session_state (dict): A dictionary to store session-specific data.
    """
    def __init__(self, agent):
        """
        Initializes a new Session object.

        Args:
            agent (Agent): The agent associated with the session.
        """
        self.session_id = uuid.uuid4()  # Generate a unique session ID
        self.start_time = time.time()   # Record the session start time
        self.agent = agent
        self.lifespan = 10 * 60  # Set the session lifespan to 10 minutes (600 seconds)
        self.expired = False  # Initialize the expired flag to False

        # Start a background thread to monitor session expiration
        self._start_expiration_timer()
        self.session_state = {}  # Initialize the session state dictionary

    def _start_expiration_timer(self):
        """
        Starts a background thread to set the session as expired after its lifespan.

        This method creates a separate thread that sleeps for the session lifespan.
        Once the thread wakes up, it sets the `expired` flag to True, effectively ending the session.
        """
        def expire():
            """Sets the session as expired after the lifespan."""
            time.sleep(self.lifespan)  # Sleep for the session lifespan
            self.expired = True  # Set the expired flag to True

        expiration_thread = threading.Thread(target=expire, daemon=True)  # Create a daemon thread for expiration
        expiration_thread.start()  # Start the expiration thread

    def is_active(self):
        """
        Checks if the session is still active.

        Returns:
            bool: True if the session is active, False otherwise.
        """
        return not self.expired  # Return the opposite of the expired flag

    def interact(self, user_input):
        """
        Interacts with the agent if the session is active.

        This method processes user input and sends it to the agent for handling.
        If the session has expired, it returns a message indicating the expiration.

        Args:
            user_input (str): The user's input message.

        Returns:
            dict: A dictionary containing the agent's response.
        """
        if not self.is_active():  # Check if the session is active
            return {"reply":"Sorry, your current session has expired."}  # Return an expiration message
        return self.agent.process_input(user_input)  # Process the input using the agent

    def get_session_info(self):
        """
        Returns basic session information.

        This method provides information about the session, including its ID, start time, and active status.

        Returns:
            dict: A dictionary containing session information.
        """
        return {
            'session_id': str(self.session_id),  # Convert the session ID to a string
            'start_time': self.start_time,  # Return the session start time
            'is_active': self.is_active()  # Return the active status
        }
    
    def set_state(self, key, value):
        """
        Sets a value in the session state dictionary.

        This method allows you to store session-specific data using key-value pairs.

        Args:
            key (str): The key for the data.
            value (any): The value to be associated with the key.
        """
        self.session_state[key] = value  # Store the value in the session state dictionary

    def get_state(self, key):
        """
        Retrieves a value from the session state dictionary.

        This method allows you to access previously stored session data.

        Args:
            key (str): The key for the data.

        Returns:
            any: The value associated with the key, or None if the key doesn't exist.
        """
        return self.session_state.get(key)  # Retrieve the value using the key

    def has_state(self):
        """
        Checks if the session state dictionary has any entries.

        Returns:
            bool: True if the session state dictionary is not empty, False otherwise.
        """
        return (self.session_state.keys())>0  # Check if the dictionary has any keys
