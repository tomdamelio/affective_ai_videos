"""Finaliza los 3 stills canonicos: copia los elegidos (desde work/) a
dataset/<id>/images/ con el nombre canonico (PNG) y actualiza el index.

  dolor   = la extremidad con el objeto + dano (generado primero, flux/dev)
  control = edicion Kontext del dolor: objeto peligroso reemplazado por uno neutro
            inofensivo en su lugar, sin dano (misma mano/posicion)
  inicio  = extremidad limpia sin el objeto (inicio compartido del video)

Ej:
  python scripts/finalize_frames.py --id E02 \
      --inicio  work/E02_.../candidates/clean.jpg \
      --dolor   work/E02_.../selected/e02_dolor_s7.jpg \
      --control work/E02_.../candidates/control.jpg
"""
import argparse
import csv
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim, INDEX, ROOT  # noqa: E402


def to_png(src: Path, dst: Path, size=None) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
        print(f"  (resize {Image.open(src).size} -> {size})")
    im.save(dst)
    print(f"  {src} -> {dst.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--dolor", required=True)
    ap.add_argument("--control", required=True)
    args = ap.parse_args()

    st = get_stim(args.id)
    st.images_dir.mkdir(parents=True, exist_ok=True)
    # Igualar los 3 stills a la resolucion del frame de DOLOR (referencia).
    ref = Image.open(args.dolor).size
    print(f"Resolucion de referencia (dolor): {ref}")
    to_png(Path(args.dolor),   st.image("dolor"),   ref)
    to_png(Path(args.inicio),  st.image("inicio"),  ref)
    to_png(Path(args.control), st.image("control"), ref)

    # actualizar n_images en el index
    rows = list(csv.DictReader(open(INDEX, newline="", encoding="utf-8")))
    for r in rows:
        if r["id"] == st.id:
            r["n_images"] = 3
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"\nStills finales en {st.images_dir.relative_to(ROOT)}")
    print("Siguiente: python scripts/run_videos.py --id", st.id)


if __name__ == "__main__":
    main()
