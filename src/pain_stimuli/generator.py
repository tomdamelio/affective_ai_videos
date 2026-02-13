"""Generador de estímulos de dolor usando Fal.ai FLUX.

Este módulo implementa la Fase 2 del protocolo: Síntesis de Activos Visuales.
Genera el "Master Anchor" (t_end_P) con safety checker deshabilitado.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fal_client
import requests


@dataclass(frozen=True)
class GenerationConfig:
    """Configuración para generación de imágenes.

    Attributes:
        model_id: Identificador del modelo en Fal.ai.
        image_size: Tamaño/aspect ratio de la imagen.
        num_inference_steps: Pasos de inferencia del modelo.
        guidance_scale: Escala de guía para adherencia al prompt.
        seed: Semilla para reproducibilidad.
        safety_tolerance: Nivel de tolerancia del filtro de seguridad (1-6, 6=más permisivo).
        cost_per_image_usd: Costo estimado por imagen en USD.
    """

    model_id: str = "fal-ai/flux-pro/v1.1-ultra"
    image_size: str = "landscape_16_9"
    num_inference_steps: int = 28
    guidance_scale: float = 3.5
    seed: int = 1001
    safety_tolerance: int = 6
    cost_per_image_usd: float = 0.06


@dataclass(frozen=True)
class ImageToImageConfig:
    """Configuración para transformación image-to-image.

    Attributes:
        model_id: Identificador del modelo en Fal.ai.
        num_inference_steps: Pasos de inferencia del modelo.
        guidance_scale: Escala de guía para adherencia al prompt.
        image_prompt_strength: Fuerza de adherencia a la imagen de referencia (0.0-1.0).
                               Valores bajos (0.1) = más libertad creativa.
                               Valores altos (0.5+) = más fidelidad a la imagen original.
        seed: Semilla para reproducibilidad.
        safety_tolerance: Nivel de tolerancia del filtro de seguridad (1-6, 6=más permisivo).
        cost_per_image_usd: Costo estimado por imagen en USD.
    """

    model_id: str = "fal-ai/flux-pro/v1.1-ultra"
    num_inference_steps: int = 40
    guidance_scale: float = 3.5
    image_prompt_strength: float = 0.1
    seed: int = 1001
    safety_tolerance: int = 6
    cost_per_image_usd: float = 0.06


def get_account_usage(limit: int = 10) -> dict:
    """Obtiene el historial de uso reciente de la cuenta de Fal.ai.

    Args:
        limit: Número de registros de uso a obtener.

    Returns:
        Diccionario con el historial de uso y costo total reciente.

    Raises:
        ValueError: Si FAL_KEY no está configurada.
        requests.HTTPError: Si hay error en la API.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError(
            "FAL_KEY no configurada. "
            "Exporta tu API key: export FAL_KEY='tu-key-aqui'"
        )

    headers = {"Authorization": f"Key {fal_key}"}
    response = requests.get(
        f"https://api.fal.ai/v1/models/usage?limit={limit}",
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()

    # Calcular costo total del historial reciente
    total_cost = 0.0
    for bucket in data.get("time_series", []):
        for result in bucket.get("results", []):
            total_cost += result.get("cost", 0.0)

    return {
        "time_series": data.get("time_series", []),
        "total_recent_cost_usd": total_cost,
        "raw_response": data,
    }


def download_image(url: str, output_path: Path) -> Path:
    """Descarga una imagen desde una URL y la guarda localmente.

    Args:
        url: URL de la imagen a descargar.
        output_path: Ruta donde guardar la imagen.

    Returns:
        Path del archivo guardado.

    Raises:
        requests.HTTPError: Si hay error al descargar.
        IOError: Si hay error al guardar el archivo.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    with open(output_path, "wb") as file:
        file.write(response.content)

    return output_path


def generate_pain_stimulus(
    prompt: str,
    config: Optional[GenerationConfig] = None,
) -> dict:
    """Genera una imagen de estímulo de dolor usando FLUX.

    Implementa la generación del "Master Anchor" (t_end_P) del protocolo.
    El safety checker está deshabilitado para permitir contenido de
    investigación científica sobre dolor.

    Args:
        prompt: Descripción densa del estímulo de dolor derivada de Fase 1.
        config: Configuración de generación. Si es None, usa valores por defecto.

    Returns:
        Diccionario con la URL de la imagen generada y metadatos:
            - image_url: URL de la imagen generada
            - seed: Semilla usada (para reproducibilidad)
            - model_id: Identificador del modelo
            - prompt: Prompt usado
            - has_nsfw_concepts: Si el modelo detectó contenido NSFW
            - timings: Tiempos de procesamiento
            - raw_response: Respuesta completa de la API

    Raises:
        ValueError: Si FAL_KEY no está configurada.
        Exception: Si hay error en la API de Fal.ai.

    Example:
        >>> config = GenerationConfig(seed=42)
        >>> result = generate_pain_stimulus(
        ...     prompt="Photorealistic, close-up of hand...",
        ...     config=config
        ... )
        >>> print(result["image_url"])
    """
    if not os.environ.get("FAL_KEY"):
        raise ValueError(
            "FAL_KEY no configurada. "
            "Exporta tu API key: export FAL_KEY='tu-key-aqui'"
        )

    if config is None:
        config = GenerationConfig()

    # Usar subscribe() en lugar de submit() para mejor manejo de logs
    result = fal_client.subscribe(
        config.model_id,
        arguments={
            "prompt": prompt,
            "image_size": config.image_size,
            "num_inference_steps": config.num_inference_steps,
            "guidance_scale": config.guidance_scale,
            "seed": config.seed,
            "safety_tolerance": config.safety_tolerance,
            "num_images": 1,
            "output_format": "jpeg",
        },
        with_logs=True,
        on_queue_update=lambda update: print(f"  Queue status: {update}"),
    )

    return {
        "image_url": result["images"][0]["url"],
        "seed": result.get("seed", config.seed),
        "model_id": config.model_id,
        "prompt": result.get("prompt", prompt),
        "has_nsfw_concepts": result.get("has_nsfw_concepts", [False])[0],
        "timings": result.get("timings", {}),
        "raw_response": result,
    }


def transform_image_perspective(
    image_path: Path,
    prompt: str,
    config: Optional[ImageToImageConfig] = None,
) -> dict:
    """Transforma una imagen existente usando FLUX image-to-image.

    Útil para cambiar la perspectiva de una imagen (ej: 3rd person a 1st person POV).

    Args:
        image_path: Ruta local de la imagen de entrada.
        prompt: Descripción de la transformación deseada.
        config: Configuración de transformación. Si es None, usa valores por defecto.

    Returns:
        Diccionario con la URL de la imagen generada y metadatos:
            - image_url: URL de la imagen generada
            - seed: Semilla usada (para reproducibilidad)
            - model_id: Identificador del modelo
            - prompt: Prompt usado
            - has_nsfw_concepts: Si el modelo detectó contenido NSFW
            - timings: Tiempos de procesamiento
            - raw_response: Respuesta completa de la API

    Raises:
        ValueError: Si FAL_KEY no está configurada.
        FileNotFoundError: Si la imagen de entrada no existe.
        Exception: Si hay error en la API de Fal.ai.
    """
    if not os.environ.get("FAL_KEY"):
        raise ValueError(
            "FAL_KEY no configurada. "
            "Exporta tu API key: export FAL_KEY='tu-key-aqui'"
        )

    if not image_path.exists():
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

    if config is None:
        config = ImageToImageConfig()

    # Subir imagen a Fal.ai storage
    print(f"  Subiendo imagen: {image_path.name}...")
    image_url = fal_client.upload_file(str(image_path))

    # Usar subscribe() para image-to-image
    result = fal_client.subscribe(
        config.model_id,
        arguments={
            "image_url": image_url,
            "prompt": prompt,
            "image_prompt_strength": config.image_prompt_strength,
            "num_inference_steps": config.num_inference_steps,
            "guidance_scale": config.guidance_scale,
            "seed": config.seed,
            "safety_tolerance": config.safety_tolerance,
            "num_images": 1,
            "output_format": "jpeg",
        },
        with_logs=True,
        on_queue_update=lambda update: print(f"  Queue status: {update}"),
    )

    return {
        "image_url": result["images"][0]["url"],
        "seed": result.get("seed", config.seed),
        "model_id": config.model_id,
        "prompt": result.get("prompt", prompt),
        "has_nsfw_concepts": result.get("has_nsfw_concepts", [False])[0],
        "timings": result.get("timings", {}),
        "raw_response": result,
    }
