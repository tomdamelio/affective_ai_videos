"""Alinea la toma inicial elegida (v3) al LOOK de los frames finales.

Kontext mantiene la composicion de v3 (plano medio frontal, sin cara, manos sobre
el pepino, cuchillo en la tabla) y le cambia solo el look para que matchee s7 /
control: piel clara, tabla de madera miel con veta, luz calida direccional desde
arriba-izquierda, fondo oscuro y desenfocado, clima intimo de documental.

No se puede pasar s7 como referencia (tiene sangre -> moderacion). Se describe el
look en texto. 1 imagen (~$0.025). Salida: work/<id>/start_variants/start_aligned.jpg.
"""
import argparse
import base64
import io
import os
import sys
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim  # noqa: E402

PROMPT = (
    "Keep this photograph's composition exactly the same - same medium front "
    "framing, same cook seen from the chest down with NO face visible, same two "
    "hands resting on the same cucumber, same chef's knife lying on the cutting "
    "board, same pose. Change ONLY two things. FIRST, the background: completely "
    "remove the kitchen, the wooden cabinets, shelves and all furniture, and "
    "replace everything behind the cook with a plain, smooth, softly blurred "
    "NEUTRAL MEDIUM-GRAY seamless studio backdrop (an even muted gray tone, no "
    "objects, no cabinets, not black and not white). SECOND, the cutting board is "
    "a LIGHT natural pale wood board with soft visible grain. Keep soft even "
    "daylight with a medium balanced exposure - not dark and moody, not overly "
    "bright; fair natural skin, gentle shadows, shallow depth of field. "
    "Photorealistic, raw style."
)


def data_uri(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--src", required=True, help="ruta a la toma media elegida (start_variant)")
    args = ap.parse_args()
    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("ERROR: FAL_KEY no configurada.")
    SRC = Path(args.src)
    OUT = get_stim(args.id).start_variants / "start_aligned.jpg"
    if not SRC.exists():
        sys.exit(f"No existe {SRC}")

    resp = requests.post(
        "https://fal.run/fal-ai/flux-kontext/dev",
        headers={"Authorization": f"Key {key}"},
        json={
            "prompt": PROMPT,
            "image_url": data_uri(SRC),
            "num_inference_steps": 30,
            "guidance_scale": 2.5,
            "seed": 1001,
            "num_images": 1,
            "output_format": "jpeg",
        },
        timeout=300,
    )
    print("HTTP", resp.status_code)
    if resp.status_code != 200:
        sys.exit(resp.text[:400])
    url = resp.json()["images"][0]["url"]
    OUT.write_bytes(requests.get(url, timeout=60).content)
    print("-> ", OUT)


if __name__ == "__main__":
    main()
