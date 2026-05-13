import os
import google.generativeai as genai

def test_sdk_methods_v4():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return
    
    genai.configure(api_key=api_key)
    model_name = "models/imagen-4.0-generate-001"
    try:
        print(f"Testing {model_name}...")
        m = genai.get_model(model_name)
        print(f"Supported methods: {m.supported_generation_methods}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_sdk_methods_v4()
