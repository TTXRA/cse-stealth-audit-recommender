import hashlib
import re
import numpy as np
import pandas as pd

_RE_SPACES = re.compile(r"\s+")

def norm_text(x):
    if pd.isna(x):
        return ""
    return _RE_SPACES.sub(" ", str(x)).strip()

def normalize_columns(df):
    df.columns = [norm_text(c).lower() for c in df.columns]
    return df

def require_cols(df, cols, name):
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise ValueError(f"Colunas obrigatórias ausentes em {name}: {miss}")

def require_unique(df, cols, name):
    cols = [cols] if isinstance(cols, str) else list(cols)
    dup = df.duplicated(cols, keep=False)
    if dup.any():
        raise ValueError(
            f"Chave duplicada em {name} para {cols}:\n{df.loc[dup, cols].sort_values(cols).to_string(index=False)}"
        )

def parse_bin01(series, label, id_series):
    s = pd.to_numeric(series.map(norm_text), errors="coerce").astype("Int64")
    bad = ~s.isin([0, 1])
    if bad.any():
        ids = id_series.loc[bad].tolist()
        raise ValueError(f"{label} deve ser 0 ou 1 para: " + ", ".join(ids))
    return s

def read_csv(path, usecols=None):
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path.as_posix()}")
    return pd.read_csv(path, dtype=str, keep_default_na=False, usecols=usecols)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_yes_no(x):
    if pd.isna(x):
        return np.nan
    v = str(x).strip().lower()
    mapa = {
        "sim": "sim",
        "yes": "sim",
        "true": "sim",
        "1": "sim",
        "nao": "nao",
        "não": "nao",
        "no": "nao",
        "false": "nao",
        "0": "nao",
    }
    return mapa.get(v, v)

def parse_fraction(x):
    if pd.isna(x):
        return np.nan
    x = float(x)
    if x > 1:
        return x / 100.0
    return x