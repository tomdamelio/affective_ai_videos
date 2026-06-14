# Dataset de estímulos (dolor / control)

Entregables finales del proyecto de generación de estímulos con IA. **Solo lo definitivo
vive acá**; toda la exploración y las pruebas van en [`../work/`](../work/). Para *cómo* se
generan ver [`../docs/PLAYBOOK_GENERACION.md`](../docs/PLAYBOOK_GENERACION.md); para la
estructura y la convención de nombres ver
[`../docs/00_ESTRUCTURA.md`](../docs/00_ESTRUCTURA.md).

## Convención

- **ID secuencial** `E01`, `E02`, … + **slug** descriptivo → `E01_corte_pepino/`.
- El mapeo a la fuente (par EPSS) y la categoría están en `stimuli_index.csv` y en el
  `E0N_meta.json` de cada estímulo.
- Nombres de archivo (detalle en `00_ESTRUCTURA.md §5`):
  - `E0N_still_<inicio|dolor|control>.png` — los 3 **stills** canónicos (`images/`).
  - `E0N_frame_<dolor|control>_<n>.png` — **fotogramas** extraídos de los videos (`frames/`).
  - `E0N_video_<dolor|control>.mp4` — los 2 videos (`videos/`).

```
dataset/
  stimuli_index.csv                 <- 1 fila por estímulo (maestro)
  E01_corte_pepino/
    images/                         <- 3 STILLS canónicos (misma resolución)
      E01_still_inicio.png          <- mano limpia SIN el objeto (inicio compartido)
      E01_still_dolor.png           <- el objeto corta/quema/golpea + daño
      E01_still_control.png         <- objeto peligroso REEMPLAZADO por uno neutro, sin daño
    frames/                         <- fotogramas extraídos de los videos
      E01_frame_dolor_1..6.png
      E01_frame_control_1..6.png
    videos/
      E01_video_dolor.mp4           <- inicio → el objeto entra y DAÑA
      E01_video_control.mp4         <- inicio → un objeto neutro entra y NO daña
    E01_meta.json                   <- fuente EPSS, modelos, prompts, seeds, costo
```

## Los 3 stills (`images/`)

- **inicio** = extremidad limpia, **sin el objeto** → es el **inicio compartido** del que
  parten los dos videos (el objeto *entra* durante el clip).
- **dolor** = el objeto peligroso corta/quema/golpea, con daño. Se genera **primero**
  (`flux/dev`); es el ancla del que se derivan los otros dos.
- **control** = **edición Kontext del dolor**: el objeto peligroso **reemplazado por uno
  NEUTRO e inofensivo** en la *misma posición y ángulo*, con el daño removido y la mano en
  la **posición exacta**. Contraste con dolor = *identidad del objeto (peligroso→neutro) +
  desenlace (daña→no daña)*, mismo layout espacial. **No** sale de un frame del video.
  (Ej. E02: el cigarrillo encendido → un lápiz dado vuelta con la goma de borrar apoyada.)

> El objeto neutro debe leerse como **claramente no doloroso**: usar el extremo
> **romo/blando**, no una punta sobre la piel. Racional completo en el PLAYBOOK §4.

`frames/` son las secuencias extraídas de los dos videos (inspección/deliverable).
`videos/` son los 2 videos finales (Kling v3 Pro, ~5 s, sin audio). `E0N_meta.json` tiene
todo lo necesario para reproducir.

## Exploración (en `../work/E0N_<slug>/`)

Las pruebas NO van acá. Cada estímulo tiene su carpeta espejo en `work/`: `candidates/`,
`selected/`, `deprecated/`, `start_variants/`, `contact_sheets/`, `video_frames/`,
`extras/`, y `ledger.json` (ver `00_ESTRUCTURA.md §4`).

## Estado actual

| ID | slug | par EPSS | categoría | estado |
|----|------|----------|-----------|--------|
| E01 | corte_pepino | 3 | corte | completo (3 stills + 2 videos) |
| E02 | lapiz_punzante_dorso | 50* | punzante | completo (3 stills + 2 videos) |

> \* E02 nació anclado al par 50 (cigarrillo quema el dorso) pero se **re-definió**
> (2026-06-13) a un **lápiz** con la punta presionando el dorso (punzante); ya **no** es un
> render fiel del par 50. Contraste = el mismo lápiz invertido (punta=dolor vs goma=control).
> La versión del cigarrillo se conserva en `../work/E02_lapiz_punzante_dorso/extras/`.
> Se mantiene **vinculado al par 50** por ahora, pero **cuenta como punzante** en la
> estratificación. Pendiente (diferido): rebalanceo de cuota (sumar una quemadura).

(Ver `stimuli_index.csv` para la versión maestra y `analysis/epss_limb_roster.csv` para el
roster E01–E18 completo.)
