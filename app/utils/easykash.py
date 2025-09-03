# app/utils/easykash_utils.py

import hashlib  # <-- NEW IMPORT
import hmac  # <-- NEW IMPORT
import os
import random
import time

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
            "paymentOptions": [2, 4, 6, 31],
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
        This version is robust against missing optional keys.
        """
        if not self.secret_key:
            print("ERROR: EASYKASH_SECRET_KEY is not set. Cannot verify callback.")
            return False

        try:
            # 1. Extract the signature hash from the payload
            received_signature = payload.get("signatureHash")
            if not received_signature:
                print("Callback verification failed: signatureHash missing.")
                return False

            # 2. Get the values to be concatenated IN THE SPECIFIED ORDER
            # IMPORTANT: Double-check this order with EasyKash documentation.
            # Use .get(key, "") to safely handle optional fields.
            data_to_secure = [
                payload.get("ProductCode", ""),
                payload.get("Amount", ""),
                payload.get("ProductType", ""),
                payload.get("PaymentMethod", ""),
                payload.get("status", ""),
                payload.get("easykashRef", ""),
                payload.get("customerReference", ""),  # This is now safe
            ]

            # 3. Concatenate the values into a single string
            concatenated_string = "".join(str(v) for v in data_to_secure)

            # For debugging purposes, you can print these:
            # print(f"String to hash: '{concatenated_string}'")

            # 4. Calculate the HMAC-SHA512 hash
            calculated_signature = hmac.new(
                self.secret_key.encode("utf-8"),
                concatenated_string.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()

            # For debugging purposes:
            # print(f"Received Signature:   {received_signature}")
            # print(f"Calculated Signature: {calculated_signature}")

            # 5. Compare the calculated hash with the received hash in a secure way
            return hmac.compare_digest(calculated_signature, received_signature)

        except Exception as e:
            # Removed KeyError catch as .get() prevents it.
            print(f"An unexpected error occurred during callback verification: {e}")
            return False

    def verify_callback_debug(self, payload: dict) -> bool:
        """
        Enhanced verification with detailed debugging
        """
        if not self.secret_key:
            print("ERROR: EASYKASH_SECRET_KEY is not set. Cannot verify callback.")
            return False

        try:
            # 1. Extract the signature hash from the payload
            received_signature = payload.get("signatureHash")
            print(f"Received signature: {received_signature}")

            if not received_signature:
                print("ERROR: No signatureHash in payload")
                return False

            # 2. Check all required fields are present
            required_fields = [
                "ProductCode",
                "Amount",
                "ProductType",
                "PaymentMethod",
                "status",
                "easykashRef",
                "customerReference",
            ]

            missing_fields = [
                field for field in required_fields if field not in payload
            ]
            if missing_fields:
                print(f"ERROR: Missing required fields: {missing_fields}")
                return False

            # 3. Get the values in the specified order
            data_to_secure = [
                payload["ProductCode"],
                payload["Amount"],
                payload["ProductType"],
                payload["PaymentMethod"],
                payload["status"],
                payload["easykashRef"],
                payload["customerReference"],
            ]

            print(f"Data to secure (ordered): {data_to_secure}")

            # 4. Concatenate the values
            concatenated_string = "".join(str(v) for v in data_to_secure)
            print(f"Concatenated string: '{concatenated_string}'")
            print(f"Concatenated length: {len(concatenated_string)}")

            # 5. Calculate the HMAC-SHA512 hash
            calculated_signature = hmac.new(
                self.secret_key.encode("utf-8"),
                concatenated_string.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()

            print(f"Calculated signature: {calculated_signature}")
            print(
                f"Signatures match: {hmac.compare_digest(calculated_signature, received_signature)}"
            )

            # 6. Try alternative concatenation methods in case EasyKash uses different approach
            print(f"=== TRYING ALTERNATIVE SIGNATURE METHODS ===")

            # Method 2: Include all fields in alphabetical order
            all_fields_alpha = sorted(
                [k for k in payload.keys() if k != "signatureHash"]
            )
            alt_data_1 = "".join(str(payload[field]) for field in all_fields_alpha)
            alt_sig_1 = hmac.new(
                self.secret_key.encode("utf-8"),
                alt_data_1.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()
            print(f"Alternative 1 (all fields alphabetical): {alt_sig_1}")
            print(
                f"Alt 1 matches: {hmac.compare_digest(alt_sig_1, received_signature)}"
            )

            # Method 3: Different field order (as they appear in JSON)
            json_order_fields = list(payload.keys())
            json_order_fields.remove("signatureHash")
            alt_data_2 = "".join(str(payload[field]) for field in json_order_fields)
            alt_sig_2 = hmac.new(
                self.secret_key.encode("utf-8"),
                alt_data_2.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()
            print(f"Alternative 2 (JSON order): {alt_sig_2}")
            print(
                f"Alt 2 matches: {hmac.compare_digest(alt_sig_2, received_signature)}"
            )

            # Return original comparison
            return hmac.compare_digest(calculated_signature, received_signature)

        except KeyError as e:
            print(f"Callback verification failed due to missing key: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during callback verification: {e}")
            return False

    def create_test_callback(self) -> dict:
        """
        Creates a simulated EasyKash callback payload with a valid signatureHash.
        Useful for testing verify_callback().
        """
        # Example data (you can change values to test)
        payload = {
            "ProductCode": "EDV4471",
            "Amount": "5.00",
            "ProductType": "Direct Pay",
            "PaymentMethod": "Cash Through Fawry",
            "BuyerName": "mee",
            "BuyerEmail": "test@mail.com",
            "BuyerMobile": "0123456789",
            "Timestamp": str(int(time.time())),
            "status": "PAID",
            "voucher": "",
            "easykashRef": "291112234",
            "VoucherData": "Direct Pay",
            "customerReference": "32594128644",
        }

        # ترتيب القيم زي التوثيق
        data_to_secure = [
            payload["ProductCode"],
            payload["Amount"],
            payload["ProductType"],
            payload["PaymentMethod"],
            payload["status"],
            payload["easykashRef"],
            payload["customerReference"],
        ]
        concatenated_string = "".join(data_to_secure)

        # Calculate HMAC-SHA512
        signature = hmac.new(
            secret_key.encode("utf-8"),
            concatenated_string.encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()

        # Attach the signature to payload
        payload["signatureHash"] = signature

        return payload


# Create a single instance to be used throughout the app
easykash_client = EasyKash(private_key=private_key, secret_key=secret_key)
