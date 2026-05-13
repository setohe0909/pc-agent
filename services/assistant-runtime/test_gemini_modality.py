import os
from litellm import completion

def test_gemini_image_modality():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return
    
    try:
        print("Testing gemini-2.0-flash image generation...")
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": "Generate an image of a cat"}],
            # modalities=["image"] # Some versions use this
        )
        print(f"Response: {response}")
        # Check if there is an image in the response
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_gemini_image_modality()
