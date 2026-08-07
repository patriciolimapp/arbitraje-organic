import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

def descargar_video_aliexpress(url_producto, ruta_salida):
    print("[EXTRACTOR CDP] Conectando al navegador activo en el puerto 9222...")
    
    with sync_playwright() as p:
        try:
            # Conectamos al Chrome Zombie que tienes abierto
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            default_context = browser.contexts[0]
            page = default_context.new_page()
        except Exception as e:
            print("[ERROR CDP] No se pudo conectar a Chrome. Asegúrate de que el puerto 9222 está abierto.")
            return False

        print(f"[EXTRACTOR] Navegando sigilosamente a: {url_producto}")
        
        try:
            page.goto(url_producto, timeout=60000)
        except Exception:
            print("[ALERTA] La página tardó mucho en cargar, intentando extraer de todos modos...")

        video_url = None
        print("[EXTRACTOR] Analizando el árbol DOM en busca del archivo de video...")
        
        try:
            # Buscamos agresivamente la etiqueta <source> dentro del reproductor <video>
            page.wait_for_selector("video source", timeout=15000)
            elemento_source = page.locator("video source").first
            video_url = elemento_source.get_attribute("src")
        except Exception:
            print("[-] No se detectó ninguna etiqueta de video en el DOM. Es un producto estático o requiere scroll.")

        page.close()

        if video_url:
            # Limpiamos la URL por si AliExpress la entrega sin "https:"
            if video_url.startswith("//"):
                video_url = "https:" + video_url
                
            print(f"[+] URL DE VIDEO LOCALIZADA: {video_url}")
            print("[EXTRACTOR] Iniciando descarga binaria del activo...")
            
            try:
                # Forzamos la descarga del MP4 usando la URL extraída
                respuesta = requests.get(video_url, stream=True, timeout=30)
                if respuesta.status_code == 200:
                    with open(ruta_salida, 'wb') as archivo:
                        for chunk in respuesta.iter_content(chunk_size=8192):
                            archivo.write(chunk)
                    print(f"[FINALIZADO] Video guardado correctamente en: {ruta_salida}")
                    return True
                else:
                    print(f"[ERROR] El servidor rechazó la descarga del MP4. Código HTTP: {respuesta.status_code}")
                    return False
            except Exception as e:
                print(f"[ERROR] Falló la conexión de descarga con el servidor de medios: {e}")
                return False
        else:
            return False

if __name__ == "__main__":
    # Blindaje contra errores de codificación en PowerShell/Windows
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print("[ERROR] Falta la URL del producto.")
        sys.exit(1)
        
    url_recibida = sys.argv[1]
    
    # Rutas dinámicas
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    VIDEOS_CRUDOS = os.path.join(DATA_DIR, "videos_crudos")
    os.makedirs(VIDEOS_CRUDOS, exist_ok=True)
    
    # Nombramos el archivo con un timestamp único
    nombre_archivo = f"crudo_{int(time.time())}.mp4"
    ruta_salida = os.path.join(VIDEOS_CRUDOS, nombre_archivo)
    
    exito = descargar_video_aliexpress(url_recibida, ruta_salida)
    
    if not exito:
        sys.exit(1)