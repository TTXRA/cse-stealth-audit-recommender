import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from scripts.utils.common import read_csv
from scripts.utils.config import ARQUIVO_SAIDA_ROBUSTEZ


def preparar_base(df):
    base = df.copy()

    for col in ['modalidade', 'modelo_familia']:
        if col in base.columns:
            base[col] = base[col].astype(str).str.strip()

    for col in ['R']:
        if col in base.columns:
            base[col] = pd.to_numeric(base[col], errors='coerce')

    return base


def plot_r_modalidade(df, arquivo):
    base = preparar_base(df)[['modalidade', 'R']].dropna().copy()

    ordem = (
        base.groupby('modalidade')['R']
        .median()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    xpos = np.arange(len(ordem))
    grupos = [base.loc[base['modalidade'].eq(m), 'R'].to_numpy(dtype=float) for m in ordem]

    fig, ax = plt.subplots(figsize=(10.2, 6.0), constrained_layout=True)

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

    medianas = np.array([np.median(g) if len(g) else np.nan for g in grupos], dtype=float)

    ax.plot(
        xpos,
        medianas,
        linewidth=1.4,
        alpha=0.8,
        zorder=2
    )

    for x, y in zip(xpos, medianas):
        if pd.notna(y):
            ax.annotate(
                f'{y:.3f}',
                (x, y),
                xytext=(0, 7),
                textcoords='offset points',
                ha='center',
                va='bottom',
                fontsize=8.5,
                bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='black', lw=0.7, alpha=0.95)
            )

    ax.set_xticks(xpos)
    ax.set_xticklabels([f'{m}\n(n={len(g)})' for m, g in zip(ordem, grupos)])
    ax.set_ylabel('Índice de Robustez (R)')
    ax.set_xlabel('Modalidade')
    ax.set_title('Distribuição de R por Modalidade', pad=12)

    ax.grid(axis='y', linestyle='--', linewidth=0.8, alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.margins(x=0.05)

    fig.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)


def heatmap_modalidade_familia(df, arquivo):
    base = preparar_base(df)[['modalidade', 'modelo_familia', 'R']].dropna().copy()

    ordem_modalidades = (
        base.groupby('modalidade')['R']
        .mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    ordem_familias = (
        base.groupby('modelo_familia')['R']
        .mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    matriz = (
        base.pivot_table(
            index='modalidade',
            columns='modelo_familia',
            values='R',
            aggfunc='mean'
        )
        .reindex(index=ordem_modalidades, columns=ordem_familias)
    )

    contagens = (
        base.groupby(['modalidade', 'modelo_familia'])
        .size()
        .unstack(fill_value=0)
        .reindex(index=ordem_modalidades, columns=ordem_familias)
    )

    h = max(5.5, 0.55 * len(ordem_modalidades) + 2.0)
    w = max(10.5, 0.72 * len(ordem_familias) + 4.8)

    fig = plt.figure(figsize=(w, h), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[max(10, 0.78 * len(ordem_familias) + 3), 0.26])

    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])

    cmap = plt.get_cmap('cividis').copy()
    cmap.set_bad('#ececec')

    imagem = ax.imshow(
        matriz.to_numpy(dtype=float),
        aspect='auto',
        cmap=cmap,
        interpolation='nearest'
    )

    ax.set_xticks(np.arange(len(ordem_familias)))
    ax.set_xticklabels(ordem_familias)
    ax.set_yticks(np.arange(len(ordem_modalidades)))
    ax.set_yticklabels(ordem_modalidades)

    ax.tick_params(axis='x', labelsize=10.2, pad=8, top=True, bottom=False, labeltop=True, labelbottom=False)
    ax.tick_params(axis='y', labelsize=9.5)

    ax.set_xlabel('Famílias de Modelo', labelpad=12)
    ax.xaxis.set_label_position('top')
    ax.set_ylabel('Modalidades')
    ax.set_title('Média de R por Modalidade × Família de Modelo', pad=16)

    ax.set_xticks(np.arange(-0.5, len(ordem_familias), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ordem_modalidades), 1), minor=True)
    ax.grid(which='minor', color='white', linestyle='-', linewidth=0.35, alpha=0.65)
    ax.tick_params(which='minor', bottom=False, left=False)

    valores = matriz.to_numpy(dtype=float)
    ns = contagens.to_numpy(dtype=int)

    for i in range(valores.shape[0]):
        for j in range(valores.shape[1]):
            v = valores[i, j]
            if pd.notna(v):
                txt = ax.text(
                    j,
                    i,
                    f'{v:.3f}\n(n={ns[i, j]})',
                    ha='center',
                    va='center',
                    fontsize=8.2,
                    color='white',
                    fontweight='semibold'
                )
                txt.set_path_effects([
                    pe.Stroke(linewidth=1.2, foreground='black'),
                    pe.Normal()
                ])

    for spine in ax.spines.values():
        spine.set_visible(False)

    barra = fig.colorbar(imagem, cax=cax)
    barra.set_label('Média de R')

    fig.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)


def executar():
    df = read_csv(ARQUIVO_SAIDA_ROBUSTEZ)

    pasta_saida = ARQUIVO_SAIDA_ROBUSTEZ.parent / 'graficos'
    pasta_saida.mkdir(parents=True, exist_ok=True)

    plot_r_modalidade(
        df.copy(),
        pasta_saida / 'boxplot_modalidade.png'
    )

    heatmap_modalidade_familia(
        df.copy(),
        pasta_saida / 'heatmap_modalidade_familia.png'
    )

    print(f'Arquivo gerado: {pasta_saida / "boxplot_modalidade.png"}')
    print(f'Arquivo gerado: {pasta_saida / "heatmap_modalidade_familia.png"}')


if __name__ == '__main__':
    executar()