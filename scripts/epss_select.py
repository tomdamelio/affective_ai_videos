"""Fase A - Seleccion de estimulos EPSS-Limb.

1. Parsea las normas (EPSS-Limb data.xlsx: Pain intensity, Affective valance,
   Arousal, Dominance) y arma una tabla por par (N.1 = no doloroso, N.2 = doloroso).
2. Calcula metricas de seleccion (delta de dolor, delta de arousal, etc.).
3. Genera contact sheets (laminas con los pares lado a lado) para screening visual.

No consume API: todo local. Salidas en analysis/.
"""
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
LIMB_DIR = (
    ROOT
    / "EPSS"
    / "Empathy for Limb Pain Picture Database (EPSS-Limb)"
    / "Empathy for Limb Pain Picture Database (EPSS-Limb)"
)
XLSX = LIMB_DIR / "EPSS-Limb data.xlsx"
OUT_DIR = ROOT / "analysis"
SHEETS_DIR = OUT_DIR / "contact_sheets"

SHEET_METRIC = {
    "Pain intensity": "pain",
    "Affective valance": "valence",
    "Arousal": "arousal",
    "Dominance": "dominance",
}


def load_norms() -> pd.DataFrame:
    xl = pd.ExcelFile(XLSX)
    frames = []
    for sheet, metric in SHEET_METRIC.items():
        df = xl.parse(sheet)
        df = df.rename(
            columns={
                df.columns[0]: "name",
                df.columns[1]: "pain_flag",
                df.columns[2]: "actor_gender",
                df.columns[3]: f"{metric}_mean",
                df.columns[4]: f"{metric}_sd",
            }
        )
        df = df[["name", "pain_flag", "actor_gender", f"{metric}_mean", f"{metric}_sd"]]
        df = df.dropna(subset=["name"])
        df["name"] = df["name"].astype(float).round(1).astype(str)
        frames.append(df.set_index("name"))
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.join(f.drop(columns=["pain_flag", "actor_gender"]))
    merged = merged.reset_index()
    merged["pair"] = merged["name"].str.split(".").str[0].astype(int)
    merged["version"] = merged["name"].str.split(".").str[1].astype(int)
    return merged


def per_pair_table(norms: pd.DataFrame) -> pd.DataFrame:
    nopain = norms[norms["version"] == 1].set_index("pair")
    pain = norms[norms["version"] == 2].set_index("pair")
    t = pd.DataFrame(index=sorted(norms["pair"].unique()))
    t.index.name = "pair"
    t["actor_gender"] = pain["actor_gender"]
    for m in ["pain", "valence", "arousal", "dominance"]:
        t[f"{m}_pain"] = pain[f"{m}_mean"]
        t[f"{m}_nopain"] = nopain[f"{m}_mean"]
        t[f"{m}_delta"] = t[f"{m}_pain"] - t[f"{m}_nopain"]
    # Score compuesto (z-scores): contraste de dolor y arousal altos,
    # control limpio (dolor percibido bajo en N.1).
    z = lambda s: (s - s.mean()) / s.std()
    t["score"] = (
        z(t["pain_delta"]) + z(t["arousal_delta"]) - z(t["pain_nopain"])
    ).round(3)
    return t.round(2).sort_values("score", ascending=False)


def contact_sheets(pairs: list[int], per_sheet: int = 3) -> None:
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    w, h, label_h = 354, 266, 28
    for i in range(0, len(pairs), per_sheet):
        chunk = pairs[i : i + per_sheet]
        sheet = Image.new("RGB", (w * 2 + 30, (h + label_h) * len(chunk)), "white")
        draw = ImageDraw.Draw(sheet)
        for row, pair in enumerate(chunk):
            y = row * (h + label_h)
            draw.text((10, y + 6), f"Par {pair}:  izquierda = {pair}.1 (control)   derecha = {pair}.2 (dolor)", fill="black")
            for col, ver in enumerate([1, 2]):
                img = Image.open(LIMB_DIR / f"{pair}.{ver}.bmp").convert("RGB")
                sheet.paste(img, (col * (w + 30), y + label_h))
        out = SHEETS_DIR / f"sheet_{i // per_sheet + 1:02d}.png"
        sheet.save(out)
        print("OK", out.name, "pares:", chunk)


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    norms = load_norms()
    table = per_pair_table(norms)
    table.to_csv(OUT_DIR / "epss_limb_pairs.csv")
    print(f"{len(table)} pares procesados -> analysis/epss_limb_pairs.csv")
    print("\nTop 10 por score normativo:")
    print(table.head(10)[["pain_pain", "pain_nopain", "pain_delta", "arousal_delta", "score"]].to_string())
    contact_sheets(list(table.index))
