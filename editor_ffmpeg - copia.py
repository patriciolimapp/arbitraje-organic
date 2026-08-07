import sys
import os
import ffmpeg
import random
import sys
import ffmpeg

# Forzar la consola de Windows a usar UTF-8 para evitar cuelgues con emojis
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
def ofuscar_y_quemar_texto(input_file, texto_gancho, ruta_fuente, output_file):
    """
    Ejecuta estricta evasión algorítmica:
    1. Micro-recortes de framing.
    2. Mutación de hashes (re-encode).
    3. Limpieza de metadatos (-map_metadata -1).
    4. INYECCIÓN DEL GANCHO (drawtext) en los primeros 3 segundos.
    """
    print(f"🎬 [MOTOR MULTIMEDIA] Aplicando ofuscación y gancho a: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"❌ [ERROR] No se encontró el archivo '{input_file}'.")
        sys.exit(1)

    # 1. Micro-recorte de Framing (1% al 3%) estocástico
    recorte_w = random.uniform(0.01, 0.03)
    recorte_h = random.uniform(0.01, 0.03)
    
    entrada = ffmpeg.input(input_file)
    video = entrada.video
    audio = entrada.audio

    ancho_recorte = f'in_w*(1-{recorte_w})'
    alto_recorte = f'in_h*(1-{recorte_h})'
    
    # Filtro Complejo 1: Crop
    video = ffmpeg.filter(video, 'crop', w=ancho_recorte, h=alto_recorte)
    
    # Filtro Complejo 2: Drawtext (Gancho de 3 segundos)
    # Centrado vertical (h/4) y horizontal. Tipografía dinámica.
    # NOTA: En Windows, las rutas a la fuente en FFmpeg requieren reemplazar las barras invertidas.
    fuente_ffmpeg = ruta_fuente.replace('\\', '/')
    
    video = ffmpeg.filter(
        video, 
        'drawtext', 
        text=texto_gancho, 
        fontfile=fuente_ffmpeg,
        fontsize='(h/12)',          # Tamaño responsivo a la altura del video
        fontcolor='white',
        borderw=3,                  # Borde negro para máximo contraste
        bordercolor='black',
        x='(w-text_w)/2',           # Centrado horizontal
        y='(h-text_h)/4',           # En el cuarto superior de la pantalla
        enable='between(t,0,3)'     # Desaparece exactamente al segundo 3
    )

    try:
        # Configuración de salida
        # vcodec='libx264' (Cambiable a 'h264_amf' si quieres forzar uso exclusivo de tu Radeon)
        salida = ffmpeg.output(
            video, 
            audio, 
            output_file, 
            map_metadata='-1',      # Destruye metadatos originales
            vcodec='libx264',       # Recodificación forzada = Hash Mutado
            pix_fmt='yuv420p',
            crf=23                  # Tasa de compresión visual estándar
        )
        
        # Ejecución silenciosa (quiet=True) para no saturar la terminal del Orquestador
        ffmpeg.run(salida, overwrite_output=True, quiet=True)
        print(f"✅ [ÉXITO] Video ofuscado generado: {output_file}")
        return True
    except ffmpeg.Error as e:
        # Manejo de fallos en el renderizado
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        print(f"❌ [ERROR FFMPEG] El renderizado falló: {error_msg}")
        return False

if __name__ == "__main__":
    # Recepción de parámetros desde el Orquestador
    if len(sys.argv) < 5:
        print("❌ [ERROR] Argumentos insuficientes.")
        print("Uso: python editor_ffmpeg.py <video_crudo> <texto_gancho> <ruta_fuente> <ruta_exportacion>")
        sys.exit(1)
        
    video_crudo = sys.argv[1]
    texto_gancho = sys.argv[2]
    ruta_fuente = sys.argv[3]
    ruta_exportacion = sys.argv[4]
    
    exito = ofuscar_y_quemar_texto(video_crudo, texto_gancho, ruta_fuente, ruta_exportacion)
    print(f"[+] [MOTOR MULTIMEDIA] Aplicando ofuscacion y gancho a: {input_file}")
    # Retornamos código de estado
    sys.exit(0 if exito else 1)