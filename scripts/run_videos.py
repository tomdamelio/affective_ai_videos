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
import json
import os
import sys
import time
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim, archive_if_exists, update_index_fields, CONDITIONS  # noqa: E402
from seal_endframe import seal_condition  # noqa: E402

MODELS = {
    "v3pro": ("fal-ai/kling-video/v3/pro/image-to-video", 0.112),
    "v3std": ("fal-ai/kling-video/v3/standard/image-to-video", 0.084),
}

# Prompts de movimiento. Inicio compartido = still 'inicio' (extremidad limpia,
# sin objeto); el objeto ENTRA durante el clip. Ajustar el texto por estimulo.
# MOTION por estimulo: se lee de work/<id>/motion.json ({dolor, control}) via load_motion().
# El dict de abajo es solo un FALLBACK/template (ultimo: E06) para uso suelto si no existe
# el motion.json. En paralelo CADA sesion crea su propio motion.json y NO toca este archivo.
MOTION = {
    "dolor": (
        "Hold the tight close-up on the bare foot resting flat on the dark wooden "
        "floor. A woman's black stiletto high-heeled shoe enters from the top and "
        "presses its slender heel down onto the top of the bare foot, pressing in "
        "firmly but only a little, not too deep. In one single slow reaction to the "
        "pain, the bare toes rise and curl upward off the floor ONE time and stay "
        "lifted, the foot tensing as the raised toes hold their position. A single "
        "smooth lift of the toes - no bouncing, no second lift, no repeating, the "
        "motion happens only once. No blood, no wound, no cut."
    ),
    "control": (
        "Hold the tight close-up on the bare foot resting flat and calm on the dark "
        "wooden floor. An ordinary soft makeup brush enters from the top and comes to "
        "rest with its soft fluffy bristle head lying gently on the instep - in the "
        "same spot where the heel would press - without causing any harm. The skin "
        "stays smooth, intact and unharmed, the toes relaxed. A calm, safe, soft and "
        "painless movement, no heel, no sharp object, no mark."
    ),
}


def data_uri(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def load_motion(st) -> dict:
    """Prompts de movimiento del estimulo: de work/<id>/motion.json si existe
    ({\"dolor\": ..., \"control\": ...}), si no del MOTION template de este script."""
    mp = st.motion_path
    if mp.exists():
        data = json.loads(mp.read_text(encoding="utf-8"))
        missing = [c for c in CONDITIONS if c not in data]
        if missing:
            sys.exit(f"{mp} no tiene los prompts: {missing}")
        print(f"Motion: {mp.relative_to(st.work.parent.parent)}")
        return data
    print(f"Motion: (no hay {mp.name}; uso el MOTION template del script)")
    return MOTION


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
    ap.add_argument("--cfg", type=float, default=0.5,
                    help="cfg_scale Kling: mas alto = sigue mas el prompt de movimiento (default 0.5)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    st = get_stim(args.id)
    model, price = MODELS[args.tier]
    motion = load_motion(st)
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
            "prompt": motion[c],
            "start_image_url": start_uri,
            "end_image_url": data_uri(ends[c]),
            "duration": args.duration,
            "generate_audio": False,
            "negative_prompt": "blur, distort, low quality, warped, deformed, extra fingers",
            "cfg_scale": args.cfg,
        }
        result = submit_and_wait(model, payload, key)
        out = st.video(c)
        archive_if_exists(out)  # NO-OVERWRITE: guarda el video anterior en videos/_archive/
        out.write_bytes(requests.get(result["video"]["url"], timeout=180).content)
        print(f"  -> {out.relative_to(st.dataset.parent.parent)}")
        # Sellar el ultimo frame con el still aprobado (el video termina EXACTO en el).
        seal_condition(st, c)

    # Actualizar el index (con lock, seguro ante sesiones en paralelo).
    n = sum(1 for cc in CONDITIONS if st.video(cc).exists())
    estado = "completo" if n == len(CONDITIONS) else "en_proceso"
    update_index_fields(st.id, n_videos=n, estado=estado)
    print(f"\nIndex: n_videos={n}, estado={estado}")


if __name__ == "__main__":
    main()
