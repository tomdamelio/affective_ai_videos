"""Genera los videos finales de un estimulo con Kling (dolor / control).

Usa fal-ai/kling-video/v3/pro/image-to-video (frame inicial + final). API REST +
cola de Fal (sin fal_client). Sin audio. Lee los frames de dataset/<id>/frames/ y
escribe los videos en dataset/<id>/videos/ (convencion en stimulus.py).

Estructura: INICIO compartido = still 'inicio' (extremidad limpia, sin objeto);
durante el clip ENTRA un objeto. Dolor: el objeto peligroso entra y dana (fin =
still 'dolor'). Control: un objeto NEUTRO (p. ej. lapiz) entra y queda en la misma
posicion sin danar (fin = still 'control').

Precio v3/pro: $0.112/seg sin audio -> 5s = $0.56/clip -> par = $1.12.

Uso:
    python scripts/run_videos.py --id E01 --dry-run
    python scripts/run_videos.py --id E01 --condition both
"""
import argparse
import base64
import io
import os
import sys
import time
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim  # noqa: E402
from seal_endframe import seal_condition  # noqa: E402

MODELS = {
    "v3pro": ("fal-ai/kling-video/v3/pro/image-to-video", 0.112),
    "v3std": ("fal-ai/kling-video/v3/standard/image-to-video", 0.084),
}

# Prompts de movimiento. Inicio compartido = still 'inicio' (extremidad limpia,
# sin objeto); el objeto ENTRA durante el clip. Ajustar el texto por estimulo.
# TODO: mover a meta por estimulo. Actual: E07 (jeringa inyecta el pliegue del codo).
MOTION = {
    "dolor": (
        "Hold the tight close-up on the bare inner elbow resting still. A medical "
        "syringe enters from the top; its thin steel needle moves down and pierces "
        "into the skin of the inner-elbow crease for a blood draw, the skin pressed "
        "and punctured at the point of entry as the needle goes in. A clinical "
        "venipuncture, the needle inserting into the arm."
    ),
    "control": (
        "Hold the tight close-up on the bare inner elbow resting calmly. An ordinary "
        "cotton swab enters from the top and comes to rest with its soft white cotton "
        "tip pressing gently on the skin of the inner elbow - in the same spot the "
        "needle would enter - without causing any harm. The skin stays smooth, intact "
        "and unharmed. A calm, safe, soft and painless movement, no needle, no "
        "piercing, no mark."
    ),
}


def data_uri(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def submit_and_wait(model: str, payload: dict, key: str) -> dict:
    headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    r = requests.post(f"https://queue.fal.run/{model}", headers=headers, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"submit HTTP {r.status_code}: {r.text[:400]}")
    job = r.json()
    print(f"  job {job.get('request_id')} encolado; esperando render...")
    while True:
        time.sleep(8)
        s = requests.get(job["status_url"], headers=headers, timeout=30).json()
        st = s.get("status")
        if st == "COMPLETED":
            break
        if st in ("FAILED", "ERROR"):
            raise RuntimeError(f"job fallo: {s}")
        print(f"    estado: {st}")
    return requests.get(job["response_url"], headers=headers, timeout=60).json()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="ID del estimulo (ej. E01)")
    ap.add_argument("--condition", choices=["dolor", "control", "both"], default="both")
    ap.add_argument("--duration", default="5")
    ap.add_argument("--tier", choices=["v3pro", "v3std"], default="v3pro")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    st = get_stim(args.id)
    model, price = MODELS[args.tier]
    # INICIO compartido = still 'inicio' (extremidad limpia, sin el objeto).
    # FIN: dolor -> still 'dolor' (objeto + dano); control -> still 'control'
    #      (objeto NEUTRO que reemplaza al peligroso, misma posicion, sin dano).
    start = st.image("inicio")
    ends = {"dolor": st.image("dolor"), "control": st.image("control")}
    conds = ["dolor", "control"] if args.condition == "both" else [args.condition]
    cost = price * int(args.duration) * len(conds)

    print(f"Estimulo: {st.name}   Modelo: {model} ({price}/s)")
    print(f"Inicio compartido: {start.name}")
    print(f"Condiciones: {conds}   Duracion: {args.duration}s")
    print(f"COSTO ESTIMADO: ${cost:.2f}")

    if not start.exists():
        sys.exit(f"Falta el still inicio: {start}")
    for c in conds:
        if not ends[c].exists():
            sys.exit(f"Falta el still final de {c}: {ends[c]}")

    if args.dry_run:
        print("\n[dry-run] No se genero nada.")
        return

    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("ERROR: FAL_KEY no configurada.")
    st.videos_dir.mkdir(parents=True, exist_ok=True)
    start_uri = data_uri(start)

    for c in conds:
        print(f"\n=== {c} ===")
        payload = {
            "prompt": MOTION[c],
            "start_image_url": start_uri,
            "end_image_url": data_uri(ends[c]),
            "duration": args.duration,
            "generate_audio": False,
            "negative_prompt": "blur, distort, low quality, warped, deformed, extra fingers",
            "cfg_scale": 0.5,
        }
        result = submit_and_wait(model, payload, key)
        out = st.video(c)
        out.write_bytes(requests.get(result["video"]["url"], timeout=180).content)
        print(f"  -> {out.relative_to(st.dataset.parent.parent)}")
        # Sellar el ultimo frame con el still aprobado (el video termina EXACTO en el).
        seal_condition(st, c)


if __name__ == "__main__":
    main()
