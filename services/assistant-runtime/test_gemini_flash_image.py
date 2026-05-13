import os
import asyncio
from litellm import completion

async def test_gemini_image_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return
    
    try:
        print("Testing gemini-2.5-flash-image...")
        response = await completion(
            model="gemini/gemini-2.5-flash-image",
            messages=[{"role": "user", "content": "Generate a beautiful landscape image"}],
            api_key=api_key
        )
        print(f"Response: {response}")
        # Check if there is an image in the message parts
        msg = response.choices[0].message
        if hasattr(msg, 'content') and msg.content:
            print(f"Content: {msg.content}")
        # LiteLLM usually converts image parts to a specific format
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_image_model())
