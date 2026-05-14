import os
import asyncio
from litellm import aimage_generation

async def hunt_for_working_model():
    api_key = os.getenv("GEMINI_API_KEY")
    candidates = [
        "gemini/imagen-4.0-fast-generate-001",
        "gemini/imagen-4.0-generate-001",
        "gemini/gemini-3.1-flash-image-preview",
        "gemini/gemini-2.5-flash-image",
        "gemini/gemini-3-pro-image-preview",
        "gemini/imagen-3.0-generate-001",
        "gemini/imagen-3.0-fast-generate-001",
    ]
    
    for model in candidates:
        try:
            print(f"Probando {model}...")
            response = await aimage_generation(
                model=model,
                prompt="A small floating island with a tree",
                api_key=api_key
            )
            if response.data and len(response.data) > 0:
                item = response.data[0]
                if item.url:
                    print(f"!!! SUCCESS with {model} (URL): {item.url}")
                    return model
                elif hasattr(item, 'b64_json') and item.b64_json:
                    print(f"!!! SUCCESS with {model} (B64): {item.b64_json[:50]}...")
                    return model
                else:
                    print(f"Data found but no URL/B64 in {model}: {item}")
            else:
                print(f"Empty data list from {model}")
        except Exception as e:
            print(f"Error en {model}: {str(e)[:100]}")
            
    return None

if __name__ == "__main__":
    asyncio.run(hunt_for_working_model())
