"""Script para generación de imágenes POV (1st Person) desde imágenes 3rd Person.

Este script toma las imágenes de referencia en 3rd Person y las transforma
a perspectiva POV (1st Person) usando FLUX image-to-image.

Uso:
    1. Configura tu API key: set FAL_KEY=tu-key-aqui (Windows)
    2. Ejecuta: micromamba run -n gen-ai python scripts/generate_pov_img.py
"""

import os
import re
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pain_stimuli.generator import (
    ImageToImageConfig,
    download_image,
    transform_image_perspective,
)

# Constantes
IMG_DIR = Path(__file__).parent.parent / "img"
INPUT_PATTERN = r"^S\d{2}_3P_EndP_v\d+\.jpg$"  # e.g., S01_3P_EndP_v1.jpg
EXPECTED_NUM_IMAGES = 5

# Prompt para transformar a POV (1st Person)
POV_TRANSFORMATION_PROMPT = (
    "First person POV perspective, looking down at own body. "
    "The viewer is the person experiencing the pain. "
    "Same scene, same objects, same lighting, but from the victim's point of view. "
    "The limb belongs to the viewer. "
    "Photorealistic, 8k, raw style, cinematic lighting."
)


def find_3p_images(img_dir: Path) -> list[Path]:
    """Encuentra las imágenes 3rd Person en el directorio.

    Args:
        img_dir: Directorio donde buscar las imágenes.

    Returns:
        Lista de paths a las imágenes 3P encontradas.

    Raises:
        FileNotFoundError: Si el directorio no existe.
    """
    if not img_dir.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {img_dir}")

    pattern = re.compile(INPUT_PATTERN)
    images = [
        img_path
        for img_path in img_dir.glob("*.jpg")
        if pattern.match(img_path.name)
    ]

    return sorted(images)


def generate_1p_filename(original_filename: str) -> str:
    """Genera el nombre de archivo para la versión 1P.

    Args:
        original_filename: Nombre original (e.g., S01_3P_EndP_v1.jpg)

    Returns:
        Nombre para versión 1P (e.g., S01_1P_EndP_v1.jpg)
    """
    return original_filename.replace("_3P_", "_1P_")


def main() -> None:
    """Ejecuta la transformación de imágenes 3P a POV (1P)."""
    # Verificar API key
    if not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY no configurada.")
        print("Configura tu API key:")
        print("  Windows CMD:  set FAL_KEY=tu-key-aqui")
        print("  Windows PS:   $env:FAL_KEY='tu-key-aqui'")
        sys.exit(1)

    print("=" * 60)
    print("TRANSFORMACIÓN - 3rd Person a POV (1st Person)")
    print("=" * 60)

    # Buscar imágenes 3P
    print(f"\nBuscando imágenes 3P en: {IMG_DIR}")
    try:
        images_3p = find_3p_images(IMG_DIR)
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    num_images = len(images_3p)
    print(f"Imágenes 3P encontradas: {num_images}")

    # Validar número esperado
    assert num_images == EXPECTED_NUM_IMAGES, (
        f"Se esperaban {EXPECTED_NUM_IMAGES} imágenes, "
        f"pero se encontraron {num_images}"
    )

    # Configuración
    config = ImageToImageConfig(
        seed=2001,  # Seed diferente para variación
        num_inference_steps=40,
        guidance_scale=3.5,
        strength=0.85,  # Mantener algo de la imagen original
    )

    # Calcular costo estimado
    costo_estimado = config.cost_per_image_usd * num_images

    print(f"\n{'ESTIMACIÓN DE COSTOS':^60}")
    print("=" * 60)
    print(f"Número de imágenes a transformar: {num_images}")
    print(f"Costo por imagen: ${config.cost_per_image_usd:.4f} USD")
    print(f"Costo total estimado: ${costo_estimado:.4f} USD")
    print("=" * 60)

    # Mostrar lista de transformaciones
    print(f"\n{'TRANSFORMACIONES A REALIZAR':^60}")
    print("-" * 60)
    for img_path in images_3p:
        output_name = generate_1p_filename(img_path.name)
        print(f"  {img_path.name} -> {output_name}")
    print("-" * 60)

    print(f"\nPrompt de transformación:")
    print(f"  {POV_TRANSFORMATION_PROMPT[:80]}...")

    # Solicitar confirmación
    confirmacion = input("\n¿Deseas continuar con la transformación? (y/n): ").strip().lower()

    if confirmacion != "y":
        print("\nTransformación cancelada por el usuario.")
        sys.exit(0)

    # Transformar imágenes
    print(f"\n{'TRANSFORMACIÓN':^60}")
    print("=" * 60)

    resultados = []
    errores = []

    for idx, img_path in enumerate(images_3p, 1):
        output_name = generate_1p_filename(img_path.name)
        output_path = IMG_DIR / output_name

        print(f"\n[{idx}/{num_images}] Transformando: {img_path.name}")
        print(f"  Output: {output_name}")

        try:
            result = transform_image_perspective(
                image_path=img_path,
                prompt=POV_TRANSFORMATION_PROMPT,
                config=config,
            )

            # Descargar imagen transformada
            saved_path = download_image(result["image_url"], output_path)

            resultados.append({
                "input": img_path.name,
                "output": output_name,
                "url": result["image_url"],
                "local_path": str(saved_path),
                "seed": result["seed"],
            })

            print(f"  ✓ Guardada: {saved_path}")

        except Exception as error:
            errores.append({"input": img_path.name, "error": str(error)})
            print(f"  ✗ Error: {error}")

    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"\nImágenes transformadas exitosamente: {len(resultados)}/{num_images}")
    print(f"Errores: {len(errores)}")
    print(f"Costo estimado total: ${costo_estimado:.4f} USD")
    print(f"\nImágenes guardadas en: {IMG_DIR}")

    if errores:
        print(f"\n{'ERRORES':^60}")
        print("-" * 60)
        for error in errores:
            print(f"  {error['input']}: {error['error']}")

    print(f"\nPara ver tu historial de uso real:")
    print(f"  https://fal.ai/dashboard")


if __name__ == "__main__":
    main()
