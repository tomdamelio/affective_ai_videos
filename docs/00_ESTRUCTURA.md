# 00 · Estructura del repositorio y convención de archivos

> **Fuente de verdad de la organización del proyecto.** Cómo está ordenado el repo, dónde
> escribe cada paso del pipeline, y cómo se nombran los archivos. Para *cómo se genera*
> cada estímulo ver [`PLAYBOOK_GENERACION.md`](PLAYBOOK_GENERACION.md); para la narrativa
> de Métodos ver [`methodology.md`](methodology.md).
>
> Última actualización: 2026-06-13 (reorganización: se deprecó la forma vieja S01–S32 y se
> sistematizó la forma actual EPSS).

---

## 1. Dos eras del proyecto

| | Forma **vieja** (pre-EPSS) | Forma **actual** (EPSS) |
|---|---|---|
| IDs | `S01…S32` | `E01…E18` |
| Origen | prompts libres / `ai_prompts.xlsx` | base validada **EPSS-Limb** (Meng et al. 2023) |
| Modelos | FLUX.2 [pro] + Edit | `flux/dev` (dolor) + `flux-kontext/dev` (derivar) + Kling (video) |
| Estado | **DEPRECADA** → vive en `_deprecated/` | **VIGENTE** |

Todo lo de la forma vieja se movió a **`_deprecated/`** (ver `_deprecated/README.md`) y está
en `.gitignore`. **No mezclar.** Nada del pipeline actual depende de `_deprecated/`.

---

## 2. Árbol del repositorio (forma actual)

```
affective_ai_videos/
├── .env                      # FAL_KEY (gitignored; lo carga stimulus.py solo)
├── .gitignore
├── README.md                 # overview del proyecto + pipeline
│
├── EPSS/                     # BASE FUENTE read-only (gitignored, pesada)
│   └── Empathy for Limb Pain Picture Database (EPSS-Limb)/   # <- la que se usa
│
├── analysis/                 # SELECCIÓN de estímulos (one-time, reproducible)
│   ├── epss_limb_pairs.csv            # todos los pares EPSS-Limb + métricas
│   ├── epss_limb_selection.csv        # screening + scoring
│   ├── epss_limb_roster.csv           # ROSTER definitivo E01–E18 (orden de producción)
│   ├── contact_sheets/  recheck/  shortlist/   # imágenes de apoyo (gitignored)
│
├── docs/                     # documentación (este archivo, playbook, métodos)
│   ├── 00_ESTRUCTURA.md       # ← estás acá
│   ├── PLAYBOOK_GENERACION.md # guía operativa paso a paso (QUICKSTART)
│   ├── methodology.md         # Métodos estilo paper
│   ├── 01_stimulus_selection.md … 05_validation.md
│   └── README.md              # índice de docs
│
├── scripts/                  # PIPELINE vigente (todos toman --id; ver §5)
│   ├── stimulus.py            # (lib) rutas y nombres canónicos — fuente de verdad
│   ├── new_stimulus.py  pilot_v1.py  derive_variant.py  finalize_frames.py
│   ├── run_videos.py  seal_endframe.py  extract_frames.py
│   ├── start_variants.py  align_start_look.py
│   ├── epss_*.py  inspect_epss.py     # selección EPSS
│   └── _archive/             # scripts de un solo uso de la era EPSS (tests, migración)
│
├── dataset/                  # ENTREGABLES FINALES (versionado en git)
│   ├── stimuli_index.csv     # 1 fila por estímulo (maestro)
│   ├── README.md
│   └── E0N_<slug>/           # un directorio por estímulo (ver §3)
│
├── work/                     # EXPLORACIÓN / pruebas (gitignored, NO entregable; ver §4)
│   └── E0N_<slug>/
│
└── _deprecated/              # forma vieja S01–S32 (gitignored; ver _deprecated/README.md)
```

**Regla de oro:** lo **definitivo** va en `dataset/`; **toda prueba** va en `work/`. Cada
estímulo tiene una carpeta espejo en ambos (`dataset/E0N_<slug>/` y `work/E0N_<slug>/`).

---

## 3. `dataset/E0N_<slug>/` — entregable de un estímulo

```
dataset/E02_lapiz_punzante_dorso/
├── images/                            # los 3 STILLS canónicos (misma resolución)
│   ├── E02_still_inicio.png
│   ├── E02_still_dolor.png
│   └── E02_still_control.png
├── frames/                            # FOTOGRAMAS extraídos de los videos
│   ├── E02_frame_dolor_1.png … _6.png
│   └── E02_frame_control_1.png … _6.png
├── videos/                            # los 2 videos finales
│   ├── E02_video_dolor.mp4
│   └── E02_video_control.mp4
└── E02_meta.json                      # procedencia: fuente EPSS, modelos, prompts, seeds, costo
```

**Los 3 stills (`images/`):**
- **inicio** = extremidad **limpia, SIN el objeto** → inicio compartido del que parten los
  dos videos (el objeto *entra* durante el clip).
- **dolor** = el objeto peligroso corta/quema/golpea **+ daño** (se genera PRIMERO, `flux/dev`).
- **control** = **edición Kontext del dolor**: el objeto peligroso **reemplazado por uno
  NEUTRO e inofensivo** en la *misma posición y ángulo*, sin daño (misma mano pixel-a-pixel).
  Contraste con dolor = *identidad del objeto (peligroso→neutro) + desenlace (daña→no daña)*,
  mismo layout espacial. **No** sale de un frame del video. (Detalle y racional en el PLAYBOOK §4.)

---

## 4. `work/E0N_<slug>/` — exploración (no entregable)

Set canónico de subcarpetas (las crea `stimulus.make_dirs()`):

| Subcarpeta | Qué guarda | Quién escribe |
|---|---|---|
| `candidates/` | variantes derivadas con Kontext (`control.jpg`, `clean.jpg`) | `derive_variant.py` |
| `selected/` | stills de **dolor** aprobados (`keep`) | `pilot_v1.py` |
| `deprecated/` | iteraciones descartadas | `pilot_v1.py drop` (manual) |
| `start_variants/` | tomas medias "antes" (opcional/raro) | `start_variants.py` |
| `contact_sheets/` | láminas de inspección | manual / scripts |
| `video_frames/` | frames a media-res de videos de prueba | inspección |
| `extras/` | variantes guardadas para **reuso futuro** (p. ej. un control "demasiado doloroso" que sirva como estímulo punzante más adelante) | manual |
| `ledger.json` | prompt + seed + modelo de **cada** generación de imagen | `pilot_v1.py` |

> `work/E01_corte_pepino/_legacy/` contiene restos de la migración del piloto al esquema
> `dataset/` (videos de prueba y JPGs originales); es específico de E01, no del esquema general.

---

## 5. Convención de nombres de archivo

Tres prefijos, **sin ambigüedad**:

| Patrón | Qué es | Dónde |
|---|---|---|
| `<id>_still_<inicio\|dolor\|control>.png` | los **3 stills** canónicos | `dataset/<id>/images/` |
| `<id>_frame_<dolor\|control>_<n>.png` | **fotograma** n extraído de un video | `dataset/<id>/frames/` |
| `<id>_video_<dolor\|control>.mp4` | los **2 videos** | `dataset/<id>/videos/` |

- **`still` ≠ `frame`.** "still" = imagen clave canónica; "frame" = fotograma de un video.
  (Antes ambos se llamaban `frame`; se renombró el 2026-06-13 para desambiguar.)
- `<id>` = `E01`, `E02`, … `<slug>` = descriptivo en `snake_case` (`corte_pepino`).
- En `work/` los nombres son libres (iteraciones): el `ledger.json` los rastrea. Lo único
  con nombre canónico estricto es `dataset/`.
- **No tocar paths/nombres a mano:** todos salen de `scripts/stimulus.py` (`st.image()`,
  `st.video()`, `st.frames_dir`, …). Si cambia la convención, se cambia ahí y se propaga.

---

## 6. Mapa del pipeline: qué script escribe qué

```
new_stimulus.py   → fila en dataset/stimuli_index.csv + carpetas dataset/ y work/
        │
pilot_v1.py       → work/<id>/{candidates,selected,deprecated}/  + ledger.json   (DOLOR, flux/dev)
        │
derive_variant.py → work/<id>/candidates/{control,clean}.jpg                     (Kontext)
        │
finalize_frames.py→ dataset/<id>/images/<id>_still_{inicio,dolor,control}.png    (iguala resolución)
        │
run_videos.py     → dataset/<id>/videos/<id>_video_{dolor,control}.mp4           (Kling)
   └─ llama seal_endframe.py → sella último frame = still + refresca dataset/<id>/frames/
        │
extract_frames.py → dataset/<id>/frames/<id>_frame_{cond}_<n>.png   (deliverable/inspección)
```

Referencia rápida de cada script: PLAYBOOK §6.

---

## 7. Entorno de ejecución

No hay `python` en el PATH. El pipeline corre sobre el env **micromamba `campeones`**:

```bash
ENV=/c/Users/au805392/micromamba/envs/campeones
run() { PYTHONIOENCODING=utf-8 PATH="$ENV:$ENV/Library/bin:$ENV/Scripts:$PATH" python.exe "$@"; }
run scripts/new_stimulus.py --id E03 ...
```

- `ffmpeg`/`ffprobe` están en el env `affective-fnirs`
  (`/c/Users/au805392/micromamba/envs/affective-fnirs/Library/bin/`); los usan
  `seal_endframe.py` / `extract_frames.py`.
- `FAL_KEY` se carga **sola** desde `./.env` al importar `stimulus.py` (no exportar).
- El setup viejo (`environment.yml` env `gen-ai`, `pyproject.toml`) está en `_deprecated/`.

---

## 8. Qué se versiona en git

| Se versiona | NO se versiona (gitignored) |
|---|---|
| `scripts/`, `docs/`, `analysis/*.csv` | `_deprecated/` (binarios viejos) |
| `dataset/` **metadatos**: `meta.json`, `stimuli_index.csv`, READMEs | `EPSS/` (base fuente pesada) |
| | `dataset/**/*.{mp4,png,jpg,jpeg}` (videos/stills/frames — pesados) |
| | `work/` (exploración) |
| | `.env` (secreto), `analysis/{contact_sheets,recheck,shortlist}/` |

> **Binarios del entregable NO se versionan** (decisión 2026-06-13): los videos, stills y
> frames de `dataset/` quedan **gitignored** para no inflar el repo de GitHub. En git solo
> vive la **procedencia** (`meta.json` con prompts/seeds/modelos + `stimuli_index.csv`), que
> permite **regenerar** cualquier estímulo. Los binarios los respalda OneDrive.

OneDrive respalda **todo** (incluido lo gitignored) por la ruta del repo.

---

## 9. Política NO-OVERWRITE (nunca se pisa ni se borra un artefacto)

**Regla (decidida 2026-06-14):** ningún archivo ya generado —imagen, video o frame—
se sobrescribe ni se borra jamás. Cada generación cuesta plata y tiempo; un archivo
pisado es un recurso perdido. Antes de escribir una salida que **ya existe**, el
pipeline la **archiva** automáticamente en un `_archive/` al lado, versionada
(`<stem>__v01`, `__v02`, …). Nada se elimina; las versiones viejas quedan disponibles.

- **Mecanismo:** `stimulus.archive_if_exists(path)` mueve el archivo existente a
  `<dir>/_archive/<stem>__vNN<ext>` antes de cada escritura. Lo llaman **todos** los
  scripts que escriben: `run_videos.py` (videos), `seal_endframe.py` (frames — antes
  hacía `unlink()` y por eso se perdían frames de corridas previas), `finalize_frames.py`
  (stills), `derive_variant.py` y `pilot_v1.py` (candidatos de imagen).
- **Dónde aparecen los `_archive/`:** `dataset/<id>/{videos,images,frames}/_archive/`,
  `work/<id>/candidates/_archive/`, etc. Quedan **gitignored** (los binarios de
  `dataset/` y todo `work/` ya lo están) y los respalda OneDrive.
- **Comandos ad-hoc (ffmpeg/cp/extracciones manuales):** misma regla — usar nombres
  únicos por corrida y **nunca** `rm -f`/`mv` que pise; si hace falta limpiar, mover a
  `_archive/`. Si un frame intermedio de un video sirve, **copiarlo a un nombre estable
  antes** del siguiente render (que refresca `frames/`).

---

## 10. Pipeline seguro para sesiones en paralelo

Para generar varios estímulos a la vez (varias ventanas de Claude sobre el MISMO repo),
el pipeline evita que las sesiones se pisen:

- **Motion prompts por estímulo:** `run_videos.py` lee los prompts de movimiento de
  `work/<id>/motion.json` (`{"dolor": …, "control": …}`) vía `load_motion()`. Cada sesión
  edita SU propio `motion.json` y **no** toca `run_videos.py` (el dict `MOTION` del script
  quedó solo como fallback/template). Antes `MOTION` era global y dos sesiones se pisaban.
- **Index con lock:** las escrituras a `stimuli_index.csv` (alta de fila en
  `new_stimulus.py`, `n_images` en `finalize_frames.py`, `n_videos`/`estado` en
  `run_videos.py`) pasan por `stimulus.add_index_row` / `update_index_fields`, que toman un
  lock de archivo atómico (`stimuli_index.csv.lock`, gitignored) y serializan el
  read-modify-write. Evita perder filas por la race de concurrencia.
- **Regla operativa:** cada sesión trabaja UN estímulo y solo toca `work/<id>/` y
  `dataset/<id>/` de SU id. El único archivo compartido que puede tocar es el index (ya
  protegido por lock) — **nunca** editar `run_videos.py`/`stimulus.py` desde una sesión de
  generación. Combinar con la política NO-OVERWRITE (§9).
