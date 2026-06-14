"""Piloto EPSS - Paso 2: regeneracion fotorrealista de keyframes.

Para cada par seleccionado (3, 30, 29) genera 3 keyframes via FLUX.2 [pro] Edit:
  1. master  (t_end_P): re-render fotorrealista de la imagen de dolor EPSS (N.2).
  2. control (t_end_C): editado desde el master -> desenlace sin dolor.
  3. start   (t_start): editado desde el master -> estado inicial compartido.

Solo imagenes (sin video). Usa la API REST de Fal directamente (requests),
con las imagenes EPSS embebidas como data URI. Salida: img/pilot_epss/.
"""
import base64
import io
import json
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

MODEL_EDIT = "fal-ai/flux-2-pro/edit"
SEED = 1001

STYLE = (
    "Photorealistic photograph, natural lighting, realistic skin texture and "
    "anatomy, shallow depth of field, candid everyday scene shot on a modern "
    "full-frame camera. No studio backdrop: a real, lived-in environment."
)

PAIRS = {
    3: {
        "name": "corte_pepino",
        "master": (
            "Recreate this exact scene as a photorealistic photograph in a real home "
            "kitchen: close-up of a person's hands slicing a cucumber on a wooden "
            "cutting board. The kitchen knife has just accidentally slipped and cut "
            "the index finger of the hand holding the cucumber; the blade presses "
            "against the finger and a fresh bleeding cut is clearly visible. Keep the "
            "same camera angle, hand positions and action as the reference image. "
            + STYLE
        ),
        "control": (
            "Move the knife so it is safely slicing the cucumber in the middle of the "
            "board, well away from the fingers. Remove the wound and every trace of "
            "blood: the finger is completely intact and unharmed. Keep the camera "
            "angle, hands, cutting board, kitchen background and lighting identical."
        ),
        "start": (
            "Show the moment just before cutting begins: the knife is held still, "
            "resting flat on the cutting board next to the whole uncut cucumber. The "
            "other hand steadies the cucumber. No wound, no blood, finger intact. "
            "Keep the camera angle, hands, board, background and lighting identical."
        ),
    },
    30: {
        "name": "martillazo_pulgar",
        "master": (
            "Recreate this exact scene as a photorealistic photograph in a real home "
            "workshop: close-up of a person hammering a nail into a wooden board. The "
            "hammer has just accidentally struck the thumb of the hand holding the "
            "nail instead of the nail; the hammer head is in contact with the crushed "
            "thumb, which is visibly red and bruised. Keep the same camera angle, "
            "hand positions and action as the reference image. " + STYLE
        ),
        "control": (
            "Move the hammer so it is cleanly striking the head of the nail, well "
            "away from the fingers. The thumb and all fingers are completely intact, "
            "uninjured, with normal skin color. Keep the camera angle, hands, wooden "
            "board, workshop background and lighting identical."
        ),
        "start": (
            "Show the moment just before the hammer swings: the hammer is raised "
            "about twenty centimeters above the nail, the other hand steadies the "
            "nail upright on the wooden board. All fingers intact and uninjured. Keep "
            "the camera angle, hands, board, background and lighting identical."
        ),
    },
    29: {
        "name": "chinches_pie",
        "master": (
            "Recreate this exact scene as a photorealistic photograph in a real home "
            "interior with a wooden floor: close-up of a bare foot that has just "
            "stepped onto several metal thumbtacks lying on the floor; a thumbtack "
            "pierces the sole and the foot presses down on the sharp tacks. Keep the "
            "same camera angle and foot position as the reference image. " + STYLE
        ),
        "control": (
            "Move the thumbtacks so they lie scattered on the floor clearly to the "
            "side, untouched. The bare foot rests flat and safely on the empty wooden "
            "floor, completely unharmed. Keep the camera angle, foot, floor, "
            "background and lighting identical."
        ),
        "start": (
            "Show the moment just before the step: the bare foot is lifted in "
            "mid-step about ten centimeters above the wooden floor, with the metal "
            "thumbtacks lying scattered on the floor below. Foot unharmed. Keep the "
            "camera angle, floor, background and lighting identical."
        ),
    },
}


def fal_key() -> str:
    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("ERROR: FAL_KEY no configurada.")
    return key


def to_data_uri(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def run_edit(prompt: str, image_uri: str, image_size) -> bytes:
    resp = requests.post(
        f"https://fal.run/{MODEL_EDIT}",
        headers={
            "Authorization": f"Key {fal_key()}",
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "image_urls": [image_uri],
            "image_size": image_size,
            "seed": SEED,
            "enable_safety_checker": False,
            "safety_tolerance": "5",
            "output_format": "jpeg",
        },
        timeout=300,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    url = data["images"][0]["url"]
    img = requests.get(url, timeout=60)
    img.raise_for_status()
    return img.content


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    log = {}
    for pair, spec in PAIRS.items():
        tag = f"par{pair:02d}_{spec['name']}"
        print(f"\n=== {tag} ===")

        master_path = OUT / f"{tag}_endP.jpg"
        if not master_path.exists():
            print("  [1/3] master (t_end_P) desde EPSS...")
            ref = to_data_uri(LIMB / f"{pair}.2.bmp")
            master_path.write_bytes(run_edit(spec["master"], ref, "landscape_16_9"))
        master_uri = to_data_uri(master_path)

        for key, suffix in [("control", "endC"), ("start", "start")]:
            out_path = OUT / f"{tag}_{suffix}.jpg"
            if out_path.exists():
                continue
            print(f"  [{2 if key == 'control' else 3}/3] {key}...")
            out_path.write_bytes(run_edit(spec[key], master_uri, "auto"))

        log[tag] = {k: spec[k] for k in ("master", "control", "start")}
        print(f"  OK -> {OUT}")

    (OUT / "prompts_log.json").write_text(json.dumps(log, indent=2))
    print("\nListo. 9 imagenes en", OUT)


if __name__ == "__main__":
    main()
