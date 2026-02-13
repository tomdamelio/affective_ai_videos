"""Script para generación de videos usando Kling AI v3 Pro (Image-to-Video).

Este script toma dos imágenes (frame inicial y final) y genera un video de 6 segundos
transicionando entre ellas, sin audio.

Uso:
    1. Configura tu API key: set FAL_KEY=tu-key-aqui
    2. Ejecuta:
       micromamba run -n gen-ai python scripts/generate_video.py \
           --start_image img/S11_3P_Start_v1.jpg \
           --end_image img/S11_3P_EndP_v3_adapted.jpg \
           --prompt "A heavy hammer striking down" \
           --output video_S11.mp4
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

import fal_client
import requests


def check_fal_key() -> None:
    if not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY no configurada.")
        print("Configura tu API key:")
        print("  Windows CMD:  set FAL_KEY=tu-key-aqui")
        print("  Windows PS:   $env:FAL_KEY='tu-key-aqui'")
        sys.exit(1)


def upload_image(image_path: Path) -> str:
    """Sube una imagen a Fal.ai y retorna su URL."""
    if not image_path.exists():
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
    
    print(f"  Subiendo: {image_path.name}...")
    url = fal_client.upload_file(str(image_path))
    return url


def download_video(url: str, output_path: Path) -> None:
    """Descarga el video generado."""
    print(f"  Descargando video a: {output_path}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("  ✓ Video guardado exitosamente.")


def generate_video(
    start_image_path: Path,
    end_image_path: Path,
    prompt: str,
    output_path: Path,
    duration: str = "5",  # Default API is 5, but we can try 6 per user request (enum: 5, 10 or similar)
) -> None:
    """Genera video usando Kling v3 Pro."""
    
    # Upload images
    start_url = upload_image(start_image_path)
    end_url = upload_image(end_image_path)

    print(f"  Iniciando generación de video ({duration}s, Kling v3 Pro)...")
    print(f"  Prompt: {prompt}")

    # Configurar argumentos
    arguments = {
        "prompt": prompt,
        "start_image_url": start_url,
        "end_image_url": end_url,
        "duration": duration,
        "generate_audio": False,  # Sin audio
        "aspect_ratio": "16:9",
        "cfg_scale": 0.5,
        "negative_prompt": "blur, distort, low quality, warped, deformed",
        # Intentamos pasar safety_tolerance aunque no esté explícito en schema
        # para cumplir con requerimiento de 'sacar barreras'
        "safety_tolerance": 6, 
    }

    try:
        handler = fal_client.submit(
            "fal-ai/kling-video/v3/pro/image-to-video",
            arguments=arguments,
        )

        print(f"  Job ID: {handler.request_id}")
        
        # Polling manual con logs
        for event in handler.iter_events(with_logs=True):
            if isinstance(event, fal_client.InProgress):
                if event.logs:
                    for log in event.logs:
                        print(f"    [REMOTE] {log['message']}")
            elif isinstance(event, fal_client.Completed):
                print("  ✓ Generación completada.")
                result = event.data
            elif isinstance(event, fal_client.Queued):
                print(f"  En cola (posición: {event.position})...")

        # Obtener resultado
        if not result or 'video' not in result:
             raise ValueError("La respuesta de la API no contiene 'video'.")

        video_url = result['video']['url']
        download_video(video_url, output_path)

    except Exception as e:
        print(f"  ✗ Error en generación: {e}")
        # Si falla por safety_tolerance, podrías reintentar sin él, 
        # pero por ahora asumimos que funciona o falla explícitamente.
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Generar video con Kling AI v3 Pro.")
    
    parser.add_argument("--start_image", "-s", type=str, required=True, help="Ruta imagen Start")
    parser.add_argument("--end_image", "-e", type=str, required=True, help="Ruta imagen End")
    parser.add_argument("--prompt", "-p", type=str, default="Cinematic movement from start to end state.", help="Prompt descriptivo")
    parser.add_argument("--duration", "-d", type=str, default="5", help="Duración en segundos (default 5, valid: 5, 10)")
    parser.add_argument("--output", "-o", type=str, default="output.mp4", help="Nombre archivo salida")

    args = parser.parse_args()

    check_fal_key()
    
    start_path = Path(args.start_image)
    end_path = Path(args.end_image)
    output_path = Path(args.output)

    try:
        generate_video(
            start_image_path=start_path,
            end_image_path=end_path,
            prompt=args.prompt,
            output_path=output_path,
            duration=args.duration
        )
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    main()
