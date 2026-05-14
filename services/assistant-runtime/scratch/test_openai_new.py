import os
import asyncio
from litellm import aimage_generation

async def test_openai_new():
    api_key = os.getenv("OPENAI_API_KEY")
    # Intentamos los modelos nuevos de OpenAI que vimos
    models = [
        "openai/gpt-image-2",
        "openai/gpt-image-1.5",
        "openai/chatgpt-image-latest"
    ]
    
    for model in models:
        try:
            print(f"Probando {model}...")
            response = await aimage_generation(
                model=model,
                prompt="A beautiful space landscape",
                api_key=api_key
            )
            if response.data and len(response.data) > 0:
                print(f"!!! SUCCESS with {model}: {response.data[0].url}")
                return
        except Exception as e:
            print(f"FAILED {model}: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai_new())
