# Playbook de generación de estímulos (dolor / control)

Guía operativa para generar cada estímulo del set (basado en EPSS-Limb) con IA.
Resultado por estímulo: **3 stills** (`inicio`, `dolor`, `control`) + **2 videos**
(`dolor`, `control`), guardados con convención estándar en `dataset/`.

Conocimiento destilado del piloto **E01 (corte de pepino)**. Última actualización:
2026-06-13. Estructura de archivos: ver también `../dataset/README.md`.

---

## 0. Setup (una vez por shell)

```bash
ENV=/c/Users/au805392/micromamba/envs/campeones
run() { PYTHONIOENCODING=utf-8 PATH="$ENV:$ENV/Library/bin:$ENV/Scripts:$PATH" python.exe "$@"; }
```

`FAL_KEY` se carga **automáticamente** desde `./.env` (gitignored) — lo hace
`scripts/stimulus.py` al importarse, así que NO hace falta exportarla en cada shell.
Si rotás la clave, regenerá el `.env` (desde tu terminal):
`Set-Content .env "FAL_KEY=$([Environment]::GetEnvironmentVariable('FAL_KEY','User'))" -Encoding ascii`.

Todos los scripts toman `--id`. Las rutas/nombres los centraliza `scripts/stimulus.py`
(no hace falta tocar paths a mano).

---

## 1. QUICKSTART — secuencia completa para un estímulo nuevo

**Idea central del flujo (decidida 2026-06-13).** El estímulo se construye **a partir
de la imagen de DOLOR**: ése es el primer y único paso de generación "desde cero". Una
vez que la imagen de dolor convence, el **CONTROL** y el **INICIO** se **derivan de ella
con Kontext** (edición local), **conservando la misma mano, posición y el encuadre
close-up centrado en la extremidad**:
- **CONTROL** = el objeto peligroso **reemplazado por uno NEUTRO e inofensivo** en la
  *misma posición y ángulo*, sin daño (ver §4: el objeto neutro debe leerse como
  claramente no doloroso). Contraste dolor↔control = *identidad del objeto + desenlace*,
  con el mismo layout espacial. El control **no se saca de un frame del video**.
- **INICIO** = la misma extremidad **sin el objeto** (el inicio compartido del que el
  objeto *entra* durante el video).

Ejemplo real: E02, cigarrillo que quema el dorso (par EPSS 50); el control reemplaza el
cigarrillo por un lápiz dado vuelta con la **goma de borrar** apoyada (inofensivo).

> **Nota:** este ejemplo (cigarrillo) muestra el flujo y la **versión original** de E02.
> E02 se **re-definió** después (2026-06-13) a un *lápiz punzante* (`E02_lapiz_punzante_dorso`):
> el dolor pasó a ser el **mismo lápiz pero con la punta**, y el control quedó como el lápiz
> con la goma (contraste = un solo objeto invertido). Las rutas `work/E02_quemadura_cigarrillo_dorso/…`
> de los comandos de abajo corresponden al slug viejo; hoy la carpeta es `E02_lapiz_punzante_dorso/`.
> El ejemplo se mantiene como ilustración del flujo de derivación del control.

```bash
# 0) Crear el estimulo (elegir par en analysis/epss_limb_roster.csv):
run scripts/new_stimulus.py --id E02 --slug quemadura_cigarrillo_dorso --epss 50 \
    --categoria quemadura --descripcion "Cigarrillo quema el dorso de la mano" --fecha 2026-06-13

# 1) DOLOR (flux/dev) — PRIMER PASO. Iterar el prompt (lesion como sujeto PRINCIPAL
#    al inicio; close-up centrado en la extremidad). keep el que convenza:
run scripts/pilot_v1.py --id E02 gen e02_dolor "<PROMPT_DOLOR>" --seed 7
run scripts/pilot_v1.py --id E02 list                # ver candidatos
run scripts/pilot_v1.py --id E02 keep e02_dolor_s7   # aprobar (drop para descartar)

# 2) CONTROL (Kontext) — derivar del DOLOR: REEMPLAZAR el objeto peligroso por uno
#    NEUTRO inofensivo en la misma posicion/angulo, sin dano. Prompt a medida por escena
#    (--prompt); en E02 = lapiz dado vuelta con la goma de borrar apoyada en el dorso:
run scripts/derive_variant.py --id E02 \
    --anchor work/E02_quemadura_cigarrillo_dorso/selected/e02_dolor_s7.jpg control \
    --prompt "Edit this photograph: replace the cigarette with an ordinary wooden pencil held UPSIDE DOWN, its blunt pink rubber eraser end resting gently on the back of the hand exactly where the cigarette was; the sharpened tip points up, away from the skin. Remove all ember, ash, smoke, burn, scorch and redness - skin smooth and intact. Keep the hand in the EXACT same position, framing, lighting and background. A harmless pencil eraser resting where the cigarette was."
#   -> work/E02_quemadura_cigarrillo_dorso/candidates/control.jpg

# 3) INICIO (Kontext) — inicio compartido del video (extremidad limpia, sin el objeto):
run scripts/derive_variant.py --id E02 \
    --anchor work/E02_quemadura_cigarrillo_dorso/selected/e02_dolor_s7.jpg clean
#   -> work/E02_quemadura_cigarrillo_dorso/candidates/clean.jpg

# 4) Fijar los 3 stills DEFINITIVOS (ya no hay provisorio: el control esta listo):
run scripts/finalize_frames.py --id E02 \
    --inicio  work/E02_quemadura_cigarrillo_dorso/candidates/clean.jpg \
    --dolor   work/E02_quemadura_cigarrillo_dorso/selected/e02_dolor_s7.jpg \
    --control work/E02_quemadura_cigarrillo_dorso/candidates/control.jpg

# 5) VIDEOS (editar antes los motion prompts en run_videos.py -> MOTION). Generar
#    PRIMERO dolor, despues control. run_videos SELLA solo el ultimo frame de cada
#    video con su still (el video termina EXACTO en images/<id>_frame_<cond>.png):
run scripts/run_videos.py --id E02 --dry-run                 # ver costo (~$1.12)
run scripts/run_videos.py --id E02 --condition dolor         # 1ro dolor (inicio->dolor)
run scripts/run_videos.py --id E02 --condition control       # 2do control (inicio->control)

# 6) (opcional) Re-sellar / refrescar frames del deliverable si hiciera falta:
run scripts/seal_endframe.py --id E02 --condition both       # ultimo frame = still
```

`finalize_frames.py` iguala automáticamente los 3 stills a la resolución del frame
de dolor. Costo total por estímulo ≈ **$1.4** (imágenes centavos + ~$1.12 de video).

> **Por qué el control se deriva (y no sale del video).** El control debe ser la
> *misma escena espacial que el dolor*, cambiando solo el objeto (peligroso→neutro) y el
> desenlace (daña→no daña) → la mano debe quedar idéntica. Kontext (edición local) lo
> garantiza: sustituye el objeto **en su lugar** y borra el daño dejando la mano
> pixel-a-pixel en la misma posición. (Kontext **no reubica** un objeto a un costado: lo
> duplica; por eso se *reemplaza en su lugar*, no se mueve.) Ver §4.
>
> **Inicio = extremidad limpia.** El inicio compartido es la misma extremidad sin el
> objeto (de la que el objeto *entra* durante el video). El plano medio "antes"
> (`start_variants` + `align_start_look`) quedó como recurso **opcional/raro**; el flujo
> estándar usa `clean.jpg` como inicio.
>
> **Sellado del último frame.** `run_videos.py` llama a `seal_endframe.py` tras generar
> cada clip: reemplaza el último fotograma por el still exacto, así el video **termina en
> `images/<id>_frame_<cond>.png>`** (Kling aproxima el end-frame pero no lo clava). El
> último frame del deliverable `frames/` también queda = el still.

---

## 2. Estructura de datos y convención de nombres

ID secuencial **E01, E02…** + slug. Lo definitivo va en `dataset/`; TODA prueba en
`work/`. **Estructura completa y convención de nombres: [`00_ESTRUCTURA.md`](00_ESTRUCTURA.md).**

```
dataset/
  stimuli_index.csv                 <- 1 fila por estimulo (id, slug, epss, categoria, n_images, n_videos, estado)
  E01_corte_pepino/
    images/   E01_still_inicio.png   E01_still_dolor.png   E01_still_control.png   (3 STILLS, misma resolucion)
    frames/   E01_frame_dolor_1..6.png   E01_frame_control_1..6.png   (FOTOGRAMAS de los videos, resolucion nativa)
    videos/   E01_video_dolor.mp4    E01_video_control.mp4
    E01_meta.json                    <- fuente EPSS, modelo+prompt+seed de cada still, motion prompts, costo
work/
  E01_corte_pepino/
    candidates/ selected/ deprecated/    <- iteraciones de imagenes (las cura pilot_v1)
    start_variants/ contact_sheets/      <- tomas medias / laminas
    video_frames/                        <- frames a media res de videos de prueba
    extras/                              <- variantes guardadas para reuso futuro (p. ej. un control "demasiado doloroso")
    ledger.json                          <- prompt+seed+modelo de cada generacion (pilot_v1)
```

> **`still` ≠ `frame`** (convención 2026-06-13): `still` = imagen clave canónica de
> `images/`; `frame` = fotograma extraído de un video, en `frames/`. Los nombres canónicos
> salen todos de `scripts/stimulus.py` (`st.image()`, `st.video()`); no editarlos a mano.

**Los 3 stills (`images/`), igualados en resolución:**
- **inicio** = mano/zona limpia, SIN el objeto peligroso. Es el **inicio compartido**
  del que parten los dos videos.
- **dolor** = el objeto corta/quema/golpea + sangre/daño.
- **control** = **edición Kontext del dolor**: misma mano y posición exacta, con el
  objeto peligroso **reemplazado por uno NEUTRO e inofensivo** en su lugar y el daño
  removido (en E02: lápiz dado vuelta, goma de borrar apoyada). Contraste con dolor =
  objeto + desenlace, mismo layout espacial. **No** se saca de un frame del video.

---

## 3. Mapa de modelos y moderación (CLAVE)

| Modelo | Para qué | Por qué |
|---|---|---|
| `fal-ai/flux/dev` | **Dolor explícito** (texto→imagen) | Open-weights, **sin moderación de entrada**; `enable_safety_checker:False` apaga el filtro de salida. Acepta sangre/daño. |
| `fal-ai/flux-kontext/dev` | **Derivar la imagen limpia** y **alinear look** | Edición por instrucción open, sin moderación agresiva; edita local conservando encuadre. |
| `fal-ai/flux-2-pro` | **Tomas "antes" benignas** (plano medio) | Mejor calidad. SOLO contenido sin daño (si no, lo bloquea). |
| `fal-ai/kling-video/v3/pro/image-to-video` | **Videos** (inicio→fin) | Soporta `start_image_url` + `end_image_url`. $0.112/s sin audio. |

**Regla de oro de moderación:**
- Los endpoints **pro** (`flux-2-pro`, `flux-2-pro/edit`) tienen un **filtro de entrada
  del prompt** (`HTTP 422 content_policy_violation`) que **NO se apaga** y bloquea
  heridas/sangre/corte, y también imágenes de entrada con sangre. Se endureció en 2026.
- `enable_safety_checker:False` solo apaga el filtro de **salida**, NO el de entrada.
- **No reformular prompts para "colar" contenido en los pro.** Para lo explícito →
  modelo **open `flux/dev`** (sin ese filtro). Para editar quitando daño → **Kontext**.

**Qué puede y qué NO puede Kontext:**
- ✅ **Quitar** sangre/heridas/objetos · ✅ **conservar** encuadre exacto · ✅ **re-estilizar** look/luz/fondo.
- ❌ **Reubicar** un objeto saliente (no mueve el cuchillo de los dedos a la mesa; si le pedís "mover", lo **duplica**). No pelear con esto; diseñar alrededor.

---

## 4. Tips por paso

**DOLOR (flux/dev):** flux/dev tiene baja adherencia → poné la **lesión como sujeto
principal AL INICIO** del prompt; el contexto (la verdura/escena) va secundario y
borroso. Pedí "anatomically correct hand, five fingers" y foco nítido en el punto de
daño. Fijá `--seed` mientras iterás el texto; variá la seed para alternativas.
Plantilla E01 (corte): *"Extreme close-up macro photograph of a human hand on a wooden
cutting board. The sharp edge of a chef's knife is cutting directly into the pad of
the index fingertip… bright red blood wells up… Anatomically correct hand, five
fingers. Razor-sharp focus… 8k, raw documentary style."*
>
> **Aprendizajes E02 (contacto objeto↔piel).** Para que el objeto se vea **presionado
> sobre la piel** (y no flotando), forzá el contacto: *"the tip is touching the skin in
> full direct contact, with no gap; the skin is pushed inward and dented under the tip"*.
> **Evitá** palabras como "stubbed out / crushed / mashed / held": empujan a flux a poner
> el objeto **horizontal** o "sostenido" en la **palma**. Anclá la geometría
> explícitamente: *"held vertically and perpendicular, pointing straight down onto the
> BACK of the hand, NOT lying flat, NOT held between the fingers"*. La seed gobierna la
> composición: si una seed da el encuadre correcto (vertical sobre el dorso), reusala y
> variá solo el texto.

**LIMPIA / inicio (Kontext):** instrucción de quitar el objeto + todo el daño,
conservando mano/tabla/ángulo/luz. Prompt E01: *"Keep this photograph exactly the
same… Remove the knife and any blade COMPLETELY, and remove all blood and any wound.
The hand rests calmly on a bare empty wooden board… NO knife anywhere."*

**INICIO plano medio (opcional):** `start_variants.py` genera 3 tomas medias (sin
cara, "por accionar") con `flux-2-pro` → editar sus prompts por situación. Luego
`align_start_look.py` alinea el look a los finales (editar `PROMPT` in-file). Para
**cambiar el fondo** con Kontext, decir explícito *"remove the kitchen/cabinets,
replace with a plain neutral medium-gray seamless backdrop"* (si nombrás "kitchen"
regenera una cocina) y dar tono/exposición concretos.

**CONTROL still (Kontext, `derive_variant.py … control --prompt`):** se **deriva del
dolor** con una edición local que **reemplaza el objeto peligroso por uno NEUTRO e
inofensivo en su misma posición y ángulo** y remueve todo el daño, dejando la **misma
mano en la misma posición exacta**. El contraste con dolor es entonces *identidad del
objeto (peligroso→neutro) + desenlace (daña→no daña)*, manteniendo el layout espacial.
> **Elegir bien el objeto neutro (clave).** Debe leerse como **claramente no doloroso**.
> Un objeto del mismo porte pero con **punta/filo apuntando a la piel sigue pareciendo
> doloroso** (p. ej. la *punta* del lápiz) → usar el extremo **romo/blando**: en E02 el
> control es un **lápiz dado vuelta con la goma de borrar** apoyada en el dorso (la punta
> mira hacia arriba). El objeto entra "en el lugar" del peligroso, no al costado.
> **Por qué reemplazar y no "objeto presente sin dañar" ni "extremidad desnuda":** (1)
> para varias lesiones el mismo objeto *sin* daño es incoherente (un cigarrillo encendido
> sobre la piel **quema**); (2) sustituirlo por un objeto neutro **conserva el layout
> espacial** (mismo lugar/ángulo) → mejor control que la mano desnuda, que perdería el
> objeto; (3) Kontext **reemplaza en su lugar** de forma fiable (lo que **no** sabe es
> *mover* un objeto a un costado: ahí lo duplica).
> Tip de prompt: liderar con el reemplazo (*"replace the X with a harmless Y in the EXACT
> same position…"*) + remover todo el daño + conservar mano/encuadre/luz. El still de
> control queda listo en el paso 2, **sin** depender del video.
>
> *(Variantes "demasiado dolorosas" descartadas como control pueden conservarse como
> posibles estímulos dolorosos futuros — p. ej. el lápiz-punta de E02 quedó en
> `work/E02_.../extras_guardados/`.)*

**INPAINT por máscara (`inpaint_patch.py`) — FALLBACK opcional.** A veces el still de
dolor deja una **marca local** (un dimple, un pinchazo, una pequeña lesión) que querés
borrar del **inicio** (o suavizar en el control) y **Kontext NO la quita**: la edición por
instrucción es *global* y tiende a preservar features de piel como si fueran anatomía
(no cede ni subiendo `--guidance` ni variando `--seed`). Cuando pase eso, usar
`inpaint_patch.py`: regenera **solo** la región enmascarada como piel lisa con FLUX Pro
Fill (`fal-ai/flux-pro/v1/fill`), dejando el resto pixel-a-pixel intacto (~$0.05).
- Es **opcional**: si el flujo tradicional (flux/dev + Kontext) ya da un inicio/control
  limpio, **no hace falta**.
- La máscara se genera sola (círculo blanco=inpaint): `--cx --cy --r --feather` en px.
  Para ubicar el centro, dibujar una grilla/overlay sobre la imagen y leer las coords.
- Anclar sobre la imagen que ya tiene el objeto removido (no sobre el dolor), p. ej. el
  `clean.jpg` con la marca. Probar 1-2 seeds; `--guidance` alto (~15-18) compromete más
  a la consigna de "piel lisa". No buscar un codo perfectamente liso (queda plástico): el
  objetivo es que **desaparezca la marca de la lesión**, no el pliegue natural.
- Ejemplo real (E07, inyección): la marca del pinchazo en el inicio se borró con
  `--cx 485 --cy 378 --r 125 --feather 35 --seed 4002 --guidance 18` sobre el brazo ya
  sin jeringa.

---

## 5. Lógica del video (Kling)

Inicio **compartido** = still `inicio` (zona limpia, sin el objeto). Durante el clip
**entra un objeto**:
- **Video dolor:** `inicio → dolor` (el objeto **peligroso** entra y **daña**).
- **Video control:** `inicio → control` (un objeto **neutro** entra y queda apoyado en la
  misma posición, **sin dañar**).

`run_videos.py` ya cablea esto (start = still inicio; **fin dolor = still dolor; fin
control = still control**). Editar los textos en `MOTION["dolor"]` / `MOTION["control"]`
para la situación. Opciones: `--condition both|dolor|control`, `--duration 5`,
`--tier v3pro|v3std`, `--dry-run`.

**Sellado del último frame.** Tras bajar cada clip, `run_videos.py` llama a
`seal_endframe.py`: reemplaza el último fotograma por el still exacto, de modo que el
video **termina en `images/<id>_frame_<cond>.png>`** (Kling aproxima el end-frame pero no
lo clava pixel-a-pixel). Resolución/duración/fps se conservan. Se puede correr suelto:
`run scripts/seal_endframe.py --id <id> --condition both`.

Decisión validada (E01): **close-up** (no plano medio→close-up: Kling deforma menos) y
**5 s**. Inspeccionar un `.mp4` (no se reproduce en chat): `extract_frames.py` o ffmpeg
de `envs/affective-fnirs/Library/bin/ffmpeg.exe`, y armar tira con PIL.

---

## 6. Referencia rápida de scripts (todos `--id`)

| Script | Hace |
|---|---|
| `new_stimulus.py` | Crea la fila en el index + las carpetas work/dataset. |
| `pilot_v1.py` | `gen`/`keep`/`drop`/`list` del **dolor** (flux/dev) + ledger. |
| `derive_variant.py` | Deriva del dolor con Kontext: `control` (reemplaza el objeto peligroso por uno neutro inofensivo, misma pose), `clean` (inicio compartido, sin objeto), o `start_closeup`. **Pasar `--prompt` a medida por escena** (objeto neutro). Flags `--seed/--guidance/--steps` para variar la muestra o subir la fuerza de edición (default seed 1001, guidance 2.5). |
| `inpaint_patch.py` | **(Fallback opcional)** Borra una marca/feature LOCAL que Kontext no logra quitar (la trata como anatomía), vía inpaint por máscara con FLUX Pro Fill. La máscara circular se genera sola: `--cx --cy --r --feather` (px). Ver §4. |
| `start_variants.py` | 3 tomas medias "antes" (flux-2-pro). Editar prompts por situación. |
| `align_start_look.py` | Alinea el look de una toma media a los finales (Kontext). |
| `finalize_frames.py` | Copia los 3 stills elegidos a `dataset/<id>/images/`, igualando resolución. |
| `extract_frames.py` | Extrae los frames de los videos a `dataset/<id>/frames/` (ffmpeg). Solo deliverable/inspección; ya **no** se usa para el still de control. |
| `run_videos.py` | Genera los 2 videos (Kling) a `dataset/<id>/videos/`. Fin dolor = still `dolor`; fin control = still `control`. Sella el último frame automáticamente (`seal_endframe`). |
| `seal_endframe.py` | Reemplaza el último frame de cada video por el still exacto de `images/` (el video termina en el still) y refresca `frames/`. Lo llama `run_videos.py`. |
| `stimulus.py` | (lib) rutas y nombres canónicos; lo usan todos. |

---

## 7. Costos y deadline

- Imágenes: flux/dev ≈ $0.025, flux-2-pro ≈ $0.03, Kontext ≈ $0.025 c/u.
- Video: **$0.112/s** sin audio (v3pro) → 5 s = $0.56/clip → **$1.12 el par**.
- **≈ $1.4 por estímulo** → las 18 temáticas ≈ **$25** (holgado en los ~$200).
- Presupuesto Fal (team cátedra): debe ejecutarse en **2026**.
