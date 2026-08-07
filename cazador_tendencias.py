import os
import re
from playwright.sync_api import sync_playwright

CARPETA_DATA = "data"
ARCHIVO_SALIDA = os.path.join(CARPETA_DATA, "lista_productos.txt")

# ==========================================
# UMBRALES MATEMÁTICOS DE RENTABILIDAD
# ==========================================
META_DESEADA = 5         
PRECIO_MAXIMO_MXN = 350.00 
RATING_MINIMO = 4.5
VENTAS_MINIMAS = 1000

def limpiar_ventas(texto_body):
    """
    Busca en la página del producto el número real de ventas.
    Corrige el error del punto decimal en español (ej. '10.000+ vendido(s)')
    """
    # Buscamos patrones como "10.000+ vendido(s)", "5k sold", "1,500 vendidos"
    match = re.search(r'([0-9kK\+\.,]+)\s*(vendido|sold)', texto_body)
    if not match: 
        return 0
    
    # Extraemos solo la parte numérica/letras (ej. "10.000+" o "5k")
    num_str = match.group(1).lower().replace('+', '')
    
    try:
        # Si tiene 'k' (ej. 10k), removemos la k, multiplicamos por 1000
        if 'k' in num_str:
            num_limpio = num_str.replace('k', '').replace(',', '.').strip()
            return int(float(num_limpio) * 1000)
            
        # Si NO tiene 'k', asumimos que es un número completo (ej. 10.000 o 1500)
        # Eliminamos TODOS los puntos y comas para evitar el error de los decimales
        num_limpio = num_str.replace('.', '').replace(',', '').strip()
        return int(num_limpio)
        
    except Exception as e:
        print(f"   [Debug Regex] Falló al limpiar la cadena: '{num_str}'. Error: {e}")
        return 0

def cazar_tendencias_cdp(nicho="car gadgets"):
    print(f"🚀 [MOTOR V6 - 2 FASES] Conectando a Chrome para rastrear: '{nicho}'")
    os.makedirs(CARPETA_DATA, exist_ok=True)
    productos_aprobados = 0
    pagina_actual = 1

    with sync_playwright() as p:
        try:
            print("🔌 Enlazando con Chrome Real (Puerto 9222)...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] 
            page = context.new_page()
        except Exception:
            print("❌ [ERROR] Ejecuta Chrome en modo depuración (Puerto 9222) primero.")
            return
        
        keyword = nicho.replace(" ", "-")

        while productos_aprobados < META_DESEADA:
            url_busqueda = f"https://www.aliexpress.com/w/wholesale-{keyword}.html?SortType=total_tranpro_desc&page={pagina_actual}"
            
            print(f"\n📄 [FASE 1: RECONOCIMIENTO] Explorando Página {pagina_actual}...")
            try:
                page.goto(url_busqueda, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4000)
            except Exception:
                print("⚠️ La página tardó en cargar. Reintentando...")
            
            print("🌀 Haciendo scroll para revelar tarjetas (Lazy Loading)...")
            for _ in range(5):
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(1500)

            # Extraemos las tarjetas usando la clase del grid
            tarjetas = page.locator("a.search-card-item").all()
            enlaces_pre_aprobados = []

            for tarjeta in tarjetas:
                try:
                    texto_tarjeta = tarjeta.inner_text()
                    url = tarjeta.get_attribute("href")
                    
                    # Regex infalible para el precio "MX$ 149.9"
                    precios = re.findall(r'MX\$\s*([0-9]+(?:[\.,][0-9]+)?)', texto_tarjeta.replace(',', ''))
                    precio_val = float(precios[0]) if precios else 9999.0
                    
                    # Regex para calificación "4.8" o "5.0"
                    ratings = re.findall(r'\b([345]\.[0-9])\b', texto_tarjeta)
                    rating_val = float(ratings[0]) if ratings else 0.0

                    if precio_val <= PRECIO_MAXIMO_MXN and rating_val >= RATING_MINIMO:
                        url_limpia = url.split("?")[0]
                        if not url_limpia.startswith("http"): url_limpia = "https:" + url_limpia
                        if url_limpia not in enlaces_pre_aprobados:
                            enlaces_pre_aprobados.append(url_limpia)
                            print(f"   -> 🎯 Pre-Aprobado (Grid): ${precio_val} MXN | ⭐ {rating_val}")
                except Exception:
                    continue

            print(f"\n🔍 [FASE 2: ASALTO PROFUNDO] Verificando Ventas y Video en {len(enlaces_pre_aprobados)} productos...")
            
            for url in enlaces_pre_aprobados:
                if productos_aprobados >= META_DESEADA: break
                
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(3000) # Esperamos 3 segs para que cargue el texto de ventas y el reproductor de video
                    
                    # Extraer todo el texto de la página del producto
                    texto_body = page.locator("body").inner_text().lower()
                    
                    ventas_reales = limpiar_ventas(texto_body)
                    tiene_video = page.locator("video").count() > 0
                    
                    if ventas_reales >= VENTAS_MINIMAS and tiene_video:
                        print(f"   ✅ [¡BINGO!] Producto RENTABLE: {ventas_reales} ventas comprobadas y CON VIDEO.")
                        with open(ARCHIVO_SALIDA, "a", encoding="utf-8") as archivo:
                            archivo.write(url + "\n")
                        productos_aprobados += 1
                    else:
                        print(f"   ❌ Descartado interno: Ventas({ventas_reales}) | Video({tiene_video})")
                except Exception as e:
                    print("   ⚠️ Error cargando el producto o timeout. Saltando...")

            pagina_actual += 1
            if pagina_actual > 10: break
        
        try:
            page.close()
        except:
            pass
        print("\n🏆 [MISIÓN CUMPLIDA] Cacería Finalizada con éxito.")

if __name__ == "__main__":
    cazar_tendencias_cdp("car gadgets")
