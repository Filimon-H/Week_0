from pathlib import Path
import pandas as pd

def coerce_numeric(df: pd.DataFrame, cols):
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out

def daylight_filter(df: pd.DataFrame, ghi_col: str = "GHI", threshold: float = 20.0):
    if ghi_col not in df.columns:
        return df.copy()
    return df[df[ghi_col] > threshold].copy()

def find_country_files(data_dir: Path):
    """
    Auto-map common filenames to country labels if present in ./data:
    - benin*clean.csv -> 'Benin'
    - togo*clean.csv -> 'Togo'
    - sierraleone*clean.csv / sierra*clean.csv -> 'Sierra Leone'
    Returns dict {country: path}
    """
    mapping = {}
    if not data_dir.exists():
        return mapping

    globs = {
        "Benin": ["benin*clean.csv", "benin_*.csv", "benin.csv"],
        "Togo": ["togo*clean.csv", "togo_*.csv", "togo.csv"],
        "Sierra Leone": ["sierraleone*clean.csv", "sierra*clean.csv", "sierraleone.csv"],
    }
    for country, patterns in globs.items():
        for pat in patterns:
            found = list(data_dir.glob(pat))
            if found:
                mapping[country] = str(found[0])
                break
    return mapping
