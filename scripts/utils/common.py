import hashlib
import json
import re

import numpy as np
import pandas as pd

from scripts.utils.config import MAPA_FAMILIAS

_RE_SPACES = re.compile(r"\s+")


def norm_text(x):
    if pd.isna(x):
        return ""
    return _RE_SPACES.sub(" ", str(x)).strip()


def normalize_columns(df):
    df.columns = [norm_text(c).lower() for c in df.columns]
    return df


def remove_unnamed_columns(df):
    return df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed:")].copy()


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


def write_sha256(path):
    path.with_suffix(".sha256").write_text(sha256_file(path) + "\n", encoding="utf-8")


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


def is_missing(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (float, np.floating)):
        return bool(np.isnan(value))
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def as_text(value):
    if is_missing(value):
        return None
    value = str(value).strip()
    return None if value.lower() in {"nan", "none", "null"} else value


def normalizar_dominio(coluna, value):
    value = as_text(value)

    if value is None:
        return None

    if coluna == "modalidade":
        return value.upper()

    if coluna == "modelo_familia":
        return MAPA_FAMILIAS.get(value, MAPA_FAMILIAS.get(value.lower(), value))

    value = value.lower()

    if value == "não":
        value = "nao"

    if value in {"n/a", "na"}:
        return "NA"

    if coluna == "tarefa" and value in {"detecao", "detecção"}:
        return "deteccao"

    return value


def normalizar_lista(value):
    if is_missing(value):
        return None

    if isinstance(value, list):
        items = value
    else:
        value = str(value).strip()

        if value.lower() in {"nan", "none", "null", "na"}:
            return None

        try:
            parsed = json.loads(value)
            items = parsed if isinstance(parsed, list) else None
        except json.JSONDecodeError:
            sep = ";" if ";" in value else "," if "," in value else None
            items = [item.strip() for item in value.split(sep)] if sep else [value]

        if items is None:
            return None

    items = [item.lower() for item in (as_text(item) for item in items) if item is not None]
    return None if not items else json.dumps(sorted(dict.fromkeys(items)), ensure_ascii=False)