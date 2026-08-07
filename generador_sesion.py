from playwright.sync_api import sync_playwright

def generar_sesion_maestra():
    print("🌐 [SESIÓN] Abriendo navegador limpio...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Evasión básica
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        
        print("🚀 [NAVEGANDO] Entrando a AliExpress...")
        page.goto("https://www.aliexpress.com/")
        
        print("\n=======================================================")
        print("🛑 ACCIÓN REQUERIDA EN EL NAVEGADOR 🛑")
        print("1. Si aparece un Captcha o Slider, resuélvelo manualmente ahora.")
        print("2. Navega un poco, haz algo de scroll para parecer humano.")
        print("3. (Opcional) Inicia sesión en tu cuenta para máxima confianza.")
        print("=======================================================\n")
        
        input("👉 PRESIONA 'ENTER' AQUÍ EN LA TERMINAL CUANDO HAYAS TERMINADO...")
        
        # Guardamos el estado exacto del navegador (Cookies, LocalStorage, etc.)
        context.storage_state(path="aliexpress_state.json")
        print("✅ [ÉXITO] Cookies guardadas y encriptadas en 'aliexpress_state.json'.")
        browser.close()

if __name__ == "__main__":
    generar_sesion_maestra()