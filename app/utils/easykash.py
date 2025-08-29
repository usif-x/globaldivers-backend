# app/utils/easykash_utils.py

import hashlib  # <-- NEW IMPORT
import hmac  # <-- NEW IMPORT
import os
import random

import requests
from dotenv import load_dotenv

load_dotenv()

private_key = os.environ.get("EASYKASH_PRIVATE_KEY")
secret_key = os.environ.get("EASYKASH_SECRET_KEY")


class EasyKash:
    def __init__(self, private_key, secret_key):
        self.private_key = private_key
        self.secret_key = secret_key

    @staticmethod
    def generate_customer_reference(user_id: int) -> str:
        random_digits1 = str(random.randint(10000, 99999))
        random_digits2 = str(random.randint(10000, 99999))
        # Making it more robust and unique
        return f"{random_digits1}{user_id}{random_digits2}"

    def create_payment(self, payment_data, user_id: int):
        url = "https://back.easykash.net/api/directpayv1/pay"
        headers = {
            "Content-Type": "application/json",
            "authorization": self.private_key,
        }

        customer_ref = self.generate_customer_reference(user_id)

        data = {
            "amount": payment_data["amount"],
            "currency": payment_data["currency"],
            "paymentOptions": [2, 6, 31],
            "cashExpiry": payment_data.get("cash_expiry", 3),  # Added a default value
            "name": payment_data["buyer_name"],
            "email": payment_data["buyer_email"],
            "mobile": payment_data["buyer_phone"],
            "redirectUrl": "http://localhost:3000/pay",
            "customerReference": customer_ref,
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            response_json = response.json()
            data_to_return = {
                "success": True,
                # Return the customerReference we generated
                "customer_reference": customer_ref,
                "pay_url": response_json.get("redirectUrl"),
                # Return EasyKash's own reference if they provide one on creation
                "easykash_reference": response_json.get("easykashReference"),
            }
            return data_to_return
        else:
            return {
                "success": False,
                "error": f"Failed to create payment. Status code: {response.status_code}",
                "details": response.text,
            }

    def inquire_payment(self, customer_reference: str):
        url = "https://back.easykash.net/api/cash-api/inquire"
        headers = {
            "Content-Type": "application/json",
            "authorization": self.private_key,
        }
        # The inquire endpoint likely expects JSON
        data = {"customerReference": customer_reference}
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Failed to inquire payment. Status code: {response.status_code}",
                "details": response.text,
            }

    def verify_callback(self, payload: dict) -> bool:
        """
        Verifies the integrity and authenticity of an incoming callback from EasyKash.
        """
        if not self.secret_key:
            print("ERROR: EASYKASH_SECRET_KEY is not set. Cannot verify callback.")
            return False

        try:
            # 1. Extract the signature hash from the payload
            received_signature = payload.get("signatureHash")
            if not received_signature:
                return False

            # 2. Get the values to be concatenated IN THE SPECIFIED ORDER
            data_to_secure = [
                payload["ProductCode"],
                payload["Amount"],
                payload["ProductType"],
                payload["PaymentMethod"],
                payload["status"],
                payload["easykashRef"],
                payload["customerReference"],
            ]

            # 3. Concatenate the values into a single string
            concatenated_string = "".join(str(v) for v in data_to_secure)

            # 4. Calculate the HMAC-SHA512 hash
            calculated_signature = hmac.new(
                self.secret_key.encode("utf-8"),
                concatenated_string.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()

            # 5. Compare the calculated hash with the received hash in a secure way
            return hmac.compare_digest(calculated_signature, received_signature)

        except KeyError as e:
            # A key was missing from the payload, so it's invalid.
            print(f"Callback verification failed due to missing key: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during callback verification: {e}")
            return False


# Create a single instance to be used throughout the app
easykash_client = EasyKash(private_key=private_key, secret_key=secret_key)
