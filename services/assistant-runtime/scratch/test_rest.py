import os
import httpx
import json

def test_rest_imagen():
    api_key = os.getenv("GEMINI_API_KEY")
    # Intentamos el 4.0 fast que es el que vimos con 'predict'
    model = "imagen-4.0-fast-generate-001"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
    
    payload = {
        "instances": [
            { "prompt": "A futuristic cat" }
        ],
        "parameters": {
            "sampleCount": 1
        }
    }
    
    print(f"Probando REST con {model}...")
    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "predictions" in data and len(data["predictions"]) > 0:
                print("SUCCESS: Image data received!")
                # print(data["predictions"][0]) # suele ser base64
            else:
                print(f"No predictions in response: {data}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"REST FAILED: {e}")

if __name__ == "__main__":
    test_rest_imagen()
