import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


class Fawaterk:
    def __init__(self):
        self.key = os.getenv("FAWATERK_KEY")

    def get_payment_methods(self):
        url = "https://staging.fawaterk.com/api/v2/getPaymentmethods"

        payload = {}
        headers = {
            "content-type": "application/json",
            "Authorization": "Bearer " + self.key,
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        return response.json()
