import os
import google.generativeai as genai

def test_sdk_image():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return
    
    genai.configure(api_key=api_key)
    try:
        # Check if we can use Imagen with standard GenerativeModel
        model = genai.GenerativeModel("imagen-3.0-generate-001")
        response = model.generate_content("A cute cat")
        print(f"Response: {response}")
        # If it returns images, they are in response.candidates[0].content.parts
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_sdk_image()
