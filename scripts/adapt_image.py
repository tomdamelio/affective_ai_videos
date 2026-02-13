"""Script para adaptar imágenes existentes usando Flux Pro 1.1 Ultra.

Este script permite modificar una imagen existente utilizando un prompt específico
y controlando la fuerza de adherencia a la imagen original.

Uso:
    python scripts/adapt_image.py --image "img/mi_imagen.jpg" --prompt "Una versión estilo cyberpunk" --strength 0.3 --variants 3

Argumentos:
    --image, -i: Ruta a la imagen de entrada (requerido).
    --prompt, -p: Descripción del cambio deseado (requerido).
    --strength, -s: Fuerza de adherencia a la imagen original (0.0 - 1.0).
                    Valores BAJOS (0.1) = Más creatividad / Menor adherencia.
                    Valores ALTOS (0.8) = Mayor adherencia / Menor cambio.
                    Valor por defecto: 0.15
    --variants, -v: Número de variantes a generar (default: 3).
    --output, -o: Ruta de salida opcional. Si no se especifica, se genera automáticamente.
"""

import argparse
import os
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pain_stimuli.generator import (
    ImageToImageConfig,
    download_image,
    transform_image_perspective,
)


def main() -> None:
    """Ejecuta la adaptación de imagen según argumentos de CLI."""
    parser = argparse.ArgumentParser(
        description="Adaptar una imagen usando Flux Pro 1.1 Ultra."
    )
    
    parser.add_argument(
        "--image", "-i",
        type=str,
        required=True,
        help="Ruta a la imagen de entrada.",
    )
    
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        required=True,
        help="Prompt describiendo la adaptación deseada.",
    )
    
    parser.add_argument(
        "--strength", "-s",
        type=float,
        default=0.15,
        help="Fuerza de image_prompt_strength (0.0-1.0). Default: 0.15. Valores bajos = más cambio.",
    )

    parser.add_argument(
        "--variants", "-v",
        type=int,
        default=3,
        help="Número de variantes a generar (default: 3).",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Ruta de salida. Si se omite, se usa el nombre original + sufijo.",
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default="fal-ai/flux-pro/v1.1-ultra",
        help="ID del modelo de Fal.ai a usar. Default: fal-ai/flux-pro/v1.1-ultra",
    )
    
    args = parser.parse_args()
    
    # Verificar API key
    if not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY no configurada.")
        print("Configura tu API key:")
        print("  Windows PS:   $env:FAL_KEY='tu-key-aqui'")
        sys.exit(1)
        
    input_path = Path(args.image)
    if not input_path.exists():
        print(f"ERROR: No se encontró la imagen: {input_path}")
        sys.exit(1)
        
    # Determinar ruta de salida base
    if args.output:
        base_output_path = Path(args.output)
        # Si tiene extensión, se la quitamos para agregar el sufijo _vX
        if base_output_path.suffix:
            base_output_path = base_output_path.with_suffix("")
    else:
        # Generar nombre automático: imagen_adapted
        name_stem = input_path.stem
        base_output_path = input_path.parent / f"{name_stem}_adapted"
        
    print("=" * 60)
    print("ADAPTACIÓN DE IMAGEN - Flux Pro 1.1 Ultra")
    print("=" * 60)
    print(f"Imagen entrada: {input_path}")
    print(f"Prompt: {args.prompt}")
    print(f"Image Strength: {args.strength}")
    print(f"Variantes: {args.variants}")
    print(f"Salida base: {base_output_path}_vX.jpg")
    
    # Estimar costo
    cost_per_image = 0.06  # Flux Pro 1.1 Ultra
    total_cost = cost_per_image * args.variants
    print(f"\nCosto estimado total: ${total_cost:.4f} USD (${cost_per_image}/img)")
    
    confirm = input("\n¿Continuar? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelado.")
        sys.exit(0)
        
    print(f"\nGenerando {args.variants} variantes...")
    
    # Upload image once if possible, but existing functions handle upload internally per call.
    # To optimize, we could refactor generator.py to accept URL, but for now we loop.
    
    success_count = 0
    base_seed = 3000

    for i in range(args.variants):
        variant_num = i + 1
        current_seed = base_seed + i
        output_path = base_output_path.with_name(f"{base_output_path.name}_v{variant_num}.jpg")
        
        print(f"\n[{variant_num}/{args.variants}] Generando variante...")
    
        # Configuración por variante
        config = ImageToImageConfig(
            model_id=args.model,
            image_prompt_strength=args.strength,
            safety_tolerance=6,
            seed=current_seed,
        )
    
        try:
            result = transform_image_perspective(
                image_path=input_path,
                prompt=args.prompt,
                config=config,
            )
            
            # Descargar
            saved_path = download_image(result["image_url"], output_path)
            
            print(f"  ✓ Guardada: {saved_path}")
            # print(f"    URL: {result['image_url']}")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error en variante {variant_num}: {e}")

    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"Exitosos: {success_count}/{args.variants}")


if __name__ == "__main__":
    main()
