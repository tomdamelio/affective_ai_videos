"""Crea un estimulo nuevo: agrega la fila al index y crea las carpetas work/dataset.

Ej:
  python scripts/new_stimulus.py --id E02 --slug quemadura_olla --epss 15 \
      --categoria quemadura --descripcion "Mano sobre olla hirviendo"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import Stim, add_index_row  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--epss", default="")
    ap.add_argument("--categoria", default="")
    ap.add_argument("--descripcion", default="")
    ap.add_argument("--fecha", required=True, help="YYYY-MM-DD (no hay reloj en el script)")
    args = ap.parse_args()

    try:
        add_index_row({"id": args.id, "slug": args.slug, "epss_pair": args.epss,
                       "categoria": args.categoria, "descripcion": args.descripcion,
                       "n_images": 0, "n_videos": 0, "estado": "en_proceso",
                       "creado": args.fecha})
    except ValueError as e:
        sys.exit(str(e))

    st = Stim(args.id, args.slug, args.epss, args.categoria, args.descripcion)
    st.make_dirs()
    print(f"Creado {st.name}:")
    print(f"  work:    {st.work}")
    print(f"  dataset: {st.dataset}")


if __name__ == "__main__":
    main()
