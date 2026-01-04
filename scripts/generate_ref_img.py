"""Script para generación batch de imágenes de referencia (Pain condition).

Este script lee los prompts desde el archivo Excel ai_prompts.xlsx,
filtra por condición Pain, y genera todas las imágenes de referencia
usando FLUX via Fal.ai.

Uso:
    1. Configura tu API key: set FAL_KEY=tu-key-aqui (Windows)
    2. Ejecuta: micromamba run -n gen-ai python scripts/generate_ref_img.py
"""

import os
import sys
from pathlib import Path

import pandas as pd

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pain_stimuli.generator import (
    GenerationConfig,
    download_image,
    generate_pain_stimulus,
)

# Constantes
EXCEL_PATH = Path(__file__).parent.parent / "ai_prompts.xlsx"
SHEET_NAME = "text-to-image"
CONDITION_FILTER = "Pain"
PERSPECTIVE_FILTER = "POV"  # Cambiado de "3rd Person" a "POV"
EXPECTED_NUM_PROMPTS = 5
VARIANTS_PER_PROMPT = 1  # Solo 1 variante para POV


def load_pain_prompts(excel_path: Path) -> pd.DataFrame:
    """Carga los prompts de condición Pain y perspectiva 3rd Person desde el archivo Excel.

    Args:
        excel_path: Ruta al archivo Excel con los prompts.

    Returns:
        DataFrame con columnas Unique_Img_ID y AUTO_PROMPT filtrado por Pain y 3rd Person.

    Raises:
        FileNotFoundError: Si el archivo Excel no existe.
        ValueError: Si las columnas requeridas no existen.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Archivo Excel no encontrado: {excel_path}")

    dataframe = pd.read_excel(excel_path, sheet_name=SHEET_NAME)

    required_columns = ["Condition", "Perspective", "AUTO_PROMPT", "Unique_Img_ID", "Seed"]
    missing_columns = [col for col in required_columns if col not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"Columnas faltantes en Excel: {missing_columns}")

    # Filtrar por Condition=Pain AND Perspective=3rd Person
    pain_prompts = dataframe[
        (dataframe["Condition"] == CONDITION_FILTER) &
        (dataframe["Perspective"] == PERSPECTIVE_FILTER)
    ][["Unique_Img_ID", "AUTO_PROMPT", "Seed"]].copy()

    return pain_prompts


def main() -> None:
    """Ejecuta la generación batch de imágenes de dolor."""
    # Verificar API key
    if not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY no configurada.")
        print("Configura tu API key:")
        print("  Windows CMD:  set FAL_KEY=tu-key-aqui")
        print("  Windows PS:   $env:FAL_KEY='tu-key-aqui'")
        sys.exit(1)

    print("=" * 60)
    print("GENERACIÓN BATCH - Imágenes de Referencia (Pain)")
    print("=" * 60)

    # Cargar prompts desde Excel
    print(f"\nCargando prompts desde: {EXCEL_PATH}")
    try:
        pain_prompts = load_pain_prompts(EXCEL_PATH)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    num_prompts = len(pain_prompts)
    print(f"Prompts encontrados (Condition=Pain, Perspective=3rd Person): {num_prompts}")

    # Validar número esperado de prompts
    assert num_prompts == EXPECTED_NUM_PROMPTS, (
        f"Se esperaban {EXPECTED_NUM_PROMPTS} prompts, "
        f"pero se encontraron {num_prompts}"
    )

    # Calcular total de imágenes
    num_images = num_prompts * VARIANTS_PER_PROMPT

    # Configuración base (la seed se modifica por variante)
    base_config = GenerationConfig(
        seed=1001,
        num_inference_steps=28,
        guidance_scale=3.5,
    )

    # Calcular costo estimado
    costo_estimado = base_config.cost_per_image_usd * num_images

    print(f"\n{'ESTIMACIÓN DE COSTOS':^60}")
    print("=" * 60)
    print(f"Número de prompts: {num_prompts}")
    print(f"Variantes por prompt: {VARIANTS_PER_PROMPT}")
    print(f"Total de imágenes a generar: {num_images}")
    print(f"Costo por imagen: ${base_config.cost_per_image_usd:.4f} USD")
    print(f"Costo total estimado: ${costo_estimado:.4f} USD")
    print("=" * 60)

    # Mostrar lista de imágenes a generar
    print(f"\n{'IMÁGENES A GENERAR':^60}")
    print("-" * 60)
    for idx, row in pain_prompts.iterrows():
        img_id = row["Unique_Img_ID"]
        base_seed = int(row["Seed"])
        prompt_preview = row["AUTO_PROMPT"][:40] + "..."
        print(f"  {img_id} (base_seed={base_seed}, {VARIANTS_PER_PROMPT} variantes):")
        print(f"    {prompt_preview}")
    print("-" * 60)

    # Solicitar confirmación
    confirmacion = input("\n¿Deseas continuar con la generación? (y/n): ").strip().lower()

    if confirmacion != "y":
        print("\nGeneración cancelada por el usuario.")
        sys.exit(0)

    # Directorio de salida
    output_dir = Path(__file__).parent.parent / "img"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generar imágenes
    print(f"\n{'GENERACIÓN':^60}")
    print("=" * 60)

    resultados = []
    errores = []
    imagen_actual = 0

    for idx, row in pain_prompts.iterrows():
        img_id = row["Unique_Img_ID"]
        prompt = row["AUTO_PROMPT"]
        base_seed = int(row["Seed"])

        # Generar variantes con seeds incrementales
        for variant in range(VARIANTS_PER_PROMPT):
            imagen_actual += 1
            variant_seed = base_seed + variant
            variant_id = f"{img_id}_v{variant + 1}"

            # Crear config con la seed específica de esta variante
            img_config = GenerationConfig(
                seed=variant_seed,
                num_inference_steps=28,
                guidance_scale=3.5,
            )

            print(f"\n[{imagen_actual}/{num_images}] Generando: {variant_id}")
            print(f"  Seed: {variant_seed}")
            print(f"  Prompt: {prompt[:60]}...")

            try:
                result = generate_pain_stimulus(prompt=prompt, config=img_config)

                # Descargar imagen con el Unique_Img_ID + variante como nombre
                filename = f"{variant_id}.jpg"
                output_path = output_dir / filename

                saved_path = download_image(result["image_url"], output_path)

                resultados.append({
                    "img_id": variant_id,
                    "base_img_id": img_id,
                    "variant": variant + 1,
                    "url": result["image_url"],
                    "local_path": str(saved_path),
                    "seed": result["seed"],
                })

                print(f"  ✓ Guardada: {saved_path}")

            except Exception as error:
                errores.append({"img_id": variant_id, "error": str(error)})
                print(f"  ✗ Error: {error}")

    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"\nImágenes generadas exitosamente: {len(resultados)}/{num_images}")
    print(f"Errores: {len(errores)}")
    print(f"Costo estimado total: ${costo_estimado:.4f} USD")
    print(f"\nImágenes guardadas en: {output_dir}")

    if errores:
        print(f"\n{'ERRORES':^60}")
        print("-" * 60)
        for error in errores:
            print(f"  {error['img_id']}: {error['error']}")

    print(f"\nPara ver tu historial de uso real:")
    print(f"  https://fal.ai/dashboard")


if __name__ == "__main__":
    main()
