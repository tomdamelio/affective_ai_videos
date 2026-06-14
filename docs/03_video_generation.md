# Fase 3 — Interpolación a video (detalle operativo)

> Complementa la sección *Pipeline de generación* (Fase 3) de [`methodology.md`](methodology.md).
> Fuentes: `scripts/generate_video.py`, `ai_prompts.xlsx` (hoja `image-to-video`), `videos/`.

## Esquema

Cada par seleccionado produce **dos videos** a partir de su triplete de keyframes:

| Video | Keyframes | Prompt de movimiento (estilo) |
|---|---|---|
| **Dolor** | `t_start → t_end_P` | Dinámica súbita y visceral (p. ej., "Fast slam impact", "Hammer strike impact") |
| **Control** | `t_start → t_end_C` | Dinámica lenta y controlada (p. ej., "Slow closing, stops safe", "Hammer lowers gently") |

Al compartir `t_start`, ambos videos de un par son idénticos en su fotograma inicial y solo divergen al desplegarse la acción.

## Modelo y parámetros actuales (piloto)

- **Endpoint:** `fal-ai/kling-video/v3/pro/image-to-video` (Kling v3 Pro, modo first-frame → last-frame).
- **Parámetros** (`generate_video.py`):
  - `duration: "5"` (la API admite 5 o 10 s)
  - `aspect_ratio: "16:9"`
  - `generate_audio: false`
  - `cfg_scale: 0.5`
  - `negative_prompt: "blur, distort, low quality, warped, deformed"`
  - Nota: el script pasa `safety_tolerance: 6`, parámetro no documentado en el schema de Kling — probablemente ignorado por el endpoint. TODO: limpiar o verificar.
- **Registro:** hoja `image-to-video` de `ai_prompts.xlsx` (`Video_Unique_ID`, keyframes de entrada, `Motion_Prompt`, `Final_Video_URL`). Videos del piloto pre-EPSS en `videos/` (`video_SNN_{Pain|C}.mp4`).

## Decisiones pendientes

- `[PENDIENTE]` **Duración definitiva** (5 vs. 10 s). El diseño experimental pide ~5–10 s; evaluar si 5 s alcanzan para que la acción de Control se lea como "lenta y segura" sin ambigüedad.
- `[PENDIENTE]` **A/B Kling v3 Pro vs. Kling O1** (`fal-ai/kling-video/o1/image-to-video`), modelo específico para interpolación primer→último fotograma. Criterios del A/B: fidelidad al keyframe final, ausencia de morphing en la extremidad, naturalidad de la trayectoria del objeto, costo por video.
- `[PENDIENTE]` **Criterios de aceptación del video**: continuidad de identidad de la extremidad, sin objetos que aparecen/desaparecen, sin "rebote" tras el impacto, timing de la divergencia Dolor/Control comparable entre pares (relevante para el análisis time-locked de respuestas fisiológicas).
- `[PENDIENTE]` **Moderación de Kling** sobre prompts de impacto ("visceral impact"): no se observó rechazo en el piloto pre-EPSS, pero debe re-verificarse con los estímulos EPSS y la redacción actual (ver [`04_content_moderation.md`](04_content_moderation.md)).
- `[PENDIENTE]` **Costo por par** (video Dolor + video Control + regeneraciones): medirlo en el piloto EPSS (~3–5 pares) antes del batch; insumo para la reunión de selección final.
- TODO: estandarizar nomenclatura de salida para el set EPSS (p. ej., `parNN_nombre_{pain|ctrl}.mp4`) y carpeta destino (`videos/epss/`).
- TODO: especificaciones técnicas de entrega a PsychoPy (códec, resolución, fps, contenedor) acordadas con DI.
