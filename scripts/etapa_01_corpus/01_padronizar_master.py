import pandas as pd
from scripts.utils.common import norm_text, normalize_columns, require_cols, require_unique, read_csv
from scripts.utils.config import (IN_DIR, MID_DIR, INPUT_MAPEAMENTO_MASTER, MID_CORPUS_PADRONIZADO,
                                  MID_CORPUS_JANELA, ANO_INICIO, ANO_FIM, TAREFAS_VALIDAS)


def norm_tarefa(x):
    s = norm_text(x).upper()
    if s == "":
        return "NA"
    return s


def make_artigo_id(df):
    if "artigo_id" in df.columns and df["artigo_id"].astype(str).str.strip().ne("").any():
        df["artigo_id"] = df["artigo_id"].astype(str).str.strip()
        return df
    df = df.reset_index(drop=True)
    df["artigo_id"] = df.index.map(lambda i: f"ID_{i + 1:02d}")
    return df


IN_DIR.mkdir(parents=True, exist_ok=True)
MID_DIR.mkdir(parents=True, exist_ok=True)

if ANO_INICIO > ANO_FIM:
    raise ValueError("ANO_INICIO deve ser <= ANO_FIM")

df = read_csv(INPUT_MAPEAMENTO_MASTER)
df = normalize_columns(df)

required = ["titulo", "ano", "venue", "tarefa", "doi"]
require_cols(df, required, INPUT_MAPEAMENTO_MASTER.name)

df["titulo"] = df["titulo"].map(norm_text)
df["venue"] = df["venue"].map(norm_text)
df["doi"] = df["doi"].map(norm_text)

df["ano"] = pd.to_numeric(df["ano"].map(norm_text), errors="coerce").astype("Int64")
df["tarefa"] = df["tarefa"].map(norm_tarefa)

df = make_artigo_id(df)

df["elegivel_etapa1"] = ""
df["motivo_exclusao"] = ""
df["observacoes_elegibilidade"] = ""

require_unique(df, "artigo_id", MID_CORPUS_PADRONIZADO.name)

errs = []
if df["ano"].isna().any():
    errs.append("ano inválido em: " + ", ".join(df.loc[df["ano"].isna(), "artigo_id"].tolist()))
inv_task = ~df["tarefa"].isin(TAREFAS_VALIDAS)
if inv_task.any():
    errs.append("tarefa inválida em: " + ", ".join(df.loc[inv_task, "artigo_id"].tolist()))
if errs:
    raise ValueError("\n".join(errs))

cols = [
    "artigo_id",
    "ano",
    "tarefa",
    "titulo",
    "venue",
    "doi",
    "elegivel_etapa1",
    "motivo_exclusao",
    "observacoes_elegibilidade",
]
df = df[cols].sort_values(["tarefa", "ano", "artigo_id"], kind="stable")

df.to_csv(MID_CORPUS_PADRONIZADO, index=False)

mask = df["ano"].between(ANO_INICIO, ANO_FIM, inclusive="both")
df.loc[mask].to_csv(MID_CORPUS_JANELA, index=False)
