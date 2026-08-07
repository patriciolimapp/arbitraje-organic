import asyncio
import os
import csv
import random
import sys
import re

# ==========================================
# CONFIGURACIÓN DE RUTAS ABSOLUTAS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

LISTA_PRODUCTOS = os.path.join(DATA_DIR, "lista_productos.txt")
VIDEOS_CRUDOS = os.path.join(DATA_DIR, "videos_crudos")
VIDEOS_PROCESADOS = os.path.join(DATA_DIR, "videos_procesados")
CSV_GANCHOS = os.path.join(DATA_DIR, "ganchos_textos.csv")
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "proximanova_bold.ttf")

async def leer_urls():
    """Lee y limpia las URLs del archivo puente generado por el Cazador."""
    if not os.path.exists(LISTA_PRODUCTOS):
        print("SISTEMA: NO SE ENCONTRÓ LISTA_PRODUCTOS.TXT. CAZADOR NO HA SIDO EJECUTADO.")
        return []
    with open(LISTA_PRODUCTOS, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

async def obtener_gancho_aleatorio():
    """Extrae un hook persuasivo al azar del CSV para romper el patrón visual."""
    if not os.path.exists(CSV_GANCHOS):
        return "¡OFERTA EXCLUSIVA HOY!" # Fallback de seguridad
    with open(CSV_GANCHOS, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        ganchos = [row[0] for row in reader if row]
    return random.choice(ganchos) if ganchos else "¡COMPRA AHORA!"

async def ejecutar_subproceso(script_name, *args):
    """Ejecuta un subproceso y muestra su salida en tiempo real."""
    comando = [sys.executable, script_name] + list(args)
    print(f"\n🚀 EJECUTANDO: {' '.join(comando)}")

    proceso = await asyncio.create_subprocess_exec(
        *comando,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(proceso.communicate(), timeout=120.0)
    except asyncio.TimeoutError:
        print(f"⏱️ TIMEOUT: {script_name} excedió el tiempo límite. Abortando...")
        proceso.kill()
        await proceso.communicate()
        return False

    if stdout:
        print(stdout.decode('utf-8', errors='ignore').strip())
    if stderr:
        print(stderr.decode('utf-8', errors='ignore').strip())

    if proceso.returncode != 0:
        print(f"❌ ERROR: {script_name} terminó con código {proceso.returncode}")
        return False

    return True

async def orquestar_pipeline():
    print("=========================================")
    print("INICIANDO CEREBRO ORQUESTADOR ASÍNCRONO")
    print("=========================================")
    
    urls = await leer_urls()
    
    if not urls:
        print("SISTEMA: NO HAY PRODUCTOS PARA PROCESAR. TERMINANDO EJECUCIÓN.")
        return

    for url in urls:
        print(f"\n[+] INICIANDO CICLO DE ASALTO PARA: {url}")
        
        # 1. Llamar al Extractor de AliExpress
        exito_extraccion = await ejecutar_subproceso("extractor_aliexpress.py", url)
        
        if not exito_extraccion:
            print("[-] FALLÓ LA EXTRACCIÓN DE RED. SALTANDO AL SIGUIENTE PRODUCTO.")
            continue

        # 2. Obtener ID del producto para localizar el video exacto
        match = re.search(r'/item/(\d+)\.html', url)
        if not match:
            print("[-] NO SE PUDO EXTRAER EL ID DEL PRODUCTO DE LA URL. SALTANDO.")
            continue
        producto_id = match.group(1)
        archivo_crudo = os.path.join(VIDEOS_CRUDOS, f"{producto_id}.mp4")
        
        if not os.path.exists(archivo_crudo):
            print(f"[-] NO SE ENCONTRÓ EL VIDEO CRUDO ESPERADO: {archivo_crudo}")
            continue

        # 3. Preparar e inyectar el Gancho Visual
        gancho = await obtener_gancho_aleatorio()
        print(f"[+] INYECTANDO GANCHO VISUAL: {gancho}")
        
        ruta_salida = os.path.join(VIDEOS_PROCESADOS, f"OFUSCADO_{producto_id}.mp4")
        exito_edicion = await ejecutar_subproceso("editor_ffmpeg.py", archivo_crudo, gancho, FONT_PATH, ruta_salida)
        
        # 4. Gestión de Memoria y Limpieza
        if exito_edicion:
            print(f"[+] OFUSCACIÓN EXITOSA Y MATEMÁTICAMENTE EVASIVA. VIDEO LISTO EN: {ruta_salida}")
            os.remove(archivo_crudo)
            print("[+] ARCHIVO CRUDO DESTRUIDO PARA LIBERAR ESPACIO DE DISCO.")
        else:
            print("[-] FALLÓ EL MOTOR DE OFUSCACIÓN FFMPEG PARA ESTE VIDEO.")

    print("\n=========================================")
    print("LOTE DE PRODUCTOS PROCESADO AL 100%.")
    print("=========================================")

if __name__ == "__main__":
    # Solución de compatibilidad estricta para bucles asíncronos en Windows (NT)
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(orquestar_pipeline())