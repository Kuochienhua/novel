import requests
import json
import base64
from PIL import Image
import io

api_key = 'AIzaSyDKl4QXACRnPISYSiK_1tIjpdFQw7r1vO0'
url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={api_key}"

payload = {
    "instances": [
        {"prompt": "A beautiful watercolor illustration of a steampunk clock tower in a Japanese fishing village."}
    ],
    "parameters": {
        "sampleCount": 1
    }
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    data = response.json()
    
    if "predictions" in data:
        img_data = data["predictions"][0]["bytesBase64Encoded"]
        img = Image.open(io.BytesIO(base64.b64decode(img_data)))
        img.save("test_rest_image.png")
        print("Success!")
    else:
        print("Error in response:", data)
except Exception as e:
    print(f"Exception: {e}")
