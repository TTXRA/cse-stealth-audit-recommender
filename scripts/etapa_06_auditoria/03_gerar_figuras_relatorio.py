import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scripts.utils.config import OUT_ANALISE_AUDITORIA_DIR, CONFIGS


def heatmap_itens(df_itens, df_artigos, df_sensibilidade_artigos, arquivo):
    ordem_itens = ['DAD', 'ROT', 'ESC', 'PRE', 'PRT', 'MOD', 'MET', 'CAL', 'SUB', 'ROB', 'REP', 'ETH', 'VZ', 'EXT', 'CST', 'SIN']

    base = df_itens[df_itens['na'].eq(0)][['artigo_id', 'item_id', 'score_item']].copy()

    artigos_df = (
        df_artigos[['artigo_id', 'estrato', 'score_global', 'n_na']]
        .drop_duplicates('artigo_id')
        .merge(
            df_sensibilidade_artigos[['artigo_id', 'delta_uniforme_robustez']].drop_duplicates('artigo_id'),
            on='artigo_id',
            how='left'
        )
        .sort_values(['estrato', 'score_global', 'artigo_id'], ascending=[True, False, True])
        .reset_index(drop=True)
    )

    artigos = artigos_df['artigo_id'].tolist()
    itens = [i for i in ordem_itens if i in base['item_id'].unique()]

    matriz = (
        base.pivot(index='artigo_id', columns='item_id', values='score_item')
        .reindex(index=artigos, columns=itens)
    )

    delta_rob = (
        artigos_df.set_index('artigo_id')
        .reindex(artigos)['delta_uniforme_robustez']
        .to_numpy(dtype=float)
        .reshape(-1, 1)
    )

    ylabels = [
        f"{artigo} | SG={score:.1f} | NA={int(n_na)}"
        for artigo, score, n_na in zip(
            artigos_df['artigo_id'],
            artigos_df['score_global'],
            artigos_df['n_na']
        )
    ]

    h = max(8, 0.30 * len(artigos) + 2)
    w = max(15, 0.72 * len(itens) + 4.8)

    fig = plt.figure(figsize=(w, h), constrained_layout=True)
    gs = fig.add_gridspec(1, 4, width_ratios=[max(12, 0.75 * len(itens) + 3), 0.9, 0.22, 0.22])

    ax = fig.add_subplot(gs[0, 0])
    ax_delta = fig.add_subplot(gs[0, 1], sharey=ax)
    cax_main = fig.add_subplot(gs[0, 2])
    cax_delta = fig.add_subplot(gs[0, 3])

    cmap_main = plt.get_cmap('cividis').copy()
    cmap_main.set_bad('#ececec')

    imagem = ax.imshow(
        matriz.to_numpy(dtype=float),
        aspect='auto',
        vmin=0,
        vmax=100,
        cmap=cmap_main,
        interpolation='nearest'
    )

    vmax_delta = max(abs(np.nanmin(delta_rob)), abs(np.nanmax(delta_rob)), 1)
    imagem_delta = ax_delta.imshow(
        delta_rob,
        aspect='auto',
        vmin=-vmax_delta,
        vmax=vmax_delta,
        cmap='coolwarm',
        interpolation='nearest'
    )

    ax.set_xticks(np.arange(len(itens)))
    ax.set_xticklabels(itens)
    ax.set_yticks(np.arange(len(artigos)))
    ax.set_yticklabels(ylabels)

    ax.tick_params(axis='x', labelsize=10.5, pad=8, top=True, bottom=False, labeltop=True, labelbottom=False)
    ax.tick_params(axis='y', labelsize=8.3)

    ax.set_xlabel('Itens', labelpad=12)
    ax.xaxis.set_label_position('top')
    ax.set_ylabel('Artigos')
    ax.set_title('Mapa de Calor: Score por Artigo x Item', pad=16)

    ax.set_xticks(np.arange(-0.5, len(itens), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(artigos), 1), minor=True)
    ax.grid(which='minor', color='white', linestyle='-', linewidth=0.35, alpha=0.65)
    ax.tick_params(which='minor', bottom=False, left=False)

    ax_delta.set_xticks([0])
    ax_delta.set_xticklabels(['Δ\nU→R'])
    ax_delta.tick_params(axis='x', labelsize=10, pad=8, top=True, bottom=False, labeltop=True, labelbottom=False)
    ax_delta.tick_params(axis='y', left=False, labelleft=False)
    ax_delta.set_xlim(-0.5, 0.5)

    contagens = artigos_df['estrato'].value_counts(sort=False)
    limites = np.cumsum(contagens.to_numpy())[:-1] - 0.5

    for y in limites:
        ax.hlines(y, -0.5, len(itens) - 0.5, colors='black', linewidth=1.0)
        ax_delta.hlines(y, -0.5, 0.5, colors='black', linewidth=1.0)

    for eixo in [ax, ax_delta]:
        for spine in eixo.spines.values():
            spine.set_visible(False)

    barra = fig.colorbar(imagem, cax=cax_main)
    barra.set_label('Score do Item')
    barra.set_ticks([0, 25, 50, 75, 100])

    barra_delta = fig.colorbar(imagem_delta, cax=cax_delta)
    barra_delta.set_label('Δ U→R')

    fig.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_scores_estratos(df, resumo, config, arquivo):
    base = df[['estrato', 'score_global']].dropna().copy()
    estratos = sorted(base['estrato'].unique().tolist())
    xpos = np.arange(len(estratos))
    grupos = [base.loc[base['estrato'].eq(e), 'score_global'].to_numpy(dtype=float) for e in estratos]

    stats = (
        resumo[
            resumo['config_pesos'].eq(config) &
            resumo['escopo'].eq('estrato')
        ][['estrato', 'mediana', 'ic95_mediana_inf', 'ic95_mediana_sup']]
        .drop_duplicates('estrato')
        .set_index('estrato')
        .reindex(estratos)
    )

    fig, ax = plt.subplots(figsize=(10.5, 6.2))

    bp = ax.boxplot(
        grupos,
        positions=xpos,
        widths=0.52,
        patch_artist=True,
        showfliers=False,
        whis=(5, 95),
        medianprops={'linewidth': 2.2, 'zorder': 3},
        whiskerprops={'linewidth': 1.2, 'alpha': 0.8},
        capprops={'linewidth': 1.2, 'alpha': 0.8},
        boxprops={'linewidth': 1.2}
    )

    for box in bp['boxes']:
        box.set_facecolor((0, 0, 0, 0.08))

    rng = np.random.default_rng(2025)
    for i, valores in enumerate(grupos):
        jitter = rng.normal(0, 0.035, len(valores)).clip(-0.11, 0.11)
        ax.scatter(
            np.full(len(valores), xpos[i]) + jitter,
            valores,
            s=42,
            alpha=0.85,
            edgecolors='white',
            linewidths=0.7,
            zorder=4
        )

    medianas = stats['mediana'].to_numpy(dtype=float)
    ic_inf = stats['ic95_mediana_inf'].to_numpy(dtype=float)
    ic_sup = stats['ic95_mediana_sup'].to_numpy(dtype=float)

    ax.errorbar(
        xpos,
        medianas,
        yerr=[medianas - ic_inf, ic_sup - medianas],
        fmt='D',
        capsize=6,
        linewidth=1.8,
        markersize=6.5,
        zorder=5
    )

    ax.set_xticks(xpos)
    ax.set_xticklabels([f'{e}\n(n={len(g)})' for e, g in zip(estratos, grupos)])
    ax.set_ylabel('Score Global')
    ax.set_ylim(0, 100)
    ax.set_title(f'Distribuição do Score Global por Estrato ({config.title()})')

    ax.grid(axis='y', alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.margins(x=0.05)

    fig.tight_layout()
    fig.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_itens_criticos_estratos(resumo_itens, criticos, arquivo):
    base_criticos = (
        criticos[criticos['config_pesos'].eq('uniforme')]
        .nsmallest(5, 'media_item')
        .sort_values('media_item', ascending=True)
        .copy()
    )

    itens = base_criticos[['item_id', 'item_label']].copy()
    itens['label'] = itens['item_id'] + ' - ' + itens['item_label']

    base = (
        resumo_itens[resumo_itens['config_pesos'].eq('uniforme')]
        .merge(itens[['item_id', 'item_label', 'label']], on=['item_id', 'item_label'], how='inner')
        .copy()
    )

    estratos = ['FER', 'MULTI', 'SER']
    desloc = {'FER': -0.18, 'MULTI': 0.0, 'SER': 0.18}
    marcadores = {'FER': 'o', 'MULTI': 's', 'SER': '^'}
    ypos_base = np.arange(len(itens))

    fig, ax = plt.subplots(figsize=(12.0, 6.8), constrained_layout=True)

    for estrato in estratos:
        parte = (
            base[base['estrato'].eq(estrato)]
            .set_index('label')
            .reindex(itens['label'].tolist())
        )
        x = parte['mediana'].to_numpy(dtype=float)
        x_inf = parte['ic95_mediana_inf'].to_numpy(dtype=float)
        x_sup = parte['ic95_mediana_sup'].to_numpy(dtype=float)
        y = ypos_base + desloc[estrato]

        ax.errorbar(
            x,
            y,
            xerr=[x - x_inf, x_sup - x],
            fmt=marcadores[estrato],
            capsize=5,
            linewidth=1.5,
            markersize=6.5,
            label=estrato
        )

    ax.set_yticks(ypos_base)
    ax.set_yticklabels(itens['label'].tolist())
    ax.set_xlim(0, 100)
    ax.set_xlabel('Mediana do Item com IC95%')
    ax.set_title('Itens Menos Atendidos no Esquema Uniforme, por Estrato', pad=14)

    ax.grid(axis='x', linestyle='--', linewidth=0.8, alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(title='Estrato', frameon=False, loc='lower right')

    fig.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)


def medianas_estratos(df, resumo, arquivo):
    estratos = df['estrato'].tolist()
    xpos = np.arange(len(estratos))

    dx_cfg = {
        'uniforme': -0.22,
        'nucleares': 0.00,
        'robustez': 0.22,
    }

    mk_cfg = {
        'uniforme': 'o',
        'nucleares': 's',
        'robustez': '^',
    }

    stats_cfg = {}
    for config in CONFIGS:
        stats_cfg[config] = (
            resumo[
                resumo['config_pesos'].eq(config) &
                resumo['escopo'].eq('estrato')
            ][['estrato', 'ic95_mediana_inf', 'ic95_mediana_sup']]
            .drop_duplicates('estrato')
            .set_index('estrato')
            .reindex(estratos)
        )

    y_max = np.nanmax([
        df[c].to_numpy(dtype=float).max()
        for c in CONFIGS
    ] + [
        stats_cfg[c]['ic95_mediana_sup'].to_numpy(dtype=float).max()
        for c in CONFIGS
    ])

    y_min = np.nanmin([
        df[c].to_numpy(dtype=float).min()
        for c in CONFIGS
    ] + [
        stats_cfg[c]['ic95_mediana_inf'].to_numpy(dtype=float).min()
        for c in CONFIGS
    ])

    base = max(0.0, np.floor((y_min - 2) / 5) * 5)
    topo = min(100.0, np.ceil((y_max + 2) / 5) * 5)
    if topo - base < 15:
        topo = min(100.0, base + 15)

    passo_y = 5 if (topo - base) <= 40 else 10

    fig, (ax, ax_delta) = plt.subplots(
        2,
        1,
        figsize=(11.8, 7.8),
        sharex=True,
        constrained_layout=True,
        gridspec_kw={'height_ratios': [3.4, 1.5]}
    )

    cores = {}

    for config in CONFIGS:
        y = df[config].to_numpy(dtype=float)
        stats = stats_cfg[config]
        yerr = [
            y - stats['ic95_mediana_inf'].to_numpy(dtype=float),
            stats['ic95_mediana_sup'].to_numpy(dtype=float) - y
        ]

        eb = ax.errorbar(
            xpos + dx_cfg[config],
            y,
            yerr=yerr,
            fmt=mk_cfg[config],
            capsize=5,
            elinewidth=1.2,
            linewidth=1.6,
            markersize=7,
            label=config.title(),
            zorder=3
        )

        cor = eb[0].get_color()
        cores[config] = cor

        ax.plot(
            xpos + dx_cfg[config],
            y,
            linewidth=1.4,
            alpha=0.8,
            color=cor,
            zorder=2
        )

        for x, yi in zip(xpos + dx_cfg[config], y):
            ax.annotate(
                f'{yi:.1f}',
                (x, yi),
                xytext=(0, 7),
                textcoords='offset points',
                ha='center',
                va='bottom',
                fontsize=8.5,
                color=cor,
                bbox=dict(boxstyle='round,pad=0.18', fc='white', ec=cor, lw=0.7, alpha=0.95)
            )

    for x in xpos[:-1]:
        ax.axvline(x + 0.5, linestyle=':', linewidth=0.8, alpha=0.35)
        ax_delta.axvline(x + 0.5, linestyle=':', linewidth=0.8, alpha=0.35)

    delta_n = df['delta_uniforme_nucleares'].to_numpy(dtype=float)
    delta_r = df['delta_uniforme_robustez'].to_numpy(dtype=float)

    barras_n = ax_delta.bar(
        xpos - 0.16,
        delta_n,
        width=0.28,
        alpha=0.85,
        label='Δ U→N',
        color=cores.get('nucleares')
    )

    barras_r = ax_delta.bar(
        xpos + 0.16,
        delta_r,
        width=0.28,
        alpha=0.85,
        label='Δ U→R',
        color=cores.get('robustez')
    )

    ax_delta.axhline(0, linewidth=1.0, alpha=0.7, color='black')

    dmax = max(
        np.nanmax(np.abs(delta_n)) if len(delta_n) else 0,
        np.nanmax(np.abs(delta_r)) if len(delta_r) else 0,
        1.0
    )

    pad_delta = max(0.35, dmax * 0.18)
    delta_lim = np.ceil((dmax + pad_delta) / 0.5) * 0.5
    ax_delta.set_ylim(-delta_lim, delta_lim)

    pad_rotulo = max(0.10, dmax * 0.05)

    for barras in [barras_n, barras_r]:
        for barra in barras:
            h = barra.get_height()
            x_txt = barra.get_x() + barra.get_width() / 2

            if h >= 0:
                y_txt = h + pad_rotulo
                va = 'bottom'
            else:
                y_txt = h + pad_rotulo
                va = 'bottom'

            ax_delta.text(
                x_txt,
                y_txt,
                f'{h:+.1f}',
                ha='center',
                va=va,
                fontsize=8.5
            )

    ax.set_ylabel('Mediana do Score Global')
    ax.set_ylim(base, topo)
    ax.set_yticks(np.arange(base, topo + 0.1, passo_y))
    ax.set_title('Medianas por Estrato e Configuração de Pesos', pad=12)

    ax.grid(axis='y', linestyle='--', linewidth=0.8, alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(
        title='Configuração',
        frameon=False,
        loc='center right',
        bbox_to_anchor=(0.98, 0.88),
        borderaxespad=0.0
    )

    ax_delta.set_xticks(xpos)
    ax_delta.set_xticklabels(estratos)
    ax_delta.set_xlabel('Estratos')
    ax_delta.set_ylabel('Δ vs U')
    ax_delta.grid(axis='y', linestyle='--', linewidth=0.8, alpha=0.35)
    ax_delta.set_axisbelow(True)
    ax_delta.spines['top'].set_visible(False)
    ax_delta.spines['right'].set_visible(False)
    ax_delta.legend(
        title='Deltas',
        frameon=False,
        loc='center right',
        bbox_to_anchor=(0.98, 0.78),
        borderaxespad=0.0
    )

    fig.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_sensibilidade_artigos(df, arquivo):
    base = df.copy()
    base['abs_delta_robustez'] = base['delta_uniforme_robustez'].abs()
    base = base.sort_values(['abs_delta_robustez', 'delta_uniforme_robustez'], ascending=[False, False]).head(10)
    base = base.sort_values('delta_uniforme_robustez', ascending=True)

    y = np.arange(len(base))
    fig, ax = plt.subplots(figsize=(12.2, max(5.8, 0.48 * len(base) + 1.8)), constrained_layout=True)

    ax.axvline(0, linewidth=1.0, alpha=0.6)
    ax.barh(y, base['delta_uniforme_robustez'].to_numpy(dtype=float), alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels((base['artigo_id'] + ' - ' + base['estrato']).tolist())
    ax.set_xlabel('Δ de Score Global: Uniforme → Robustez')
    ax.set_title('Artigos Mais Sensíveis à Mudança de Pesos', pad=14)

    ax.grid(axis='x', linestyle='--', linewidth=0.8, alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    for yi, valor in zip(y, base['delta_uniforme_robustez'].to_numpy(dtype=float)):
        ax.text(valor + (0.15 if valor >= 0 else -0.15), yi, f'{valor:+.2f}', va='center', ha='left' if valor >= 0 else 'right', fontsize=9)

    fig.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)


def montar_relatorio(resumo, resumo_itens, scores_itens, scores_artigos, mudancas_artigos, mudancas_estratos, correlacoes, criticos, estabilidade, sensibilidade_artigos):
    global_uniforme = resumo[resumo['config_pesos'].eq('uniforme') & resumo['escopo'].eq('global')].iloc[0]
    piores_itens = criticos[criticos['config_pesos'].eq('uniforme')].nsmallest(5, 'media_item')
    top_itens = resumo_itens[resumo_itens['config_pesos'].eq('uniforme')].sort_values(['mediana', 'estrato'], ascending=[False, True]).head(5)
    bottom_itens = resumo_itens[resumo_itens['config_pesos'].eq('uniforme')].sort_values(['mediana', 'estrato'], ascending=[True, True]).head(5)

    total = scores_itens[['config_pesos', 'estrato', 'item_id']].drop_duplicates()
    observado = resumo_itens[['config_pesos', 'estrato', 'item_id']].drop_duplicates()
    faltantes = total.merge(observado, on=['config_pesos', 'estrato', 'item_id'], how='left', indicator=True)
    faltantes = faltantes[faltantes['_merge'].eq('left_only')][['config_pesos', 'estrato', 'item_id']].sort_values(['config_pesos', 'estrato', 'item_id'])

    base_uniforme_itens = scores_itens[scores_itens['config_pesos'].eq('uniforme')].copy()
    cobertura = (
        base_uniforme_itens.groupby(['estrato', 'item_id'], as_index=False)
        .agg(item_label=('item_label', 'first'), prop_na=('na', 'mean'), n=('na', 'size'))
    )
    cobertura['pct_na'] = 100 * cobertura['prop_na']
    piores_coberturas = cobertura.sort_values(['pct_na', 'estrato', 'item_id'], ascending=[False, True, True]).head(5)

    artigos_uniforme = scores_artigos[scores_artigos['config_pesos'].eq('uniforme')].copy()
    rho_na_score = artigos_uniforme['n_na'].corr(artigos_uniforme['score_global'], method='spearman')
    resumo_na_score = (
        artigos_uniforme.groupby('n_na', as_index=False)
        .agg(n=('artigo_id', 'size'), mediana_score=('score_global', 'median'))
        .sort_values('n_na')
    )

    mais_sensiveis = (
        sensibilidade_artigos.assign(abs_delta_robustez=sensibilidade_artigos['delta_uniforme_robustez'].abs())
        .sort_values(['abs_delta_robustez', 'delta_uniforme_robustez'], ascending=[False, False])
        .head(5)
    )

    linhas = [
        '# Relatorio da etapa (vi)',
        '',
        '## Escore global no esquema uniforme',
        f"- Media: {global_uniforme['media']:.2f}",
        f"- Mediana: {global_uniforme['mediana']:.2f}",
        f"- IC95% da media: [{global_uniforme['ic95_media_inf']:.2f}, {global_uniforme['ic95_media_sup']:.2f}]",
        f"- IC95% da mediana: [{global_uniforme['ic95_mediana_inf']:.2f}, {global_uniforme['ic95_mediana_sup']:.2f}]",
        '',
        '## Mudancas de ranking entre configuracoes',
    ]

    for _, row in mudancas_artigos.iterrows():
        linhas.append(f"- Artigos | {row['comparacao']}: media abs ranking={row['mudanca_media_absoluta_ranking']:.2f}; max abs ranking={row['mudanca_maxima_absoluta_ranking']:.2f}; media abs score={row['mudanca_media_absoluta_score']:.2f}; max abs score={row['mudanca_maxima_absoluta_score']:.2f}")
    for _, row in mudancas_estratos.iterrows():
        linhas.append(f"- Estratos | {row['comparacao']}: media abs ranking={row['mudanca_media_absoluta_ranking']:.2f}; max abs ranking={row['mudanca_maxima_absoluta_ranking']:.2f}; media abs mediana={row['mudanca_media_absoluta_mediana']:.2f}; max abs mediana={row['mudanca_maxima_absoluta_mediana']:.2f}")

    linhas += ['', '## Correlacoes de Spearman', '- Interpretar as correlacoes dos estratos com cautela, pois ha apenas tres estratos.']
    for _, row in correlacoes.iterrows():
        linhas.append(f"- {row['escopo']} | {row['config_a']} vs {row['config_b']}: rho={row['spearman_rho']:.4f}; p={row['p_fmt']}")

    linhas += ['', '## Itens mais criticos no esquema uniforme']
    for _, row in piores_itens.iterrows():
        linhas.append(f"- {row['item_id']} ({row['item_label']}): media={row['media_item']:.2f}; IC95%=[{row['ic95_inf']:.2f}, {row['ic95_sup']:.2f}]")

    linhas += ['', '## Estabilidade dos itens criticos']
    for _, row in estabilidade.iterrows():
        linhas.append(f"- {row['comparacao']}: rho dos ranks={row['spearman_rho_rank_itens']:.4f}; p={row['p_fmt']}; sobreposicao dos 5 piores itens={int(row['sobreposicao_bottom5'])}")

    linhas += ['', '## Itens com maiores medianas no esquema uniforme']
    for _, row in top_itens.iterrows():
        linhas.append(f"- {row['estrato']} | {row['item_id']} ({row['item_label']}): mediana={row['mediana']:.2f}")

    linhas += ['', '## Itens com menores medianas no esquema uniforme']
    for _, row in bottom_itens.iterrows():
        linhas.append(f"- {row['estrato']} | {row['item_id']} ({row['item_label']}): mediana={row['mediana']:.2f}")

    linhas += ['', '## Cobertura dos itens no esquema uniforme']
    for _, row in piores_coberturas.iterrows():
        linhas.append(f"- {row['estrato']} | {row['item_id']} ({row['item_label']}): NA={row['pct_na']:.1f}% em n={int(row['n'])}")

    linhas += ['', '## Relacao entre faltantes e score global']
    linhas.append(f'- Spearman entre n_na e score_global: rho={rho_na_score:.4f}')
    for _, row in resumo_na_score.iterrows():
        linhas.append(f"- n_na={int(row['n_na'])}: n={int(row['n'])}; mediana do score={row['mediana_score']:.2f}")

    linhas += ['', '## Artigos mais sensiveis a mudanca de pesos']
    for _, row in mais_sensiveis.iterrows():
        linhas.append(f"- {row['artigo_id']} ({row['estrato']}): Δ uniforme→nucleares={row['delta_uniforme_nucleares']:+.2f}; Δ uniforme→robustez={row['delta_uniforme_robustez']:+.2f}")

    if len(faltantes):
        linhas += ['', '## Combinacoes sem resumo de item', '- As combinacoes abaixo ficaram fora de resumo_itens.csv porque todos os registros eram NA:']
        for _, row in faltantes.iterrows():
            linhas.append(f"- {row['config_pesos']} | {row['estrato']} | {row['item_id']}")

    linhas.append('')
    return '\n'.join(linhas)


def main():
    out_dir = OUT_ANALISE_AUDITORIA_DIR

    artigos = pd.read_csv(out_dir / 'scores_artigos.csv')
    itens = pd.read_csv(out_dir / 'scores_itens.csv')
    resumo = pd.read_csv(out_dir / 'resumo_scores.csv')
    resumo_itens = pd.read_csv(out_dir / 'resumo_itens.csv')
    criticos = pd.read_csv(out_dir / 'itens_criticos.csv')
    sensibilidade_artigos = pd.read_csv(out_dir / 'sensibilidade_artigos.csv')
    sensibilidade = pd.read_csv(out_dir / 'sensibilidade_estratos.csv')
    mudancas_artigos = pd.read_csv(out_dir / 'mudancas_artigos.csv')
    mudancas_estratos = pd.read_csv(out_dir / 'mudancas_estratos.csv')
    correlacoes = pd.read_csv(out_dir / 'correlacoes_configs.csv')
    estabilidade = pd.read_csv(out_dir / 'estabilidade_criticos.csv')

    heatmap_itens(
        itens[itens['config_pesos'].eq('uniforme')].copy(),
        artigos[artigos['config_pesos'].eq('uniforme')].copy(),
        sensibilidade_artigos.copy(),
        out_dir / 'heatmap_itens.png'
    )

    medianas_estratos(sensibilidade, resumo, out_dir / 'medianas_estratos.png')

    for config in CONFIGS:
        plot_scores_estratos(
            artigos[artigos['config_pesos'].eq(config)].copy(),
            resumo,
            config,
            out_dir / f'scores_estratos_{config}.png'
        )

    plot_itens_criticos_estratos(resumo_itens.copy(), criticos.copy(), out_dir / 'itens_criticos_estratos.png')
    plot_sensibilidade_artigos(sensibilidade_artigos.copy(), out_dir / 'sensibilidade_artigos.png')

    relatorio = montar_relatorio(
        resumo,
        resumo_itens,
        itens,
        artigos,
        mudancas_artigos,
        mudancas_estratos,
        correlacoes,
        criticos,
        estabilidade,
        sensibilidade_artigos
    )

    (out_dir / 'relatorio.md').write_text(relatorio, encoding='utf-8')


if __name__ == '__main__':
    main()