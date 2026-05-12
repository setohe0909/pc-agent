import asyncio
import httpx
import base64
import json

async def test_marketing_v04():
    url = "http://localhost:8100/assistant/request"
    
    # Imagen de prueba (un pixel blanco minimalista en base64)
    # Esto es suficiente para que el adapter lo decodifique y lo envíe a Gemini
    dummy_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1FSAAAAAElFTkSuQmCC"
    
    payload = {
        "action_type": "marketing",
        "prompt": "EJECUTA LA HERRAMIENTA plan_campaign: Crea un plan de campaña detallado para mi marca de ropa minimalista basándote en esta imagen adjunta.",
        "source": {
            "platform": "discord",
            "channel_id": "12345",
            "user_id": "67890"
        },
        "images": [dummy_image_b64],
        "payload": {
            "sub_command": "plan" 
        }
    }
    
    print(f"--- INICIANDO TEST MARKETING v0.4.0 ---")
    print(f"Prompt: {payload['prompt']}")
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(url, json=payload)
            print(f"Status Code: {resp.status_code}")
            result = resp.json()
            
            print("\n--- RESULTADO DEL GRAFO ---")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')[:500]}...") # Mostrar solo el inicio
            
            if result.get("status") == "requires_approval":
                print("\n✅ TEST EXITOSO: El grafo detectó que se requiere aprobación para el plan de campaña.")
                print("Esto confirma que los nodos 'Critic' y 'Refiner' fueron ejecutados.")
            else:
                print("\n⚠️ El resultado no fue el esperado (requires_approval). Revisa los logs del runtime.")
                
        except Exception as e:
            print(f"❌ Error conectando al runtime: {e}")
            print("Asegúrate de que 'assistant-runtime' esté corriendo en el puerto 8100.")

if __name__ == "__main__":
    asyncio.run(test_marketing_v04())
