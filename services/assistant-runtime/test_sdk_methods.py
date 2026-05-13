import os
import google.generativeai as genai

def test_sdk_image():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return
    
    genai.configure(api_key=api_key)
    try:
        # Use a model from the list we got
        model_name = "models/imagen-3.0-generate-001"
        print(f"Testing {model_name}...")
        model = genai.GenerativeModel(model_name)
        # For Imagen models, the method might be different or it might not be supported via generate_content
        # In current SDK, Imagen is often handled via a different class or not supported in this version.
        
        # Let's try to see if it's in the model's supported_generation_methods
        m = genai.get_model(model_name)
        print(f"Supported methods: {m.supported_generation_methods}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_sdk_image()
