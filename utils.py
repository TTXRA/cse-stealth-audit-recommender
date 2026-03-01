import hashlib
import re
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

def require_unique(df, col, name):
    if df[col].duplicated().any():
        dups = df.loc[df[col].duplicated(), col].tolist()
        raise ValueError(f"{col} duplicado em {name}: " + ", ".join(dups))

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