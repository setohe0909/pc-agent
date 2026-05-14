import os
import asyncio
from litellm import aimage_generation

async def test():
    api_key = os.getenv("OPENAI_API_KEY")
    models = [
        "openai/gpt-image-2",
        "openai/gpt-image-1.5",
        "openai/chatgpt-image-latest"
    ]
    
    with open("/app/scratch/openai_result.txt", "w") as f:
        for model in models:
            try:
                f.write(f"Probando {model}...\n")
                f.flush()
                response = await aimage_generation(
                    model=model,
                    prompt="A beautiful sunrise",
                    api_key=api_key
                )
                if response.data and len(response.data) > 0:
                    f.write(f"SUCCESS with {model}: {response.data[0].url}\n")
                    return
            except Exception as e:
                f.write(f"FAILED {model}: {e}\n")
                f.flush()

if __name__ == "__main__":
    asyncio.run(test())
