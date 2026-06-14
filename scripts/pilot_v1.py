"""Generacion + curado del ancla de DOLOR (flux/dev) por estimulo.

Escribe en work/<id>/{candidates,selected,deprecated} y lleva work/<id>/ledger.json.

  gen   -> genera 1 candidato a work/<id>/candidates/ y lo registra en el ledger
  keep  -> mueve un candidato a work/<id>/selected/
  drop  -> mueve un candidato a work/<id>/deprecated/
  list  -> muestra el estado

La seed se fija por defecto (1001) para que las diferencias vengan del PROMPT.
Recordatorio: la herida va como sujeto PRINCIPAL al inicio del prompt (flux/dev
tiene baja adherencia). Costo ~$0.025/imagen.

Ej:
  python scripts/pilot_v1.py --id E02 gen e02_dolor "<PROMPT>" --seed 7
  python scripts/pilot_v1.py --id E02 keep e02_dolor_s7
  python scripts/pilot_v1.py --id E02 list
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim  # noqa: E402

MODEL_T2I = "fal-ai/flux/dev"


def load_ledger(st) -> dict:
    return json.loads(st.ledger.read_text(encoding="utf-8")) if st.ledger.exists() else {}


def save_ledger(st, data: dict) -> None:
    st.ledger.parent.mkdir(parents=True, exist_ok=True)
    st.ledger.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_gen(st, args) -> None:
    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("ERROR: FAL_KEY no configurada.")
    st.make_dirs()
    name = f"{args.tag}_s{args.seed}"
    resp = requests.post(
        f"https://fal.run/{MODEL_T2I}",
        headers={"Authorization": f"Key {key}"},
        json={
            "prompt": args.prompt, "image_size": args.size,
            "num_inference_steps": args.steps, "guidance_scale": args.guidance,
            "seed": args.seed, "enable_safety_checker": False,
            "num_images": 1, "output_format": "jpeg",
        },
        timeout=300,
    )
    print("HTTP", resp.status_code)
    if resp.status_code != 200:
        sys.exit(resp.text[:400])
    out = st.candidates / f"{name}.jpg"
    out.write_bytes(requests.get(resp.json()["images"][0]["url"], timeout=60).content)
    ledger = load_ledger(st)
    ledger[name] = {"status": "candidate", "tag": args.tag, "prompt": args.prompt,
                    "seed": args.seed, "model": MODEL_T2I, "guidance_scale": args.guidance,
                    "steps": args.steps, "size": args.size}
    save_ledger(st, ledger)
    print(f"-> {out.relative_to(st.work.parent.parent)}")


def _move(st, name: str, dest: Path, status: str) -> None:
    src = st.candidates / f"{name}.jpg"
    if not src.exists():
        sys.exit(f"No esta en candidates/: {name}.jpg")
    dest.mkdir(parents=True, exist_ok=True)
    src.replace(dest / f"{name}.jpg")
    ledger = load_ledger(st)
    if name in ledger:
        ledger[name]["status"] = status
        save_ledger(st, ledger)
    print(f"{name} -> {dest.name}/")


def cmd_keep(st, args) -> None:
    _move(st, args.name, st.selected, "selected")


def cmd_drop(st, args) -> None:
    _move(st, args.name, st.deprecated, "deprecated")


def cmd_list(st, args) -> None:
    ledger = load_ledger(st)
    if not ledger:
        print("Ledger vacio.")
        return
    by: dict = {}
    for n, m in ledger.items():
        by.setdefault(m["status"], []).append(n)
    for status in ("selected", "candidate", "deprecated"):
        names = by.get(status, [])
        if names:
            print(f"\n[{status}] ({len(names)})")
            for n in names:
                print(f"  {n}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True, help="ID del estimulo (ej. E02)")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen"); g.add_argument("tag"); g.add_argument("prompt")
    g.add_argument("--seed", type=int, default=1001); g.add_argument("--guidance", type=float, default=4.5)
    g.add_argument("--steps", type=int, default=30); g.add_argument("--size", default="landscape_16_9")
    g.set_defaults(func=cmd_gen)
    k = sub.add_parser("keep"); k.add_argument("name"); k.set_defaults(func=cmd_keep)
    d = sub.add_parser("drop"); d.add_argument("name"); d.set_defaults(func=cmd_drop)
    ls = sub.add_parser("list"); ls.set_defaults(func=cmd_list)
    args = p.parse_args()
    st = get_stim(args.id)
    args.func(st, args)


if __name__ == "__main__":
    main()
