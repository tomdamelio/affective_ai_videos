"""Script para generación batch de imágenes de inicio (Start - Condition Neutral - 3rd Person).

Este script lee los prompts desde el archivo Excel ai_prompts.xlsx,
filtra por condición 'Neutral' y perspectiva '3rd Person', y genera todas las imágenes
usando FLUX via Fal.ai.

Uso:
    1. Configura tu API key: set FAL_KEY=tu-key-aqui (Windows)
    2. Ejecuta: micromamba run -n gen-ai python scripts/generate_start_img.py
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
CONDITION_FILTER = "Neutral"  # Filtrar por condición Neutral (t_start)
PERSPECTIVE_FILTER = "3rd Person"  # Filtrar por perspectiva 3rd Person
EXPECTED_NUM_PROMPTS = 5  # Esperamos 5 prompts (S01, S11, S13, S17, S32)
VARIANTS_PER_PROMPT = 3  # 3 variantes por prompt


def load_start_prompts(excel_path: Path) -> pd.DataFrame:
    """Carga los prompts de condición Neutral y perspectiva 3rd Person desde el archivo Excel.

    Args:
        excel_path: Ruta al archivo Excel con los prompts.

    Returns:
        DataFrame con columnas Unique_Img_ID y AUTO_PROMPT filtrado.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Archivo Excel no encontrado: {excel_path}")

    # Use openpyxl engine explicitly if needed
    dataframe = pd.read_excel(excel_path, sheet_name=SHEET_NAME)

    required_columns = ["Condition", "Perspective", "AUTO_PROMPT", "Unique_Img_ID", "Seed"]
    missing_columns = [col for col in required_columns if col not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"Columnas faltantes en Excel: {missing_columns}")

    # Filtrar por Condition=Neutral AND Perspective=3rd Person
    # Nota: Usamos str.contains para Condition por si hay espacios o variantes como 'Neutral '
    start_prompts = dataframe[
        (dataframe["Condition"].str.strip() == CONDITION_FILTER) &
        (dataframe["Perspective"] == PERSPECTIVE_FILTER)
    ][["Unique_Img_ID", "AUTO_PROMPT", "Seed"]].copy()

    return start_prompts


def main() -> None:
    """Ejecuta la generación batch de imágenes de inicio (Start)."""
    # Verificar API key
    if not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY no configurada.")
        print("Configura tu API key:")
        print("  Windows CMD:  set FAL_KEY=tu-key-aqui")
        print("  Windows PS:   $env:FAL_KEY='tu-key-aqui'")
        sys.exit(1)

    print("=" * 60)
    print("GENERACIÓN BATCH - Imágenes de Inicio (Start/Neutral)")
    print("=" * 60)

    # Cargar prompts desde Excel
    print(f"\nCargando prompts desde: {EXCEL_PATH}")
    try:
        start_prompts = load_start_prompts(EXCEL_PATH)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    num_prompts = len(start_prompts)
    print(f"Prompts encontrados (Condition={CONDITION_FILTER}, Perspective={PERSPECTIVE_FILTER}): {num_prompts}")

    # Validar número esperado de prompts (warning en lugar de assert estricto por si acaso)
    if num_prompts != EXPECTED_NUM_PROMPTS:
        print(f"WARNING: Se esperaban {EXPECTED_NUM_PROMPTS} prompts, pero se encontraron {num_prompts}.")

    if num_prompts == 0:
        print("No hay prompts para procesar via este filtro. Revisar Excel.")
        sys.exit(0)

    # Calcular total de imágenes
    num_images = num_prompts * VARIANTS_PER_PROMPT

    # Configuración base (la seed se modifica por variante)
    # Usamos flux-pro/v1.1-ultra por defecto
    base_config = GenerationConfig(
        seed=1001,
        num_inference_steps=28,
        guidance_scale=3.5,
        safety_tolerance=6, # Permitir contenido sensible si fuera necesario, aunque es Neutral
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
    for idx, row in start_prompts.iterrows():
        img_id = row["Unique_Img_ID"]
        # Handle NaN seed if present, default to 1000
        try:
            base_seed = int(row["Seed"])
        except (ValueError, TypeError):
            base_seed = 1000
            
        prompt_preview = str(row["AUTO_PROMPT"])[:40] + "..."
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

    for idx, row in start_prompts.iterrows():
        img_id = row["Unique_Img_ID"]
        prompt = str(row["AUTO_PROMPT"])
        
        try:
            base_seed = int(row["Seed"])
        except (ValueError, TypeError):
            base_seed = 1000

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
                safety_tolerance=6,
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
