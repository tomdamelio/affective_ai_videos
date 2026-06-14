"""Extrae los frames de los videos finales a dataset/<id>/frames/.

<id>_frame_dolor_N.png  = frames del video de DOLOR
<id>_frame_control_N.png = frames del video de CONTROL
Usa ffmpeg (lo busca en los envs de micromamba). ~1.2 fps por defecto.

Ej:  python scripts/extract_frames.py --id E02
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import get_stim  # noqa: E402

HOME = Path.home()
FFMPEG_CANDIDATES = [
    HOME / "micromamba/envs/affective-fnirs/Library/bin/ffmpeg.exe",
    HOME / "micromamba/envs/campeones/Library/bin/ffmpeg.exe",
    HOME / "micromamba/envs/dmt-emotions/Library/bin/ffmpeg.exe",
]


def find_ffmpeg() -> str:
    for c in FFMPEG_CANDIDATES:
        if c.exists():
            return str(c)
    sys.exit("No encontre ffmpeg en los envs de micromamba.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--fps", default="1.2")
    args = ap.parse_args()
    ff = find_ffmpeg()
    st = get_stim(args.id)
    st.frames_dir.mkdir(parents=True, exist_ok=True)

    for cond in ("dolor", "control"):
        vid = st.video(cond)
        if not vid.exists():
            print(f"  (falta {vid.name}, salto)")
            continue
        out = st.frames_dir / f"{st.id}_frame_{cond}_%d.png"
        subprocess.run(
            [ff, "-y", "-loglevel", "error", "-i", str(vid),
             "-vf", f"fps={args.fps}", str(out)],
            check=True,
        )
        n = len(list(st.frames_dir.glob(f"{st.id}_frame_{cond}_*.png")))
        print(f"  {cond}: {n} frames -> frames/{st.id}_frame_{cond}_*.png")


if __name__ == "__main__":
    main()
