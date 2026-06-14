# Documentación metodológica

Documento vivo con la metodología del proyecto **Generación de estímulos dinámicos de dolor mediante IA generativa**, redactada en formato de sección de Métodos de un paper científico. El modelo de formato y rigor es Behnke et al. (2026), que hace lo análogo para imágenes estáticas.

## Estructura

| Archivo | Contenido |
|---|---|
| [`00_ESTRUCTURA.md`](00_ESTRUCTURA.md) | **Estructura del repo y convención de archivos.** Cómo está ordenado todo, dónde escribe cada paso, cómo se nombran los archivos, entorno y qué se versiona. Empezar por acá. |
| [`PLAYBOOK_GENERACION.md`](PLAYBOOK_GENERACION.md) | **Guía operativa** paso a paso (QUICKSTART) para generar un estímulo nuevo. Fuente de verdad del *cómo*. |
| [`methodology.md`](methodology.md) | **Texto principal de Métodos** (narrativa integrada, estilo paper). Es el documento que eventualmente se traduce/adapta al manuscrito. |
| [`01_stimulus_selection.md`](01_stimulus_selection.md) | Detalle operativo de la Fase A: normas EPSS-Limb, métricas, screening visual, shortlist y exclusiones. |
| [`02_image_generation.md`](02_image_generation.md) | Detalle de Fases 1–2 del pipeline: extracción de ground truth (VLM) y síntesis de keyframes (FLUX.2). Prompts y parámetros. |
| [`03_video_generation.md`](03_video_generation.md) | Detalle de Fase 3: interpolación a video (Kling). Parámetros y decisiones pendientes. |
| [`04_content_moderation.md`](04_content_moderation.md) | Consideraciones de moderación de contenido (filtro de salida vs. filtro de entrada) y su impacto en el diseño de prompts y de estímulos. |
| [`05_validation.md`](05_validation.md) | Plan de validación experimental del set. **[PENDIENTE — esqueleto]** |

## Convenciones para iterar

- Las partes no definidas o no validadas se marcan con **`[PENDIENTE]`** (decisión abierta) o **`TODO:`** (tarea concreta). Buscar `PENDIENTE\|TODO` antes de cada iteración.
- `methodology.md` mantiene el tono de paper; los archivos numerados pueden ser más operativos (tablas, parámetros exactos, rutas de scripts). Cuando un detalle madura, se sube resumido al texto principal.
- Las cifras (n de pares, costos, parámetros) deben poder rastrearse a un script u output del repo; cada sección indica su fuente (`scripts/...`, `analysis/...`, `ai_prompts.xlsx`).
- Idioma: borrador en español para discusión interna (Mariana/Daniela); la traducción al inglés se hace recién al armar el manuscrito. TODO: traducir al cerrar el set.
