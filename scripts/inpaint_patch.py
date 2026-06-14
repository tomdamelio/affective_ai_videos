"""Inpaint LOCAL de un parche con FLUX Pro Fill (mascara) — borra una marca/feature
que Kontext no logra quitar (p. ej. el dimple del pinchazo en el still de INICIO/control).

Kontext edita por instruccion de forma GLOBAL y tiende a preservar features de piel
(un dimple/pliegue) aunque le pidas borrarlos. Fill regenera SOLO la region enmascarada
con la piel del entorno -> elimina el parche de forma quirurgica, dejando el resto
pixel-a-pixel intacto. ~$0.05/imagen.

La mascara se genera sola: circulo/elipse blanco (=inpaint) sobre fondo negro (=keep),
con borde difuminado (feather). Pasas centro/radio en pixeles (--cx --cy --r).

Endpoint: fal-ai/flux-pro/v1/fill (image_url + mask_url; blanco=inpaint). Es un endpoint
'pro' (tiene filtro de entrada), pero para piel limpia sin sangre no se gatilla.

Uso:
  python scripts/inpaint_patch.py --id E07 \
      --image work/E07_inyeccion_codo/candidates/clean_pass2.jpg \
      --cx 477 --cy 385 --r 100 --out-tag clean_inpaint
"""
import argparse
import base64
import io
import os
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim  # noqa: E402

MODEL_FILL = "fal-ai/flux-pro/v1/fill"

DEFAULT_PROMPT = (
    "bare smooth healthy human skin, even natural skin tone, fine realistic skin "
    "texture matching the surrounding area, completely flat and unbroken, no mark, "
    "no dimple, no pucker, no crease, no wound, no discoloration"
)


def data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def make_mask(size, cx: int, cy: int, r: int, feather: int) -> Image.Image:
    """Mascara L: blanco (255)=inpaint dentro del circulo, negro=keep; borde difuminado."""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    if feather > 0:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return m


def fill(image_uri: str, mask_uri: str, prompt: str, key: str,
         seed: int, guidance: float, steps: int) -> bytes:
    resp = requests.post(
        f"https://fal.run/{MODEL_FILL}",
        headers={"Authorization": f"Key {key}"},
        json={"image_url": image_uri, "mask_url": mask_uri, "prompt": prompt,
              "seed": seed, "guidance_scale": guidance, "num_inference_steps": steps,
              "safety_tolerance": "6", "num_images": 1, "output_format": "jpeg"},
        timeout=300,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    url = (data.get("images") or [data.get("image", {})])[0]["url"]
    return requests.get(url, timeout=60).content


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--image", required=True, help="imagen base a parchear")
    ap.add_argument("--cx", type=int, required=True, help="centro X del parche (px)")
    ap.add_argument("--cy", type=int, required=True, help="centro Y del parche (px)")
    ap.add_argument("--r", type=int, required=True, help="radio del parche (px)")
    ap.add_argument("--feather", type=int, default=25, help="difuminado del borde (px); default 25")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--seed", type=int, default=4000)
    ap.add_argument("--guidance", type=float, default=15.0)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--out-tag", default="clean_inpaint", help="nombre de salida en candidates/")
    args = ap.parse_args()

    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("ERROR: FAL_KEY no configurada.")
    base = Path(args.image)
    if not base.exists():
        sys.exit(f"No existe la imagen base: {base}")
    st = get_stim(args.id)
    st.candidates.mkdir(parents=True, exist_ok=True)

    img = Image.open(base).convert("RGB")
    mask = make_mask(img.size, args.cx, args.cy, args.r, args.feather)
    mask_out = st.candidates / f"{args.out_tag}_mask.png"
    mask.save(mask_out)

    out = st.candidates / f"{args.out_tag}.jpg"
    out.write_bytes(fill(data_uri(img), data_uri(mask), args.prompt, key,
                         args.seed, args.guidance, args.steps))
    print(f"-> {out}")
    print(f"   mask: {mask_out}")


if __name__ == "__main__":
    main()
