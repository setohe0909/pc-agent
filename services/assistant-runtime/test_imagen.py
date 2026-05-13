import os
import asyncio
from litellm import image_generation

async def test_image():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return
    
    try:
        response = await image_generation(
            model="gemini/imagen-4.0-generate-001",
            prompt="A futuristic neon cat",
            api_key=api_key
        )
        print(f"Success: {response.data[0].url}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_image())
