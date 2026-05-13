import httpx
import json

async def test_save():
    url = "http://localhost:8000/config/runtime"
    token = "mi-super-secreto-123"
    
    payload = {
        "coder_web_stack": "react-ts",
        "wix_api_key": "wix_test_key_123"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Token": token
    }
    
    print(f"📡 Probando guardado en {url} con token real...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.put(url, json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_save())
