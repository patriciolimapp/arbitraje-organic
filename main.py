import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# Definimos la ruta para guardar la sesión y evadir el login manual
SESSION_FILE = "aliexpress_state.json"

async def procesar_compra(email_cliente: str, id_producto: str):
    """
    Motor logístico de Playwright. Recibe los parámetros desde FastAPI.
    """
    print(f"📦 [BOT LOGÍSTICO] Iniciando proceso para {email_cliente} | Producto: {id_producto}")

    async with async_playwright() as p:
        # Lanzamos Chromium. 
        # NOTA: args=["--disable-blink-features=AutomationControlled"] es vital para evadir detecciones básicas.
        browser = await p.chromium.launch(
            headless=False, # Mantenlo en False mientras desarrollamos para ver qué hace el bot
            args=["--disable-blink-features=AutomationControlled"]
        )

        # 1. Gestión del Contexto y Sesión (Inyección de Cookies)
        if os.path.exists(SESSION_FILE):
            print("🔑 Inyectando sesión previa...")
            context = await browser.new_context(storage_state=SESSION_FILE)
        else:
            print("⚠️ No se encontró estado. Levantando contexto limpio.")
            context = await browser.new_context()

        # 2. Creación de página y aplicación estricta del Stealth Mode
        page = await context.new_page()
        
        # IMPORTANTE: El stealth debe inyectarse ANTES de navegar a cualquier URL
        await stealth_async(page)

        try:
            # 3. Navegación inicial a AliExpress
            print("🌐 Navegando a AliExpress...")
            await page.goto("https://www.aliexpress.com/", wait_until="domcontentloaded")

            # 4. Lógica de captura de sesión (Solo se ejecuta la primera vez)
            if not os.path.exists(SESSION_FILE):
                print("\n🛑 ALTO AHÍ: Necesitamos crear la sesión maestra.")
                print("1. Inicia sesión manualmente en la ventana del navegador que se acaba de abrir.")
                print("2. Resuelve cualquier Captcha de Cloudflare o de AliExpress.")
                print("3. Vuelve a esta consola y presiona ENTER.")
                input() # Detiene la ejecución asíncrona momentáneamente
                
                # Guardamos todas las cookies y el local storage
                await context.storage_state(path=SESSION_FILE)
                print("✅ Estado guardado exitosamente. La próxima vez el bot entrará directo.")
            else:
                print("✅ Sesión validada. Listo para interactuar con el producto.")
                
                # ---------------------------------------------------------
                # AQUÍ COMENZAREMOS LA LÓGICA DE COMPRA EN EL PRÓXIMO PASO
                # await page.goto(f"https://es.aliexpress.com/item/{id_producto}.html")
                # ---------------------------------------------------------

        except Exception as e:
            print(f"❌ Error crítico en la tubería logística: {e}")
        finally:
            await context.close()
            await browser.close()

# Bloque de prueba local para ejecutarlo de forma aislada sin FastAPI
if __name__ == "__main__":
    asyncio.run(procesar_compra("cliente_prueba@gmail.com", "1005001234567890"))