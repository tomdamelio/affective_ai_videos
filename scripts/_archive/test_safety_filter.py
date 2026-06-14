"""Diagnostico del filtro de contenido de Fal: que endpoint/redaccion pasa.

Prueba combinaciones (endpoint x prompt) y reporta cual es aceptada.
Los rechazos 422 no se cobran; cada exito cuesta ~$0.03-0.06.
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
OUT = ROOT / "img" / "pilot_epss" / "filter_tests"

PROMPT_GRAFICO = (
    "Photorealistic photograph in a real home kitchen: close-up of a person's "
    "hands slicing a cucumber on a wooden cutting board. The kitchen knife has "
    "just accidentally slipped and cut the index finger of the hand holding the "
    "cucumber; the blade presses against the finger and a fresh bleeding cut is "
    "clearly visible. Natural lighting, realistic skin texture, shallow depth of "
    "field, candid everyday scene."
)

PROMPT_SUAVE = (
    "Photorealistic photograph in a real home kitchen: close-up of a person's "
    "hands slicing a cucumber on a wooden cutting board. The kitchen knife blade "
    "is making direct contact with the side of the index finger of the hand "
    "steadying the cucumber, pressing into the skin, a high-threat moment during "
    "food preparation. A single small bead of red is visible at the contact "
    "point. The surrounding skin is tense. Natural lighting, realistic skin "
    "texture, shallow depth of field, candid everyday scene."
)

PROMPT_ENERO = (
    "Photorealistic, 3rd Person perspective, low angle. A 20-year-old Female, "
    "anatomically correct right foot with exactly five distinct toes, bare on a "
    "weathered wooden log. A sharp steel hatchet blade is making precise contact "
    "with the extreme tip of the small toe (pinky). The blade is actively "
    "slicing off just a small, superficial portion of the toe's end. A clean, "
    "shallow cut is visible, with only a small, single bead of bright red blood "
    "beginning to form at the incision point, without running down the log. "
    "Cinematic lighting, 8k, raw style, close-up focus on the contact point."
)


def data_uri(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def call(model: str, payload: dict, name: str) -> bool:
    resp = requests.post(
        f"https://fal.run/{model}",
        headers={"Authorization": f"Key {os.environ['FAL_KEY']}"},
        json=payload,
        timeout=300,
    )
    if resp.status_code == 200:
        url = resp.json()["images"][0]["url"]
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{name}.jpg").write_bytes(requests.get(url, timeout=60).content)
        print(f"  PASA  -> {name}.jpg")
        return True
    detail = resp.json().get("detail", resp.text[:200])
    kind = detail[0].get("type", "?") if isinstance(detail, list) else str(detail)[:120]
    print(f"  RECHAZA ({resp.status_code}: {kind})")
    return False


COMMON = {
    "seed": 1001,
    "enable_safety_checker": False,
    "safety_tolerance": "5",
    "output_format": "jpeg",
}

tests = sys.argv[1:] or ["t2i_grafico", "edit_grafico_suave"]

if "t2i_grafico" in tests:
    print("[1] flux-2-pro TEXT-TO-IMAGE, prompt grafico (pepino):")
    call(
        "fal-ai/flux-2-pro",
        {"prompt": PROMPT_GRAFICO, "image_size": "landscape_16_9", **COMMON},
        "t2i_grafico",
    )
    print("[2] flux-2-pro TEXT-TO-IMAGE, prompt de enero (hacha/pie):")
    call(
        "fal-ai/flux-2-pro",
        {"prompt": PROMPT_ENERO, "image_size": "landscape_16_9", **COMMON},
        "t2i_enero",
    )

if "edit_grafico_suave" in tests:
    ref = data_uri(LIMB / "3.2.bmp")
    print("[3] flux-2-pro/EDIT, prompt grafico + imagen EPSS:")
    call(
        "fal-ai/flux-2-pro/edit",
        {"prompt": "Recreate this exact scene, same camera angle and hand positions: " + PROMPT_GRAFICO,
         "image_urls": [ref], "image_size": "landscape_16_9", **COMMON},
        "edit_grafico",
    )
    print("[4] flux-2-pro/EDIT, prompt suave + imagen EPSS:")
    call(
        "fal-ai/flux-2-pro/edit",
        {"prompt": "Recreate this exact scene, same camera angle and hand positions: " + PROMPT_SUAVE,
         "image_urls": [ref], "image_size": "landscape_16_9", **COMMON},
        "edit_suave",
    )
