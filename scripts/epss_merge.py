"""Fase A - paso final: cruza normas EPSS-Limb con el screening visual.

Salida: analysis/epss_limb_selection.csv (tabla completa) + shortlist propuesta.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis"

SHORTLIST = {
    "corte": [3, 8, 17, 22, 41],
    "punzante": [29, 16, 52, 23],
    "quemadura": [50, 13, 15, 33, 61],
    "aplastamiento": [30, 19, 20, 63],
    "inyeccion": [48, 68],
}

norms = pd.read_csv(OUT / "epss_limb_pairs.csv").set_index("pair")
visual = pd.read_csv(OUT / "epss_limb_screening_visual.csv").set_index("pair")
t = norms.join(visual)

flat = [p for ps in SHORTLIST.values() for p in ps]
t["shortlist"] = t.index.isin(flat)

t = t.sort_values(["shortlist", "score"], ascending=[False, False])
cols = [
    "categoria", "shortlist", "score", "pain_pain", "pain_nopain", "pain_delta",
    "arousal_delta", "valence_pain", "credibilidad", "imaginabilidad_1p",
    "aptitud_video", "actor_gender", "nota",
]
t[cols].to_csv(OUT / "epss_limb_selection.csv")

print(f"Shortlist: {len(flat)} pares")
print(t[t["shortlist"]][["categoria", "score", "pain_delta", "credibilidad", "aptitud_video", "nota"]].to_string())
print("\nExcluidos notables (alto score normativo pero descartados):")
for p, why in [(62, "estado de herida, no accion"), (67, "estado de herida, no accion"),
               (46, "connotacion de autolesion (cuchillo en muneca)"),
               (58, "tijera clavandose en antebrazo: cuasi-agresion, evaluar con Mariana"),
               (51, "montaje poco natural"), (59, "accion ambigua")]:
    print(f"  par {p} (score {norms.loc[p,'score']}): {why}")
