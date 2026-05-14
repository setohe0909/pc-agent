import os
import asyncio
from litellm import aimage_generation

async def test():
    api_key = os.getenv("GEMINI_API_KEY")
    # Intentamos los modelos que detectamos como disponibles
    models = [
        "gemini/gemini-3.1-flash-image-preview",
        "gemini/imagen-4.0-generate-001",
        "gemini/imagen-4.0-fast-generate-001",
    ]
    
    for model in models:
        try:
            print(f"Probando {model}...")
            response = await aimage_generation(
                model=model,
                prompt="A futuristic neon cat in a cyberpunk city",
                api_key=api_key
            )
            print(f"RESPONSE from {model}: {response}")
            if response.data and len(response.data) > 0:
                print(f"SUCCESS with {model}: {response.data[0].url}")
                return
            else:
                 print(f"EMPTY DATA from {model}")
        except Exception as e:
            print(f"FAILED {model}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
