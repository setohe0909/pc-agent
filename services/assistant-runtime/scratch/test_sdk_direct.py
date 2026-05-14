import os
import google.generativeai as genai

def test_sdk():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    # Intentamos el modelo que vimos disponible
    model_name = "imagen-4.0-generate-001"
    print(f"Probando SDK con {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        # Nota: Imagen en el SDK no siempre usa generate_content
        # Pero veamos si responde algo
        response = model.generate_content("A beautiful sunrise")
        print(f"SDK Response: {response}")
    except Exception as e:
        print(f"SDK FAILED {model_name}: {e}")

if __name__ == "__main__":
    test_sdk()
