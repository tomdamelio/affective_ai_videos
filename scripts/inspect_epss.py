"""Inspeccion rapida del archivo de normas EPSS-Limb."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
XLSX = (
    ROOT
    / "EPSS"
    / "Empathy for Limb Pain Picture Database (EPSS-Limb)"
    / "Empathy for Limb Pain Picture Database (EPSS-Limb)"
    / "EPSS-Limb data.xlsx"
)

xl = pd.ExcelFile(XLSX)
print("Hojas:", xl.sheet_names)
for sheet in xl.sheet_names:
    df = xl.parse(sheet)
    print(f"\n--- {sheet} --- shape={df.shape}")
    print("Primeras 8 columnas:", df.columns.tolist()[:8])
    print(df.iloc[:8, :6].to_string())
