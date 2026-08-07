# modulos/organico/enriquecedor_catalogo.py
import os
import re
import json
import statistics
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

# ==========================================
# CONFIGURACIÓN
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
LISTA_PRODUCTOS = os.path.join(DATA_DIR, "lista_productos.txt")
OUTPUT_JSON = os.path.join(DATA_DIR, "products.json")

# Umbrales para enriquecer (los mismos que usó el cazador)
PRECIO_MAXIMO_MXN = 350.00
RATING_MINIMO = 4.5
VENTAS_MINIMAS = 1000

# ==========================================
# FUNCIONES AUXILIARES (Reutilizadas del cazador)
# ==========================================
def limpiar_ventas(texto_body):
    """Extrae el número de ventas del texto de la página."""
    match = re.search(r'([0-9kK\+\.,]+)\s*(vendido|sold)', texto_body)
    if not match: 
        return 0
    num_str = match.group(1).lower().replace('+', '')
    try:
        if 'k' in num_str:
            num_limpio = num_str.replace('k', '').replace(',', '.').strip()
            return int(float(num_limpio) * 1000)
        num_limpio = num_str.replace('.', '').replace(',', '').strip()
        return int(num_limpio)
    except Exception:
        return 0

def extraer_datos_producto(page, url):
    """
    Navega a la URL del producto y extrae Título, Imagen, Precio, Rating y Video.
    Retorna un diccionario con los campos normalizados.
    """
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(4000)  # Espera crítica para que carguen los scripts de imagen/video
        
        # 1. Título (H1 principal)
        titulo = page.locator("h1").first.inner_text().strip()
        if not titulo:
            # Fallback a meta tag
            titulo = page.locator('meta[property="og:title"]').get_attribute("content") or "Producto sin nombre"
        
        # 2. ID del producto (desde la URL)
        match_id = re.search(r'/item/(\d+)\.html', url)
        producto_id = match_id.group(1) if match_id else "000000"
        
        # 3. Imagen principal (usamos meta og:image que es la más fiable)
        imagen_url = page.locator('meta[property="og:image"]').get_attribute("content")
        if not imagen_url:
            # Fallback: buscar la primera imagen grande en el carrusel
            imagen_url = page.locator("img[data-role='main-image']").get_attribute("src") or ""
        
        # 4. Precio (usamos la regex exacta del cazador)
        texto_body = page.locator("body").inner_text()
        precios = re.findall(r'MX\$\s*([0-9]+(?:[\.,][0-9]+)?)', texto_body.replace(',', ''))
        precio_val = float(precios[0]) if precios else 9999.0
        
        # 5. Rating (usamos la regex del cazador)
        ratings = re.findall(r'\b([345]\.[0-9])\b', texto_body)
        rating_val = float(ratings[0]) if ratings else 0.0
        
        # 6. Ventas (usamos la función del cazador)
        ventas_val = limpiar_ventas(texto_body)
        
        # 7. Video (buscamos cualquier tag <video> y su source)
        video_url = ""
        if page.locator("video").count() > 0:
            # Intentar obtener el src del source o del propio video
            video_url = page.locator("video source").get_attribute("src") or ""
            if not video_url:
                video_url = page.locator("video").get_attribute("src") or ""
            # Limpiar URL relativa
            if video_url and video_url.startswith("//"):
                video_url = "https:" + video_url
        
        # 8. Categoría (intentamos extraer la miga de pan)
        categoria = "General"
        breadcrumbs = page.locator("nav[aria-label='Breadcrumb'] a").all_text_contents()
        if len(breadcrumbs) >= 2:
            categoria = breadcrumbs[-1].strip()
        elif len(breadcrumbs) == 1:
            categoria = breadcrumbs[0].strip()
            
        return {
            "id": producto_id,
            "title": titulo[:120],  # Limitar longitud
            "price": precio_val,
            "currency": "MXN",
            "rating": rating_val,
            "sales": ventas_val,
            "image_url": imagen_url,
            "video_url": video_url,
            "category": categoria,
            "url": url
        }
    except Exception as e:
        print(f"   ⚠️ Error extrayendo datos de {url}: {e}")
        return None

def guardar_catalogo(productos, ruta=OUTPUT_JSON):
    """Enriquece y guarda el catálogo en JSON con texto comparativo."""
    if not productos:
        print("[!] No hay productos para guardar.")
        return False
    
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    
    # Calcular mediana de precios
    precios = [p['price'] for p in productos if p.get('price', 0) > 0]
    mediana = statistics.median(precios) if precios else 0
    
    enriched = []
    for p in productos:
        # Generar texto comparativo (exactamente como lo planeamos)
        if mediana and p['price'] < mediana * 0.9:
            ahorro = int((1 - p['price']/mediana)*100)
            comparacion = f"{ahorro}% más barato que el promedio de su categoría."
        else:
            comparacion = "Precio competitivo dentro de su categoría."
        
        if p.get('rating', 0) >= 4.7:
            comparacion += f" ⭐ {p['rating']} estrellas con más de {p.get('sales', 0)} ventas."
        elif p.get('sales', 0) > 1000:
            comparacion += f" Más de {p['sales']} ventas en los últimos meses."
        
        enriched.append({
            "id": p['id'],
            "title": p['title'],
            "price": float(p['price']),
            "currency": p['currency'],
            "rating": float(p['rating']),
            "sales": int(p['sales']),
            "image_url": p['image_url'],
            "video_url": p.get('video_url', ''),
            "category": p['category'],
            "comparison_text": comparacion,
            "updated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        })
    
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump({"products": enriched}, f, indent=2, ensure_ascii=False)
    
    print(f"[✔] Catálogo orgánico guardado: {len(enriched)} productos en {ruta}")
    return True

# ==========================================
# ORQUESTADOR DEL ENRIQUECEDOR
# ==========================================
def enriquecer_catalogo():
    """Lee lista_productos.txt, visita cada URL, extrae datos y genera products.json."""
    print("🚀 INICIANDO ENRIQUECEDOR DE CATÁLOGO (Fase Orgánica)")
    
    if not os.path.exists(LISTA_PRODUCTOS):
        print(f"❌ No se encuentra {LISTA_PRODUCTOS}. Ejecuta primero el cazador.")
        return False
    
    with open(LISTA_PRODUCTOS, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        print("❌ La lista de productos está vacía.")
        return False
    
    print(f"[+] Se encontraron {len(urls)} URLs para enriquecer.")
    
    productos_extraidos = []
    
    with sync_playwright() as p:
        try:
            print("🔌 Conectando a Chrome en modo depuración (Puerto 9222)...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()
        except Exception:
            print("❌ ERROR: Ejecuta Chrome con --remote-debugging-port=9222 primero.")
            return False
        
        for idx, url in enumerate(urls, 1):
            print(f"\n📦 [{idx}/{len(urls)}] Procesando: {url}")
            datos = extraer_datos_producto(page, url)
            
            if datos:
                # Filtrar por si acaso (redundante porque el cazador ya filtró)
                if datos['price'] <= PRECIO_MAXIMO_MXN and datos['rating'] >= RATING_MINIMO and datos['sales'] >= VENTAS_MINIMAS:
                    print(f"   ✅ {datos['title'][:40]}... | ${datos['price']} | ⭐{datos['rating']} | {datos['sales']} ventas")
                    productos_extraidos.append(datos)
                else:
                    print(f"   ⚠️ El producto ya no cumple los umbrales. Saltando.")
            else:
                print(f"   ❌ No se pudieron extraer datos.")
        
        try:
            page.close()
        except:
            pass
    
    if productos_extraidos:
        guardar_catalogo(productos_extraidos)
        print("\n✅ ENRIQUECIMIENTO COMPLETADO CON ÉXITO.")
        return True
    else:
        print("\n❌ No se extrajo ningún producto válido.")
        return False

if __name__ == "__main__":
    enriquecer_catalogo()