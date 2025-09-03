# app/utils/easykash_utils.py

import hashlib  # <-- NEW IMPORT
import hmac  # <-- NEW IMPORT
import json
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

    def verify_callback_official(self, payload: dict) -> bool:
        """
        Official EasyKash callback verification based on their documentation.
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

            # 2. Extract the required fields in the EXACT order specified by EasyKash
            # From documentation: ProductCode, Amount, ProductType, PaymentMethod, status, easykashRef, customerReference
            required_fields = [
                "ProductCode",
                "Amount",
                "ProductType",
                "PaymentMethod",
                "status",
                "easykashRef",
                "customerReference",
            ]

            # 3. Get values and handle missing fields
            data_to_secure = []
            for field in required_fields:
                if field not in payload:
                    print(f"ERROR: Required field '{field}' missing from payload")
                    return False
                data_to_secure.append(str(payload[field]))

            # 4. Concatenate the values (no separators, just join)
            concatenated_string = "".join(data_to_secure)

            print(f"=== OFFICIAL METHOD ===")
            print(f"Fields in order: {required_fields}")
            print(f"Values: {data_to_secure}")
            print(f"Concatenated: '{concatenated_string}'")
            print(f"Concatenated length: {len(concatenated_string)}")

            # 5. Calculate HMAC-SHA512 with HEX digest
            calculated_signature = hmac.new(
                self.secret_key.encode("utf-8"),
                concatenated_string.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()

            print(f"Calculated signature: {calculated_signature}")
            print(f"Received signature:   {received_signature}")

            # 6. Compare signatures securely
            is_valid = hmac.compare_digest(calculated_signature, received_signature)
            print(f"Signatures match: {is_valid}")

            return is_valid

        except Exception as e:
            print(f"An unexpected error occurred during callback verification: {e}")
            return False

    def verify_callback_debug_comprehensive(self, payload: dict) -> bool:
        """
        Comprehensive debugging to find any potential issues
        """
        if not self.secret_key:
            print("ERROR: EASYKASH_SECRET_KEY is not set. Cannot verify callback.")
            return False

        try:
            received_signature = payload.get("signatureHash")
            if not received_signature:
                print("ERROR: No signatureHash in payload")
                return False

            print(f"=== DEBUGGING SIGNATURE VERIFICATION ===")
            print(f"Full payload: {json.dumps(payload, indent=2)}")
            print(f"Secret key: '{self.secret_key}' (length: {len(self.secret_key)})")
            print(f"Received signature: {received_signature}")
            print(f"Received signature length: {len(received_signature)}")

            # Method 1: Official method (exact implementation)
            print(f"\n--- Method 1: Official Documentation ---")
            required_fields = [
                "ProductCode",
                "Amount",
                "ProductType",
                "PaymentMethod",
                "status",
                "easykashRef",
                "customerReference",
            ]

            # Check all fields exist
            missing_fields = [
                field for field in required_fields if field not in payload
            ]
            if missing_fields:
                print(f"Missing fields: {missing_fields}")
            else:
                print("All required fields present")

            data_to_secure = [str(payload[field]) for field in required_fields]
            concatenated = "".join(data_to_secure)

            print(f"Fields: {required_fields}")
            print(f"Values: {data_to_secure}")
            print(f"Concatenated: '{concatenated}'")

            sig1 = hmac.new(
                self.secret_key.encode("utf-8"),
                concatenated.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()
            print(f"Calculated: {sig1}")
            match1 = hmac.compare_digest(sig1, received_signature)
            print(f"Match: {match1}")

            # Method 2: Check for case sensitivity issues
            print(f"\n--- Method 2: Case Sensitivity Test ---")
            # Try lowercase secret key
            sig2_lower = hmac.new(
                self.secret_key.lower().encode("utf-8"),
                concatenated.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()
            match2_lower = hmac.compare_digest(sig2_lower, received_signature)
            print(f"Lowercase secret key: {sig2_lower}, Match: {match2_lower}")

            # Try uppercase secret key
            sig2_upper = hmac.new(
                self.secret_key.upper().encode("utf-8"),
                concatenated.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()
            match2_upper = hmac.compare_digest(sig2_upper, received_signature)
            print(f"Uppercase secret key: {sig2_upper}, Match: {match2_upper}")

            # Method 3: Try different string encodings
            print(f"\n--- Method 3: Encoding Variations ---")
            for encoding in ["utf-8", "ascii", "latin-1"]:
                try:
                    sig3 = hmac.new(
                        self.secret_key.encode(encoding),
                        concatenated.encode(encoding),
                        hashlib.sha512,
                    ).hexdigest()
                    match3 = hmac.compare_digest(sig3, received_signature)
                    print(f"{encoding}: {sig3}, Match: {match3}")
                except Exception as e:
                    print(f"{encoding}: Error - {e}")

            # Method 4: Try with empty fields as empty strings vs missing
            print(f"\n--- Method 4: Empty Field Handling ---")
            data_with_empties = []
            for field in required_fields:
                value = payload.get(field, "")  # Use empty string for missing fields
                data_with_empties.append(str(value))

            concatenated_empty = "".join(data_with_empties)
            print(f"With empty handling: '{concatenated_empty}'")

            sig4 = hmac.new(
                self.secret_key.encode("utf-8"),
                concatenated_empty.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()
            match4 = hmac.compare_digest(sig4, received_signature)
            print(f"Empty handling: {sig4}, Match: {match4}")

            # Method 5: Check the example from documentation
            print(f"\n--- Method 5: Documentation Example Verification ---")
            doc_payload = {
                "ProductCode": "EDV4471",
                "Amount": "11.00",
                "ProductType": "Direct Pay",
                "PaymentMethod": "Cash Through Fawry",
                "status": "PAID",
                "easykashRef": "2911105009",
                "customerReference": "TEST11111",
                "signatureHash": "0bd9ce502950ffa358314c170dace42e7ba3e0c776f5a32eb15c3d496bc9c294835036dd90d4f287233b800c9bde2f6591b6b8a1f675b6bfe64fd799da29d1d0",
            }
            doc_secret = "da9fe30575517d987762a859842b5631"
            doc_expected_concat = (
                "EDV447111.00Direct PayCash Through FawryPAID2911105009TEST11111"
            )

            doc_data = [str(doc_payload[field]) for field in required_fields]
            doc_concat = "".join(doc_data)
            print(f"Doc example concat: '{doc_concat}'")
            print(f"Expected concat:    '{doc_expected_concat}'")
            print(f"Concat matches expected: {doc_concat == doc_expected_concat}")

            doc_sig = hmac.new(
                doc_secret.encode("utf-8"), doc_concat.encode("utf-8"), hashlib.sha512
            ).hexdigest()
            print(f"Doc calculated: {doc_sig}")
            print(f"Doc expected:   {doc_payload['signatureHash']}")
            print(
                f"Doc example works: {hmac.compare_digest(doc_sig, doc_payload['signatureHash'])}"
            )

            # Return True if any method worked
            return any([match1, match2_lower, match2_upper, match4])

        except Exception as e:
            print(f"Debug error: {e}")
            return False


# Create a single instance to be used throughout the app
easykash_client = EasyKash(private_key=private_key, secret_key=secret_key)
