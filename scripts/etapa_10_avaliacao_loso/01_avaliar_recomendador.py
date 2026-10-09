import matplotlib.pyplot as plt
from scripts.utils.common import *
from scripts.utils.config import *


def normalizar_valor(coluna, value):
    if is_missing(value, extra_values={"na", "--"}, empty_collections=True):
        return None
    if coluna == "dataset_id":
        return as_text(value)
    if coluna == "canais_dados_presentes":
        return normalizar_lista(value)
    return normalizar_dominio(coluna, value)


def nome_coluna_lambda(lambda_value):
    return f"R_lambda_{str(lambda_value).replace('.', '_')}"


def primeira_coluna(df, candidatas):
    return next(coluna for coluna in candidatas if coluna in df.columns)


def bootstrap_ci(values, rng):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return np.nan, np.nan
    if len(values) == 1:
        return float(values[0]), float(values[0])
    means = [rng.choice(values, size=len(values), replace=True).mean() for _ in range(RECOMENDACAO_N_BOOTSTRAP)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def carregar_base():
    df = remove_unnamed_columns(normalize_columns(read_csv(ARQUIVO_SAIDA_ROBUSTEZ_CLEAN)).rename(columns={"r": "R"}))
    df["R"] = pd.to_numeric(df["R"], errors="coerce")
    if df["R"].isna().any():
        raise ValueError("A coluna R possui valores inválidos ou ausentes.")
    for coluna in FILTROS_OBRIGATORIOS + FILTROS_OPCIONAIS + ["modelo_familia"]:
        df[coluna] = df[coluna].map(lambda value, c=coluna: normalizar_valor(c, value))
    df["M"] = pd.to_numeric(df[primeira_coluna(df, ["metrica_principal_valor", "M", "m"])], errors="coerce")
    p_norm = pd.to_numeric(df[primeira_coluna(df, ["p_norm", "P_norm", "pnorm", "p_normalizado"])], errors="coerce")
    w = pd.to_numeric(df[primeira_coluna(df, ["W", "w"])], errors="coerce")
    coluna_s_linha = next((c for c in ["s_prime", "S_prime", "s_linha", "s_norm"] if c in df.columns), None)
    s_linha = pd.to_numeric(df[coluna_s_linha], errors="coerce") if coluna_s_linha else np.minimum(1, pd.to_numeric(df[primeira_coluna(df, ["S", "s"])], errors="coerce") / 2)
    for lambda_value in AVALIACAO_LOSO_LAMBDAS:
        df[nome_coluna_lambda(lambda_value)] = w * (lambda_value * p_norm + (1 - lambda_value) * s_linha)
    return df.sort_values(["artigo_id", "modelo_familia"], kind="stable").reset_index(drop=True)


def montar_alvos():
    return [{"analise": "R", "coluna": "R"}, {"analise": "M", "coluna": "M"}] + [
        {"analise": f"R_lambda_{lambda_value}", "coluna": nome_coluna_lambda(lambda_value)}
        for lambda_value in AVALIACAO_LOSO_LAMBDAS
    ]


def query_da_linha(row):
    return {coluna: normalizar_valor(coluna, row[coluna]) for coluna in FILTROS_OBRIGATORIOS + FILTROS_OPCIONAIS}


def filtrar_por_query(df, query, filtros):
    for coluna in filtros:
        value = query[coluna]
        if value is not None:
            df = df.loc[df[coluna].notna()]
            df = df.loc[df[coluna].map(lambda x: x == value)] if coluna == "canais_dados_presentes" else df.loc[df[coluna] == value]
    return df


def montar_ranking(df, query, coluna_alvo):
    opcionais_ativos = [coluna for coluna in FILTROS_OPCIONAIS if query[coluna] is not None]
    final_filtered = final_agregada = final_ranking = pd.DataFrame()
    final_opcionais, abstencao, motivo = [], True, "evidencia_insuficiente"

    for i in range(len(opcionais_ativos) + 1):
        final_opcionais = opcionais_ativos[i:]
        final_filtered = filtrar_por_query(df, query, FILTROS_OBRIGATORIOS + final_opcionais)
        final_agregada = (
            final_filtered.groupby(["artigo_id", "modelo_familia"], as_index=False)
            .agg(valor_artigo=(coluna_alvo, "median"), n_experimentos_artigo=(coluna_alvo, "size"))
            .sort_values(["modelo_familia", "artigo_id"], kind="stable")
            .reset_index(drop=True)
        )
        rng = np.random.default_rng(RECOMENDACAO_RANDOM_SEED)
        final_ranking = pd.DataFrame([
            {
                "modelo_familia": familia,
                "valor_medio": float(np.nanmean(valores := grupo["valor_artigo"].to_numpy(dtype=float))),
                "ic95_inf": (ic := bootstrap_ci(valores, rng))[0],
                "ic95_sup": ic[1],
                "largura_ic95": float(ic[1] - ic[0]),
                "n_artigos": int(len(grupo)),
                "n_experimentos": int(grupo["n_experimentos_artigo"].sum()),
                "elegivel_principal": bool(len(grupo) >= RECOMENDACAO_MIN_ARTIGOS_POR_FAMILIA),
            }
            for familia, grupo in final_agregada.groupby("modelo_familia", sort=True)
        ])
        if not final_ranking.empty:
            final_ranking["status_suporte"] = np.where(final_ranking["elegivel_principal"], "principal", "exploratoria")
            final_ranking = final_ranking.sort_values(
                ["elegivel_principal", "valor_medio", "n_artigos", "largura_ic95", "modelo_familia"],
                ascending=[False, False, False, True, True],
                ignore_index=True,
                kind="stable",
            )
            final_ranking.insert(0, "ordem", range(1, len(final_ranking) + 1))
        principal = final_ranking.loc[final_ranking["elegivel_principal"]] if not final_ranking.empty else final_ranking
        if len(final_agregada) >= RECOMENDACAO_MIN_OBSERVACOES_AGREGADAS and len(final_ranking) >= RECOMENDACAO_MIN_FAMILIAS and len(principal) >= RECOMENDACAO_MIN_FAMILIAS:
            abstencao, motivo = False, None
            break

    principal = final_ranking.loc[final_ranking["elegivel_principal"]] if not final_ranking.empty else final_ranking
    return final_ranking, {
        "filtros_opcionais_utilizados": final_opcionais,
        "filtros_relaxados": [f for f in opcionais_ativos if f not in final_opcionais],
        "linhas_elegiveis": int(len(final_filtered)),
        "observacoes_agregadas": int(len(final_agregada)),
        "familias_candidatas": int(len(final_ranking)),
        "familias_principais": int(0 if final_ranking.empty else final_ranking["elegivel_principal"].sum()),
        "abstencao": abstencao,
        "motivo_abstencao": motivo,
        "familia_recomendada": None if abstencao or principal.empty else principal.iloc[0]["modelo_familia"],
    }


def base_obrigatoria(df, query):
    for coluna in FILTROS_OBRIGATORIOS:
        if query[coluna] is None:
            return df.iloc[0:0]
        df = df.loc[df[coluna] == query[coluna]]
    return df


def familia_mais_frequente(df, query):
    base = base_obrigatoria(df, query)
    if base.empty:
        return None
    return (
        base.groupby("modelo_familia", as_index=False)
        .agg(n_artigos=("artigo_id", "nunique"), n_experimentos=("modelo_familia", "size"))
        .sort_values(["n_artigos", "n_experimentos", "modelo_familia"], ascending=[False, False, True], kind="stable")
        .iloc[0]["modelo_familia"]
    )


def familias_aleatorias(df, query, rng):
    freq = (
        base_obrigatoria(df, query)
        .groupby("modelo_familia", as_index=False)
        .agg(n_artigos=("artigo_id", "nunique"))
        .sort_values("modelo_familia", kind="stable")
        .reset_index(drop=True)
    )
    if freq.empty:
        return []
    pesos = freq["n_artigos"].to_numpy(dtype=float)
    return rng.choice(freq["modelo_familia"].to_numpy(), size=AVALIACAO_N_RANDOM, replace=True, p=pesos / pesos.sum()).tolist()


def valor_da_familia(grupo, familia, coluna_alvo):
    if familia is None:
        return 0.0, False
    valores = grupo.loc[grupo["modelo_familia"] == familia, coluna_alvo]
    return (0.0, False) if valores.empty else (float(valores.max()), True)


def avaliar_cenario(treino, teste, row, idx, rng, analise, coluna_alvo):
    query = query_da_linha(row)
    ranking, log = montar_ranking(treino, query, coluna_alvo)
    grupo = teste.loc[(teste["modalidade"] == row["modalidade"]) & (teste["tarefa"] == row["tarefa"])]
    idx_ref = grupo[coluna_alvo].idxmax()
    familia_ref, valor_ref = grupo.loc[idx_ref, "modelo_familia"], float(grupo.loc[idx_ref, coluna_alvo])
    familia_rec, familia_freq = log["familia_recomendada"], familia_mais_frequente(treino, query)
    valor_rec, rec_observada = valor_da_familia(grupo, familia_rec, coluna_alvo)
    valor_freq, freq_observada = valor_da_familia(grupo, familia_freq, coluna_alvo)
    familias_rand = familias_aleatorias(treino, query, rng)
    valor_rand_medio = np.nan if not familias_rand else float(np.mean([valor_da_familia(grupo, familia, coluna_alvo)[0] for familia in familias_rand]))
    familias_topk_principal = [] if ranking.empty else ranking.loc[ranking["elegivel_principal"]].head(AVALIACAO_TOP_K)["modelo_familia"].tolist()
    familias_topk_completo = [] if ranking.empty else ranking.head(AVALIACAO_TOP_K)["modelo_familia"].tolist()
    cenario_id = next((row[c] for c in ["cenario_id", "experimento_id"] if c in row.index and not is_missing(row[c])), f"{row['artigo_id']}::{idx}")

    return {
        "analise": analise,
        "coluna_alvo": coluna_alvo,
        "artigo_id": row["artigo_id"],
        "cenario_id": cenario_id,
        "modalidade": row["modalidade"],
        "tarefa": row["tarefa"],
        "dataset_id": row["dataset_id"],
        "ambiente_coleta": row["ambiente_coleta"],
        "pretreino": row["pretreino"],
        "familia_referencia": familia_ref,
        "valor_referencia": valor_ref,
        "familia_recomendada": familia_rec,
        "valor_recomendada": valor_rec,
        "familia_recomendada_observada": rec_observada,
        "familia_frequente": familia_freq,
        "valor_frequente": valor_freq,
        "familia_frequente_observada": freq_observada,
        "valor_aleatoria_media": valor_rand_medio,
        "acerto_top1": bool(familia_rec == familia_ref),
        f"acerto_top{AVALIACAO_TOP_K}_principal": bool(familia_ref in familias_topk_principal),
        f"acerto_top{AVALIACAO_TOP_K}_exploratorio": bool(familia_ref in familias_topk_completo),
        "delta_freq": float(valor_rec - valor_freq),
        "delta_aleatoria": float(valor_rec - valor_rand_medio) if not np.isnan(valor_rand_medio) else np.nan,
        "delta_referencia": float(valor_rec - valor_ref),
        "abstencao": bool(log["abstencao"]),
        "familias_topk_principal": json.dumps(familias_topk_principal, ensure_ascii=False),
        "familias_topk_exploratorio": json.dumps(familias_topk_completo, ensure_ascii=False),
        "filtros_relaxados": json.dumps(log["filtros_relaxados"], ensure_ascii=False),
        "familias_candidatas": log["familias_candidatas"],
        "familias_principais": log["familias_principais"],
        "observacoes_agregadas": log["observacoes_agregadas"],
    }


def avaliar_leave_one_out(df, analise, coluna_alvo):
    rng = np.random.default_rng(RECOMENDACAO_RANDOM_SEED)
    df_alvo = df.loc[df[coluna_alvo].notna()].copy()
    return pd.DataFrame([
        avaliar_cenario(df_alvo.loc[df_alvo["artigo_id"] != artigo_id].copy(), teste, row, idx, rng, analise, coluna_alvo)
        for artigo_id, teste in df_alvo.groupby("artigo_id", sort=True)
        if not df_alvo.loc[df_alvo["artigo_id"] != artigo_id].empty
        for idx, row in teste.iterrows()
    ])


def media_ic(values, rng):
    values = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) == 0:
        return np.nan, np.nan, np.nan
    ic_inf, ic_sup = bootstrap_ci(values, rng)
    return float(values.mean()), ic_inf, ic_sup


def resumir_bloco(df, analise, escopo, grupo, valor, rng):
    metricas = {
        "delta_freq": media_ic(df["delta_freq"], rng),
        "delta_aleatoria": media_ic(df["delta_aleatoria"], rng),
        "delta_referencia": media_ic(df["delta_referencia"], rng),
    }
    return {
        "analise": analise,
        "escopo": escopo,
        "grupo": grupo,
        "valor": valor,
        "n_cenarios": int(len(df)),
        "n_artigos": int(df["artigo_id"].nunique()),
        "taxa_abstencao": float(df["abstencao"].mean()),
        "acerto_top1": float(df["acerto_top1"].mean()),
        f"acerto_top{AVALIACAO_TOP_K}_principal": float(df[f"acerto_top{AVALIACAO_TOP_K}_principal"].mean()),
        f"acerto_top{AVALIACAO_TOP_K}_exploratorio": float(df[f"acerto_top{AVALIACAO_TOP_K}_exploratorio"].mean()),
        **{
            f"{nome}_{sufixo}": valor
            for nome, valores in metricas.items()
            for sufixo, valor in zip(["medio", "ic95_inf", "ic95_sup"], valores)
        },
    }


def adicionar_resumos(linhas, df, analise, escopo, rng):
    if df.empty:
        return
    linhas.append(resumir_bloco(df, analise, escopo, "geral", "geral", rng))
    for grupo in GRUPOS_RESUMO:
        for valor, bloco in df.groupby(grupo, dropna=False, sort=True):
            linhas.append(resumir_bloco(bloco, analise, escopo, grupo, "NA" if is_missing(valor) else str(valor), rng))


def resumir_resultados(resultados):
    rng = np.random.default_rng(RECOMENDACAO_RANDOM_SEED)
    linhas = []
    for analise, bloco in resultados.groupby("analise", sort=False):
        adicionar_resumos(linhas, bloco, analise, "incluindo_abstencoes", rng)
        adicionar_resumos(linhas, bloco.loc[~bloco["abstencao"]].copy(), analise, "somente_recomendacoes", rng)
    return pd.DataFrame(linhas)


def salvar_grafico_deltas(resumo):
    base = resumo.loc[(resumo["grupo"] == "geral") & (resumo["valor"] == "geral") & (resumo["escopo"] == "incluindo_abstencoes")].copy()
    if base.empty:
        return

    x = np.arange(len(base))
    width = 0.34
    fig, ax = plt.subplots(figsize=(max(10, len(base) * 1.3), 5.8))
    barras_freq = ax.bar(
        x - width / 2,
        base["delta_freq_medio"],
        width,
        yerr=np.vstack([base["delta_freq_medio"] - base["delta_freq_ic95_inf"], base["delta_freq_ic95_sup"] - base["delta_freq_medio"]]),
        capsize=4,
        label="Família mais frequente",
    )
    barras_aleatoria = ax.bar(
        x + width / 2,
        base["delta_aleatoria_medio"],
        width,
        yerr=np.vstack([base["delta_aleatoria_medio"] - base["delta_aleatoria_ic95_inf"], base["delta_aleatoria_ic95_sup"] - base["delta_aleatoria_medio"]]),
        capsize=4,
        label="Aleatória ponderada",
    )
    ax.axhline(0, linewidth=1.1)
    ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.45)
    ax.set_axisbelow(True)
    ax.set_xticks(x)
    ax.set_xticklabels(base["analise"].astype(str).str.replace("R_lambda_", "Rλ=", regex=False), rotation=0, ha="center")
    ax.set_ylabel("Diferença Média do Alvo")
    ax.set_xlabel("Métrica Avaliada", labelpad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.bar_label(barras_freq, fmt="%.3f", padding=3, fontsize=8)
    ax.bar_label(barras_aleatoria, fmt="%.3f", padding=3, fontsize=8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(ARQUIVO_GRAFICO_DELTAS, dpi=300, bbox_inches="tight")
    plt.close(fig)
    write_sha256(ARQUIVO_GRAFICO_DELTAS)


def salvar_saidas(resultados, resumo, alvos):
    DIRETORIO_AVALIACAO.mkdir(parents=True, exist_ok=True)
    resultados.to_csv(ARQUIVO_AVALIACAO, index=False, encoding="utf-8-sig")
    resumo.to_csv(ARQUIVO_RESUMO, index=False, encoding="utf-8-sig")
    write_sha256(ARQUIVO_AVALIACAO)
    write_sha256(ARQUIVO_RESUMO)
    salvar_grafico_deltas(resumo)
    ARQUIVO_LOG.write_text(json.dumps({
        "entrada": str(ARQUIVO_SAIDA_ROBUSTEZ_CLEAN),
        "saida_avaliacao": str(ARQUIVO_AVALIACAO),
        "saida_resumo": str(ARQUIVO_RESUMO),
        "saida_grafico_deltas": str(ARQUIVO_GRAFICO_DELTAS),
        "n_cenarios": int(len(resultados)),
        "n_artigos": int(resultados["artigo_id"].nunique()),
        "top_k": AVALIACAO_TOP_K,
        "n_random": AVALIACAO_N_RANDOM,
        "seed": RECOMENDACAO_RANDOM_SEED,
        "n_bootstrap": RECOMENDACAO_N_BOOTSTRAP,
        "lambdas": AVALIACAO_LOSO_LAMBDAS,
        "alvos_avaliados": alvos,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    write_sha256(ARQUIVO_LOG)


def executar():
    df = carregar_base()
    alvos = montar_alvos()
    resultados = pd.concat([
        parcial
        for alvo in alvos
        if not (parcial := avaliar_leave_one_out(df, alvo["analise"], alvo["coluna"])).empty
    ], ignore_index=True)
    resumo = resumir_resultados(resultados)
    salvar_saidas(resultados, resumo, alvos)
    print(resumo.loc[(resumo["grupo"] == "geral") & (resumo["valor"] == "geral")].to_string(index=False))


if __name__ == "__main__":
    executar()
