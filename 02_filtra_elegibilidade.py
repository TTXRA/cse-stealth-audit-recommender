import pandas as pd
from utils import norm_text, normalize_columns, require_cols, require_unique, parse_bin01
from config import (
    IN_DIR,
    MID_DIR,
    OUT_ELEGIVEIS_DIR,
    MID_CORPUS_JANELA,
    INPUT_ROTULOS_ELEG,
    MID_CORPUS_EMP_QUANT,
    OUT_ELEG_FER,
    OUT_ELEG_SER,
    OUT_ELEG_MULTI,
    TAREFAS_VALIDAS,
)

IN_DIR.mkdir(parents=True, exist_ok=True)
MID_DIR.mkdir(parents=True, exist_ok=True)
OUT_ELEGIVEIS_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(MID_CORPUS_JANELA, dtype=str, keep_default_na=False)
df = normalize_columns(df)
require_cols(df, ["artigo_id", "ano", "tarefa", "titulo", "venue", "doi"], MID_CORPUS_JANELA.name)
require_unique(df, "artigo_id", MID_CORPUS_JANELA.name)
df["artigo_id"] = df["artigo_id"].map(norm_text)

rot = pd.read_csv(INPUT_ROTULOS_ELEG, dtype=str, keep_default_na=False)
rot = normalize_columns(rot)
require_cols(rot, ["artigo_id", "empirico", "quantitativo"], INPUT_ROTULOS_ELEG.name)
require_unique(rot, "artigo_id", INPUT_ROTULOS_ELEG.name)
rot["artigo_id"] = rot["artigo_id"].map(norm_text)

rot["empirico"] = parse_bin01(rot["empirico"], "empirico", rot["artigo_id"])
rot["quantitativo"] = parse_bin01(rot["quantitativo"], "quantitativo", rot["artigo_id"])

df2 = df.merge(rot[["artigo_id", "empirico", "quantitativo"]], on="artigo_id", how="left")

falt = df2["empirico"].isna() | df2["quantitativo"].isna()
if falt.any():
    raise ValueError("Faltou rotular (empirico/quantitativo) para: " + ", ".join(df2.loc[falt, "artigo_id"].tolist()))

df_eq = df2[(df2["empirico"] == 1) & (df2["quantitativo"] == 1)].copy()

df_eq["tarefa"] = df_eq["tarefa"].map(lambda x: norm_text(x).upper() if norm_text(x) != "" else "NA")
inv = ~df_eq["tarefa"].isin(TAREFAS_VALIDAS)
if inv.any():
    raise ValueError("tarefa inválida em: " + ", ".join(df_eq.loc[inv, "artigo_id"].tolist()))

df_eq = df_eq.drop(columns=["empirico", "quantitativo"])
df_eq.to_csv(MID_CORPUS_EMP_QUANT, index=False)

df_eq[df_eq["tarefa"] == "FER"].to_csv(OUT_ELEG_FER, index=False)
df_eq[df_eq["tarefa"] == "SER"].to_csv(OUT_ELEG_SER, index=False)
df_eq[df_eq["tarefa"] == "MULTI"].to_csv(OUT_ELEG_MULTI, index=False)
