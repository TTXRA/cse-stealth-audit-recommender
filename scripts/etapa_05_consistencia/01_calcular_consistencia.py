import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from scripts.utils.common import norm_text, normalize_columns, require_cols, read_csv, sha256_file
from scripts.utils.config import (AUDIT_DIR, OUT_CONSISTENCIA_DIR, INPUT_AUDITORIA, INPUT_RETESTE,
                                  OUT_PAREAMENTO_ITEM_A_ITEM, OUT_KAPPA_ITENS_NUCLEARES, OUT_SCORES_AUDITORIA,
                                  OUT_SCORES_RETESTE, OUT_SCORES_PAREADOS, OUT_ICC_3_1, OUT_RESUMO_VALIDACAO, PESO_KAPPA)

AUDIT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CONSISTENCIA_DIR.mkdir(parents=True, exist_ok=True)

KEY_COLS = ["artigo_id", "item_id"]
REQUIRED_COLS = ["artigo_id", "estrato", "item_id", "grau", "na", "justificativa_na", "evidencia", "observacoes"]
NUCLEAR_ITEMS = ["DAD", "ROT", "ESC", "PRT", "MOD", "MET", "REP", "VZ", "EXT"]


def require_unique_keys(df, cols, name):
    dup = df.duplicated(cols, keep=False)
    if dup.any():
        raise ValueError(
            f"Chaves duplicadas em {name} para {cols}:\n{df.loc[dup, cols].sort_values(cols).to_string(index=False)}"
        )


def load_audit_csv(path: Path) -> pd.DataFrame:
    df = read_csv(path)
    df = normalize_columns(df)
    require_cols(df, REQUIRED_COLS, path.name)

    df["artigo_id"] = df["artigo_id"].map(norm_text)
    df["item_id"] = df["item_id"].map(norm_text)
    df["estrato"] = df["estrato"].map(lambda x: norm_text(x).upper())
    df["justificativa_na"] = df["justificativa_na"].map(norm_text)
    df["evidencia"] = df["evidencia"].map(norm_text)
    df["observacoes"] = df["observacoes"].map(norm_text)

    df = df[df["artigo_id"].ne("") & df["item_id"].ne("")].copy()
    require_unique_keys(df, KEY_COLS, path.name)

    df["grau"] = pd.to_numeric(df["grau"].map(norm_text), errors="coerce").astype("Int64")
    df["na"] = pd.to_numeric(df["na"].map(norm_text), errors="coerce").astype("Int64")

    if df["grau"].isna().any():
        rows = df.index[df["grau"].isna()].tolist()
        raise ValueError(f"Valores inválidos em grau no arquivo {path.name}, linhas: {rows[:10]}")

    if df["na"].isna().any():
        rows = df.index[df["na"].isna()].tolist()
        raise ValueError(f"Valores inválidos em na no arquivo {path.name}, linhas: {rows[:10]}")

    bad_grau = sorted(df.loc[~df["grau"].isin([0, 1, 2]), "grau"].dropna().unique().tolist())
    bad_na = sorted(df.loc[~df["na"].isin([0, 1]), "na"].dropna().unique().tolist())

    if bad_grau:
        raise ValueError(f"Valores fora do domínio em grau no arquivo {path.name}: {bad_grau}")

    if bad_na:
        raise ValueError(f"Valores fora do domínio em na no arquivo {path.name}: {bad_na}")

    return df


def score_article(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["aplicavel"] = (x["na"] != 1).astype(int)
    x["grau_aplicavel"] = np.where(x["aplicavel"] == 1, x["grau"], 0)

    out = (
        x.groupby("artigo_id", as_index=False)
        .agg(
            estrato=("estrato", lambda s: s.dropna().astype(str).iloc[0] if len(s.dropna()) else np.nan),
            soma_graus_aplicaveis=("grau_aplicavel", "sum"),
            n_itens_aplicaveis=("aplicavel", "sum"),
            n_itens_na=("na", "sum"),
        )
    )

    out["score_global"] = np.where(
        out["n_itens_aplicaveis"] > 0,
        100 * out["soma_graus_aplicaveis"] / (2 * out["n_itens_aplicaveis"]),
        np.nan,
    )
    return out


def weighted_kappa(y1: pd.Series, y2: pd.Series, weighting: str = "quadratic") -> float:
    a = pd.to_numeric(y1, errors="coerce").to_numpy()
    b = pd.to_numeric(y2, errors="coerce").to_numpy()
    mask = ~(np.isnan(a) | np.isnan(b))
    a = a[mask].astype(int)
    b = b[mask].astype(int)

    if len(a) == 0:
        return np.nan

    if np.array_equal(a, b) and len(np.unique(np.r_[a, b])) == 1:
        return 1.0

    return float(cohen_kappa_score(a, b, labels=[0, 1, 2], weights=weighting))


def icc_3_1(scores_wide: pd.DataFrame, col1: str, col2: str) -> dict:
    x = scores_wide[[col1, col2]].dropna().to_numpy(dtype=float)
    n, k = x.shape

    if n < 2 or k != 2:
        return {
            "n_artigos": int(n),
            "k_avaliacoes": int(k),
            "MSR": np.nan,
            "MSC": np.nan,
            "MSE": np.nan,
            "ICC_3_1": np.nan,
        }

    grand_mean = x.mean()
    row_means = x.mean(axis=1, keepdims=True)
    col_means = x.mean(axis=0, keepdims=True)

    ss_total = ((x - grand_mean) ** 2).sum()
    ss_rows = k * ((row_means - grand_mean) ** 2).sum()
    ss_cols = n * ((col_means - grand_mean) ** 2).sum()
    ss_error = ss_total - ss_rows - ss_cols

    df_rows = n - 1
    df_cols = k - 1
    df_error = (n - 1) * (k - 1)

    msr = ss_rows / df_rows
    msc = ss_cols / df_cols if df_cols > 0 else np.nan
    mse = ss_error / df_error if df_error > 0 else np.nan
    icc = (msr - mse) / (msr + (k - 1) * mse) if (msr + (k - 1) * mse) != 0 else np.nan

    return {
        "n_artigos": int(n),
        "k_avaliacoes": int(k),
        "MSR": float(msr),
        "MSC": float(msc),
        "MSE": float(mse),
        "ICC_3_1": float(icc),
    }


def write_sha256(path: Path) -> None:
    path.with_suffix(path.suffix + ".sha256").write_text(sha256_file(path) + "\n", encoding="utf-8")


def main():
    audit = load_audit_csv(INPUT_AUDITORIA)
    retest = load_audit_csv(INPUT_RETESTE)

    artigos_audit = set(audit["artigo_id"])
    artigos_retest = set(retest["artigo_id"])
    artigos_comuns = sorted(artigos_audit & artigos_retest)

    audit_common = audit[audit["artigo_id"].isin(artigos_comuns)].copy()
    retest_common = retest[retest["artigo_id"].isin(artigos_comuns)].copy()

    pareado = audit_common.merge(
        retest_common,
        on=KEY_COLS,
        how="inner",
        suffixes=("_audit", "_retest"),
    )

    kappa_rows = []
    nuclear = pareado[pareado["item_id"].isin(NUCLEAR_ITEMS)].copy()

    for item, g in nuclear.groupby("item_id", sort=True):
        kappa_rows.append(
            {
                "item_id": item,
                "n_pares": int(len(g)),
                "graus_auditoria": json.dumps(g["grau_audit"].astype(int).tolist(), ensure_ascii=False),
                "graus_reteste": json.dumps(g["grau_retest"].astype(int).tolist(), ensure_ascii=False),
                "kappa_w": weighted_kappa(g["grau_audit"], g["grau_retest"], weighting=PESO_KAPPA),
            }
        )

    if kappa_rows:
        kappa_df = pd.DataFrame(kappa_rows).sort_values(["item_id"]).reset_index(drop=True)
    else:
        kappa_df = pd.DataFrame(columns=["item_id", "n_pares", "graus_auditoria", "graus_reteste", "kappa_w"])

    scores_audit = score_article(audit_common).rename(columns={"score_global": "score_global_auditoria"})
    scores_retest = score_article(retest_common).rename(columns={"score_global": "score_global_reteste"})

    scores_pareados = scores_audit.merge(
        scores_retest[["artigo_id", "score_global_reteste"]],
        on="artigo_id",
        how="inner",
    )

    icc_df = pd.DataFrame([icc_3_1(scores_pareados, "score_global_auditoria", "score_global_reteste")])

    resumo = {
        "artigos_auditoria": len(artigos_audit),
        "artigos_reteste": len(artigos_retest),
        "artigos_comuns": len(artigos_comuns),
        "pares_item_a_item": int(len(pareado)),
        "peso_kappa": PESO_KAPPA,
    }

    pareado.to_csv(OUT_PAREAMENTO_ITEM_A_ITEM, index=False)
    kappa_df.to_csv(OUT_KAPPA_ITENS_NUCLEARES, index=False)
    scores_audit.to_csv(OUT_SCORES_AUDITORIA, index=False)
    scores_retest.to_csv(OUT_SCORES_RETESTE, index=False)
    scores_pareados.to_csv(OUT_SCORES_PAREADOS, index=False)
    icc_df.to_csv(OUT_ICC_3_1, index=False)

    with open(OUT_RESUMO_VALIDACAO, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    write_sha256(OUT_PAREAMENTO_ITEM_A_ITEM)
    write_sha256(OUT_KAPPA_ITENS_NUCLEARES)
    write_sha256(OUT_SCORES_AUDITORIA)
    write_sha256(OUT_SCORES_RETESTE)
    write_sha256(OUT_SCORES_PAREADOS)
    write_sha256(OUT_ICC_3_1)

    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print("\nKappa ponderado por item nuclear:")
    print(kappa_df.to_string(index=False))
    print("\nICC(3,1) do escore global:")
    print(icc_df.to_string(index=False))


if __name__ == "__main__":
    main()