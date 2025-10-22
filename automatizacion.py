import os
import time
import cv2
from typing import Callable, Dict, List, Optional

# Default path where input videos live
DEFAULT_VIDEOS_PATH = os.path.join(os.path.dirname(__file__), "input")


def listar_videos(videos_path: Optional[str] = None) -> List[str]:
    """Lista todos los archivos de video en el directorio de entrada"""
    vp = videos_path or DEFAULT_VIDEOS_PATH
    if not os.path.isdir(vp):
        return []
    archivos_video = [f for f in os.listdir(vp) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
    return archivos_video


def configurar_lineas_para_todos(videos_path: Optional[str] = None, on_progress: Optional[Callable[[str], None]] = None) -> Dict[str, List]:
    """Configura las líneas de conteo para todos los videos (interactivo).

    on_progress: optional callable to receive status messages (string)
    """
    from analizar_video import setup_counting_lines

    vp = videos_path or DEFAULT_VIDEOS_PATH
    videos = listar_videos(vp)
    configuraciones: Dict[str, List] = {}

    if on_progress:
        on_progress(f"Se configurarán líneas para {len(videos)} video(s)")

    for i, video in enumerate(videos, 1):
        ruta_video = os.path.join(vp, video)
        vs = cv2.VideoCapture(ruta_video)

        if not vs.isOpened():
            if on_progress:
                on_progress(f"[ERROR] No se pudo abrir el video: {video}")
            continue

        ret, first_frame = vs.read()
        vs.release()

        if not ret:
            if on_progress:
                on_progress(f"[ERROR] No se pudo leer el primer frame de: {video}")
            continue

        # Interactive setup
        if on_progress:
            on_progress(f"Configurando líneas para: {video} ({i}/{len(videos)})")

        lineas = setup_counting_lines(first_frame)
        configuraciones[video] = lineas

        if on_progress:
            on_progress(f"[✓] {len(lineas)} línea(s) configurada(s) para {video}")

    return configuraciones


def run_automation(videos_path: Optional[str] = None, output_path: Optional[str] = None, on_progress: Optional[Callable[[str], None]] = None) -> Dict:
    """Run the full automation: configure lines interactively, then run analysis for each video.

    Returns a dict with per-video results.
    """
    results = {}

    # Phase 1: configure lines
    if on_progress:
        on_progress("FASE 1: CONFIGURACIÓN DE LÍNEAS DE CONTEO")

    configuraciones_lineas = configurar_lineas_para_todos(videos_path, on_progress=on_progress)

    # Phase 2: automatic analysis
    if on_progress:
        on_progress("FASE 2: ANÁLISIS AUTOMÁTICO DE VIDEOS")

    # Import here so the module is loaded only when automation runs
    from analizar_video import analizar_con_lineas_predefinidas
    import analizar_video

    # If caller provided an output path, set the module-level salida_path used by analizar_video
    if output_path:
        out = output_path
        if not out.endswith(os.sep):
            out = out + os.sep
        analizar_video.salida_path = out

    vp = videos_path or DEFAULT_VIDEOS_PATH
    videos = list(configuraciones_lineas.keys())
    t0 = time.time()

    for video in videos:
        lineas = configuraciones_lineas[video]
        ruta_video = os.path.join(vp, video)
        if on_progress:
            on_progress(f"Analizando {video} ({videos.index(video)+1}/{len(videos)})")

        try:
            # Pass output_path explicitly to the analyzer so it doesn't rely on module globals
            resultados = analizar_con_lineas_predefinidas(ruta_video, video, lineas, output_path=out if output_path else None)
            results[video] = resultados
            if on_progress:
                on_progress(f"[✓] {video}: total={resultados.get('total')}")
        except Exception as e:
            results[video] = {'error': str(e)}
            if on_progress:
                on_progress(f"[ERROR] {video}: {e}")

    t1 = time.time()
    total_minutes = (t1 - t0) / 60.0
    if on_progress:
        on_progress(f"Automatización completada en {total_minutes:.2f} minutos")

    return results


if __name__ == '__main__':
    # Preserve original script behavior when executed directly
    def _print(msg):
        print(msg)

    print("\n FASE 1: CONFIGURACIÓN DE LÍNEAS DE CONTEO")
    configuraciones_lineas = configurar_lineas_para_todos(on_progress=_print)

    print("\n FASE 2: ANÁLISIS AUTOMÁTICO DE VIDEOS")
    resultados = run_automation(on_progress=_print)

    print("\nANÁLISIS COMPLETADO")
    print(f"Videos procesados: {len(resultados)}")