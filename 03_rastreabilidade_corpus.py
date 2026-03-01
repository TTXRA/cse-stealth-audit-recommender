import pandas as pd
from utils import norm_text, normalize_columns, require_cols, require_unique, parse_bin01, read_csv
from config import (
    IN_DIR,
    MID_DIR,
    OUT_ELEGIVEIS_DIR,
    OUT_PRISMA_DIR,
    MID_CORPUS_PADRONIZADO,
    INPUT_ROTULOS_ELEG,
    MID_CORPUS_EMP_QUANT,
    OUT_ELEG_FER,
    OUT_ELEG_SER,
    OUT_ELEG_MULTI,
    OUT_EXCLUIDOS,
    OUT_PRISMA,
    ANO_INICIO,
    ANO_FIM,
)

IN_DIR.mkdir(parents=True, exist_ok=True)
MID_DIR.mkdir(parents=True, exist_ok=True)
OUT_ELEGIVEIS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PRISMA_DIR.mkdir(parents=True, exist_ok=True)

def read(path, usecols=None):
    return read_csv(path, usecols=usecols)

df_pad = read(MID_CORPUS_PADRONIZADO)
df_pad = normalize_columns(df_pad)
require_cols(df_pad, ["artigo_id", "ano"], MID_CORPUS_PADRONIZADO.name)
require_unique(df_pad, "artigo_id", MID_CORPUS_PADRONIZADO.name)

df_pad["ano"] = pd.to_numeric(df_pad["ano"].map(norm_text), errors="coerce").astype("Int64")
if df_pad["ano"].isna().any():
    raise ValueError("ano inválido em corpus_padronizado para: " + ", ".join(df_pad.loc[df_pad["ano"].isna(), "artigo_id"].tolist()))

mask_janela = df_pad["ano"].between(ANO_INICIO, ANO_FIM, inclusive="both")
janela_ids = set(df_pad.loc[mask_janela, "artigo_id"].tolist())

rot = read(INPUT_ROTULOS_ELEG)
rot = normalize_columns(rot)
require_cols(rot, ["artigo_id", "empirico", "quantitativo"], INPUT_ROTULOS_ELEG.name)
require_unique(rot, "artigo_id", INPUT_ROTULOS_ELEG.name)

rot["artigo_id"] = rot["artigo_id"].map(norm_text)
rot["empirico"] = parse_bin01(rot["empirico"], "empirico", rot["artigo_id"])
rot["quantitativo"] = parse_bin01(rot["quantitativo"], "quantitativo", rot["artigo_id"])

rot_j = rot[rot["artigo_id"].isin(janela_ids)].copy()
falt = rot_j["empirico"].isna() | rot_j["quantitativo"].isna()
if falt.any():
    raise ValueError("Faltou rotular (empirico/quantitativo) para: " + ", ".join(rot_j.loc[falt, "artigo_id"].tolist()))

excl = []

fora = df_pad.loc[~mask_janela, ["artigo_id"]].copy()
if len(fora) > 0:
    fora["motivo_exclusao"] = f"fora_janela_{ANO_INICIO}_{ANO_FIM}"
    excl.append(fora)

nao_emp = rot_j[rot_j["empirico"] == 0][["artigo_id"]].copy()
if len(nao_emp) > 0:
    nao_emp["motivo_exclusao"] = "nao_empirico"
    excl.append(nao_emp)

sem_q = rot_j[(rot_j["empirico"] == 1) & (rot_j["quantitativo"] == 0)][["artigo_id"]].copy()
if len(sem_q) > 0:
    sem_q["motivo_exclusao"] = "sem_resultados_quantitativos"
    excl.append(sem_q)

df_eq = read(MID_CORPUS_EMP_QUANT, usecols=["artigo_id", "tarefa"])
df_eq = normalize_columns(df_eq)
require_cols(df_eq, ["artigo_id", "tarefa"], MID_CORPUS_EMP_QUANT.name)
require_unique(df_eq, "artigo_id", MID_CORPUS_EMP_QUANT.name)

df_eq["tarefa"] = df_eq["tarefa"].map(lambda x: norm_text(x).upper() if norm_text(x) != "" else "NA")
na_task = df_eq[df_eq["tarefa"] == "NA"][["artigo_id"]].copy()
if len(na_task) > 0:
    na_task["motivo_exclusao"] = "tarefa_na_fora_estratos"
    excl.append(na_task)

if excl:
    excl_df = pd.concat(excl, ignore_index=True).sort_values(["artigo_id"], kind="stable")
    dup = excl_df["artigo_id"].duplicated(keep=False)
    if dup.any():
        ids = excl_df.loc[dup, "artigo_id"].unique().tolist()
        raise ValueError("artigo_id com múltiplos motivos em excluidos (conflito): " + ", ".join(ids))
    excl_df.to_csv(OUT_EXCLUIDOS, index=False)
else:
    pd.DataFrame(columns=["artigo_id", "motivo_exclusao"]).to_csv(OUT_EXCLUIDOS, index=False)

n_pad = int(df_pad["artigo_id"].nunique())
n_jan = int(df_pad.loc[mask_janela, "artigo_id"].nunique())
n_emp = int(rot_j[rot_j["empirico"] == 1]["artigo_id"].nunique())
n_eq = int(rot_j[(rot_j["empirico"] == 1) & (rot_j["quantitativo"] == 1)]["artigo_id"].nunique())

df_fer = read(OUT_ELEG_FER, usecols=["artigo_id"])
require_cols(df_fer, ["artigo_id"], OUT_ELEG_FER.name)
n_fer = int(df_fer["artigo_id"].nunique())

df_ser = read(OUT_ELEG_SER, usecols=["artigo_id"])
require_cols(df_ser, ["artigo_id"], OUT_ELEG_SER.name)
n_ser = int(df_ser["artigo_id"].nunique())

df_multi = read(OUT_ELEG_MULTI, usecols=["artigo_id"])
require_cols(df_multi, ["artigo_id"], OUT_ELEG_MULTI.name)
n_multi = int(df_multi["artigo_id"].nunique())

n_na = int(na_task["artigo_id"].nunique())
n_in_strata = n_fer + n_ser + n_multi

prisma = pd.DataFrame([
    {"etapa": "corpus_padronizado", "n": n_pad},
    {"etapa": "apos_filtro_janela", "n": n_jan},
    {"etapa": "apos_filtro_empirico", "n": n_emp},
    {"etapa": "apos_filtro_quantitativo", "n": n_eq},
    {"etapa": "elegiveis_FER", "n": n_fer},
    {"etapa": "elegiveis_SER", "n": n_ser},
    {"etapa": "elegiveis_MULTI", "n": n_multi},
    {"etapa": "fora_estratos_tarefa_NA", "n": n_na},
    {"etapa": "elegiveis_em_estratos", "n": n_in_strata},
])
prisma.to_csv(OUT_PRISMA, index=False)
