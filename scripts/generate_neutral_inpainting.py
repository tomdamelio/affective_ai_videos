"""Script para generar imágenes de control usando Flux Pro Fill (Inpainting).

Este script permite modificar regiones específicas de una imagen usando una máscara,
manteniendo el resto de la imagen intacta (pixel-perfect).

Uso:
    python scripts/generate_neutral_inpainting.py --image "img/pain.jpg" --mask "img/mask.jpg" --prompt "Neutral prompt"

Argumentos:
    --image, -i: Ruta a la imagen de entrada (Master Anchor).
    --mask, -m: Ruta a la imagen de máscara (Blanco = Inpaint, Negro = Conservar).
    --prompt, -p: Prompt para rellenar la zona enmascarada.
    --output, -o: Ruta de salida opcional.
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pain_stimuli.generator import (
    fal_client,
    download_image,
    get_account_usage,
)


def upload_file(path: Path) -> str:
    """Sube un archivo a Fal.ai y retorna la URL."""
    print(f"  Subiendo: {path.name}...")
    return fal_client.upload_file(str(path))


def main() -> None:
    """Ejecuta el inpainting usando Flux Pro Fill."""
    parser = argparse.ArgumentParser(
        description="Generar imagen de control usando Flux Pro Fill (Inpainting)."
    )
    
    parser.add_argument(
        "--image", "-i",
        type=str,
        required=True,
        help="Ruta a la imagen de entrada (Master Anchor).",
    )
    
    parser.add_argument(
        "--mask", "-m",
        type=str,
        required=True,
        help="Ruta a la máscara (Blanco=Inpaint, Negro=Keep).",
    )
    
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        required=True,
        help="Prompt para la zona enmascarada.",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Ruta de salida.",
    )

    parser.add_argument(
        "--variants", "-v",
        type=int,
        default=1,
        help="Número de variantes a generar (default: 1).",
    )
    
    args = parser.parse_args()
    
    # Verificar API key
    if not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY no configurada.")
        print("Configura tu API key:")
        print("  Windows PS:   $env:FAL_KEY='tu-key-aqui'")
        sys.exit(1)
        
    image_path = Path(args.image)
    mask_path = Path(args.mask)
    
    if not image_path.exists():
        print(f"ERROR: No se encontró la imagen: {image_path}")
        sys.exit(1)
    if not mask_path.exists():
        print(f"ERROR: No se encontró la máscara: {mask_path}")
        sys.exit(1)
        
    # Determinar ruta de salida base
    if args.output:
        base_output_path = Path(args.output)
        if base_output_path.suffix:
            base_output_path = base_output_path.with_suffix("")
    else:
        name_stem = image_path.stem
        base_output_path = image_path.parent / f"{name_stem}_inpainted"
        
    print("=" * 60)
    print("CONTROL GENERATION - FLUX PRO FILL")
    print("=" * 60)
    print(f"Imagen: {image_path}")
    print(f"Máscara: {mask_path}")
    print(f"Prompt: {args.prompt}")
    print(f"Variantes: {args.variants}")
    
    # Modelo: Flux Pro Fill v1
    # Costo aproximado: $0.05 / imagen (verificar en dashboard)
    MODEL_ID = "fal-ai/flux-pro/v1/fill"

    print(f"Modelo: {MODEL_ID}")
    
    print("\nSubiendo archivos...")
    image_url = upload_file(image_path)
    mask_url = upload_file(mask_path)
    print("✓ Archivos subidos")
    
    confirm = input("\n¿Continuar? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelado.")
        sys.exit(0)
        
    success_count = 0
    base_seed = 4000
    
    for i in range(args.variants):
        variant_num = i + 1
        current_seed = base_seed + i
        output_path = base_output_path.with_name(f"{base_output_path.name}_v{variant_num}.jpg")
        
        print(f"\n[{variant_num}/{args.variants}] Generando variante...")
        
        try:
            # Usar subscribe para Flux Pro Fill
            result = fal_client.subscribe(
                MODEL_ID,
                arguments={
                    "image_url": image_url,
                    "mask_url": mask_url,
                    "prompt": args.prompt,
                    "seed": current_seed,
                    "safety_tolerance": 6,
                    "guidance_scale": 20, # Máximo permitido
                    "steps": 50,
                },
                with_logs=True,
                on_queue_update=lambda update: print(f"  Queue status: {update}"),
            )
            
            # El resultado suele venir en 'images': [{'url': ...}]
            if 'images' in result and len(result['images']) > 0:
                result_url = result['images'][0]['url']
            elif 'image' in result:
                 result_url = result['image']['url']
            else:
                 # Fallback, print keys
                 print(f"Estructura desconocida: {result.keys()}")
                 result_url = result.get('url') # Try direct url

            if result_url:
                saved_path = download_image(result_url, output_path)
                print(f"  ✓ Guardada: {saved_path}")
                success_count += 1
            else:
                print("  ✗ No se encontró URL en la respuesta")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\n" + "=" * 60)
    print(f"Finalizado: {success_count}/{args.variants}")


if __name__ == "__main__":
    main()
