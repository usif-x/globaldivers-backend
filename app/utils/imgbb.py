import base64
import os

import requests
from dotenv import load_dotenv

load_dotenv()


def upload_image_to_imgbb(image: bytes) -> dict:
    key = os.getenv("IMGBB_KEY")
    url = "https://api.imgbb.com/1/upload"
    encoded_image = base64.b64encode(image).decode("utf-8")
    payload = {
        "key": key,
        "image": encoded_image,
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": f"Failed to upload. Status code: {response.status_code}",
            "details": response.text,
        }
