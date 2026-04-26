import pandas as pd

from scripts.utils.common import norm_text, normalize_columns, require_cols, require_unique, read_csv, sha256_file
from scripts.utils.config import (OUT_LOGS_DIR, OUT_PRISMA_DIR, OUT_PRISMA, AMOSTRA_POR_TAREFA, ELEGIVEIS_POR_TAREFA)

OUT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PRISMA_DIR.mkdir(parents=True, exist_ok=True)

ESTRATOS = ["FER", "SER", "MULTI"]
OUT_PRISMA_FINAL = OUT_PRISMA_DIR / "prisma_final.csv"

def read_ids(path):
    df = read_csv(path)
    df = normalize_columns(df)
    require_cols(df, ["artigo_id"], path.name)
    df["artigo_id"] = df["artigo_id"].map(norm_text)
    df = df[df["artigo_id"].ne("")]
    require_unique(df, "artigo_id", path.name)
    return df["artigo_id"].tolist()

def read_amostra(path):
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de amostra não encontrado: {path.as_posix()}")
    df = read_csv(path)
    df = normalize_columns(df)
    require_cols(df, ["artigo_id", "estrato", "tipo"], path.name)
    df["artigo_id"] = df["artigo_id"].map(norm_text)
    df["estrato"] = df["estrato"].map(lambda x: norm_text(x).upper())
    df["tipo"] = df["tipo"].map(lambda x: norm_text(x).lower())
    df = df[df["artigo_id"].ne("")]
    return df

def main():
    prisma = read_csv(OUT_PRISMA)
    prisma = normalize_columns(prisma)
    require_cols(prisma, ["etapa", "n"], OUT_PRISMA.name)

    prisma["etapa"] = prisma["etapa"].map(norm_text)
    prisma["n"] = pd.to_numeric(prisma["n"], errors="coerce").astype("Int64")
    if prisma["n"].isna().any():
        raise ValueError("Campo n inválido em OUT_PRISMA para: " + ", ".join(prisma.loc[prisma["n"].isna(), "etapa"].tolist()))

    remover = {
        "amostra_final_FER",
        "amostra_final_SER",
        "amostra_final_MULTI",
        "amostra_final_total",
        "suplentes_FER",
        "suplentes_SER",
        "suplentes_MULTI",
        "suplentes_total",
    }
    prisma = prisma[~prisma["etapa"].isin(remover)].copy()

    cont_tit = {}
    cont_sup = {}

    for s in ESTRATOS:
        eleg_ids = set(read_ids(ELEGIVEIS_POR_TAREFA[s]))
        df_a = read_amostra(AMOSTRA_POR_TAREFA[s])
        df_a = df_a[df_a["estrato"] == s].copy()

        tit = df_a[df_a["tipo"] == "titular"]["artigo_id"].drop_duplicates().tolist()
        sup = df_a[df_a["tipo"] == "suplente"]["artigo_id"].drop_duplicates().tolist()

        falt = sorted(list(set(tit) - eleg_ids))
        if falt:
            raise ValueError(f"Amostra {s} contém titulares fora dos elegíveis: " + ", ".join(falt))

        cont_tit[s] = int(len(tit))
        cont_sup[s] = int(len(sup))

    n_amostra_total = sum(cont_tit.values())
    n_supl_total = sum(cont_sup.values())

    linhas = []
    for s in ESTRATOS:
        linhas.append({"etapa": f"amostra_final_{s}", "n": cont_tit[s]})
    linhas.append({"etapa": "amostra_final_total", "n": n_amostra_total})

    for s in ESTRATOS:
        linhas.append({"etapa": f"suplentes_{s}", "n": cont_sup[s]})
    linhas.append({"etapa": "suplentes_total", "n": n_supl_total})

    prisma_final = pd.concat([prisma, pd.DataFrame(linhas)], ignore_index=True)
    prisma_final.to_csv(OUT_PRISMA_FINAL, index=False)
    OUT_PRISMA_FINAL.with_suffix(".sha256").write_text(sha256_file(OUT_PRISMA_FINAL) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
