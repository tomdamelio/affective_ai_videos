# Fase A — Selección de estímulos (detalle operativo)

> Complementa la sección *Selección de estímulos* de [`methodology.md`](methodology.md).
> Fuentes: `scripts/epss_select.py`, `scripts/epss_merge.py`, **`scripts/epss_roster.py`** (selección sistemática, §7); outputs `analysis/epss_limb_pairs.csv`, `analysis/epss_limb_screening_visual.csv`, `analysis/epss_limb_selection.csv` (+columnas de roster), **`analysis/epss_limb_roster.csv`**, `analysis/contact_sheets/`, `analysis/shortlist/`.
>
> **La selección vigente del set (18 estímulos, E01–E18) está en el [§7](#7-protocolo-de-selección-sistemática-definitivo).** Las §4–§6 son históricas.

## 1. Material fuente

- **EPSS-Limb** (Meng et al., 2024; CC BY 4.0): 68 pares dolor/no-dolor, 136 imágenes BMP 354 × 266 px. Copia local en `EPSS/Empathy for Limb Pain Picture Database (EPSS-Limb)/`.
- Nomenclatura: `N.1` = versión no dolorosa (control), `N.2` = versión dolorosa.
- Normas: `EPSS-Limb data.xlsx`, 4 hojas — *Pain intensity*, *Affective valance* [sic], *Arousal*, *Dominance* — con media y DE por imagen (total y por género del evaluador).

## 2. Métricas normativas por par (`epss_select.py`)

Para cada par y dimensión *m* ∈ {dolor, valencia, arousal, dominancia}:

- `m_pain` (valor de N.2), `m_nopain` (valor de N.1), `m_delta = m_pain − m_nopain`.
- Puntaje compuesto (z-scores sobre los 68 pares):

```
score = z(pain_delta) + z(arousal_delta) − z(pain_nopain)
```

Lógica: maximizar el contraste de dolor y arousal entre condiciones, penalizando pares cuyo control ya es percibido como doloroso ("control sucio").

## 3. Screening visual

Los 68 pares se revisaron en láminas de contacto (3 pares por lámina, control a la izquierda, dolor a la derecha; `analysis/contact_sheets/sheet_01..23.png`). Calificación 1–5 por par (juez único: TD — TODO: segundo juez / consenso para reportar fiabilidad en el manuscrito):

| Criterio | Definición | Motivación |
|---|---|---|
| `credibilidad` | Verosimilitud de la escena como productor de dolor (validez ecológica) | La IP señaló que parte de EPSS-Limb es "poco creíble"; la selección no puede ser top-N por normas |
| `imaginabilidad_1p` | Facilidad de imaginar la extremidad como propia | Requisito de la manipulación de toma de perspectiva |
| `aptitud_video` | Si el par codifica una acción interrumpible con estado inicial común y dos desenlaces (estructura inicio→fin) | Requisito del esquema de interpolación start→end |

Más `categoria` temática y `nota` descriptiva.

## 4. Shortlist exploratoria (20 pares) — *superada por §7*

> **Histórico.** El `score` compuesto (§2) y la shortlist de 20 pares se usaron para
> el screening inicial, pero **no** definen la selección final. Desde 2026-06-13 la
> selección se rige por el **protocolo sistemático del §7** (orden transparente por
> `pain_delta`, reproducible para Métodos). Se conserva esta sección como registro.

Distribución por categoría de la shortlist exploratoria (`scripts/epss_merge.py`):

| Categoría | Pares |
|---|---|
| Corte | 3, 8, 17, 22, 41 |
| Punzante | 29, 16, 52, 23 |
| Quemadura | 50, 13, 15, 33, 61 |
| Aplastamiento | 30, 19, 20, 63 |
| Inyección | 48, 68 |

Láminas individuales en `analysis/shortlist/`. Tabla completa (normas × screening) en `analysis/epss_limb_selection.csv`.

## 5. Criterios de exclusión — versión exploratoria *(revisada en §7)*

> **Histórico, revisado.** Esta tabla excluía 62/67 (estado consumado), 46 (autolesión)
> y 58 (cuasi-agresión). El §7 **revierte** esas exclusiones por dos refinamientos
> metodológicos: (a) un *estado consumado* sí sirve como **outcome** (frame final) de un
> video cuyo onset diseñamos nosotros → 62/67 entran (recategorizados a *quemadura*);
> (b) la connotación de autolesión se neutraliza **en la puesta en escena** (encuadrar
> como accidente externo) en vez de excluir → 46/58 entran. Ver §7 para la lista vigente.

## 6. ~~Selección final pendiente (9 pares)~~ — *cerrada por §7*

> **Superada.** El objetivo de "9 pares finales por reunión" quedó reemplazado, tras el
> pivote EPSS, por **un set único de 18 estímulos** (imágenes + videos juntos), fijado
> por el protocolo sistemático del §7. La cobertura de categorías, el orden y la
> justificación ya no se delegan a una reunión ad hoc sino a una regla reproducible.

## 7. Protocolo de selección sistemática (DEFINITIVO)

> Fuente reproducible: `scripts/epss_roster.py` → `analysis/epss_limb_roster.csv` y
> columnas `incluido / exclude_reason / cat_final / category_rank / stimulus_id /
> selection_rank / slug_sugerido` añadidas a `analysis/epss_limb_selection.csv`.
> Decidido con TD el 2026-06-13.

**Motivación.** Reemplazar el `score` compuesto (pesos opacos) por una regla que se
pueda describir literalmente en Métodos. Como el estímulo se **re-genera** con IA (no se
reutiliza la imagen EPSS), lo que importa es la **norma de la situación**, no la calidad
de la imagen original → la columna vertebral del orden es el **contraste de dolor
normativo** `pain_delta = pain_pain − pain_nopain`.

**Algoritmo (4 pasos):**

1. **Elegibilidad.** De los 68 pares se excluyen *solo* los que no se pueden escenificar
   como un **evento accidental/externo, animable onset→outcome, sobre un miembro
   visible**. La capacidad/moderación del modelo **no** es criterio (lo explícito se
   genera con `flux/dev`). La **autolesión no excluye**: se reencuadra como accidente.
2. **Recategorización.** `estado_herida` es una etiqueta de *formato* (estado ya
   consumado), no una modalidad → se reclasifica por la lesión real y el desenlace se usa
   como **outcome** del video (par 62, 67 → *quemadura*).
3. **Ranking.** Dentro de cada categoría, los elegibles se ordenan por `pain_delta`
   descendente. Desempate: `pain_pain` desc, luego nº de par asc.
4. **Estratificación.** 18 cupos a 5 categorías: base 3 c/u; los 3 cupos restantes a las
   categorías cuyo 4º par (por delta) es más fuerte → **corte 4, quemadura 4,
   aplastamiento 4, punzante 3, inyección 3**. Recorrido *round-robin* (1º de cada
   categoría, luego 2º…); dentro de cada ronda las categorías se ordenan por el delta del
   par colocado, de modo que la secuencia global decae de mayor a menor contraste
   manteniendo el balance.

**Exclusiones vigentes (7).** Único criterio = no escenificable como accidente externo
animable sobre miembro visible:

| Par | Motivo |
|---|---|
| 6 | Insecto vivo: sin agente discreto controlable (difícil de animar) |
| 28 | Evento clavo/bisagra poco legible (ambiguo) |
| 31 | Pie cubierto por calzado: lesión no visible |
| 32 | Torsión autoinfligida: fuera del esquema de 5 categorías |
| 51 | Soporte artificial: escena no accidental |
| 56 | Cuchillo apoyado estático: sin evento onset→outcome |
| 59 | Instrumento no legible como lesión clara (ambiguo) |

**Anclas.** `E01 = par 3` (piloto canónico, corte de pepino) quedó fijado **antes** de
cerrar el protocolo: se conserva (*grandfathered*) y ocupa un cupo de *corte*,
desplazando al 4º corte por ranking. `E02 = par 50` (quemadura cigarrillo), acordado.
El resto (E03–E18) sigue estrictamente el orden del protocolo.

> **Re-definición de E02 (2026-06-13).** E02 se cambió de *quemadura* (cigarrillo, par 50)
> a **punzante**: un **lápiz** con la punta presionando el dorso (dolor) vs el mismo lápiz
> invertido con la goma (control). Ya **no** es un render fiel del par 50. **Decidido
> (2026-06-13):** (1) se **mantiene vinculado al par 50** por ahora; (2) **cuenta como
> punzante** en la estratificación — `scripts/epss_roster.py` ya lo recategoriza
> (`RECAT[50]='punzante'`, `SLUGS[50]='lapiz_punzante_dorso'`). Esto deja la cuota nominal
> en quemadura −1 / punzante +1 (3/4). **Pendiente (diferido):** sumar una quemadura y
> fijar la cuota final; hasta entonces el roster de producción NO se regenera (re-correr el
> script reordenaría E03–E18) y `epss_limb_roster.csv` lleva E02 como override manual. La
> versión cigarrillo se conserva en `work/E02_lapiz_punzante_dorso/extras/`.

> `selection_rank` es **orden de producción/prioridad**, NO orden de presentación al
> participante (eso se contrabalancea/aleatoriza en el experimento). Los desenlaces
> severos sin agente discreto (E03 par 62, E08 par 67) encabezan por `pain_delta` pero
> son los más exigentes de escenificar (onset diseñado por nosotros, riesgo de *gore*
> artefactual); conviene producirlos **después** de afinar el pipeline con un par de
> casos de agente discreto.

### Roster definitivo E01–E18

| ID | rank | par | categoría | c.rank | pain_Δ | pain_pain | ancla | slug sugerido | situación EPSS |
|---|---|---|---|---|---|---|---|---|---|
| E01 | 1 | 3 | corte | 4 | 4.53 | 6.55 | piloto | corte_pepino | Cortar pepino; cuchillo corta dedo |
| E02 | 2 | 50* | punzante | 3 | 4.92 | 6.23 | acordada→re-def | lapiz_punzante_dorso | Lápiz: punta presiona el dorso (dolor) vs goma (control). *Re-definido de quemadura/cigarrillo; ya no es el par 50 fiel |
| E03 | 3 | 62 | quemadura | 1 | 6.06 | 8.37 | | quemadura_pie_grave | Pie con quemadura/herida grave (outcome) |
| E04 | 4 | 46 | corte | 1 | 5.65 | 7.03 | | corte_muneca | Cuchillo corta la muñeca (escenificar accidental) |
| E05 | 5 | 58 | punzante | 1 | 5.08 | 6.34 | | punzante_tijera_antebrazo | Tijera se clava en el antebrazo |
| E06 | 6 | 11 | aplastamiento | 1 | 4.32 | 5.92 | | aplastamiento_taco_pie | Taco aguja pisa el pie |
| E07 | 7 | 48 | inyección | 1 | 4.32 | 5.85 | | inyeccion_codo | Jeringa en el pliegue del codo |
| E08 | 8 | 67 | quemadura | 2 | 5.60 | 8.08 | | escaldadura_pie | Pie escaldado (outcome) |
| E09 | 9 | 41 | corte | 2 | 5.15 | 6.66 | | corte_tijera_dedos | Tijera corta entre los dedos |
| E10 | 10 | 27 | aplastamiento | 2 | 4.29 | 5.82 | | aplastamiento_cortaunias | Cortaúñas corta piel de más |
| E11 | 11 | 55 | inyección | 2 | 4.29 | 5.63 | | inyeccion_muneca | Jeringa en la muñeca |
| E12 | 12 | 52 | punzante | 2 | 4.23 | 5.76 | | punzante_erizo_mar | Manos sostienen un erizo de mar |
| E13 | 13 | 39 | corte | 3 | 4.81 | 6.39 | | corte_hoja_mano | Mano empuña la hoja del cuchillo |
| E14 | 14 | 53 | quemadura | 4 | 4.53 | 6.65 | | quemadura_fosforo | Fósforo encendido quema los dedos |
| E15 | 15 | 36 | aplastamiento | 3 | 4.24 | 6.34 | | aplastamiento_abrochadora | Abrochadora sobre la mano |
| E16 | 16 | 29 | punzante | 3 | 4.15 | 5.79 | | punzante_chinches | Pie pisa chinches |
| E17 | 17 | 60 | inyección | 3 | 3.95 | 5.18 | | inyeccion_antebrazo | Jeringa inyecta el antebrazo |
| E18 | 18 | 37 | aplastamiento | 4 | 4.21 | 5.95 | | aplastamiento_pinza | Pinza aprieta el dedo |

Reproducir / actualizar: `run scripts/epss_roster.py` (edita `EXCLUDE`, `RECAT` o
`SLUGS` ahí si cambia algún criterio).
