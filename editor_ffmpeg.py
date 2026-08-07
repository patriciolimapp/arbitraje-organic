import sys
import os
import random
import ffmpeg

ffmpeg._run.DEFAULT_FFMPEG_PATH = r'C:\ffmpeg-9.0-essentials_build\ffmpeg-9.0-essentials_build\bin\ffmpeg.exe'

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def ofuscar_y_quemar_texto(input_file, texto_gancho, ruta_fuente, output_file):
    print(f"🎬 [MOTOR MULTIMEDIA] Aplicando ofuscación cuántica y gancho a: {input_file}")

    if not os.path.exists(input_file):
        print(f"❌ [ERROR] No se encontró el archivo '{input_file}'.")
        return False

    # Gestión de fuente
    if not os.path.isfile(ruta_fuente):
        print(f"⚠️ [ADVERTENCIA] Fuente '{ruta_fuente}' no encontrada. Usando Arial como respaldo.")
        ruta_fuente = "C:/Windows/Fonts/arial.ttf"
        if not os.path.isfile(ruta_fuente):
            print("❌ [ERROR] No se encontró ninguna fuente válida. Abortando.")
            return False

    fuente_ffmpeg = ruta_fuente.replace('\\', '/')

    # Factores estocásticos de evasión
    aplicar_hflip = random.choice([True, False])
    crop_left = random.uniform(0.02, 0.06)
    crop_right = random.uniform(0.02, 0.06)
    crop_top = random.uniform(0.02, 0.06)
    crop_bottom = random.uniform(0.02, 0.06)
    speed_factor = random.uniform(0.97, 1.05)
    decimate_cycle = random.randint(20, 40)
    contrast = random.uniform(0.96, 1.08)
    brightness = random.uniform(-0.04, 0.06)
    saturation = random.uniform(0.98, 1.10)
    noise_strength = random.randint(1, 3)

    try:
        entrada = ffmpeg.input(input_file)
        video = entrada.video
        audio = entrada.audio

        # Cadena de ofuscación espacial y temporal
        w_expr = f'iw*(1-{crop_left}-{crop_right})'
        h_expr = f'ih*(1-{crop_top}-{crop_bottom})'
        x_expr = f'iw*{crop_left}'
        y_expr = f'ih*{crop_top}'
        video = ffmpeg.filter(video, 'crop', w=w_expr, h=h_expr, x=x_expr, y=y_expr)
        video = ffmpeg.filter(video, 'scale', 1080, 1920)

        if aplicar_hflip:
            video = ffmpeg.filter(video, 'hflip')
            print("[+] Aplicando inversión horizontal (hflip) – rotura masiva del hash PDQ.")

        video = ffmpeg.filter(video, 'eq', contrast=contrast, brightness=brightness, saturation=saturation)
        video = ffmpeg.filter(video, 'noise', alls=noise_strength, allf='t+u')
        video = ffmpeg.filter(video, 'setpts', f'{1/speed_factor:.4f}*PTS')
        video = ffmpeg.filter(video, 'mpdecimate', hi=f'{decimate_cycle}*12', lo='1', frac='0.33')

        # ================================================================
        # NUEVO GANCHO VISUAL DINÁMICO
        # ================================================================
        # Separar palabra de impacto (hasta 6 caracteres)
        palabras = texto_gancho.split()
        if len(palabras) > 1 and len(palabras[0]) <= 6:
            palabra_impacto = palabras[0]
            resto = " ".join(palabras[1:])
        else:
            palabra_impacto = ""
            resto = texto_gancho

        # Dividir el resto en líneas de ~40 caracteres
        max_chars = 40
        lineas = []
        linea_actual = ""
        for palabra in resto.split():
            if len(linea_actual) + len(palabra) + 1 <= max_chars:
                linea_actual = (linea_actual + " " + palabra).strip()
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)
        texto_resto = "\\n".join(lineas) if lineas else ""

        # Animación de opacidad y movimiento vertical suave
        anim_opacity = "if(lt(t,0.5), t/0.5, if(gt(t,2.5), (3-t)/0.5, 1))"
        anim_y_offset = "if(lt(t,0.5), 15*(1-t/0.5), if(gt(t,2.5), 15*(t-2.5)/0.5, 0))"

        # Fondo oscuro en el 15% inferior (efecto "lower third")
        video = ffmpeg.filter(
            video, 'drawbox',
            x='0', y='h-h*0.18',
            width='iw', height='h*0.18',
            color='black@0.7',
            thickness='fill',
            enable='between(t,0,3)'
        )
        # Línea decorativa superior del fondo
        video = ffmpeg.filter(
            video, 'drawbox',
            x='0', y='h-h*0.18-2',
            width='iw', height='2',
            color='white@0.3',
            thickness='fill',
            enable='between(t,0,3)'
        )

        # Palabra de impacto (grande, amarillo vibrante)
        if palabra_impacto:
            video = ffmpeg.filter(
                video, 'drawtext',
                text=palabra_impacto.upper(),
                fontfile=fuente_ffmpeg,
                fontsize='(h/18)',
                fontcolor='yellow',
                shadowcolor='black@0.8',
                shadowx=3, shadowy=3,
                borderw=0,
                alpha=anim_opacity,
                x='(w-text_w)/2',
                y=f'(h-text_h)/1.2 + {anim_y_offset}',
                enable='between(t,0,3)'
            )

        # Texto secundario (blanco, más pequeño)
        if texto_resto:
            video = ffmpeg.filter(
                video, 'drawtext',
                text=texto_resto,
                fontfile=fuente_ffmpeg,
                fontsize='(h/26)',
                fontcolor='white',
                shadowcolor='black@0.7',
                shadowx=2, shadowy=2,
                borderw=0,
                alpha=anim_opacity,
                x='(w-text_w)/2',
                y=f'(h-text_h)/1.1 + {anim_y_offset}',
                enable='between(t,0,3)'
            )
        # ================================================================

        # Cadena de audio
        audio = ffmpeg.filter(audio, 'atempo', speed_factor)
        audio = ffmpeg.filter(audio, 'asetrate', '44100')

        salida = ffmpeg.output(video, audio, output_file,
                               map_metadata='-1',
                               vcodec='libx264',
                               acodec='aac',
                               pix_fmt='yuv420p',
                               crf=23,
                               preset='medium')
        ffmpeg.run(salida, overwrite_output=True, quiet=True)
        print(f"✅ [ÉXITO] Video ofuscado generado: {output_file}")
        return True

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        print(f"❌ [ERROR FFMPEG] Falló la cadena de ofuscación: {error_msg}")
        print("[!] Intentando ofuscación de emergencia...")
        try:
            entrada = ffmpeg.input(input_file)
            video = entrada.video
            audio = entrada.audio
            video = ffmpeg.filter(video, 'crop', w='iw*0.96', h='ih*0.96')
            # Texto de emergencia simplificado
            video = ffmpeg.filter(video, 'drawtext',
                                  text=texto_gancho,
                                  fontfile=fuente_ffmpeg,
                                  fontsize='(h/22)',
                                  fontcolor='white',
                                  box=1, boxcolor='black@0.5', boxborderw=10,
                                  x='(w-text_w)/2', y='(h-text_h)/1.5',
                                  enable='between(t,0,3)')
            salida = ffmpeg.output(video, audio, output_file,
                                   map_metadata='-1',
                                   vcodec='libx264', acodec='aac',
                                   pix_fmt='yuv420p', crf=23)
            ffmpeg.run(salida, overwrite_output=True, quiet=True)
            print(f"✅ [FALLBACK] Video generado con éxito reducido: {output_file}")
            return True
        except Exception as fallback_e:
            print(f"❌ [FATAL] Falló incluso la ofuscación de emergencia: {fallback_e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("❌ [ERROR] Argumentos insuficientes.")
        print("Uso: python editor_ffmpeg.py <video_crudo> <texto_gancho> <ruta_fuente> <ruta_exportacion>")
        sys.exit(1)

    exito = ofuscar_y_quemar_texto(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    sys.exit(0 if exito else 1)