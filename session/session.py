import uuid
import time
import threading


class Session:
    def __init__(self, agent):
        self.session_id = uuid.uuid4()  # Unique session identifier
        self.start_time = time.time()   # POSIX timestamp of initialization
        self.agent = agent
        self.lifespan = 10 * 60  # Session lifespan in seconds (1 minute)
        self.expired = False

        # Start a background thread to monitor session expiration
        self._start_expiration_timer()
        self.session_state = {}

    def _start_expiration_timer(self):
        """Start a background thread to set the session as expired after its lifespan."""
        def expire():
            time.sleep(self.lifespan)
            self.expired = True

        expiration_thread = threading.Thread(target=expire, daemon=True)
        expiration_thread.start()

    def is_active(self):
        """Check if the session is still active."""
        return not self.expired

    def interact(self, user_input):
        """Interact with the agent if the session is active."""
        if not self.is_active():
            return {"reply":"Sorry, your current session has expired."}
        return self.agent.process_input(user_input)

    def get_session_info(self):
        """Return basic session information."""
        return {
            'session_id': str(self.session_id),
            'start_time': self.start_time,
            'is_active': self.is_active()
        }
    
    def set_state(self, key, value):
        self.session_state[key] = value
    
    def get_state(self, key):
        return self.session_state[key]
    def has_state(self):
        return (self.session_state.keys())>0
