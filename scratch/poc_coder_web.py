import asyncio
import httpx
import json

async def poc_coder_web():
    url = "http://localhost:8100/assistant/request"
    
    # Simular una solicitud de creación de e-commerce
    payload = {
        "action_type": "coder-web",
        "prompt": "crea un ecommerce de café orgánico con un diseño minimalista, usa el stack de react y supabase",
        "source": {
            "platform": "discord",
            "channel_id": "123456789",
            "user_id": "987654321"
        },
        "payload": {}
    }
    
    print(f"🚀 Enviando solicitud PoC a {url}...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                print("\n✅ Respuesta del Agente:")
                print(f"Status: {result.get('status')}")
                print(f"Mensaje:\n{result.get('message')}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    # Nota: Este script asume que el servicio assistant-runtime está corriendo localmente en el puerto 8100
    # Como estoy en un entorno de edición, solo lo dejo como referencia de cómo se vería la ejecución.
    # asyncio.run(poc_coder_web())
    print("Script de PoC preparado. Para ejecutarlo, asegúrate de que el servicio assistant-runtime esté activo.")
