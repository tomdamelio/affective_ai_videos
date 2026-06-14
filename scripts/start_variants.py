"""Genera variantes de TOMA INICIAL (plano medio, 'antes' de cocinar).

Concepto: un cocinero sin cara (cabeza fuera de cuadro), en plano medio, a punto
de cortar una verdura (pepino, para continuidad con el frame de dolor del par 3).
La toma inicial es mas amplia y cinematografica; el video luego cierra al close-up
de la mano (dolor o control).

Modelo: flux-2-pro (contenido benigno -> sin problema de moderacion, mejor calidad).
Salida: work/<id>/start_variants/. ~$0.03 c/u.
"""
import argparse
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim  # noqa: E402

# NOTA: editar los prompts de VARIANTS para la situacion del estimulo nuevo
# (aca son especificos de "cocinero por cortar pepino" = E01).

STYLE = (
    "Photorealistic candid documentary photograph, realistic home kitchen, "
    "natural soft light, shallow depth of field, 8k, raw style."
)

VARIANTS = {
    "v1_overshoulder": (
        "Medium over-the-shoulder shot from behind and slightly above a home cook "
        "standing at a kitchen counter, seen from the back so the FACE IS NOT "
        "VISIBLE (head cropped at the top of the frame). The cook holds a chef's "
        "knife in one hand and is about to start slicing a fresh cucumber on a "
        "wooden cutting board; a few cucumbers and vegetables sit on the counter. "
        "Hands and forearms clearly visible, no injury, calm preparation moment. "
        + STYLE
    ),
    "v2_sideprofile": (
        "Medium side-profile shot of a home cook standing at a kitchen counter, "
        "framed from the chest down so the FACE IS OUT OF FRAME. The cook stands "
        "sideways, holding a chef's knife in one hand and steadying a fresh "
        "cucumber on a wooden cutting board with the other hand, about to begin "
        "cutting. Torso, arms and hands visible, apron, calm preparation moment, "
        "no injury. " + STYLE
    ),
    "v3_frontcounter": (
        "Medium shot looking across a kitchen counter toward a home cook, framed "
        "from the shoulders and chest down so the FACE IS NOT VISIBLE (cropped "
        "above the chest). Both hands rest on a wooden cutting board with a fresh "
        "cucumber and a chef's knife, about to start chopping. Warm cozy home "
        "kitchen, hands and torso visible, no injury, calm preparation moment. "
        + STYLE
    ),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    args = ap.parse_args()
    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("ERROR: FAL_KEY no configurada.")
    OUT = get_stim(args.id).start_variants
    OUT.mkdir(parents=True, exist_ok=True)

    for name, prompt in VARIANTS.items():
        resp = requests.post(
            "https://fal.run/fal-ai/flux-2-pro",
            headers={"Authorization": f"Key {key}"},
            json={
                "prompt": prompt,
                "image_size": "landscape_16_9",
                "seed": 1001,
                "enable_safety_checker": False,
                "safety_tolerance": "5",
                "output_format": "jpeg",
            },
            timeout=300,
        )
        print(f"[{name}] HTTP {resp.status_code}")
        if resp.status_code != 200:
            print("  ", resp.text[:250])
            continue
        url = resp.json()["images"][0]["url"]
        (OUT / f"start_{name}.jpg").write_bytes(requests.get(url, timeout=60).content)
        print(f"  -> start_variants/start_{name}.jpg")


if __name__ == "__main__":
    main()
