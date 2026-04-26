from itertools import combinations
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from scripts.utils.config import OUT_ANALISE_AUDITORIA_DIR, ANALISE_AUDITORIA_N_BOOTSTRAP, ANALISE_AUDITORIA_SEED, CONFIGS

COLS_META = ['artigo_id', 'estrato', 'tarefa', 'titulo', 'ano', 'venue', 'doi']


def formatar_p(valor):
    if pd.isna(valor):
        return ''
    if valor == 0.0:
        return '<1e-300'
    return f'{valor:.3e}'


def reamostra_estratos(df, rng):
    return pd.concat([
        grupo.sample(n=len(grupo), replace=True, random_state=int(rng.integers(0, 2**32 - 1)))
        for _, grupo in df.groupby('tarefa', sort=True)
    ], ignore_index=True)


def correlacoes_configs(df, escopo):
    linhas = []
    for a, b in combinations(CONFIGS, 2):
        rho, p_valor = spearmanr(df[a], df[b], nan_policy='omit')
        linhas.append({
            'escopo': escopo,
            'config_a': a,
            'config_b': b,
            'spearman_rho': rho,
            'p_valor': p_valor,
            'p_fmt': formatar_p(p_valor),
        })
    return pd.DataFrame(linhas)


def sensibilidade_artigos(df):
    meta = df[COLS_META].drop_duplicates(subset=['artigo_id'])
    valores = df[['artigo_id', 'config_pesos', 'score_global']].pivot(index='artigo_id', columns='config_pesos', values='score_global').reset_index()
    out = meta.merge(valores, on='artigo_id', how='left')

    for config in CONFIGS:
        out[f'rank_{config}'] = out[config].rank(method='min', ascending=False)

    out['delta_uniforme_nucleares'] = out['nucleares'] - out['uniforme']
    out['delta_uniforme_robustez'] = out['robustez'] - out['uniforme']
    out['delta_rank_uniforme_nucleares'] = out['rank_nucleares'] - out['rank_uniforme']
    out['delta_rank_uniforme_robustez'] = out['rank_robustez'] - out['rank_uniforme']

    mudancas = pd.DataFrame({
        'comparacao': ['uniforme_vs_nucleares', 'uniforme_vs_robustez'],
        'mudanca_media_absoluta_ranking': [float(out['delta_rank_uniforme_nucleares'].abs().mean()), float(out['delta_rank_uniforme_robustez'].abs().mean())],
        'mudanca_maxima_absoluta_ranking': [float(out['delta_rank_uniforme_nucleares'].abs().max()), float(out['delta_rank_uniforme_robustez'].abs().max())],
        'mudanca_media_absoluta_score': [float(out['delta_uniforme_nucleares'].abs().mean()), float(out['delta_uniforme_robustez'].abs().mean())],
        'mudanca_maxima_absoluta_score': [float(out['delta_uniforme_nucleares'].abs().max()), float(out['delta_uniforme_robustez'].abs().max())],
    })

    return out.sort_values('rank_uniforme').reset_index(drop=True), mudancas, correlacoes_configs(out, 'artigos')


def sensibilidade_estratos(df):
    out = df[df['escopo'].eq('estrato')].pivot(index='estrato', columns='config_pesos', values='mediana').reset_index()

    for config in CONFIGS:
        out[f'rank_{config}'] = out[config].rank(method='min', ascending=False)

    out['delta_uniforme_nucleares'] = out['nucleares'] - out['uniforme']
    out['delta_uniforme_robustez'] = out['robustez'] - out['uniforme']
    out['delta_rank_uniforme_nucleares'] = out['rank_nucleares'] - out['rank_uniforme']
    out['delta_rank_uniforme_robustez'] = out['rank_robustez'] - out['rank_uniforme']

    mudancas = pd.DataFrame({
        'comparacao': ['uniforme_vs_nucleares', 'uniforme_vs_robustez'],
        'mudanca_media_absoluta_ranking': [float(out['delta_rank_uniforme_nucleares'].abs().mean()), float(out['delta_rank_uniforme_robustez'].abs().mean())],
        'mudanca_maxima_absoluta_ranking': [float(out['delta_rank_uniforme_nucleares'].abs().max()), float(out['delta_rank_uniforme_robustez'].abs().max())],
        'mudanca_media_absoluta_mediana': [float(out['delta_uniforme_nucleares'].abs().mean()), float(out['delta_uniforme_robustez'].abs().mean())],
        'mudanca_maxima_absoluta_mediana': [float(out['delta_uniforme_nucleares'].abs().max()), float(out['delta_uniforme_robustez'].abs().max())],
    })

    return out.sort_values('rank_uniforme').reset_index(drop=True), mudancas, correlacoes_configs(out, 'estratos')


def itens_criticos(df, n_boot, seed):
    rng = np.random.default_rng(seed)
    linhas = []
    base = df[df['na'].eq(0)].copy()

    for config, grupo in base.groupby('config_pesos', sort=True):
        observado = grupo.groupby(['item_id', 'item_label'], as_index=False)['score_item'].mean().rename(columns={'score_item': 'media_item'})
        bolsa = {item: [] for item in observado['item_id']}
        artigos = grupo[['artigo_id', 'estrato', 'tarefa']].drop_duplicates()

        for _ in range(n_boot):
            amostra = reamostra_estratos(artigos, rng).merge(grupo[['artigo_id', 'estrato', 'tarefa', 'item_id', 'score_item']], on=['artigo_id', 'estrato', 'tarefa'], how='left')
            medias = amostra.groupby('item_id')['score_item'].mean()
            for item in observado['item_id']:
                bolsa[item].append(float(medias.get(item, np.nan)))

        observado['config_pesos'] = config
        observado['ic95_inf'] = observado['item_id'].map(lambda item: float(np.nanquantile(bolsa[item], 0.025)))
        observado['ic95_sup'] = observado['item_id'].map(lambda item: float(np.nanquantile(bolsa[item], 0.975)))
        observado['rank_critico'] = observado['media_item'].rank(method='dense', ascending=True).astype(int)
        linhas.append(observado)

    return pd.concat(linhas, ignore_index=True).sort_values(['config_pesos', 'media_item', 'item_id']).reset_index(drop=True)


def estabilidade_criticos(df):
    out = df.pivot(index=['item_id', 'item_label'], columns='config_pesos', values='rank_critico').reset_index()

    for config in CONFIGS:
        if config not in out.columns:
            out[config] = np.nan

    out['delta_rank_uniforme_nucleares'] = out['nucleares'] - out['uniforme']
    out['delta_rank_uniforme_robustez'] = out['robustez'] - out['uniforme']

    bottom = {
        config: set(df[df['config_pesos'].eq(config)].nsmallest(5, 'media_item')['item_id'].tolist())
        for config in CONFIGS
    }

    linhas = []
    for a, b in combinations(CONFIGS, 2):
        rho, p_valor = spearmanr(out[a], out[b], nan_policy='omit')
        linhas.append({
            'comparacao': f'{a}_vs_{b}',
            'spearman_rho_rank_itens': rho,
            'p_valor': p_valor,
            'p_fmt': formatar_p(p_valor),
            'sobreposicao_bottom5': len(bottom[a] & bottom[b]),
        })

    resumo = pd.DataFrame(linhas).sort_values('comparacao').reset_index(drop=True)
    return out.sort_values('uniforme').reset_index(drop=True), resumo


def main():
    out_dir = OUT_ANALISE_AUDITORIA_DIR

    artigos = pd.read_csv(out_dir / 'scores_artigos.csv')
    resumo = pd.read_csv(out_dir / 'resumo_scores.csv')
    itens = pd.read_csv(out_dir / 'scores_itens.csv')

    tabela_artigos, mudancas_artigos, corr_artigos = sensibilidade_artigos(artigos)
    tabela_estratos, mudancas_estratos, corr_estratos = sensibilidade_estratos(resumo)
    criticos = itens_criticos(itens, ANALISE_AUDITORIA_N_BOOTSTRAP, ANALISE_AUDITORIA_SEED)
    ranks, estabilidade = estabilidade_criticos(criticos)

    tabela_artigos.to_csv(out_dir / 'sensibilidade_artigos.csv', index=False, encoding='utf-8-sig')
    tabela_estratos.to_csv(out_dir / 'sensibilidade_estratos.csv', index=False, encoding='utf-8-sig')
    mudancas_artigos.to_csv(out_dir / 'mudancas_artigos.csv', index=False, encoding='utf-8-sig')
    mudancas_estratos.to_csv(out_dir / 'mudancas_estratos.csv', index=False, encoding='utf-8-sig')
    pd.concat([corr_artigos, corr_estratos], ignore_index=True).to_csv(out_dir / 'correlacoes_configs.csv', index=False, encoding='utf-8-sig')
    criticos.to_csv(out_dir / 'itens_criticos.csv', index=False, encoding='utf-8-sig')
    ranks.to_csv(out_dir / 'ranks_criticos.csv', index=False, encoding='utf-8-sig')
    estabilidade.to_csv(out_dir / 'estabilidade_criticos.csv', index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    main()