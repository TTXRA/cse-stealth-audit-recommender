import json

import numpy as np
import pandas as pd

from scripts.utils.common import (
    as_text,
    normalize_columns,
    normalizar_dominio,
    normalizar_lista,
    read_csv,
    remove_unnamed_columns,
    require_cols,
    write_sha256,
)
from scripts.utils.config import (
    ARQUIVO_LOG_RECOMENDACAO,
    ARQUIVO_RANKING_RECOMENDACAO,
    ARQUIVO_SAIDA_ROBUSTEZ_CLEAN,
    COLUNAS_RANKING,
    FILTROS_OBRIGATORIOS,
    FILTROS_OPCIONAIS,
    RECOMENDACAO_MIN_ARTIGOS_POR_FAMILIA,
    RECOMENDACAO_MIN_FAMILIAS,
    RECOMENDACAO_MIN_OBSERVACOES_AGREGADAS,
    RECOMENDACAO_N_BOOTSTRAP,
    RECOMENDACAO_RANDOM_SEED,
)


def bootstrap_ci(values, rng):
    if len(values) == 1:
        value = float(values[0])
        return value, value

    means = np.empty(RECOMENDACAO_N_BOOTSTRAP, dtype=float)

    for i in range(RECOMENDACAO_N_BOOTSTRAP):
        means[i] = rng.choice(values, size=len(values), replace=True).mean()

    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def recomendar_familias(query):
    if not isinstance(query, dict):
        raise ValueError("A query deve ser informada explicitamente como dicionário.")

    df = read_csv(ARQUIVO_SAIDA_ROBUSTEZ_CLEAN)
    df = normalize_columns(df).rename(columns={"r": "R"})
    df = remove_unnamed_columns(df)

    colunas_query = {
        coluna
        for coluna in FILTROS_OPCIONAIS
        if query.get(coluna) is not None
    }

    require_cols(
        df,
        sorted({"artigo_id", "modelo_familia", "R"} | set(FILTROS_OBRIGATORIOS) | colunas_query),
        ARQUIVO_SAIDA_ROBUSTEZ_CLEAN.name,
    )

    df["R"] = pd.to_numeric(df["R"], errors="coerce")

    if df["R"].isna().any():
        raise ValueError("A coluna R possui valores inválidos ou ausentes.")

    for coluna in {
        "modalidade",
        "tarefa",
        "ambiente_coleta",
        "pretreino",
        "dependencia_temporal",
        "modelo_familia",
    } & set(df.columns):
        df[coluna] = df[coluna].map(lambda value, c=coluna: normalizar_dominio(c, value))

    if "dataset_id" in df.columns:
        df["dataset_id"] = df["dataset_id"].map(as_text)

    if "canais_dados_presentes" in df.columns:
        df["canais_dados_presentes"] = df["canais_dados_presentes"].map(normalizar_lista)

    query_normalizada = {}

    for key, value in query.items():
        if value is None:
            query_normalizada[key] = None
        elif key == "dataset_id":
            query_normalizada[key] = as_text(value)
        elif key == "canais_dados_presentes":
            query_normalizada[key] = normalizar_lista(value)
        else:
            query_normalizada[key] = normalizar_dominio(key, value)

    obrigatorios_ausentes = [
        coluna
        for coluna in FILTROS_OBRIGATORIOS
        if query_normalizada.get(coluna) is None
    ]

    if obrigatorios_ausentes:
        raise ValueError(f"Filtros obrigatórios ausentes: {obrigatorios_ausentes}")

    opcionais_ativos = [
        coluna
        for coluna in FILTROS_OPCIONAIS
        if query_normalizada.get(coluna) is not None
    ]

    final_filtered = pd.DataFrame()
    final_agregada = pd.DataFrame()
    final_ranking = pd.DataFrame()
    final_opcionais = []
    abstencao = True
    motivo = "evidencia_insuficiente"

    for i in range(len(opcionais_ativos) + 1):
        opcionais_atuais = opcionais_ativos[i:]
        filtered = df.copy()

        for coluna in FILTROS_OBRIGATORIOS + opcionais_atuais:
            value = query_normalizada.get(coluna)

            if value is not None:
                filtered = filtered.loc[~filtered[coluna].isna()]
                filtered = filtered.loc[filtered[coluna] == value]

        agregada = (
            filtered.groupby(["artigo_id", "modelo_familia"], as_index=False)
            .agg(R_artigo=("R", "median"), n_experimentos_artigo=("R", "size"))
            .sort_values(["modelo_familia", "artigo_id"], kind="stable")
            .reset_index(drop=True)
        )

        rng = np.random.default_rng(RECOMENDACAO_RANDOM_SEED)
        linhas = []

        for familia, grupo in agregada.groupby("modelo_familia", sort=True):
            valores = grupo["R_artigo"].to_numpy(dtype=float)
            ic_inf, ic_sup = bootstrap_ci(valores, rng)

            linhas.append(
                {
                    "modelo_familia": familia,
                    "R_medio": float(valores.mean()),
                    "ic95_inf": ic_inf,
                    "ic95_sup": ic_sup,
                    "largura_ic95": float(ic_sup - ic_inf),
                    "n_artigos": int(len(grupo)),
                    "n_experimentos": int(grupo["n_experimentos_artigo"].sum()),
                    "elegivel_principal": bool(len(grupo) >= RECOMENDACAO_MIN_ARTIGOS_POR_FAMILIA),
                }
            )

        ranking = pd.DataFrame(linhas)

        if not ranking.empty:
            ranking["status_suporte"] = np.where(
                ranking["elegivel_principal"],
                "principal",
                "exploratoria",
            )

            ranking = ranking.sort_values(
                by=["elegivel_principal", "R_medio", "n_artigos", "largura_ic95", "modelo_familia"],
                ascending=[False, False, False, True, True],
                ignore_index=True,
                kind="stable",
            )

            ranking.insert(0, "ordem", range(1, len(ranking) + 1))

        principal = ranking.loc[ranking["elegivel_principal"]] if not ranking.empty else ranking

        final_filtered = filtered
        final_agregada = agregada
        final_ranking = ranking
        final_opcionais = opcionais_atuais

        if (
            len(agregada) >= RECOMENDACAO_MIN_OBSERVACOES_AGREGADAS
            and len(ranking) >= RECOMENDACAO_MIN_FAMILIAS
            and len(principal) >= RECOMENDACAO_MIN_FAMILIAS
        ):
            abstencao = False
            motivo = None
            break

    if not final_ranking.empty:
        final_ranking.insert(
            1,
            "filtros_utilizados",
            json.dumps(FILTROS_OBRIGATORIOS + final_opcionais, ensure_ascii=False),
        )
        final_ranking.insert(
            2,
            "filtros_relaxados",
            json.dumps([f for f in opcionais_ativos if f not in final_opcionais], ensure_ascii=False),
        )
        final_ranking.insert(
            3,
            "query",
            json.dumps(query_normalizada, ensure_ascii=False),
        )

    principal = final_ranking.loc[final_ranking["elegivel_principal"]] if not final_ranking.empty else final_ranking
    familia_recomendada = None if principal.empty else principal.iloc[0]["modelo_familia"]

    log = {
        "query": query_normalizada,
        "filtros_obrigatorios": FILTROS_OBRIGATORIOS,
        "filtros_opcionais_solicitados": opcionais_ativos,
        "filtros_opcionais_utilizados": final_opcionais,
        "filtros_relaxados": [f for f in opcionais_ativos if f not in final_opcionais],
        "linhas_elegiveis": int(len(final_filtered)),
        "observacoes_agregadas": int(len(final_agregada)),
        "familias_candidatas": int(0 if final_ranking.empty else len(final_ranking)),
        "familias_principais": int(0 if final_ranking.empty else final_ranking["elegivel_principal"].sum()),
        "abstencao": abstencao,
        "motivo_abstencao": motivo,
        "familia_recomendada": familia_recomendada,
    }

    ARQUIVO_RANKING_RECOMENDACAO.parent.mkdir(parents=True, exist_ok=True)

    if final_ranking.empty:
        pd.DataFrame(columns=COLUNAS_RANKING).to_csv(ARQUIVO_RANKING_RECOMENDACAO, index=False)
    else:
        final_ranking.to_csv(ARQUIVO_RANKING_RECOMENDACAO, index=False)

    write_sha256(ARQUIVO_RANKING_RECOMENDACAO)

    ARQUIVO_LOG_RECOMENDACAO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_LOG_RECOMENDACAO.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    write_sha256(ARQUIVO_LOG_RECOMENDACAO)

    return log


def executar():
    query = {
        "modalidade": "FER",
        "tarefa": "multiclasse",
        "pretreino": "nao",
        "dataset_id": None,
        "ambiente_coleta": None,
        "dependencia_temporal": None,
        "canais_dados_presentes": None,
    }

    print(json.dumps(recomendar_familias(query), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
