"""Prueba Camino B: modelo open-weights fal-ai/flux/dev, safety checker OFF.

Es el modelo ORIGINAL del repo (GenerationConfig pre-migracion). A diferencia
de flux-2-pro, en el endpoint open `enable_safety_checker:False` apaga el filtro
y no hay moderacion de entrada del mismo tipo. Confirma si acepta el contenido
de dolor clinico (equivalente a lo que muestra la propia base EPSS) y con que
calidad. 1 imagen (~$0.025). Salida: img/pilot_epss/.
"""
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "img" / "pilot_epss"

# Redaccion clinica estilo enero (la misma que flux-2-pro ahora rechaza).
PROMPT = (
    "Photorealistic, 3rd Person perspective, close-up focus on the contact point. "
    "A hand is slicing a cucumber on a wooden cutting board in a home kitchen. "
    "A sharp steel kitchen knife is making precise contact with the side of the "
    "index finger of the hand steadying the cucumber. A clean, shallow cut is "
    "visible, with only a small, single bead of bright red blood beginning to "
    "form at the incision point. The surrounding skin is tense. Natural soft "
    "light, blurred domestic background, realistic skin texture, 8k, raw style."
)


def main() -> None:
    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("ERROR: FAL_KEY no configurada.")
    OUT.mkdir(parents=True, exist_ok=True)

    resp = requests.post(
        "https://fal.run/fal-ai/flux/dev",
        headers={"Authorization": f"Key {key}"},
        json={
            "prompt": PROMPT,
            "image_size": "landscape_16_9",
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "seed": 1001,
            "enable_safety_checker": False,
            "num_images": 1,
            "output_format": "jpeg",
        },
        timeout=300,
    )
    print("HTTP", resp.status_code)
    if resp.status_code != 200:
        print(resp.text[:600])
        sys.exit("-> flux/dev tambien rechaza.")

    data = resp.json()
    url = data["images"][0]["url"]
    out = OUT / "fluxdev_par03_clinico.jpg"
    out.write_bytes(requests.get(url, timeout=60).content)
    print("nsfw:", data.get("has_nsfw_concepts"))
    print("-> PASA. Guardada en", out)


if __name__ == "__main__":
    main()
