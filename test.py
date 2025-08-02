import random
import string
import time

import requests
from faker import Faker

fake = Faker()
url = "http://0.0.0.0:8000/auth/register"

while True:
    full_name = fake.name()
    email = fake.unique.email()
    password = "".join(random.choices(string.ascii_letters + string.digits, k=10))

    data = {"full_name": full_name, "email": email, "password": password}

    try:
        response = requests.post(url, json=data)
        print(response.status_code, response.json())
    except Exception as e:
        print("Error:", e)

    time.sleep(1)
