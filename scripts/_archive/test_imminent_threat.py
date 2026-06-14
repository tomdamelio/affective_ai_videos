"""Prueba de reencuadre: 'amenaza inminente' sin herida ni sangre.

Genera el instante ANTES del dano (no la lesion) para la escena del corte.
flux-2-pro, texto->imagen. 1 imagen (~$0.03). Salida: img/pilot_epss/.
"""
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "img" / "pilot_epss"

# Sin sangre, sin corte: solo proximidad/amenaza y tension corporal.
PROMPT = (
    "Photorealistic, 3rd Person perspective, close-up. A hand steadies a cucumber "
    "on a wooden cutting board in a home kitchen while the other hand holds a "
    "kitchen knife. The sharp blade is dangerously close to the index finger, "
    "almost touching it, a tense risky moment during food preparation. The skin "
    "is intact and unharmed, the muscles slightly tense. Natural soft light, "
    "blurred domestic background, realistic skin texture, shallow depth of field, "
    "8k, raw style."
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
        sys.exit("-> Tambien rechazado.")

    data = resp.json()
    url = data["images"][0]["url"]
    out = OUT / "imminent_par03_threat.jpg"
    out.write_bytes(requests.get(url, timeout=60).content)
    print("nsfw:", data.get("has_nsfw_concepts"))
    print("-> PASA. Guardada en", out)


if __name__ == "__main__":
    main()
