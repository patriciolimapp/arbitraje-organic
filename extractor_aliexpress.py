import os
import sys
import re
import requests
from playwright.sync_api import sync_playwright

def descargar_video_aliexpress(url_producto):
    print("[EXTRACTOR CDP] Conectando al navegador activo en el puerto 9222...")
    with sync_playwright() as p:
        try:
            # 1. Conexión CDP al navegador "Zombie" con sesión autenticada
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            default_context = browser.contexts[0]
            page = default_context.new_page()
            
            print(f"[EXTRACTOR CDP] Navegando a la URL objetivo: {url_producto}")
            page.goto(url_producto, timeout=60000)
            
            # 2. Esperar a que la galería cargue y exista un elemento <video>
            page.wait_for_selector("video", timeout=15000)
            
            # 3. Extraer la URL real del video (desde <source>, currentSrc, o src)
            video_url = page.eval_on_selector(
                "video",
                """el => {
                    // Intenta obtener la URL del source hijo (caso más común en AliExpress)
                    const source = el.querySelector('source');
                    if (source && source.src) return source.src;
                    // Alternativa: currentSrc (la fuente activa, aunque no esté reproduciendo)
                    if (el.currentSrc) return el.currentSrc;
                    // Último recurso: el atributo src directo
                    return el.src || null;
                }"""
            )
            
            if not video_url:
                print("[-] ERROR CRÍTICO: No se encontró URL de video en el DOM tras inspeccionar todos los atributos.")
                page.close()
                sys.exit(1)
            
            # Limpiar URLs que empiezan con "//"
            if video_url.startswith("//"):
                video_url = "https:" + video_url
                
            print(f"[+] URL de video extraída exitosamente: {video_url}")
            
            # 4. Extraer el ID del producto de la URL para nombrar el archivo
            # Formato típico: .../item/1005008119544843.html
            match = re.search(r'/item/(\d+)\.html', url_producto)
            if match:
                producto_id = match.group(1)
            else:
                # Fallback: usar un timestamp parcial si no se detecta
                producto_id = f"producto_{int(__import__('time').time())}"
            
            nombre_archivo = f"{producto_id}.mp4"
            ruta_salida = os.path.join("data", "videos_crudos", nombre_archivo)
            os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
            
            # 5. Descarga binaria del video usando requests
            print(f"[EXTRACTOR CDP] Descargando video como '{nombre_archivo}'...")
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(ruta_salida, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            print(f"[+] EXTRACCIÓN EXITOSA. Video guardado en: {ruta_salida}")
            
            page.close()
            return True
            
        except Exception as e:
            print(f"[-] ERROR CRÍTICO EN extractor_aliexpress.py: {e}")
            sys.exit(1)

if __name__ == "__main__":
    # Compatibilidad Unicode en consola Windows
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    if len(sys.argv) < 2:
        print("ERROR: NO SE PROPORCIONÓ NINGUNA URL COMO ARGUMENTO.")
        sys.exit(1)
        
    url_objetivo = sys.argv[1]
    descargar_video_aliexpress(url_objetivo)