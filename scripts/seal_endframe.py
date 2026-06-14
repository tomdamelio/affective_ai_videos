"""Sella el ULTIMO frame de cada video con el still aprobado de images/, para que
el final del video sea EXACTAMENTE la imagen guardada en dataset/<id>/images/.

Kling aproxima el end_image_url pero no lo clava pixel-a-pixel; este paso reemplaza
el ultimo frame por el still exacto (escalado a la resolucion del video), conservando
duracion, fps y resolucion. Luego refresca los frames del deliverable (frames/) y deja
el ultimo = el still.

  video dolor   -> termina en images/<id>_still_dolor.png
  video control -> termina en images/<id>_still_control.png

Usa ffmpeg/ffprobe de los envs de micromamba. Reusable; run_videos.py lo llama al
generar cada video. Tambien se puede correr suelto:

  python scripts/seal_endframe.py --id E02 --condition both
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim, CONDITIONS, archive_if_exists  # noqa: E402

HOME = Path.home()
_BIN = [HOME / "micromamba/envs/affective-fnirs/Library/bin",
        HOME / "micromamba/envs/campeones/Library/bin"]

# El still final de cada condicion (= end_frame del video en run_videos.py).
END_STILL = {"dolor": "dolor", "control": "control"}


def _tool(name: str) -> str:
    for d in _BIN:
        p = d / f"{name}.exe"
        if p.exists():
            return str(p)
    sys.exit(f"No encontre {name} en los envs de micromamba.")


def _probe(video: Path):
    out = subprocess.run(
        [_tool("ffprobe"), "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_frames,r_frame_rate",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout
    s = json.loads(out)["streams"][0]
    return int(s["width"]), int(s["height"]), int(s["nb_frames"])


def seal_condition(st, cond: str, fps: str = "1.2") -> None:
    """Sella el ultimo frame del video <cond> con el still aprobado y refresca
    los frames del deliverable dejando el ultimo = el still."""
    video = st.video(cond)
    still = st.image(END_STILL[cond])
    if not video.exists() or not still.exists():
        print(f"  (falta {video.name} o {still.name}, salto {cond})")
        return
    ff = _tool("ffmpeg")
    w, h, n = _probe(video)

    # 1) Reemplazar SOLO el ultimo frame (n-1) por el still escalado al tamanio del video.
    tmp = video.with_suffix(".sealing.mp4")
    subprocess.run(
        [ff, "-y", "-loglevel", "error", "-i", str(video), "-i", str(still),
         "-filter_complex",
         f"[1:v]scale={w}:{h},setsar=1[s];[0:v][s]overlay=enable='gte(n,{n - 1})'[v]",
         "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16",
         "-preset", "medium", "-pix_fmt", "yuv420p", str(tmp)],
        check=True,
    )
    tmp.replace(video)

    # 2) Refrescar los frames del deliverable; el ultimo = el still exacto.
    st.frames_dir.mkdir(parents=True, exist_ok=True)
    # NO-OVERWRITE: archiva los frames anteriores en frames/_archive/ en vez de borrarlos
    # (antes esto hacia old.unlink() y se perdian frames de corridas previas).
    for old in st.frames_dir.glob(f"{st.id}_frame_{cond}_*.png"):
        archive_if_exists(old)
    subprocess.run(
        [ff, "-y", "-loglevel", "error", "-i", str(video), "-vf", f"fps={fps}",
         str(st.frames_dir / f"{st.id}_frame_{cond}_%d.png")],
        check=True,
    )
    frames = sorted(st.frames_dir.glob(f"{st.id}_frame_{cond}_*.png"),
                    key=lambda p: int(p.stem.split("_")[-1]))
    last = frames[-1] if frames else st.frames_dir / f"{st.id}_frame_{cond}_1.png"
    Image.open(still).convert("RGB").resize((w, h), Image.LANCZOS).save(last)
    print(f"  {cond}: video sellado (ultimo frame = images/{still.name}); "
          f"{len(frames)} frames, ultimo = still")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--condition", choices=["dolor", "control", "both"], default="both")
    ap.add_argument("--fps", default="1.2")
    args = ap.parse_args()
    st = get_stim(args.id)
    conds = list(CONDITIONS) if args.condition == "both" else [args.condition]
    for c in conds:
        seal_condition(st, c, fps=args.fps)


if __name__ == "__main__":
    main()
