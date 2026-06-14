"""Prueba de control: reproduce el metodo de enero (texto->imagen puro,
flux-2-pro, redaccion clinica) sobre una escena EPSS, sin embeber la foto.

Objetivo: confirmar si el 422 de antes venia del endpoint /edit + foto real,
o de la redaccion. Una sola imagen (~$0.03). Salida: img/pilot_epss/.
"""
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "img" / "pilot_epss"

# Redaccion en el MISMO estilo clinico/anatomico que los prompts de enero
# (S01_3P_EndP: "shallow cut ... single bead of bright red blood").
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
        "https://fal.run/fal-ai/flux-2-pro",
        headers={"Authorization": f"Key {key}"},
        json={
            "prompt": PROMPT,
            "image_size": "landscape_16_9",
            "seed": 1001,
            "enable_safety_checker": False,
            "safety_tolerance": "5",
            "output_format": "jpeg",
        },
        timeout=300,
    )
    print("HTTP", resp.status_code)
    if resp.status_code != 200:
        print(resp.text[:600])
        sys.exit("-> El metodo de enero TAMBIEN es rechazado (filtro endurecido).")

    data = resp.json()
    url = data["images"][0]["url"]
    out = OUT / "control_par03_t2i_clinico.jpg"
    out.write_bytes(requests.get(url, timeout=60).content)
    print("nsfw:", data.get("has_nsfw_concepts"))
    print("-> PASA. Guardada en", out)


if __name__ == "__main__":
    main()
