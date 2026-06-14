"""Fuente unica de verdad para la estructura de datos de estimulos.

Convencion (decidida 2026-06-13):

  dataset/                     <- SOLO entregables finales
    stimuli_index.csv          <- 1 fila por estimulo
    E01_corte_pepino/
      images/  E01_still_inicio.png  E01_still_dolor.png  E01_still_control.png  (3 stills)
      frames/  E01_frame_dolor_1..6.png  E01_frame_control_1..6.png  (fotogramas de los videos)
      videos/  E01_video_dolor.mp4   E01_video_control.mp4
      E01_meta.json

Nomenclatura de archivos (convencion 2026-06-13):
  <id>_still_<inicio|dolor|control>.png   <- los 3 STILLS canonicos (images/)
  <id>_frame_<dolor|control>_<n>.png      <- FOTOGRAMAS extraidos de cada video (frames/)
  <id>_video_<dolor|control>.mp4          <- los 2 videos (videos/)
("still" = imagen clave canonica; "frame" = fotograma de un video. No confundir.)
  work/                        <- exploracion / pruebas (no entregable)
    E01_corte_pepino/
      candidates/  deprecated/  start_variants/  contact_sheets/  video_frames/  ledger.json

Stills canonicos (`images/`): dolor = la extremidad con el objeto + dano (se genera
PRIMERO, flux/dev); control = edicion Kontext del dolor con el objeto peligroso
REEMPLAZADO por uno NEUTRO e inofensivo en su misma posicion, sin dano (misma
mano/posicion exacta); inicio = extremidad limpia sin el objeto (inicio compartido del
video, del que el objeto entra). El control NO sale de un frame del video. Las
secuencias de video van en `frames/`.

ID secuencial E01, E02, ...  +  slug descriptivo.

Uso en un script:
    from stimulus import get_stim, active
    st = get_stim("E01")
    st.image("dolor")                 # dataset/E01_.../images/E01_still_dolor.png
    st.video("control")               # dataset/E01_.../videos/E01_video_control.mp4
    st.frames_dir                     # dataset/E01_.../frames/ (frames de video)
    st.candidates                     # work/E01_.../candidates/
"""
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"
WORK = ROOT / "work"
INDEX = DATASET / "stimuli_index.csv"


def _load_dotenv() -> None:
    """Carga <ROOT>/.env en os.environ (KEY=VALUE) si la var no esta ya seteada.

    Parser propio (sin dependencias). Asi los scripts toman FAL_KEY del .env del
    proyecto sin tener que exportarla en cada shell. El .env esta en .gitignore.
    """
    envf = ROOT / ".env"
    if not envf.exists():
        return
    for line in envf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()

STILLS = ("inicio", "dolor", "control")
CONDITIONS = ("dolor", "control")


class Stim:
    def __init__(self, sid: str, slug: str, epss_pair=None, categoria=None, descripcion=None):
        self.id = sid
        self.slug = slug
        self.epss_pair = epss_pair
        self.categoria = categoria
        self.descripcion = descripcion
        self.name = f"{sid}_{slug}"

    # --- dataset (final) ---
    @property
    def dataset(self) -> Path:
        return DATASET / self.name

    @property
    def images_dir(self) -> Path:
        return self.dataset / "images"

    @property
    def frames_dir(self) -> Path:
        return self.dataset / "frames"

    @property
    def videos_dir(self) -> Path:
        return self.dataset / "videos"

    @property
    def meta_path(self) -> Path:
        return self.dataset / f"{self.id}_meta.json"

    def image(self, which: str) -> Path:
        assert which in STILLS, which
        return self.images_dir / f"{self.id}_still_{which}.png"

    def video(self, which: str) -> Path:
        assert which in CONDITIONS, which
        return self.videos_dir / f"{self.id}_video_{which}.mp4"

    # --- work (exploracion) ---
    @property
    def work(self) -> Path:
        return WORK / self.name

    @property
    def candidates(self) -> Path:
        return self.work / "candidates"

    @property
    def selected(self) -> Path:
        return self.work / "selected"

    @property
    def deprecated(self) -> Path:
        return self.work / "deprecated"

    @property
    def start_variants(self) -> Path:
        return self.work / "start_variants"

    @property
    def contact_sheets(self) -> Path:
        return self.work / "contact_sheets"

    @property
    def ledger(self) -> Path:
        return self.work / "ledger.json"

    @property
    def video_frames(self) -> Path:
        return self.work / "video_frames"

    @property
    def extras(self) -> Path:
        """Variantes guardadas para reuso futuro (p. ej. un control 'demasiado
        doloroso' que sirve como posible estimulo punzante mas adelante)."""
        return self.work / "extras"

    def make_dirs(self) -> None:
        for d in (self.images_dir, self.frames_dir, self.videos_dir,
                  self.candidates, self.selected, self.deprecated,
                  self.start_variants, self.contact_sheets, self.video_frames,
                  self.extras):
            d.mkdir(parents=True, exist_ok=True)


def _load_rows() -> list[dict]:
    if not INDEX.exists():
        return []
    with open(INDEX, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_stim(sid: str) -> Stim:
    for r in _load_rows():
        if r["id"] == sid:
            return Stim(r["id"], r["slug"], r.get("epss_pair") or None,
                        r.get("categoria") or None, r.get("descripcion") or None)
    raise KeyError(f"Estimulo no encontrado en {INDEX}: {sid}")


def active() -> Stim:
    """Ultimo estimulo del index (el que se esta trabajando)."""
    rows = _load_rows()
    if not rows:
        raise RuntimeError("stimuli_index.csv vacio")
    r = rows[-1]
    return Stim(r["id"], r["slug"], r.get("epss_pair") or None,
                r.get("categoria") or None, r.get("descripcion") or None)


def all_stims() -> list[Stim]:
    return [Stim(r["id"], r["slug"], r.get("epss_pair") or None,
                 r.get("categoria") or None, r.get("descripcion") or None)
            for r in _load_rows()]
