"""Script de Prueba de Concepto para generación de estímulos de dolor.

Este script demuestra la generación del "Master Anchor" (t_end_P)
usando FLUX via Fal.ai con safety checker deshabilitado.

Uso:
    1. Configura tu API key: set FAL_KEY=tu-key-aqui (Windows)
    2. Ejecuta: micromamba run -n gen-ai python scripts/generate_poc.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pain_stimuli.generator import (
    GenerationConfig,
    download_image,
    generate_pain_stimulus,
    get_account_usage,
)


def main() -> None:
    """Ejecuta la prueba de concepto de generación."""
    # Verificar API key
    if not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY no configurada.")
        print("Configura tu API key:")
        print("  Windows CMD:  set FAL_KEY=tu-key-aqui")
        print("  Windows PS:   $env:FAL_KEY='tu-key-aqui'")
        print("  Linux/Mac:    export FAL_KEY='tu-key-aqui'")
        sys.exit(1)

    print("=" * 60)
    print("PRUEBA DE CONCEPTO - Generación de Estímulo de Dolor")
    print("=" * 60)

    # Configuración
    config = GenerationConfig(
        seed=1001,  # Semilla fija para reproducibilidad
        num_inference_steps=28,
        guidance_scale=3.5,
    )

    # Calcular costo estimado
    num_images = 1  # Por ahora solo 1, pero puede ser configurable
    costo_estimado = config.cost_per_image_usd * num_images

    print(f"\n{'ESTIMACIÓN DE COSTOS':^60}")
    print("=" * 60)
    print(f"Número de imágenes a generar: {num_images}")
    print(f"Costo por imagen: ${config.cost_per_image_usd:.4f} USD")
    print(f"Costo total estimado: ${costo_estimado:.4f} USD")
    print("=" * 60)

    # Solicitar confirmación
    confirmacion = input("\n¿Deseas continuar con la generación? (y/n): ").strip().lower()

    if confirmacion != "y":
        print("\nGeneración cancelada por el usuario.")
        sys.exit(0)

    # Prompt de prueba - Fase 2: Master Anchor (t_end_P)
    # Estructura: Photorealistic, [PERSPECTIVE], [SUBJECT], [DENSE DESCRIPTION]
    prompt_dolor = (
        "Photorealistic, 3rd Person perspective. "
        "A 40-year-old Male, left foot is subjected to a crushing weight as the head of a heavy "
        "claw hammer rests directly on the dorsal surface of the toes. "
        "The worn steel face of the tool compresses the skin and underlying tissue of the first "
        "and second phalanges, creating visible contact pressure and tension in the foot structure. "
        "The red fiberglass handle extends upward, emphasizing the downward force of the object. "
        "The background consists of textured beige ceramic tiles illuminated by harsh, direct flash "
        "lighting that accentuates the contrast between the metal tool and the skin. "
        "Cinematic lighting, 8k, raw style."
    )

    print(f"\n{'GENERACIÓN':^60}")
    print("=" * 60)
    print(f"Modelo: {config.model_id}")
    print(f"Seed: {config.seed}")
    print(f"Safety Checker: {'ON' if config.enable_safety_checker else 'OFF'}")
    print(f"\nPrompt:\n{prompt_dolor[:100]}...")
    print("\nGenerando imagen...")

    try:
        result = generate_pain_stimulus(prompt=prompt_dolor, config=config)

        print("\n" + "=" * 60)
        print("RESULTADO")
        print("=" * 60)
        print(f"\nImagen generada exitosamente!")
        print(f"URL: {result['image_url']}")
        print(f"\nMetadatos para reproducibilidad:")
        print(f"  - Seed: {result['seed']}")
        print(f"  - Model: {result['model_id']}")
        print(f"  - NSFW detectado: {'Sí' if result['has_nsfw_concepts'] else 'No'}")

        # Mostrar timings si están disponibles
        if result.get("timings"):
            print(f"\nTiempos de procesamiento:")
            for key, value in result["timings"].items():
                print(f"  - {key}: {value:.2f}s")

        # Descargar imagen localmente
        print("\n" + "=" * 60)
        print("DESCARGA")
        print("=" * 60)

        # Crear nombre de archivo con timestamp y seed
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pain_stimulus_seed{config.seed}_{timestamp}.jpg"
        output_dir = Path(__file__).parent.parent / "img"
        output_path = output_dir / filename

        print(f"\nDescargando imagen...")
        try:
            saved_path = download_image(result["image_url"], output_path)
            print(f"Imagen guardada en: {saved_path}")
        except Exception as error:
            print(f"Error al descargar imagen: {error}")

        print("\n" + "=" * 60)
        print("RESUMEN FINAL")
        print("=" * 60)
        print(f"Costo estimado: ${costo_estimado:.4f} USD")
        print(f"\nPara ver tu historial de uso y balance real:")
        print(f"  https://fal.ai/dashboard")

    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
