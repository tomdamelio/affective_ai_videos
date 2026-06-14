"""Deriva el CONTROL y el INICIO desde el ancla de DOLOR, con Kontext (edicion local).

El dolor es el unico keyframe generado desde cero; control e inicio son ediciones
sustractivas de el, lo que mantiene la extremidad IDENTICA (misma mano/posicion/encuadre
close-up). Variantes:
  control -> still de CONTROL: REEMPLAZA el objeto peligroso por uno NEUTRO e inofensivo
             (extremo romo/blando, no una punta sobre la piel) en su misma posicion, y
             quita todo el dano. Misma pose exacta que el dolor.
  clean   -> INICIO compartido del video: extremidad limpia sin el objeto.
  start_closeup -> opcional/raro: deja el objeto en posicion, quita solo el dano.

fal-ai/flux-kontext/dev (open, edicion por instruccion, sin moderacion agresiva).
El objeto neutro depende de la escena: PASAR --prompt a medida (el default es plantilla).

Escribe en work/<id>/candidates/.  ~$0.025 por imagen.

Uso:
  python scripts/derive_variant.py --id E02 --anchor work/E02_.../selected/e02_dolor_s7.jpg control
  python scripts/derive_variant.py --id E02 --anchor work/E02_.../selected/e02_dolor_s7.jpg clean
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

MODEL_KONTEXT = "fal-ai/flux-kontext/dev"

PROMPTS = {
    # Clean: misma escena, SIN el objeto ni sangre (mano/zona limpia) -> sirve de inicio.
    "clean": (
        "Keep this photograph exactly the same - same hand, same fingers, same "
        "wooden cutting board, same camera angle, same lighting and background. "
        "Remove the knife and any blade COMPLETELY, and remove all blood and any "
        "wound. The hand now rests calmly on a bare empty wooden cutting board: "
        "the fingertips touch only smooth clean wood, the index finger is intact "
        "and unharmed. There is NO knife and NO blade anywhere in the image, just "
        "the hand on the empty board."
    ),
    # Control: REEMPLAZA el objeto peligroso por uno NEUTRO inofensivo en su misma
    # posicion, y quita el dano. El contraste dolor/control = objeto + desenlace, mismo
    # layout. PLANTILLA escena-especifica (es la de E02 = cigarrillo -> goma de borrar);
    # PASAR --prompt a medida para otras escenas/objetos neutros.
    "control": (
        "Edit this photograph: replace the cigarette with an ordinary wooden pencil "
        "held UPSIDE DOWN, its blunt pink rubber eraser end resting gently on the "
        "back of the hand exactly where the cigarette was; the sharpened tip points "
        "up, away from the skin. Completely remove all ember, ash, smoke, glowing "
        "tip, burn mark, scorch, blister and redness - the skin is smooth and "
        "intact. The soft eraser only rests lightly, causing no harm. Keep the hand "
        "in the EXACT same position and pose, same fingers, same framing, camera "
        "angle, lighting, surface and background. A harmless pencil eraser resting "
        "where the cigarette was, the hand unharmed."
    ),
    # Inicio close-up opcional: quita SOLO la sangre, deja el filo en posicion.
    "start_closeup": (
        "Keep this photograph EXACTLY the same - identical close-up framing, same "
        "hand, fingers, board, camera angle, lighting and background, and the "
        "knife blade STILL in the same diagonal position resting against the "
        "fingertip. Remove all blood and any wound completely - the skin is "
        "intact, smooth and unbroken, NOT yet cut. The blade is poised against the "
        "skin in the instant just before cutting, no wound and no blood. A tense "
        "moment right before the cut."
    ),
}


def data_uri(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def kontext(prompt: str, image_uri: str, key: str,
            seed: int = 1001, guidance: float = 2.5, steps: int = 30) -> bytes:
    resp = requests.post(
        f"https://fal.run/{MODEL_KONTEXT}",
        headers={"Authorization": f"Key {key}"},
        json={"prompt": prompt, "image_url": image_uri, "num_inference_steps": steps,
              "guidance_scale": guidance, "seed": seed, "num_images": 1, "output_format": "jpeg"},
        timeout=300,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    return requests.get(resp.json()["images"][0]["url"], timeout=60).content


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--anchor", required=True, help="ruta al frame de dolor (ancla)")
    ap.add_argument("variant", choices=["clean", "control", "start_closeup"])
    ap.add_argument("--prompt", default=None,
                    help="instruccion Kontext a medida (sobreescribe el default de la escena E01)")
    ap.add_argument("--seed", type=int, default=1001,
                    help="seed Kontext (variar para muestras distintas; default 1001)")
    ap.add_argument("--guidance", type=float, default=2.5,
                    help="guidance_scale Kontext (subir para ediciones mas fuertes; default 2.5)")
    ap.add_argument("--steps", type=int, default=30, help="num_inference_steps (default 30)")
    args = ap.parse_args()

    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("ERROR: FAL_KEY no configurada.")
    anchor = Path(args.anchor)
    if not anchor.exists():
        sys.exit(f"No existe el ancla: {anchor}")
    st = get_stim(args.id)
    st.candidates.mkdir(parents=True, exist_ok=True)

    prompt = args.prompt or PROMPTS[args.variant]
    out = st.candidates / f"{args.variant}.jpg"
    out.write_bytes(kontext(prompt, data_uri(anchor), key,
                            seed=args.seed, guidance=args.guidance, steps=args.steps))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
