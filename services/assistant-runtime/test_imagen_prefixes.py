import os
from litellm import image_generation

def test_image():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return
    
    # Try different prefixes
    models = ["google/imagen-3.0-generate-001", "google_ai/imagen-3.0-generate-001", "gemini/imagen-3.0-generate-001"]
    for model in models:
        try:
            print(f"Testing {model}...")
            response = image_generation(
                model=model,
                prompt="A cute cat",
                api_key=api_key
            )
            print(f"Success {model}: {response.data[0].url}")
            return
        except Exception as e:
            print(f"Failed {model}: {e}")

if __name__ == "__main__":
    test_image()
