from pathlib import Path
from datetime import datetime
import json
import numpy as np
import pandas as pd

from utils import norm_text, normalize_columns, require_cols, require_unique, read_csv, sha256_file
from config import (
    OUT_AMOSTRAS_DIR,
    OUT_LOGS_DIR,
    ELEGIVEIS_POR_TAREFA,
    AMOSTRA_POR_TAREFA,
    OUT_REGISTRO_SORTEIO,
    MID_CORPUS_EMP_QUANT,
    RNG_SEED,
    N_ALVO_TOTAL,
    MIN_POR_ESTRATO,
    N_SUPLENTES,
    META_COLS,
    OUT_LOG_CONTINGENCIA,
    OUT_ALOCACAO_SORTEIO,
)

OUT_AMOSTRAS_DIR.mkdir(parents=True, exist_ok=True)
OUT_LOGS_DIR.mkdir(parents=True, exist_ok=True)

ESTRATOS = ["FER", "SER", "MULTI"]

def read_ids(path):
    df = read_csv(path)
    df = normalize_columns(df)
    require_cols(df, ["artigo_id"], path.name)
    df["artigo_id"] = df["artigo_id"].map(norm_text)
    df = df[df["artigo_id"].ne("")]
    require_unique(df, "artigo_id", path.name)
    return df["artigo_id"].tolist()

def read_meta():
    df = read_csv(MID_CORPUS_EMP_QUANT)
    df = normalize_columns(df)
    require_cols(df, ["artigo_id"], MID_CORPUS_EMP_QUANT.name)
    df["artigo_id"] = df["artigo_id"].map(norm_text)
    df = df[df["artigo_id"].ne("")]
    require_unique(df, "artigo_id", MID_CORPUS_EMP_QUANT.name)
    for c in META_COLS:
        if c not in df.columns:
            df[c] = ""
    df = df[META_COLS].copy()
    df["ano"] = pd.to_numeric(df["ano"].map(norm_text), errors="coerce").astype("Int64")
    return df

def redistribui(n_eleg, n_alvo_total, min_por_estrato):
    base = {e: min(int(min_por_estrato), int(n_eleg[e])) for e in ESTRATOS}
    n_base = sum(base.values())
    resto = int(n_alvo_total) - n_base
    if resto < 0:
        raise ValueError("N_ALVO_TOTAL menor que a soma dos mínimos aplicáveis.")
    cap = {e: max(0, int(n_eleg[e]) - int(base[e])) for e in ESTRATOS}
    cap_total = sum(cap.values())
    if resto > cap_total:
        raise ValueError("N_ALVO_TOTAL maior que o total elegível disponível nos estratos.")
    aloc = base.copy()
    if resto == 0:
        return aloc
    quotas = {e: (cap[e] / cap_total) * resto if cap_total > 0 else 0 for e in ESTRATOS}
    floors = {e: int(quotas[e] // 1) for e in ESTRATOS}
    aloc = {e: aloc[e] + floors[e] for e in ESTRATOS}
    rem = resto - sum(floors.values())
    frac = sorted(ESTRATOS, key=lambda e: (quotas[e] - floors[e], cap[e]), reverse=True)
    for i in range(rem):
        e = frac[i % len(frac)]
        if aloc[e] < n_eleg[e]:
            aloc[e] += 1
        else:
            for e2 in frac:
                if aloc[e2] < n_eleg[e2]:
                    aloc[e2] += 1
                    break
    return aloc

def sortear_estrato(estrato, df_meta_stratum, n_titulares, n_suplentes, rng):
    df = df_meta_stratum.copy()
    df = df.sort_values(["artigo_id"], kind="stable").reset_index(drop=True)
    df["numero_estrato"] = (df.index + 1).astype(int)

    perm = rng.permutation(len(df))
    df = df.iloc[perm].reset_index(drop=True)

    n_t = min(int(n_titulares), len(df))
    n_s = min(int(n_suplentes), max(0, len(df) - n_t))

    titulares = df.iloc[:n_t].copy()
    suplentes = df.iloc[n_t:n_t + n_s].copy()

    def pack(sub, tipo):
        if len(sub) == 0:
            return pd.DataFrame(columns=["estrato", "tipo", "ordem"] + META_COLS + ["numero_estrato"])
        out = sub.copy()
        out.insert(0, "ordem", (np.arange(len(out)) + 1).astype(int))
        out.insert(0, "tipo", tipo)
        out.insert(0, "estrato", estrato)
        cols = ["estrato", "tipo", "ordem"] + META_COLS + ["numero_estrato"]
        for c in cols:
            if c not in out.columns:
                out[c] = ""
        return out[cols]

    out_df = pd.concat([pack(titulares, "titular"), pack(suplentes, "suplente")], ignore_index=True)
    tit_ids = titulares["artigo_id"].tolist()
    sup_ids = suplentes["artigo_id"].tolist()
    return out_df, tit_ids, sup_ids, len(df)

def validate_params():
    if int(N_ALVO_TOTAL) <= 0 or int(MIN_POR_ESTRATO) < 0:
        raise ValueError("Parâmetros inválidos.")
    if int(MIN_POR_ESTRATO) * len(ESTRATOS) > int(N_ALVO_TOTAL):
        raise ValueError("MIN_POR_ESTRATO * n_estratos não pode ser maior que N_ALVO_TOTAL.")

def main():
    validate_params()

    ids = {s: read_ids(p) for s, p in ELEGIVEIS_POR_TAREFA.items()}
    meta = read_meta()

    dfs = {}
    counts = {}
    for s in ESTRATOS:
        id_list = ids.get(s, [])
        s_ids = set(id_list)
        m = meta[meta["artigo_id"].isin(s_ids)].copy()
        if m["artigo_id"].nunique() != len(s_ids):
            falt = sorted(list(s_ids - set(m["artigo_id"].tolist())))
            raise ValueError(f"Metadados faltando em {MID_CORPUS_EMP_QUANT.name} para {s}: " + ", ".join(falt))
        dfs[s] = m
        counts[s] = int(m["artigo_id"].nunique())

    faltantes = {e: max(0, int(MIN_POR_ESTRATO) - int(counts[e])) for e in ESTRATOS}
    aloc = redistribui(counts, N_ALVO_TOTAL, MIN_POR_ESTRATO)

    now = datetime.now().isoformat(timespec="seconds")
    script = Path(__file__).name

    log = pd.DataFrame([{
        "data_execucao": now,
        "script": script,
        "seed": RNG_SEED,
        "n_alvo_total": N_ALVO_TOTAL,
        "min_por_estrato": MIN_POR_ESTRATO,
        "fer_elegiveis": counts["FER"],
        "ser_elegiveis": counts["SER"],
        "multi_elegiveis": counts["MULTI"],
        "deficit_fer": faltantes["FER"],
        "deficit_ser": faltantes["SER"],
        "deficit_multi": faltantes["MULTI"],
        "acao": "redistribuicao_proporcional",
        "busca_complementar": "nao_aplicavel",
        "aloc_fer": aloc["FER"],
        "aloc_ser": aloc["SER"],
        "aloc_multi": aloc["MULTI"],
        "observacao": "sem busca complementar; texto integral assumido disponivel",
    }])
    log.to_csv(OUT_LOG_CONTINGENCIA, index=False)
    OUT_LOG_CONTINGENCIA.with_suffix(".sha256").write_text(sha256_file(OUT_LOG_CONTINGENCIA) + "\n", encoding="utf-8")

    pd.DataFrame([{"estrato": e, "n_titulares_planejado": aloc[e], "n_elegiveis": counts[e]} for e in ESTRATOS]).to_csv(OUT_ALOCACAO_SORTEIO, index=False)
    OUT_ALOCACAO_SORTEIO.with_suffix(".sha256").write_text(sha256_file(OUT_ALOCACAO_SORTEIO) + "\n", encoding="utf-8")

    rng = np.random.default_rng(RNG_SEED)

    registro_rows = []
    for s in ESTRATOS:
        df_out, tit_ids, sup_ids, n_eleg = sortear_estrato(s, dfs[s], aloc.get(s, 0), N_SUPLENTES, rng)
        df_out.to_csv(AMOSTRA_POR_TAREFA[s], index=False)
        h = sha256_file(AMOSTRA_POR_TAREFA[s])

        registro_rows.append({
            "data_execucao": now,
            "script": script,
            "seed": RNG_SEED,
            "n_alvo_total": N_ALVO_TOTAL,
            "min_por_estrato": MIN_POR_ESTRATO,
            "n_suplentes_por_estrato": N_SUPLENTES,
            "estrato": s,
            "n_elegiveis": n_eleg,
            "n_titulares": len(tit_ids),
            "n_suplentes": len(sup_ids),
            "titulares": json.dumps(tit_ids, ensure_ascii=False),
            "suplentes": json.dumps(sup_ids, ensure_ascii=False),
            "sha256_amostra_csv": h,
            "arquivo_amostra_csv": AMOSTRA_POR_TAREFA[s].as_posix(),
        })

    pd.DataFrame(registro_rows).to_csv(OUT_REGISTRO_SORTEIO, index=False)
    OUT_REGISTRO_SORTEIO.with_suffix(".sha256").write_text(sha256_file(OUT_REGISTRO_SORTEIO) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
