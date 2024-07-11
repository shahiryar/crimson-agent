import requests
from string import Template
import json
import re


class Webhook:

    def __init__(self, name:str, fulfilments_path:str="./fulfilments.json"):
        self.name = name
        with open(fulfilments_path) as file:
            fulfilments = file.read()
        
        fulfilments = json.loads(fulfilments)
        webhook_dict = fulfilments[name]

        self.display_name = webhook_dict["display_name"]
        self.description = webhook_dict["description"]
        webhook_dict = webhook_dict["webhook"]

        self.url = webhook_dict.get('url')
        self.request_type = webhook_dict.get('request_type')

        if self.request_type == 'POST':
            self.template_payload = webhook_dict.get('template_payload')
            self.payload_data_needed = self.get_variables(self.template_payload)
            self.template_payload = Template(self.template_payload)
        elif self.request_type == 'GET':
            self.url = Template(self.url)

    def get_variables(self, tmp_str):
        """
        Extracts variable names from a template payload within a dictionary.

        Args:
            data (dict): The dictionary containing the `template_payload` key.

        Returns:
            list: A list of variable names found within the template payload.

        Raises:
            TypeError: If the input data is not a dictionary.
            KeyError: If the 'template_payload' key is not found in the dictionary.
        """

        variable_pattern = r"\$(?P<variable_name>\w+)"  # Improved pattern for word characters
        variables = re.findall(variable_pattern, tmp_str)

        return variables

    def call(self, data_dict):
        # Make the HTTP request
        if self.request_type == "POST":
            # Substitute placeholders in the template with data from data_dict
            payload = self.template_payload.safe_substitute(data_dict)
            payload = json.loads(payload)
            headers = {'Content-Type': 'application/json'}
            try:
                response = requests.post(self.url, headers=headers, json=payload)
                return response.status_code, response.json() if 'application/json' in response.headers['Content-Type'] else response.text
            except json.JSONDecodeError as e:
                return 400, {'error': f'Invalid JSON payload: {e}'}
        elif self.request_type == "GET":
            try:
                url = self.url.safe_substitute(data_dict)
                response = requests.get(url)
                return response.json()["balance"]
            except:
                return 400, {'error': 'could not send the request'}



