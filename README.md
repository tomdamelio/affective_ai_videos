# Generación de estímulos dinámicos de dolor mediante IA generativa

Código y documentación para generar un set estandarizado de **estímulos de video
dolor-vs-control** para estudios de procesamiento afectivo, con IA generativa, a partir de
una base validada. El objetivo: pares (Dolor / Control) donde lo único que varía es la
interacción dolorosa, manteniendo idénticos fondo, iluminación, anatomía y contexto.

> **Nota de organización (2026-06):** el proyecto pivoteó de un primer enfoque
> (`S01–S32`, prompts libres) a la forma actual basada en **EPSS-Limb**. Todo lo del
> enfoque viejo se movió a [`_deprecated/`](_deprecated/README.md) y no se usa.
> **Empezá por [`docs/00_ESTRUCTURA.md`](docs/00_ESTRUCTURA.md).**

## Qué se produce

Set comprometido: **18 estímulos** `E01…E18` seleccionados sistemáticamente de la base
**EPSS-Limb** (Meng et al. 2023, CC BY 4.0). Cada estímulo =

- **3 stills** (`inicio`, `dolor`, `control`) — `dataset/E0N_<slug>/images/`
- **2 videos** de ~5 s (`dolor`, `control`) — `dataset/E0N_<slug>/videos/`
- `meta.json` con procedencia completa (fuente EPSS, modelos, prompts, seeds, costo).

> La manipulación de **perspectiva** (propia vs. ajena) **no** se genera como videos
> distintos: se induce en PsychoPy con instrucción + un **borde de color (azul/amarillo)**
> sobre el mismo video. Por eso el entregable son videos únicos por estímulo, no el doble.

## Pipeline (resumen)

El estímulo se construye **a partir de la imagen de DOLOR** (único paso "desde cero"); el
control y el inicio se **derivan de ella con edición local (Kontext)** para garantizar que
la mano/posición queden idénticas:

1. **Selección** — `analysis/epss_limb_roster.csv` fija el orden `E01…E18` (ver `docs/01_stimulus_selection.md`).
2. **Dolor** (`flux/dev`, sin moderación de entrada) — primer y único paso text→image.
3. **Control e Inicio** (`flux-kontext/dev`) — derivados del dolor: el control reemplaza el
   objeto peligroso por uno **neutro e inofensivo** en la misma posición; el inicio quita el objeto.
4. **Videos** (Kling v3 Pro, image-to-video, `inicio → dolor/control`) — el último frame se
   *sella* con el still exacto.

| Modelo | Para qué |
|---|---|
| `fal-ai/flux/dev` | dolor explícito (open-weights, sin filtro de entrada) |
| `fal-ai/flux-kontext/dev` | derivar control/inicio (edición local conservando encuadre) |
| `fal-ai/kling-video/v3/pro/image-to-video` | videos inicio→fin |

> Los endpoints `flux-2-pro*` se descartan: su filtro de **entrada** bloquea daño/sangre y
> no se desactiva (ver `docs/04_content_moderation.md`).

**Guía operativa completa: [`docs/PLAYBOOK_GENERACION.md`](docs/PLAYBOOK_GENERACION.md).**

## Estructura del repositorio

Detalle y convención de nombres en **[`docs/00_ESTRUCTURA.md`](docs/00_ESTRUCTURA.md)**. En corto:

```
EPSS/        base fuente (read-only)        scripts/     pipeline (todos --id; lib: stimulus.py)
analysis/    selección E01–E18              dataset/     ENTREGABLES finales (E0N_<slug>/)
docs/        documentación                  work/        exploración / pruebas (no entregable)
_deprecated/ forma vieja S01–S32 (no usar)
```

## Entorno

No hay `python` en el PATH; el pipeline corre sobre el env micromamba **`campeones`**
(`ffmpeg` en `affective-fnirs`). `FAL_KEY` se carga sola desde `./.env`. Detalle en
`docs/00_ESTRUCTURA.md §7`.

```bash
ENV=/c/Users/au805392/micromamba/envs/campeones
run() { PYTHONIOENCODING=utf-8 PATH="$ENV:$ENV/Library/bin:$ENV/Scripts:$PATH" python.exe "$@"; }
run scripts/new_stimulus.py --id E03 --slug <slug> --epss <par> --categoria <cat> --descripcion "<...>"
```

## Estado

- [x] Pivote a EPSS-Limb + selección sistemática `E01–E18` (`analysis/epss_limb_roster.csv`).
- [x] Pipeline reproducible (scripts `--id`, `stimulus.py` como fuente de rutas/nombres).
- [x] **E01** (corte de pepino) y **E02** (quemadura de cigarrillo) completos.
- [ ] Checkpoint con Mariana/Daniela validando E01–E02 antes de producir el set completo.
- [ ] Generar E03–E18.
- [ ] Validación experimental del set.

---
*Investigación en curso sobre procesamiento afectivo y dolor (Tomás D'Amelio; PI Mariana;
colab. Daniela). Estándares adaptados de Behnke et al. (2025/2026) para video.*
