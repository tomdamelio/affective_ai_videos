# Moderación de contenido (detalle técnico)

> Complementa la sección *Consideraciones técnicas: moderación de contenido* de [`methodology.md`](methodology.md).
> Fuentes: `scripts/test_safety_filter.py`, `scripts/control_test_jan_method.py`, `src/pain_stimuli/generator.py`, `img/pilot_epss/`.

## Dos filtros independientes

| | Filtro de **salida** | Filtro de **entrada** |
|---|---|---|
| Qué inspecciona | La **imagen generada** (clasificador NSFW) | El **prompt** (y/o la imagen de referencia) antes de generar |
| Control por API | Sí: `enable_safety_checker` (bool) + `safety_tolerance` (`"1"`–`"5"`) | **No** — ningún parámetro lo modifica |
| Comportamiento al activarse | Marca/bloquea la imagen producida (`has_nsfw_concepts`) | `HTTP 422` con `content_policy_violation`; la generación nunca ocurre (y no se cobra) |
| Configuración del proyecto | Desactivado: `enable_safety_checker: false`, `safety_tolerance: "5"` | Se gestiona vía redacción del prompt |

Implicancia: desactivar el safety checker **no** habilita prompts explícitos de herida. Son capas separadas; toda la estrategia de prompts debe diseñarse para atravesar el filtro de entrada.

## Cronología del endurecimiento (evidencia)

- **Enero 2026:** prompts text-to-image con redacción clínica explícita ("a clean, shallow cut is visible, with only a small, single bead of bright red blood…") generaban correctamente en `fal-ai/flux-2-pro` (escenarios S01–S32).
- **2026-06-12:** los mismos prompts (reproducción exacta del método de enero, `scripts/control_test_jan_method.py`) devuelven `422 content_policy_violation`. También fallan variantes "suavizadas" con sangre mínima (`scripts/test_safety_filter.py`, prompts `GRAFICO` y `SUAVE`).
- Conclusión: **regresión del proveedor** (Fal/Black Forest Labs endureció la moderación de entrada de los endpoints FLUX.2 [pro] entre enero y junio de 2026), no un error de configuración local. Es exactamente el riesgo de "censura de dolor" por el que se había descartado Google/Nano Banana, materializado en FLUX.

## Estrategia adoptada: "amenaza inminente, sin herida"

Redacción del estado final doloroso como el **instante inmediatamente anterior al daño**: el objeto en contacto/presión peligrosa con la piel **intacta**, musculatura tensa, **sin sangre ni herida visible**.

- Estado: **PASA** la moderación (HTTP 200) y produce salida fotorrealista de calidad (primer éxito: `img/pilot_epss/imminent_par03_threat.jpg`).
- Justificación convergente: (a) muchas imágenes de dolor de EPSS-Limb ya representan el momento de contacto/amenaza, no la lesión consumada; (b) la anticipación del daño es un elicitador potente en la literatura de empatía por dolor; (c) para video, el formato amenaza→casi-impacto conserva la estructura temporal inicio→fin.
- Costo: la composición requiere iteración de prompts (en la primera generación la posición del cuchillo se leía ambigua).
- `[PENDIENTE]` **Aprobación de la IP**: pasar de estímulos "daño visible" a "amenaza inminente" es un cambio de diseño (constructo: dolor observado vs. dolor anticipado), no solo de redacción.
- `[PENDIENTE]` Verificar par por par de la shortlist que la versión "amenaza" siga siendo discriminable del Control (el Control también es "sin daño"; la diferencia debe sostenerse en proximidad/contacto/tensión).

## Reglas de redacción derivadas (para todos los prompts FLUX.2 [pro])

1. Sin léxico de herida consumada: evitar "cut", "wound", "bleeding", "blood", "pierced", "crushed" referidos a tejido.
2. Describir amenaza y contacto: "blade pressing against the skin", "in direct contact", "high-threat moment", "muscles tense", "skin intact".
3. Mantener el detalle material del objeto y la cláusula de invariancia de escena (ver [`02_image_generation.md`](02_image_generation.md)).
4. No intentar derrotar el filtro con reformulaciones del mismo contenido explícito: además de inestable, ese contenido puede regenerarse en cualquier endurecimiento futuro y romper la reproducibilidad del método.

## Planes de contingencia (no probados)

- **B — Pesos abiertos:** `fal-ai/flux/dev` (modelo original del repo): `enable_safety_checker: false` desactiva genuinamente el filtrado y no habría moderación de entrada; menor calidad de imagen.
- **C — Otro proveedor / auto-alojamiento** de un modelo abierto.
- `[PENDIENTE]` Moderación de **Kling** (video): sin datos con los estímulos EPSS; re-verificar antes del batch.

## Nota para el manuscrito

Reportar esta restricción como limitación/condición de reproducibilidad del método: los pipelines de estímulos aversivos sobre APIs comerciales dependen de políticas de moderación que cambian sin aviso ni versionado. Recomendación replicable: registrar fecha, endpoint y redacción exacta de cada generación (como hace este repo en `prompts_log.json` / `ai_prompts.xlsx`).
