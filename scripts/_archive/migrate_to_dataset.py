"""Migracion one-shot: par03 (img/pilot_epss + videos_epss) -> dataset/ + work/ E01.

Crea la estructura sistematizada, mueve finales a dataset/, exploracion a work/,
y escribe stimuli_index.csv + E01_meta.json + dataset/README.md.
"""
import csv
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stimulus import Stim, DATASET, WORK, INDEX, ROOT  # noqa: E402

from PIL import Image  # noqa: E402

PILOT = ROOT / "img" / "pilot_epss"
VIDS = ROOT / "videos_epss"

st = Stim("E01", "corte_pepino", epss_pair="3", categoria="corte",
          descripcion="Cortar pepino; el cuchillo corta el dedo indice")


def mv(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"  mv {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")


def jpg_to_png(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.open(src).convert("RGB").save(dst)
    print(f"  png {dst.relative_to(ROOT)}")


def main() -> None:
    st.make_dirs()

    # --- FRAMES finales (jpg -> png) ---
    jpg_to_png(PILOT / "final" / "par03_FINAL_inicio.jpg",  st.frame("inicio"))
    jpg_to_png(PILOT / "final" / "par03_FINAL_dolor.jpg",   st.frame("dolor"))
    jpg_to_png(PILOT / "final" / "par03_FINAL_control.jpg", st.frame("control"))

    # --- VIDEOS finales (par canonico = closeup_noknife) ---
    mv(VIDS / "par03_dolor_closeup_noknife_5s.mp4",   st.video("dolor"))
    mv(VIDS / "par03_control_closeup_noknife_5s.mp4", st.video("control"))

    # --- EXPLORACION -> work/ ---
    for sub in ("candidates", "selected", "deprecated", "start_variants"):
        s = PILOT / sub
        if s.exists():
            for item in s.iterdir():
                mv(item, st.work / sub / item.name)
    mv(PILOT / "ledger.json", st.ledger)
    # laminas sueltas
    for png in ("continuidad_par03.png", "triptico_par03.png", "triptico_par03_FINAL.png"):
        mv(PILOT / png, st.contact_sheets / png)
    # primeras pruebas sueltas
    for jpg in ("fluxdev_par03_clinico.jpg", "fluxdev_par03_explicit_v1.jpg",
                "fluxdev_par03_explicit_v2_i2i.jpg", "imminent_par03_threat.jpg"):
        mv(PILOT / jpg, st.deprecated / jpg)
    # restos finales del pilot
    mv(PILOT / "final", st.work / "_final_jpg_originales")

    # --- VIDEO: pruebas y frames extraidos -> work/ ---
    for mp4 in ("par03_dolor_closeup_5s.mp4", "par03_dolor_medium_5s.mp4"):
        mv(VIDS / mp4, st.work / "video_tests" / mp4)
    for strip in VIDS.glob("*_strip.png"):
        mv(strip, st.contact_sheets / strip.name)
    mv(VIDS / "frames", st.work / "video_frames")

    # limpiar dirs viejos vacios
    for d in (PILOT, VIDS):
        try:
            d.rmdir()
            print(f"  rm dir vacio {d.relative_to(ROOT)}")
        except OSError:
            print(f"  (queda con contenido) {d.relative_to(ROOT)}")

    # --- META ---
    meta = {
        "id": st.id, "slug": st.slug, "name": st.name,
        "epss_pair": st.epss_pair, "categoria": st.categoria,
        "descripcion": st.descripcion,
        "fuente": "EPSS-Limb (Meng et al. 2023, CC BY 4.0), par 3 (cortar pepino)",
        "creado": "2026-06-13",
        "estado": "completo",
        "frames": {
            "dolor": {
                "modelo": "fal-ai/flux/dev", "seed": 7,
                "metodo": "texto->imagen; herida como sujeto principal al inicio del prompt",
                "prompt": "Extreme close-up macro photograph of a human hand on a wooden kitchen cutting board. The sharp edge of a chef's knife is cutting directly into the pad of the index fingertip: the blade edge is sunk into the flesh, splitting the skin open in a clean deep laceration. The wound gapes slightly along the cut line, with bright red blood flowing out of the open gash, running down the finger and pooling on the board. The blade edge is in clear contact with the cut, biting into the fingertip. The other fingers are tense and curled. Anatomically correct hand, five fingers. Razor-sharp focus on the open cut on the fingertip and the knife edge entering the skin. Natural soft kitchen light, shallow depth of field, hyperrealistic skin pores, wound and blood, 8k, raw documentary style.",
            },
            "control": {
                "modelo": "fal-ai/flux-kontext/dev",
                "metodo": "edicion por instruccion desde el frame de dolor: quitar cuchillo + sangre",
                "prompt": "Keep this photograph exactly the same - same hand, same fingers, same wooden cutting board, same camera angle, same lighting and background. Remove the knife and any blade COMPLETELY, and remove all blood and any wound. The hand now rests calmly on a bare empty wooden cutting board: the fingertips touch only smooth clean wood, the index finger is intact and unharmed. There is NO knife and NO blade anywhere in the image, just the hand on the empty board.",
            },
            "inicio": {
                "modelo": "fal-ai/flux-2-pro (base) + fal-ai/flux-kontext/dev (alineacion de look)",
                "metodo": "plano medio cocinero sin cara (v3 frontal), luego Kontext alinea look (tabla clara, fondo gris)",
                "prompt_base": "Medium shot looking across a kitchen counter toward a home cook, framed from the shoulders and chest down so the FACE IS NOT VISIBLE (cropped above the chest). Both hands rest on a wooden cutting board with a fresh cucumber and a chef's knife, about to start chopping. Warm cozy home kitchen, hands and torso visible, no injury, calm preparation moment.",
                "prompt_align": "Keep composition; remove kitchen/cabinets -> plain neutral medium-gray seamless backdrop; LIGHT natural pale wood board; medium balanced exposure.",
            },
        },
        "videos": {
            "modelo": "fal-ai/kling-video/v3/pro/image-to-video", "duracion_s": 5,
            "audio": False, "tier": "v3pro", "costo_usd_aprox": 1.12,
            "estructura": "inicio compartido = frame de control (mano limpia sin cuchillo); el cuchillo ENTRA durante el clip",
            "dolor": {
                "start_frame": "frame control (mano limpia)", "end_frame": "frame dolor",
                "motion_prompt": "Hold the tight close-up on the intact fingertips resting on the wooden board. A sharp chef's knife blade enters from the upper left and slices into the index fingertip; the skin splits open and bright red blood wells up and runs onto the board. A sudden accidental cut.",
            },
            "control": {
                "start_frame": "frame control (mano limpia)", "end_frame": "frame control (mano limpia)",
                "motion_prompt": "Hold the tight close-up on the intact fingertips resting calmly on the wooden board. A chef's knife blade enters briefly from the upper left, rests near the board beside the hand and is lifted away again without ever cutting; the fingers stay intact and unharmed. A calm, safe, controlled movement, no injury, no blood.",
            },
        },
    }
    st.meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  meta {st.meta_path.relative_to(ROOT)}")

    # --- INDEX ---
    cols = ["id", "slug", "epss_pair", "categoria", "descripcion", "n_frames", "n_videos", "estado", "creado"]
    row = {"id": st.id, "slug": st.slug, "epss_pair": st.epss_pair,
           "categoria": st.categoria, "descripcion": st.descripcion,
           "n_frames": 3, "n_videos": 2, "estado": "completo", "creado": "2026-06-13"}
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerow(row)
    print(f"  index {INDEX.relative_to(ROOT)}")

    print("\nMigracion completa.")


if __name__ == "__main__":
    main()
