import os
import requests
from playwright.sync_api import sync_playwright

def descargar_video_aliexpress(url_producto, nombre_salida="video_crudo.mp4"):
    """
    Navega a un producto de AliExpress, intercepta la red para capturar
    el archivo .mp4 y lo descarga localmente.
    """
    print(f"🕵️‍♂️ [EXTRACTOR] Iniciando escaneo sigiloso en: {url_producto}")
    
    with sync_playwright() as p:
        # Usamos headless=False al inicio para ver cómo opera el bot
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 1. Inyectamos evasión algorítmica para evitar captchas
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        
        page = context.new_page()
        video_url = None
        
        # 2. Listener de Intercepción de Red
        def manejar_respuesta(response):
            nonlocal video_url
            # Detectamos si el tráfico entrante es un video MP4
            if ".mp4" in response.url or response.headers.get("content-type", "") == "video/mp4":
                video_url = response.url
                
        page.on("response", manejar_respuesta)
        
        print("⏳ [NAVEGANDO] Cargando la página del producto y escuchando la red...")
        # wait_until="domcontentloaded" acelera el proceso sin esperar imágenes pesadas
        page.goto(url_producto, wait_until="domcontentloaded", timeout=60000)
        
        # 3. Forzar la aparición del video en el DOM
        try:
            # Esperamos hasta 15 segundos a que el contenedor del video exista
            page.wait_for_selector("video", timeout=15000)
            print("▶️ [INTERACCIÓN] Etiqueta de video detectada. Forzando reproducción...")
            # Un clic forza la carga del buffer del mp4 disparando la intercepción
            page.locator("video").first.click(force=True)
            page.wait_for_timeout(4000) # Damos 4 segundos para que el paquete de red pase
        except Exception:
            print("⚠️ [AVISO] No se encontró etiqueta <video> para hacer clic. Buscando URL estática...")
        
        # 4. Plan de Respaldo: Extraer del atributo SRC si la intercepción no funcionó
        if not video_url:
            try:
                src = page.locator("video").first.get_attribute("src")
                if src:
                    if src.startswith("//"):
                        video_url = "https:" + src
                    elif src.startswith("http"):
                        video_url = src
            except Exception:
                pass

        browser.close()
        
        # 5. Descarga del Activo Multimedia
        if video_url:
            print(f"✅ [ÉXITO] URL del video capturada: {video_url}")
            print(f"📥 [DESCARGANDO] Escribiendo archivo en disco como {nombre_salida}...")
            
            # Descargamos el video usando streams para no saturar la memoria RAM
            respuesta_descarga = requests.get(video_url, stream=True)
            if respuesta_descarga.status_code == 200:
                with open(nombre_salida, 'wb') as archivo:
                    for chunk in respuesta_descarga.iter_content(chunk_size=8192):
                        archivo.write(chunk)
                ruta_absoluta = os.path.abspath(nombre_salida)
                print(f"🎉 [FINALIZADO] Video guardado correctamente en:\n   -> {ruta_absoluta}")
            else:
                print(f"❌ [ERROR] El servidor rechazó la descarga. Código HTTP: {respuesta_descarga.status_code}")
        else:
            print("❌ [ERROR] El bot no detectó ningún video. Asegúrate de que el producto realmente tenga uno.")

if __name__ == "__main__":
    # Sustituye esta variable por la URL real de tu producto de Pet Care / Tech
    URL_PRUEBA = "https://es.aliexpress.com/item/1005012420494258.html?spm=a2g0o.productlist.main.3.14d4Y8zRY8zRsR&algo_pvid=39122d18-a3d9-4063-a6b9-f869396e96e4&pdp_ext_f=%7B%22order%22%3A%22-1%22%2C%22eval%22%3A%221%22%2C%22fromPage%22%3A%22search%22%7D&utparam-url=scene%3Asearch%7Cquery_from%3A%7Cx_object_id%3A1005012420494258%7C_p_origin_prod%3A" # Ejemplo genérico
    descargar_video_aliexpress(URL_PRUEBA)