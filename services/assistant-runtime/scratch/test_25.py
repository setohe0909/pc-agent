import os
import google.generativeai as genai

def test_multimodal_25():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    model_name = "gemini-2.5-flash-image"
    print(f"Probando {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Generate a simple image of a blue square. Return the image data.")
        print(f"Response: {response}")
        # Si tiene éxito, buscamos el blob
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                print("SUCCESS: Found inline_data (image)!")
                return
    except Exception as e:
        print(f"FAILED {model_name}: {e}")

if __name__ == "__main__":
    test_multimodal_25()
