# Métodos

> **Documento vivo** (última actualización: 2026-06-12). Las decisiones abiertas están marcadas con `[PENDIENTE]` y las tareas con `TODO`. El detalle operativo de cada sección está en los archivos numerados de este directorio.

## Visión general

El objetivo del presente trabajo es desarrollar y validar un set de **estímulos dinámicos (video) de dolor** para investigación en procesamiento afectivo y empatía, generados mediante inteligencia artificial generativa. Siguiendo la lógica metodológica propuesta por Behnke et al. (2026) para imágenes afectivas estáticas —anclar la generación sintética en bases de estímulos ya validadas, en lugar de partir de prompts libres—, extendemos ese enfoque al dominio del video y a modelos generativos de la generación actual (FLUX.2, Kling v3).

La unidad experimental es el **par de videos apareados Dolor/Control**: dos videos que comparten idéntico fotograma inicial (misma escena, misma identidad, misma iluminación y encuadre) y divergen únicamente en el desenlace —una interacción dolorosa en la condición de Dolor, una interacción inocua en la condición de Control—. Este apareamiento por construcción, imposible de garantizar con material filmado convencional, permite aislar la manipulación afectiva de cualquier confundido visual de bajo nivel (cf. Behnke et al., 2026, sobre la controlabilidad como ventaja central de los estímulos generados).

El procedimiento comprende cuatro etapas: (1) selección de estímulos fuente desde una base normada, (2) extracción semántica de *ground truth* desde esas imágenes, (3) síntesis de fotogramas clave (*keyframes*) fotorrealistas, y (4) interpolación de los keyframes a video. Las secciones siguientes describen cada etapa; la validación experimental del set se describe en la sección Validación.

## Base de estímulos fuente: EPSS-Limb

Como material fuente se utilizó el **Empathy for Pain Stimuli System (EPSS**; Meng et al., 2024**)**, una base de imágenes de dolor validada y de libre uso (licencia CC BY 4.0). De sus cinco subconjuntos se seleccionó **EPSS-Limb** (*Empathy for Limb Pain Picture Database*), que contiene **68 pares dolor/no-dolor (136 imágenes BMP, 354 × 266 px)** de manos y pies interactuando con objetos cotidianos (cuchillos, martillos, jeringas, fuentes de calor, etc.). Cada par consta de una versión dolorosa (`N.2`) y una versión de control visualmente análoga (`N.1`).

EPSS-Limb provee **normas de valoración** por imagen en cuatro dimensiones: intensidad de dolor percibido, valencia afectiva, arousal y dominancia (media y DE, totales y por género del evaluador). TODO: documentar la escala (¿1–9?) y el N de evaluadores del estudio normativo de Meng et al. (2024) al citarlo en el manuscrito.

La elección de EPSS-Limb respondió a tres criterios: (a) normas publicadas que permiten una preselección cuantitativa de los pares con mayor contraste afectivo; (b) licencia abierta compatible con la derivación de nuevos estímulos y su eventual publicación; y (c) contenido centrado en extremidades en escenas cotidianas, condición necesaria para la manipulación de toma de perspectiva del diseño (el participante debe poder imaginar fácilmente que la extremidad es la propia; ver Diseño experimental). La baja resolución del material fuente (354 × 266 px) es irrelevante para el pipeline, dado que las imágenes EPSS no se presentan a los participantes: funcionan como referencia semántica y composicional para la regeneración fotorrealista (ver Pipeline, Fase 2).

## Selección de estímulos

*Detalle operativo: [`01_stimulus_selection.md`](01_stimulus_selection.md); scripts `scripts/epss_select.py`, `scripts/epss_merge.py`; outputs en `analysis/`.*

La selección combinó un **criterio normativo** (cuantitativo) con un **screening visual** (cualitativo), de modo análogo al cribado en dos pasos de Behnke et al. (2026), donde la preselección por datos se complementa con una evaluación humana de calidad y adecuación.

**Paso 1 — Métricas normativas.** A partir de las normas EPSS-Limb se construyó una tabla por par con, para cada dimensión, el valor de la versión dolorosa, el de la versión control y su diferencia (Δ). Se definió un puntaje compuesto de aptitud por par:

> *score* = z(Δ intensidad de dolor) + z(Δ arousal) − z(intensidad de dolor de la versión control)

que prioriza pares con máximo contraste afectivo entre condiciones y penaliza controles "sucios" (controles que ya son percibidos como dolorosos). Los 68 pares fueron rankeados por este puntaje (`analysis/epss_limb_pairs.csv`).

**Paso 2 — Screening visual.** Los 68 pares se inspeccionaron en láminas de contacto (`analysis/contact_sheets/`) y se calificaron (escala 1–5, juez único: TD; TODO: considerar segundo juez/consenso con el equipo para reportar fiabilidad) en tres criterios:

1. **Credibilidad** como productor de dolor (validez ecológica de la escena; p. ej., un taco que pisa un pie calzado fue puntuado bajo).
2. **Imaginabilidad en primera persona**: facilidad con que un participante puede imaginar que la extremidad es la suya. Es un requisito del diseño impuesto por la manipulación de perspectiva (condición señalada explícitamente por la IP).
3. **Aptitud para animación** (*video-readiness*): que el par codifique una **acción interrumpible** con estado inicial y dos desenlaces posibles, condición necesaria para el esquema de video inicio→fin.

Cada par recibió además una categoría temática (corte, punzante, quemadura, aplastamiento, inyección, etc.).

**Paso 3 — Selección sistemática del set (18 estímulos).** La selección no se resuelve por un puntaje compuesto ni por consenso ad hoc, sino por una **regla reproducible** (detalle y roster completo en [`01_stimulus_selection.md` §7](01_stimulus_selection.md#7-protocolo-de-selección-sistemática-definitivo); fuente `scripts/epss_roster.py`):

1. **Elegibilidad** — de los 68 pares se excluyen *solo* los no escenificables como un evento **accidental/externo, animable inicio→desenlace, sobre un miembro visible** (7 pares: 6, 28, 31, 32, 51, 56, 59). La capacidad/moderación del modelo **no** es criterio; la **autolesión no excluye**, se reencuadra como accidente en la puesta en escena.
2. **Recategorización** — `estado_herida` es formato (estado consumado), no modalidad: los pares 62 y 67 (mayor contraste normativo de la base) se reclasifican a *quemadura* y su desenlace se usa como **outcome** del video, con el onset diseñado por nosotros.
3. **Ranking** — dentro de cada categoría, por `pain_delta` (contraste de dolor normativo) descendente.
4. **Estratificación** — 18 cupos balanceados entre las 5 categorías (corte 4, quemadura 4, aplastamiento 4, punzante 3, inyección 3), recorridos *round-robin* de mayor a menor contraste.

> Esto **revierte** las exclusiones tentativas previas: 62/67 (estado consumado → outcome válido), 46 (autolesión → encuadre accidental) y 58 (cuasi-agresión → accidente) **entran** al set. La shortlist exploratoria de 20 pares y el `score` compuesto quedan como antecedente.

El resultado es el set fijo **E01–E18** (anclas: E01 = par 3, piloto; E02 = par 50, acordado). `selection_rank` es orden de producción, no de presentación (esta última se contrabalancea en el experimento).

## Pipeline de generación

El pipeline transforma cada par EPSS seleccionado en un triplete de keyframes y, de allí, en dos videos. Sigue un **protocolo de generación inversa**: primero se fija la imagen de dolor (el estado más difícil de generar) y de ella se derivan las demás, garantizando la identidad de escena entre condiciones.

### Fase 1 — Extracción de *ground truth* semántico (imagen → texto)

*Detalle: [`02_image_generation.md`](02_image_generation.md); prompts en `ai_prompts.xlsx`, hojas `system-prompt` e `image-to-text`.*

Cada imagen EPSS se procesa con un modelo de visión y lenguaje (VLM; Gemini 3) bajo un *system prompt* estructurado que instruye al modelo a producir descripciones densas y objetivas ("Computer Vision Analyst"), con reglas explícitas de: (a) **anonimización** (no describir edad/género del actor original, referirse a partes del cuerpo); (b) **acción y física** (en Dolor: impacto anatómico específico, indentación de piel, tensión; en Control: descripción explícita de la *ausencia* de daño); (c) **detalle material de los objetos**; y (d) **iluminación y fondo**. Este paso cumple dos funciones: ancla la generación en el contenido validado de EPSS (validez de contenido) y elimina la identidad del actor original (las imágenes generadas no son derivados visuales de personas identificables).

La descripción de la condición de Dolor (estado final doloroso, **t_end_P**) actúa como descripción *maestra*; las descripciones del desenlace de Control (**t_end_C**) y del estado inicial compartido (**t_start**) se derivan de ella como variaciones sustractivas (mismo escenario y objetos; cambia solo la relación espacial objeto–cuerpo).

### Fase 2 — Síntesis de keyframes fotorrealistas (texto/imagen → imagen)

*Detalle: [`02_image_generation.md`](02_image_generation.md); implementación en `src/pain_stimuli/generator.py` y `scripts/pilot_epss_keyframes.py`.*

Los keyframes se sintetizan con la familia **FLUX.2 [pro]** (Black Forest Labs) vía la API de Fal.ai, en dos pasos:

1. **Master anchor (t_end_P).** Se genera primero la imagen del estado final doloroso. En el flujo actual (piloto EPSS) se usa **FLUX.2 [pro] Edit** condicionado en la imagen EPSS original ("recrear esta escena exacta como fotografía fotorrealista, mismo ángulo de cámara y posición de manos"), lo que preserva la composición validada del estímulo fuente a la vez que lo regenera en alta resolución (16:9) con apariencia fotográfica contemporánea. El master anchor fija el fondo, la iluminación y la identidad (anónima) de la extremidad.
2. **Variantes derivadas (t_end_C y t_start).** Se derivan *desde el anchor de dolor* mediante **edición local por instrucción** (en la implementación actual, FLUX.2 **Kontext** open — los endpoints *pro* bloquean entradas con daño; ver Moderación de contenido). El **anchor de dolor es el primer y único keyframe generado desde cero**; el resto son ediciones sustractivas de él, lo que mantiene la extremidad **idéntica** (misma mano, posición, encuadre close-up centrado en la extremidad, fondo e iluminación):
   - **t_end_C (control):** el objeto peligroso se **reemplaza por un objeto neutro e inofensivo** en su *misma posición y ángulo*, y se remueve todo signo de daño. El objeto neutro debe leerse como claramente no doloroso —un extremo romo/blando, no una punta sobre la piel— (en E02, un lápiz invertido con la goma de borrar apoyada). El contraste Dolor↔Control queda así en la **identidad del objeto** (peligroso vs. neutro) y el **desenlace** (daña vs. no daña), manteniendo idéntico el layout espacial. Se reemplaza *en su lugar* (Kontext sustituye de forma fiable; **no** sabe *mover* un objeto a un costado: ahí lo duplica). Una alternativa más pobre sería la extremidad desnuda, que perdería el emparejamiento del objeto.
   - **t_start (inicio):** misma extremidad limpia, instante previo a la acción; es el fotograma inicial compartido por ambos videos, del que el objeto *entra* durante el clip.

   Esta derivación encadenada —y no la generación independiente de cada keyframe— es lo que garantiza que el Control sea un verdadero control experimental. El still de control queda definido en esta fase, **sin** depender de la interpolación a video.

Parámetros de reproducibilidad: semilla fija (`seed = 1001`), prompts registrados por estímulo (`prompts_log.json`, `ai_prompts.xlsx`), filtro de salida desactivado (`enable_safety_checker = false`, `safety_tolerance = "5"`; ver Moderación de contenido). Costo aproximado: ~USD 0.03 por imagen.

`[PENDIENTE]` Criterio de aceptación/regeneración de keyframes (cuántas variantes por prompt, quién decide, registro de descartes) — en el piloto se itera manualmente; formalizar para el batch final.

### Fase 3 — Interpolación dinámica (imagen → video)

*Detalle: [`03_video_generation.md`](03_video_generation.md); implementación en `scripts/generate_video.py`; prompts de movimiento en `ai_prompts.xlsx`, hoja `image-to-video`.*

Cada par de keyframes se interpola a video con **Kling v3 Pro** (modo *image-to-video* con fotograma inicial y final; `fal-ai/kling-video/v3/pro/image-to-video`):

- **Video Dolor** = t_start → t_end_P (el objeto peligroso entra y daña), con dinámica súbita ("fast slam impact").
- **Video Control** = t_start → t_end_C (el objeto neutro entra y queda apoyado, sin dañar), con dinámica lenta y controlada.

Ambos videos de un par comparten el mismo fotograma inicial, de modo que las condiciones son indistinguibles hasta que la acción diverge. Parámetros actuales del piloto: duración 5 s (la API admite 5 o 10 s), 16:9, sin audio, `cfg_scale = 0.5`, prompt negativo estándar contra artefactos ("blur, distort, low quality, warped, deformed").

**Sellado del fotograma final.** El interpolador aproxima el fotograma final pero no lo reproduce pixel-a-pixel. Para que cada video **termine exactamente en su keyframe aprobado** (t_end_P / t_end_C, los stills de `images/`), un paso de post-proceso (`scripts/seal_endframe.py`, conservando resolución/duración/fps) **reemplaza el último fotograma por el keyframe exacto**. Así el estado terminal de cada condición —el momento crítico para el análisis time-locked— es idéntico al still validado.

`[PENDIENTE]` Parámetros finales de Kling: duración definitiva (5 vs. 10 s), comparación A/B entre Kling v3 Pro y Kling O1 (modelo específico para interpolación primer→último fotograma), criterios de aceptación del video (continuidad de identidad, ausencia de morphing/artefactos), y n de regeneraciones permitidas por estímulo.

## Diseño experimental y condiciones

El experimento manipula dos factores: **Condición** (Dolor vs. Control) y **Perspectiva** (propia vs. ajena), en un diseño 2 × 2 intra-sujeto.

Críticamente, la **perspectiva no es un factor visual de los estímulos**: no se generan versiones POV y de tercera persona de cada video. La toma de perspectiva se induce en el software de presentación (PsychoPy) mediante **instrucción explícita más una clave visual sostenida: un borde de color (azul/amarillo) que enmarca el video** según la perspectiva que el participante debe adoptar. Cada video se presenta, por tanto, bajo ambas perspectivas en distintos ensayos.

De allí que el entregable de generación sea de **36 videos únicos: 18 temáticas de dolor + 18 controles apareados** (y no 72), con duraciones de ~5–10 s. Las cuatro celdas del diseño (Dolor/Control × Propia/Ajena) surgen de cruzar esos 36 videos con el encuadre de perspectiva en PsychoPy (el borde de color duplica las *celdas*, no los videos). Cada estímulo aporta además 3 stills (inicio/dolor/control) para el set de imágenes del mismo experimento.

Los estímulos se generan en un encuadre de perspectiva neutra (primer plano de la extremidad, compatible con ambas lecturas), lo que es coherente con que la manipulación recaiga en la instrucción y no en la óptica de la escena.

`[PENDIENTE]` La implementación del borde azul/amarillo + instrucción en el protocolo PsychoPy aún no está construida (la versión actual solo registra la etiqueta de perspectiva). `[PENDIENTE]` Asignación de colores a perspectivas y contrabalanceo.

Conforme a la decisión del equipo, la validación se realizará en **un único experimento completo** que incluye conjuntamente el set de imágenes y el set de videos (no en dos estudios secuenciales), por restricciones de reclutamiento y de ejecución presupuestaria (2026).

## Consideraciones técnicas: moderación de contenido

*Detalle: [`04_content_moderation.md`](04_content_moderation.md); diagnóstico en `scripts/test_safety_filter.py` y `scripts/control_test_jan_method.py`.*

La generación de imágenes de dolor con servicios comerciales está condicionada por **dos capas independientes de moderación**, cuya distinción es metodológicamente relevante:

1. **Filtro de salida** (clasificador NSFW sobre la imagen generada): controlable por API en los endpoints FLUX.2 [pro] (`enable_safety_checker`, booleano; `safety_tolerance`, "1"–"5"). En este proyecto se desactiva (`false` / `"5"`), lo cual es legítimo para contenido de investigación.
2. **Filtro de entrada** (moderación del prompt en el servidor): los endpoints FLUX.2 [pro] de Fal.ai rechazan con `HTTP 422 content_policy_violation` los prompts con descripciones explícitas de herida/sangre (p. ej., "cut", "bleeding", contacto de filo con dedo). Este filtro **no es desactivable por ningún parámetro** y es independiente del anterior. Una prueba de control (junio de 2026) reprodujo prompts de redacción clínica que en enero de 2026 generaban correctamente, y hoy son rechazados: el filtro fue endurecido por el proveedor entre ambas fechas.

Esta asimetría condiciona directamente la **redacción de los prompts** y, en última instancia, el **diseño de los estímulos**: los prompts del estado final doloroso se formulan como **amenaza inminente sin herida consumada** (el instante inmediatamente anterior al daño: filo presionando la piel intacta, musculatura tensa, sin sangre), redacción que atraviesa la moderación y produce salidas fotorrealistas de alta calidad. Cabe notar que este formato es convergente con el propio EPSS-Limb (muchas de cuyas imágenes de dolor representan el momento de contacto/amenaza más que la lesión visible) y con la literatura de empatía por dolor, donde la anticipación del daño es un potente elicitador. `[PENDIENTE]` La adopción definitiva del formato "amenaza inminente" vs. "daño visible" es un cambio de diseño que requiere aprobación de la IP. `[PENDIENTE]` Verificar la moderación propia de Kling sobre los prompts de movimiento de impacto.

Como plan de contingencia, se identificaron alternativas no probadas: modelos de pesos abiertos (p. ej., `flux/dev`, sin moderación de entrada, a costa de menor calidad) u otro proveedor/auto-alojamiento. Documentamos estas restricciones porque constituyen una variable de reproducibilidad del método: la viabilidad de un pipeline de estímulos de dolor con modelos comerciales depende de políticas de moderación del proveedor que pueden cambiar sin aviso (cf. la discusión de barreras prácticas en Behnke et al., 2026).

## Validación

`[PENDIENTE — ver esqueleto en `[`05_validation.md`](05_validation.md)`]` Validación experimental del set (ratings dimensionales y de dolor percibido sobre imágenes y videos en un único experimento; comparación con las normas EPSS de los pares fuente; criterios de inclusión final de estímulos). TODO: definir medidas, tamaño muestral y análisis tomando como referencia el protocolo de validación de Behnke et al. (2026, Studies 1–6) y las normas originales de Meng et al. (2024).

## Referencias

- Behnke, M., Kłoskowski, M., Klichowski, M., Krzyżaniak, W., Szymański, K., Maciejewski, P., … Gross, J. J., & Coles, N. A. (2026). Using artificial intelligence to generate affective images: Methodology and initial library. *Advances in Methods and Practices in Psychological Science, 9*(1), 1–28. https://doi.org/10.1177/25152459251415336
- Meng, J., Li, Y., Luo, L., Li, L., Jiang, J., Liu, X., & Shen, L. (2024). The Empathy for Pain Stimuli System (EPSS): Development and preliminary validation. *Behavior Research Methods, 56*(2), 784–803. https://doi.org/10.3758/s13428-023-02087-4
- TODO: referencias técnicas de los modelos (Black Forest Labs FLUX.2; Kuaishou Kling v3; Gemini 3) según el formato que pida la revista.
