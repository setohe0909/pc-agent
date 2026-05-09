import os
import google.generativeai as genai
from dotenv import load_dotenv

def list_models():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: No se encontró API Key")
        return
    
    genai.configure(api_key=api_key)
    try:
        print(f"--- Listando modelos para la llave que empieza por {api_key[:4]} ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Modelo: {m.name}")
    except Exception as e:
        print(f"ERROR al listar modelos: {e}")

if __name__ == "__main__":
    list_models()
