import os
import google.generativeai as genai

def test_multimodal_image():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    model_name = "gemini-3.1-flash-image-preview"
    print(f"Probando {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Generate a detailed image of a futuristic city. Return the image data.")
        print(f"Response parts: {len(response.candidates[0].content.parts)}")
        for i, part in enumerate(response.candidates[0].content.parts):
            print(f"Part {i}: {type(part)}")
            # En modelos que generan imágenes, a veces vienen como inline_data o similar
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"Part {i} has inline_data!")
            if hasattr(part, 'text') and part.text:
                print(f"Part {i} text: {part.text[:100]}")
    except Exception as e:
        print(f"FAILED {model_name}: {e}")

if __name__ == "__main__":
    test_multimodal_image()
