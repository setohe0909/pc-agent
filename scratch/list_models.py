import os
import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY") or ""
genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}, DisplayName: {m.display_name}")
except Exception as e:
    print(f"Error listing models: {e}")
