"""flux/dev: subir adherencia para que renderice la lesion (no la moderacion).

flux/dev no filtra la entrada (HTTP 200), pero por baja adherencia rindio una
escena segura. Probamos 2 variantes:
  V1) texto->imagen, con la LESION como sujeto principal al inicio del prompt.
  V2) imagen->imagen, usando la foto EPSS del par 3 como referencia de
      composicion (diseno i2i original del repo) para forzar la herida.
Contenido equivalente al que la propia base EPSS (validada, CC BY 4.0) muestra.
2 imagenes (~$0.05). Salida: img/pilot_epss/.
"""
import base64
import io
import os
import sys
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LIMB = (
    ROOT
    / "EPSS"
    / "Empathy for Limb Pain Picture Database (EPSS-Limb)"
    / "Empathy for Limb Pain Picture Database (EPSS-Limb)"
)
OUT = ROOT / "img" / "pilot_epss"

# La lesion va PRIMERO, como foco; la escena de cocina es secundaria.
PROMPT_V1 = (
    "Extreme close-up of a deep accidental knife cut on a human index finger. A "
    "sharp steel kitchen knife blade is slicing into the side of the fingertip, "
    "splitting the skin; bright red blood wells up from the open cut and runs "
    "down the finger. The other hand and a half-sliced cucumber on a wooden "
    "cutting board are visible, blurred, in the background of a home kitchen. "
    "Graphic, visceral, photorealistic, sharp focus on the wound, natural light, "
    "realistic skin and blood, 8k, raw style."
)

PROMPT_V2 = (
    "Re-render this scene as a graphic, photorealistic, high-resolution "
    "photograph, keeping the same composition and camera angle: a kitchen knife "
    "slicing into a finger while cutting a cucumber, an open bleeding cut on the "
    "fingertip with bright red blood. Realistic skin texture, sharp focus on the "
    "wound, natural light, 8k, raw style."
)


def data_uri(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def post(model: str, payload: dict, out_name: str) -> None:
    resp = requests.post(
        f"https://fal.run/{model}",
        headers={"Authorization": f"Key {os.environ['FAL_KEY']}"},
        json=payload,
        timeout=300,
    )
    print(f"[{out_name}] HTTP {resp.status_code}")
    if resp.status_code != 200:
        print("  ", resp.text[:300])
        return
    data = resp.json()
    url = data["images"][0]["url"]
    (OUT / out_name).write_bytes(requests.get(url, timeout=60).content)
    print(f"  nsfw={data.get('has_nsfw_concepts')} -> {out_name}")


def main() -> None:
    if not os.environ.get("FAL_KEY"):
        sys.exit("ERROR: FAL_KEY no configurada.")
    OUT.mkdir(parents=True, exist_ok=True)

    print("V1: texto->imagen, lesion como sujeto principal")
    post(
        "fal-ai/flux/dev",
        {
            "prompt": PROMPT_V1,
            "image_size": "landscape_16_9",
            "num_inference_steps": 28,
            "guidance_scale": 4.5,
            "seed": 1001,
            "enable_safety_checker": False,
            "num_images": 1,
            "output_format": "jpeg",
        },
        "fluxdev_par03_explicit_v1.jpg",
    )

    print("V2: imagen->imagen con referencia EPSS (par 3.2)")
    post(
        "fal-ai/flux/dev/image-to-image",
        {
            "image_url": data_uri(LIMB / "3.2.bmp"),
            "prompt": PROMPT_V2,
            "strength": 0.75,
            "num_inference_steps": 30,
            "guidance_scale": 4.5,
            "seed": 1001,
            "enable_safety_checker": False,
            "num_images": 1,
            "output_format": "jpeg",
        },
        "fluxdev_par03_explicit_v2_i2i.jpg",
    )


if __name__ == "__main__":
    main()
