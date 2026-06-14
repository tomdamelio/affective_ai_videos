# Fases 1–2 — De la imagen EPSS a los keyframes (detalle operativo)

> Complementa la sección *Pipeline de generación* (Fases 1 y 2) de [`methodology.md`](methodology.md).
> Fuentes: `ai_prompts.xlsx` (hojas `system-prompt`, `image-to-text`, `text-to-image`), `src/pain_stimuli/generator.py`, `scripts/pilot_epss_keyframes.py`, `img/pilot_epss/`.

## Esquema de keyframes

Cada par seleccionado produce un **triplete de keyframes** que comparten escena, encuadre e identidad:

| Keyframe | Rol | Derivación |
|---|---|---|
| `t_end_P` | Estado final **Dolor** (*master anchor*) | Generado primero; fija fondo, iluminación e identidad |
| `t_end_C` | Estado final **Control** | Editado (Kontext) desde el anchor de dolor: el objeto peligroso **reemplazado por uno neutro inofensivo** (extremo romo/blando) en su misma posición/ángulo, sin daño. Misma mano/posición exacta |
| `t_start` | Estado **inicial compartido** | Editado (Kontext) desde el anchor de dolor: extremidad limpia **sin el objeto** (el objeto *entra* durante el video) |

El orden (dolor primero, derivación inversa) responde a que el estado doloroso es el más difícil de generar; condicionar las variantes en él garantiza el apareamiento visual.

## Fase 1 — Ground truth semántico (VLM)

- **Modelo:** Gemini 3 (VLM), con system prompt estructurado (rol "Computer Vision Analyst"; texto completo en `ai_prompts.xlsx`, hoja `system-prompt`).
- **Reglas del system prompt:** (1) anonimización (sin edad/género del actor original; referirse a la parte del cuerpo); (2) acción y física — en Dolor, impacto anatómico específico con verbos viscerales ("crushing", "piercing"); en Control, descripción explícita de la ausencia de daño ("resting gently", "safe distance"); (3) detalle material del objeto; (4) iluminación y fondo. La salida comienza directamente con la parte del cuerpo, para concatenarse tras una plantilla demográfica ("A [AGE] [GENDER]…") controlada por el investigador.
- **Derivación de t_start:** instrucción adicional al LLM ("describir el estado *antes* de la acción, objeto en posición neutra/idle, mismo objeto e iluminación") aplicada sobre la descripción de Control. Registro en hoja `image-to-text` (`Stim_Base_ID`, `Source_File`, `LLM_Task_Instruction`, `Generated_Description`).

Nota histórica: este flujo se desarrolló sobre el piloto previo al pivote a EPSS (escenarios S01–S32, derivados de otra base). `[PENDIENTE]` Decidir si para el batch EPSS definitivo la Fase 1 se re-ejecuta formalmente sobre las imágenes EPSS-Limb seleccionadas, o si los prompts se redactan manualmente anclados en la imagen (como en el piloto `pilot_epss_keyframes.py`, donde la imagen EPSS entra directamente como condición visual del modelo de edición y el prompt fue escrito a mano). En cualquier caso, documentar la procedencia de cada prompt por estímulo.

## Fase 2 — Síntesis con FLUX.2 (Fal.ai)

### Modelos y parámetros

| Paso | Endpoint | Parámetros clave |
|---|---|---|
| Master anchor (t_end_P) | `fal-ai/flux-2-pro/edit` condicionado en la imagen EPSS (`N.2` como data URI) — flujo del piloto EPSS. Alternativa text-to-image pura: `fal-ai/flux-2-pro` (flujo S01–S32) | `image_size: landscape_16_9`, `seed: 1001`, `output_format: jpeg` |
| Variantes (t_start, t_end_C) | `fal-ai/flux-2-pro/edit` condicionado en el master anchor | `image_size: auto` (conserva el del master), misma seed |
| Ambos | — | `enable_safety_checker: false`, `safety_tolerance: "5"` (ver [`04_content_moderation.md`](04_content_moderation.md)) |

- FLUX.2 [pro] es "zero-config": no expone `num_inference_steps` ni `guidance_scale`.
- Costo: ~USD 0.03 por imagen (primer megapíxel) ⇒ ~USD 0.09 por triplete, sin contar regeneraciones.
- Estilo fotográfico común inyectado en el prompt del master (piloto EPSS): fotografía fotorrealista, luz natural, piel y anatomía realistas, poca profundidad de campo, escena cotidiana "vivida" (no estudio).

### Estructura de los prompts (piloto EPSS, `pilot_epss_keyframes.py`)

- **Master:** "Recreate this exact scene as a photorealistic photograph in a real [entorno]: [acción + amenaza/daño]. Keep the same camera angle, hand positions and action as the reference image." + bloque de estilo. ⚠️ La redacción del componente de daño está restringida por la moderación de entrada (ver `04_content_moderation.md`): formato "amenaza inminente, piel intacta, sin sangre".
- **Control:** **reemplaza el objeto peligroso por uno neutro e inofensivo** en la misma posición/ángulo + elimina todo signo de daño + "Keep the hand in the exact same position, same camera angle, background and lighting." El objeto neutro debe leerse como claramente no doloroso —extremo romo/blando, no una punta sobre la piel (p. ej. en E02, un lápiz invertido con la goma de borrar apoyada). Liderar con el reemplazo (*"replace the X with a harmless Y in the EXACT same position…"*). No reubicar el objeto a un costado (la edición que *mueve* lo duplica; la que *reemplaza en su lugar* es fiable).
- **Start:** misma extremidad limpia, **sin el objeto**, instante previo a la acción + misma cláusula de invariancia. (El objeto entra durante el video.)

### Reproducibilidad y registro

- Semilla fija `1001` (variantes con seeds incrementales en el flujo batch `generate_ref_img.py`).
- Prompts y metadatos registrados en `ai_prompts.xlsx` (hoja `text-to-image`: `Unique_Img_ID`, `Scenario`, `Perspective`, `Condition`, `Frame_Type`, `Gender`, `Age`, `Seed`, `AUTO_PROMPT`, `Output_URL`) y en `img/pilot_epss/prompts_log.json`.
- Nomenclatura de archivos del piloto EPSS: `parNN_nombre_{endP|endC|start}.jpg`.

### Pendientes

- `[PENDIENTE]` Criterio formal de aceptación/regeneración de keyframes (checklist: anatomía correcta, invariancia de fondo entre triplete, ausencia de artefactos; nº máx. de reintentos; registro de descartes).
- `[PENDIENTE]` Resolución/upscaling final para presentación (los keyframes salen 16:9 ~1 MP; definir si alcanza para PsychoPy o se interpone un upscaler).
- TODO: actualizar la tabla `ai_prompts.xlsx` (hoy poblada con los escenarios obsoletos S01–S32) al set EPSS definitivo, o reemplazarla por un registro por-par derivado de `prompts_log.json`.
