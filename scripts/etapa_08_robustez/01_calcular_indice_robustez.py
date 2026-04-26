import numpy as np
import pandas as pd

from scripts.utils.common import norm_text, read_csv, parse_yes_no, parse_fraction
from scripts.utils.config import (
    DATASETS_BASE_MULTICLASSE_PADRAO,
    ITENS_W,
    ARQUIVO_CENARIOS,
    ARQUIVO_AUDITORIA,
    ARQUIVO_SAIDA_ROBUSTEZ,
    ARQUIVO_RESUMO_MODALIDADE,
    ARQUIVO_RESUMO_FAMILIA,
    LAMBDA_R,
)


def calcular_p_norm(m, b):
    if pd.isna(m) or pd.isna(b):
        return np.nan
    if b >= 1:
        return 0.0

    return max(0.0, min(1.0, (m - b) / (1 - b)))


def detectar_estratificado(row):
    valor = parse_yes_no(row.get("protocolo_estratificado", np.nan))

    if valor == "sim":
        return True

    if valor == "nao":
        return False

    obs = row.get("observacoes", np.nan)

    if pd.isna(obs):
        return False

    return any(t in str(obs).lower() for t in ["estratific", "stratif"])


def inferir_b(row):
    for col in [
        "acuracia_classe_majoritaria",
        "majority_class_accuracy",
        "baseline_majoritaria",
        "baseline_majority",
        "b",
    ]:
        if pd.notna(row.get(col, np.nan)):
            return parse_fraction(row[col]), "classe_majoritaria", False

    for col in ["n_classes", "num_classes", "k_classes", "K"]:
        if pd.notna(row.get(col, np.nan)):
            n = float(row[col])
            if n > 0:
                return 1.0 / n, "1_sobre_k", False

    dataset = str(row.get("dataset_id", "")).strip()

    if dataset in DATASETS_BASE_MULTICLASSE_PADRAO:
        return 1.0 / 7.0, "base_multiclasse_padrao", False

    if norm_text(row.get("tarefa", np.nan)) in {"binaria", "binário", "binary"}:
        return 0.5, "tarefa_binaria", False

    return 0.0, "fallback_zero", True


def calcular_s(row):
    s = float(parse_yes_no(row["protocolo_person_indep"]) == "sim")
    s += float(parse_yes_no(row["protocolo_cross_dataset"]) == "sim")

    if s == 0.0 and detectar_estratificado(row):
        s = 0.5

    return s, min(1.0, s / 2.0)


def calcular_w_artigo(auditoria):
    aud = auditoria.copy()

    aud["artigo_id"] = aud["artigo_id"].astype(str).str.strip()
    aud["item_id"] = aud["item_id"].astype(str).str.strip().str.upper()
    aud["grau"] = pd.to_numeric(aud["grau"], errors="coerce")
    aud["NA"] = pd.to_numeric(aud["NA"], errors="coerce").fillna(0).astype(int)

    aud = aud[aud["item_id"].isin(ITENS_W)].copy()

    duplicados = aud.duplicated(["artigo_id", "item_id"], keep=False)

    if duplicados.any():
        duplicados_df = aud.loc[duplicados, ["artigo_id", "item_id"]].sort_values(
            ["artigo_id", "item_id"]
        )

        raise ValueError(
            "Existem linhas duplicadas em auditoria.csv para artigo_id + item_id nos itens de W:\n"
            + duplicados_df.to_string(index=False)
        )

    aud["aplicavel"] = aud["NA"].eq(0)
    aud["grau_norm"] = aud["grau"] / 2.0

    total = aud.groupby("artigo_id", as_index=False).agg(
        n_itens_w_total=("item_id", "count")
    )

    w = (
        aud[aud["aplicavel"]]
        .groupby("artigo_id", as_index=False)
        .agg(
            W=("grau_norm", "mean"),
            n_itens_w_aplicaveis=("item_id", "count"),
        )
    )

    return (
        total.merge(w, on="artigo_id", how="left")
        .fillna({"W": 0.0, "n_itens_w_aplicaveis": 0})
        .astype({"n_itens_w_aplicaveis": int})
    )


def resumir(resultado, coluna):
    return (
        resultado.groupby(coluna, dropna=False)["R"]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
    )


def executar():
    ARQUIVO_SAIDA_ROBUSTEZ.parent.mkdir(parents=True, exist_ok=True)

    cenarios = read_csv(ARQUIVO_CENARIOS)
    auditoria = read_csv(ARQUIVO_AUDITORIA)

    cenarios["artigo_id"] = cenarios["artigo_id"].astype(str).str.strip()
    cenarios["M"] = pd.to_numeric(
        cenarios["metrica_principal_valor"],
        errors="coerce",
    ).apply(parse_fraction)

    resultado = cenarios.merge(calcular_w_artigo(auditoria), on="artigo_id", how="left")

    resultado[["W", "n_itens_w_total", "n_itens_w_aplicaveis"]] = resultado[
        ["W", "n_itens_w_total", "n_itens_w_aplicaveis"]
    ].fillna(0)

    resultado[["n_itens_w_total", "n_itens_w_aplicaveis"]] = resultado[
        ["n_itens_w_total", "n_itens_w_aplicaveis"]
    ].astype(int)

    resultado[["b", "b_regra", "b_baixa_confianca"]] = resultado.apply(
        inferir_b,
        axis=1,
        result_type="expand",
    )

    resultado[["S", "S_linha"]] = resultado.apply(
        calcular_s,
        axis=1,
        result_type="expand",
    )

    resultado["P_norm"] = resultado.apply(
        lambda row: calcular_p_norm(row["M"], row["b"]),
        axis=1,
    )

    resultado["lambda_r"] = LAMBDA_R
    resultado["R"] = resultado["W"] * (
        LAMBDA_R * resultado["P_norm"] + (1 - LAMBDA_R) * resultado["S_linha"]
    )

    colunas_saida = [
        "artigo_id",
        "artigo_titulo",
        "dataset_id",
        "modalidade",
        "tarefa",
        "ambiente_coleta",
        "dependencia_temporal",
        "n_amostras_total",
        "pretreino",
        "modalidades_presentes",
        "modelo_familia",
        "modelo_especifico",
        "protocolo_person_indep",
        "protocolo_cross_dataset",
        "metricas_principais",
        "metrica_principal_valor",
        "M",
        "b",
        "b_regra",
        "b_baixa_confianca",
        "S",
        "S_linha",
        "W",
        "n_itens_w_total",
        "n_itens_w_aplicaveis",
        "lambda_r",
        "P_norm",
        "R",
        "augmentations",
        "code_available",
        "weights_available",
        "observacoes",
    ]

    resultado = resultado[colunas_saida].sort_values(
        ["artigo_id", "dataset_id", "modelo_familia", "modelo_especifico"],
        na_position="last",
    )

    resumo_modalidade = resumir(resultado, "modalidade")
    resumo_familia = resumir(resultado, "modelo_familia")

    resultado.to_csv(ARQUIVO_SAIDA_ROBUSTEZ, index=False)
    resumo_modalidade.to_csv(ARQUIVO_RESUMO_MODALIDADE, index=False)
    resumo_familia.to_csv(ARQUIVO_RESUMO_FAMILIA, index=False)

    print(f"Arquivo gerado: {ARQUIVO_SAIDA_ROBUSTEZ}")
    print(f"Arquivo gerado: {ARQUIVO_RESUMO_MODALIDADE}")
    print(f"Arquivo gerado: {ARQUIVO_RESUMO_FAMILIA}")
    print(f"Linhas processadas: {len(resultado)}")
    print(f"Artigos com W calculado: {resultado['artigo_id'].nunique()}")
    print()
    print("Resumo por modalidade:")
    print(resumo_modalidade.to_string(index=False))
    print()
    print("Resumo por família:")
    print(resumo_familia.to_string(index=False))


if __name__ == "__main__":
    executar()