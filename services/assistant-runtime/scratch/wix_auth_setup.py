import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    """
    Este script abre un navegador persistente para que el usuario pueda hacer login 
    manualmente en Wix. Una vez logueado, las cookies se guardarán en el perfil local
    y el agente podrá usarlas después de forma autónoma.
    """
    user_data_dir = os.path.abspath("./playwright_wix_session")
    
    print(f"--- Wix Auth Setup ---")
    print(f"Se abrirá un navegador (con UI).")
    print(f"Por favor, inicia sesión en Wix Studio.")
    print(f"Cuando termines y veas tu dashboard, cierra el navegador o presiona Ctrl+C aquí.")
    print(f"Perfil guardado en: {user_data_dir}")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False, # Necesitamos ver la UI para loguearnos
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        await page.goto("https://www.wix.com/login")
        
        # Mantener abierto hasta que el usuario decida
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nCerrando sesión y guardando perfil...")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(run())
