"""Fase A bis - Protocolo de seleccion sistematica del set de estimulos (E01-E18).

Reemplaza el `score` compuesto (pesos opacos) por una regla transparente y
reproducible, pensada para describirse tal cual en la seccion de Metodos del paper:

  1. ELEGIBILIDAD. Partiendo de los 68 pares EPSS-Limb, se excluyen solo los
     pares que NO se pueden escenificar como un evento accidental/externo,
     animable onset->outcome, sobre un miembro claramente visible (lista
     EXCLUDE, con motivo). La capacidad/moderacion del modelo NO es criterio
     (lo explicito se genera con flux/dev). La connotacion de autolesion NO
     excluye: se trata como instruccion de encuadre (escenificar como accidente).

  2. RECATEGORIZACION. `estado_herida` es una etiqueta de FORMATO (estado ya
     consumado), no una modalidad de lesion. Se recategoriza por la lesion real
     (RECAT); el desenlace consumado se usa como OUTCOME (frame final) del video,
     diseniando nosotros el evento de onset.

  3. RANKING. Dentro de cada categoria, los pares elegibles se ordenan por
     `pain_delta` descendente (= contraste de dolor, la metrica alineada con lo
     que se manipula). Desempate: `pain_pain` desc, luego nro de par asc.

  4. ESTRATIFICACION. Se asignan N_TOTAL=18 cupos a las 5 categorias en forma
     balanceada: base = 18//5 = 3 por categoria; los 3 cupos restantes van a las
     categorias cuyo 4to par (por delta) es mas fuerte. Se recorre round-robin
     (1ro de cada categoria, luego 2do, ...); dentro de cada ronda las categorias
     se ordenan por el delta del par que se coloca (mas fuerte primero), de modo
     que la secuencia global decae de mayor a menor contraste manteniendo balance.

  ANCLAS. E01 = par 3 (piloto canonico, corte de pepino) quedo fijado antes de
  cerrar el protocolo: se conserva (grandfathered) y ocupa un cupo de `corte`,
  desplazando al 4to corte por ranking. E02 = par 50: nacio como quemadura
  (cigarrillo) pero se RE-DEFINIO a PUNZANTE (lapiz con la punta sobre el dorso;
  ver dataset/E02_lapiz_punzante_dorso/E02_meta.json). Se mantiene vinculado al
  par 50 (decision 2026-06-13) pero cuenta como PUNZANTE en la estratificacion
  (via RECAT). Ambas anclas se respetan; el resto (E03-E18) sigue el orden del
  protocolo.

  TODO (rebalanceo pendiente, 2026-06-13). Al pasar E02 de quemadura a punzante,
  la estratificacion nominal queda quemadura -1 / punzante +1 (3/4 en vez de 4/3).
  Decision acordada: sumar UNA quemadura mas ("lo vemos despues"). Hasta resolver
  eso NO se regenera el roster de produccion: analysis/epss_limb_roster.csv tiene
  E02 como OVERRIDE MANUAL (punzante) y NO refleja una corrida limpia de este
  script (re-correrlo reordenaria E03-E18 y recalcularia cupos). Definir la cuota
  final (p. ej. N_TOTAL=19, o mover un cupo entre categorias) y recien ahi correr.

  selection_rank = orden de PRODUCCION/prioridad, NO orden de presentacion al
  participante (eso se contrabalancea/aleatoriza en el experimento).

No consume API: todo local. Lee analysis/epss_limb_selection.csv; escribe las
columnas de roster de vuelta en ese CSV y un tidy analysis/epss_limb_roster.csv.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / "analysis" / "epss_limb_selection.csv"
ROSTER = ROOT / "analysis" / "epss_limb_roster.csv"

N_TOTAL = 18
CATEGORIES = ["corte", "quemadura", "punzante", "aplastamiento", "inyeccion"]

# --- Parametros del protocolo (editables; documentados en docs/PROTOCOLO_SELECCION.md) ---

# Pares NO escenificables como accidente externo animable sobre miembro visible.
# (Autolesion NO entra aca: se reencuadra como accidente en la puesta en escena.)
EXCLUDE = {
    6:  "animable: insecto vivo, sin agente discreto controlable",
    28: "ambiguo: evento clavo/bisagra poco legible",
    31: "visibilidad: pie cubierto por calzado, lesion no visible",
    32: "modalidad: torsion autoinfligida, fuera del esquema de 5 categorias",
    51: "montaje: soporte artificial, escena no accidental",
    56: "estatico: cuchillo apoyado, sin evento onset->outcome",
    59: "ambiguo: instrumento no legible como lesion clara",
}

# estado_herida -> modalidad real de la lesion (desenlace = OUTCOME del video).
# 50: re-definido de quemadura (cigarrillo) a punzante (lapiz punta), sigue ligado
#     al par 50 pero estratifica como punzante (ver docstring, TODO de rebalanceo).
RECAT = {62: "quemadura", 67: "quemadura", 50: "punzante"}

# Anclas fijas.
PILOT = 3        # E01 - piloto canonico (corte de pepino), grandfathered
ANCHOR_E02 = 50  # E02 - par 50 (vinculo mantenido); re-definido a punzante (lapiz). Ver RECAT.

# Slugs sugeridos (renombrables) para cada par, derivados de la nota EPSS.
SLUGS = {
    3:  "corte_pepino",            50: "lapiz_punzante_dorso",
    62: "quemadura_pie_grave",     46: "corte_muneca",
    58: "punzante_tijera_antebrazo", 11: "aplastamiento_taco_pie",
    48: "inyeccion_codo",          67: "escaldadura_pie",
    41: "corte_tijera_dedos",      27: "aplastamiento_cortaunias",
    55: "inyeccion_muneca",        52: "punzante_erizo_mar",
    39: "corte_hoja_mano",         53: "quemadura_fosforo",
    36: "aplastamiento_abrochadora", 29: "punzante_chinches",
    60: "inyeccion_antebrazo",     37: "aplastamiento_pinza",
}


def load_rows():
    with open(SEL, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["pair"] = int(r["pair"])
        r["pain_delta"] = float(r["pain_delta"])
        r["pain_pain"] = float(r["pain_pain"])
        r["cat_final"] = RECAT.get(r["pair"], r["categoria"])
    return rows


def build_roster(rows):
    by_pair = {r["pair"]: r for r in rows}

    # 1-3. Elegibles, agrupados por categoria final, ordenados por delta.
    eligible = [r for r in rows if r["pair"] not in EXCLUDE and r["cat_final"] in CATEGORIES]
    sort_key = lambda r: (-r["pain_delta"], -r["pain_pain"], r["pair"])
    by_cat = {c: sorted([r for r in eligible if r["cat_final"] == c], key=sort_key)
              for c in CATEGORIES}

    # 4. Cupos por categoria: base + extras a las de 4to par mas fuerte.
    base, extra = divmod(N_TOTAL, len(CATEGORIES))  # 3, 3
    fourth = sorted(CATEGORIES,
                    key=lambda c: (by_cat[c][base]["pain_delta"] if len(by_cat[c]) > base else -99),
                    reverse=True)
    quota = {c: base + (1 if c in fourth[:extra] else 0) for c in CATEGORIES}

    # Seleccion por categoria (top-k). Piloto grandfathered en 'corte'.
    selected = {c: [r["pair"] for r in by_cat[c][:quota[c]]] for c in CATEGORIES}
    pilot_cat = by_pair[PILOT]["cat_final"]
    if PILOT not in selected[pilot_cat]:
        selected[pilot_cat] = [p for p in selected[pilot_cat][:-1]] + [PILOT]
    # Reordenar cada categoria por ranking (delta), con el par dentro.
    for c in CATEGORIES:
        selected[c] = sorted(selected[c], key=lambda p: sort_key(by_pair[p]))

    # category_rank (1-based) dentro de la categoria seleccionada.
    cat_rank = {p: i + 1 for c in CATEGORIES for i, p in enumerate(selected[c])}

    # Anclas + round-robin para el resto.
    roster = [PILOT, ANCHOR_E02]
    queues = {c: [p for p in selected[c] if p not in roster] for c in CATEGORIES}
    max_rounds = max(len(q) for q in queues.values())
    for rnd in range(max_rounds):
        ronda = [(c, queues[c][rnd]) for c in CATEGORIES if rnd < len(queues[c])]
        ronda.sort(key=lambda cp: sort_key(by_pair[cp[1]]))
        roster += [p for _, p in ronda]

    assert len(roster) == N_TOTAL, f"roster={len(roster)} != {N_TOTAL}"
    return roster, cat_rank, quota, selected, by_pair


def main():
    rows = load_rows()
    roster, cat_rank, quota, selected, by_pair = build_roster(rows)

    rank_of = {pair: i + 1 for i, pair in enumerate(roster)}
    sid_of = {pair: f"E{i + 1:02d}" for i, pair in enumerate(roster)}

    # Augmentar el CSV de seleccion con las columnas del protocolo.
    new_cols = ["incluido", "exclude_reason", "cat_final", "category_rank",
                "stimulus_id", "selection_rank", "slug_sugerido"]
    with open(SEL, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        base_cols = reader.fieldnames
    for r in rows:
        p = r["pair"]
        r["incluido"] = "1" if p in rank_of else "0"
        r["exclude_reason"] = EXCLUDE.get(p, "")
        r["category_rank"] = cat_rank.get(p, "")
        r["stimulus_id"] = sid_of.get(p, "")
        r["selection_rank"] = rank_of.get(p, "")
        r["slug_sugerido"] = SLUGS.get(p, "")
    out_cols = base_cols + [c for c in new_cols if c not in base_cols]
    with open(SEL, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in sorted(rows, key=lambda r: r["pair"]):
            w.writerow({k: r.get(k, "") for k in out_cols})

    # Tidy roster (solo los 18, en orden de produccion).
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stimulus_id", "selection_rank", "epss_pair", "categoria",
                    "category_rank", "pain_delta", "pain_pain", "slug_sugerido",
                    "es_ancla", "nota_epss"])
        for i, p in enumerate(roster):
            r = by_pair[p]
            ancla = "piloto" if p == PILOT else ("acordada" if p == ANCHOR_E02 else "")
            w.writerow([sid_of[p], i + 1, p, r["cat_final"], cat_rank[p],
                        r["pain_delta"], r["pain_pain"], SLUGS.get(p, ""),
                        ancla, r.get("nota", "")])

    # Reporte por consola.
    print(f"Cupos por categoria: {quota}  (total {sum(quota.values())})")
    print(f"Excluidos ({len(EXCLUDE)}): {sorted(EXCLUDE)}")
    print(f"Recategorizados: {RECAT}\n")
    print(f"{'ID':<5}{'rank':<5}{'par':<5}{'categoria':<15}{'c_rk':<5}"
          f"{'delta':<7}{'ancla':<9}slug")
    for i, p in enumerate(roster):
        r = by_pair[p]
        ancla = "piloto" if p == PILOT else ("acordada" if p == ANCHOR_E02 else "")
        print(f"{sid_of[p]:<5}{i+1:<5}{p:<5}{r['cat_final']:<15}{cat_rank[p]:<5}"
              f"{r['pain_delta']:<7}{ancla:<9}{SLUGS.get(p, '')}")
    print(f"\nOK -> {SEL.name} (+columnas)  y  {ROSTER.name}")


if __name__ == "__main__":
    main()
