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


from app.schemas.invoice import EasyKashCallbackPayload


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
            "redirectUrl": "https://topdivers.online/pay",
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

    def verify_official_callback(
        self, payload: EasyKashCallbackPayload, secret_key: str
    ) -> bool:
        """
        Verifies the integrity of an EasyKash callback payload.

        Args:
            payload: The parsed Pydantic model of the incoming callback data.
            secret_key: Your HMAC secret key provided by EasyKash support.

        Returns:
            True if the signature is valid, False otherwise.
        """
        # Step 1 & 2: Sort and concatenate the values in the specified order.
        # The order is critical: ProductCode, Amount, ProductType, PaymentMethod, status, easykashRef, customerReference
        data_to_sign = [
            payload.ProductCode,
            payload.Amount,
            payload.ProductType,
            payload.PaymentMethod,
            payload.status,
            payload.easykashRef,
            payload.customerReference,
        ]
        concatenated_string = "".join(data_to_sign)

        # Step 3: Calculate the HMAC SHA512 hash.
        # The key and message must be converted to bytes.
        calculated_signature = hmac.new(
            key=secret_key.encode("utf-8"),
            msg=concatenated_string.encode("utf-8"),
            digestmod=hashlib.sha512,
        ).hexdigest()

        # Step 4: Compare the calculated signature with the one from the payload.
        # Use hmac.compare_digest for a timing-attack-resistant comparison.
        return hmac.compare_digest(calculated_signature, payload.signatureHash)

    # --- 3. Example Verification Function ---
    def verify_example_callback(self):
        """
        Uses the specific example data from the EasyKash documentation to test
        the verification logic.
        """
        print("--- Running EasyKash Example Verification ---")

        # The example payload from the documentation
        example_payload_dict = {
            "ProductCode": "EDV4471",
            "Amount": "11.00",
            "ProductType": "Direct Pay",
            "PaymentMethod": "Cash Through Fawry",
            "BuyerName": "mee",
            "BuyerEmail": "test@mail.com",
            "BuyerMobile": "0123456789",
            "status": "PAID",
            "voucher": "",
            "easykashRef": "2911105009",
            "VoucherData": "Direct Pay",
            "customerReference": "TEST11111",
            "signatureHash": "0bd9ce502950ffa358314c170dace42e7ba3e0c776f5a32eb15c3d496bc9c294835036dd90d4f287233b800c9bde2f6591b6b8a1f675b6bfe64fd799da29d1d0",
        }

        # The example secret key from the documentation
        example_secret_key = "da9fe30575517d987762a859842b5631"

        # The expected concatenated string from the documentation for cross-checking
        expected_concatenated_data = (
            "EDV447111.00Direct PayCash Through FawryPAID2911105009TEST11111"
        )
        print(f"Expected concatenated string: {expected_concatenated_data}")

        # Parse the dictionary into our Pydantic model
        payload_obj = EasyKashCallbackPayload(**example_payload_dict)

        # Recreate the concatenated string to ensure our logic is correct
        data_to_sign = [
            payload_obj.ProductCode,
            payload_obj.Amount,
            payload_obj.ProductType,
            payload_obj.PaymentMethod,
            payload_obj.status,
            payload_obj.easykashRef,
            payload_obj.customerReference,
        ]
        actual_concatenated_data = "".join(data_to_sign)
        print(f"  Actual concatenated string: {actual_concatenated_data}")
        print(
            f"Strings match: {expected_concatenated_data == actual_concatenated_data}"
        )
        print("-" * 20)

        # Call the official verification function
        is_valid = self.verify_official_callback(payload_obj, example_secret_key)

        # Print the result
        if is_valid:
            print("✅ SUCCESS: The example signature was verified successfully!")
        else:
            print("❌ FAILURE: The example signature is invalid. Check the logic.")
        print("-" * 50)


# Create a single instance to be used throughout the app
easykash_client = EasyKash(private_key=private_key, secret_key=secret_key)
