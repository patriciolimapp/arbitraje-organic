import asyncio
import os
from playwright.async_api import async_playwright

SESSION_FILE = "aliexpress_state.json"
MODO_TEST_SEGURO = True  # True = Se detiene antes de gastar dinero para auditar el checkout

async def aplicar_stealth_nativo(page):
    """Inyecta los scripts anti-detección de forma nativa."""
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.navigator.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es', 'en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    """)

async def procesar_compra(email_cliente: str, id_producto: str):
    print(f"📦 [BOT LOGÍSTICO] Iniciando proceso para {email_cliente} | Producto ID: {id_producto}")
    print(f"🛡️ [MODO DE SEGURIDAD] Dry Run activo: {MODO_TEST_SEGURO}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"]
        )

        if os.path.exists(SESSION_FILE):
            print("🔑 [AUTENTICACIÓN] Inyectando sesión maestra...")
            context = await browser.new_context(storage_state=SESSION_FILE)
        else:
            print("❌ [ERROR] No se encontró 'aliexpress_state.json'.")
            await browser.close()
            return

        page = await context.new_page()
        await aplicar_stealth_nativo(page)

        try:
            # 1. Navegación al producto
            url_producto = f"https://es.aliexpress.com/item/{id_producto}.html"
            print(f"🌐 Navegando al producto: {url_producto}")
            
            await page.goto(url_producto, timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            print("✅ Producto cargado correctamente.")
            await asyncio.sleep(4)

            # 2. Selección de variantes (si aplica)
            print("🎨 Verificando opciones de variantes...")
            try:
                sku_opciones = page.locator(".sku-item--image--3S-8X9f, img.sku-item").all()
                if sku_opciones and len(sku_opciones) > 0:
                    await sku_opciones[0].click()
                    print("✅ Primera variante seleccionada.")
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"ℹ️ Nota de variantes: {e}")

            # 3. Clic en el botón "Comprar" de la ficha de producto
            print("🛒 Pulsando el botón 'Comprar'...")
            selector_comprar = "button.buy-now--buynow--OH44OI8, button:has-text('Comprar')"
            await page.wait_for_selector(selector_comprar, state="visible", timeout=10000)
            await page.click(selector_comprar, force=True)
            print("✅ ¡Clic ejecutado en la ficha del producto!")

            # 4. Esperar la transición a la pantalla de Checkout (confirm.html)
            print("⏳ Esperando transición a la pasarela de pago (Checkout)...")
            try:
                await page.wait_for_url("**/trade/confirm.html**", timeout=15000)
                print("🚀 ¡Aterrizaje exitoso en la pantalla de Checkout!")
            except Exception as e:
                print(f"⚠️ La URL de confirmación tardó en cargar o es distinta, continuando de todos modos: {e}")

            # Estabilización del DOM del Checkout
            await asyncio.sleep(5)

            # 5. Localización del botón final "Realizar pedido" (Extraído de tu inspección)
            print("🔍 Localizando botón final de pago en el Checkout...")
            selector_realizar_pedido = "button.place-order-primary-btn, button:has-text('Realizar pedido')"
            
            await page.wait_for_selector(selector_realizar_pedido, state="visible", timeout=10000)
            print("✅ ¡Botón 'Realizar pedido' localizado y verificado en pantalla!")

            # 6. Evaluación de la Bandera de Seguridad (Dry Run)
            if MODO_TEST_SEGURO:
                print("\n" + "🛡️" + "="*50 + "🛡️")
                print("🛑 MODO TEST SEGURO ACTIVADO: DETENIENDO ANTES DE PAGAR 🛑")
                print("El bot ha completado el flujo completo: Carrito -> Variantes -> Checkout.")
                
                screenshot_path = "captura_checkout_final.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Evidencia visual completa del Checkout guardada en: {screenshot_path}")
                print("🛡️" + "="*50 + "🛡️\n")
            else:
                # ZONA DE PRODUCCIÓN REAL (Dinero real)
                print("⚡ [PRODUCCIÓN] Ejecutando clic final en 'Realizar pedido'...")
                # await page.click(selector_realizar_pedido, force=True)

            print("⏸️ Pausa de inspección de 10 segundos antes de cerrar el navegador...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"❌ Error durante el flujo automatizado: {e}")
        finally:
            await browser.close()
            print("🔒 Navegador cerrado de forma segura.")

if __name__ == "__main__":
    id_producto_piloto = "1005008751496327"  # Guante para mascotas
    asyncio.run(procesar_compra("cliente_prueba@gmail.com", id_producto_piloto))