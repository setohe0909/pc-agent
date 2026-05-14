import os
import asyncio
from litellm import aimage_generation

async def test_candidates():
    api_key = os.getenv("GEMINI_API_KEY")
    candidates = [
        "gemini/imagen-3.0-fast-generate-001",
        "gemini/imagen-3.0-generate-001",
        "gemini/imagen-4.0-fast-generate-001",
        "gemini/imagen-4.0-generate-001"
    ]
    
    for model in candidates:
        try:
            print(f"Testing {model}...")
            response = await aimage_generation(
                model=model,
                prompt="A small robot repairing a spaceship",
                api_key=api_key
            )
            print(f"SUCCESS with {model}: {response.data[0].url}")
            return
        except Exception as e:
            print(f"FAILED {model}: {e}")

if __name__ == "__main__":
    asyncio.run(test_candidates())
