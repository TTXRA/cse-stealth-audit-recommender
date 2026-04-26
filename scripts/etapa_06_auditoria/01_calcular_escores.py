import numpy as np
import pandas as pd
from scripts.utils.common import read_csv, normalize_columns, parse_bin01
from scripts.utils.config import INPUT_AUDITORIA, INPUT_MAPEAMENTO_MASTER, OUT_ANALISE_AUDITORIA_DIR, ANALISE_AUDITORIA_N_BOOTSTRAP, ANALISE_AUDITORIA_SEED, CONFIGS

ROTULOS_ITENS = {
    'DAD': 'Dados e Demografia',
    'ROT': 'Anotacao e Qualidade do Rotulo',
    'ESC': 'Escopo e Construto',
    'PRE': 'Pre-processamento e Caracteristicas',
    'PRT': 'Particionamento e Validacao',
    'MOD': 'Modelo, Hiperparametros e Treino',
    'MET': 'Metricas e Incerteza',
    'CAL': 'Calibracao',
    'SUB': 'Subgrupos e Equidade',
    'ROB': 'Robustez e Sensibilidade',
    'REP': 'Reprodutibilidade e Artefatos',
    'ETH': 'Etica, Privacidade e Uso Responsavel',
    'VZ': 'Prevencao de Vazamento',
    'EXT': 'Testes entre Bases',
    'CST': 'Custo e Latencia',
    'SIN': 'Sincronizacao Multimodal',
}

ITENS_NUCLEARES = {'DAD', 'ROT', 'ESC', 'PRT', 'MOD', 'MET', 'REP', 'VZ', 'EXT'}
ITENS_ROBUSTEZ = {'PRT', 'MET', 'VZ', 'EXT', 'ROB'}


def mapa_pesos(itens):
    return {
        'uniforme': {item: 1.0 for item in itens},
        'nucleares': {item: 2.0 if item in ITENS_NUCLEARES else 1.0 for item in itens},
        'robustez': {item: 2.0 if item in ITENS_ROBUSTEZ else 1.0 for item in itens},
    }


def aplicar_pesos(df, pesos):
    out = df.copy()
    out['peso'] = out['item_id'].map(pesos).astype(float)
    out['peso_ok'] = np.where(out['na'].eq(1), 0.0, out['peso'])
    out['contrib'] = np.where(out['na'].eq(1), 0.0, out['grau'] * out['peso'])
    out['denom'] = 2.0 * out['peso_ok']
    out['score_item'] = np.where(out['na'].eq(1), np.nan, 50.0 * out['grau'])
    return out


def scores_artigos(df, meta, config):
    out = df.groupby(['artigo_id', 'estrato'], as_index=False).agg(
        n_itens=('item_id', 'size'),
        n_na=('na', 'sum'),
        soma=('contrib', 'sum'),
        denom=('denom', 'sum'),
    )
    out['score_global'] = np.where(out['denom'].gt(0), out['soma'] / out['denom'] * 100.0, np.nan)
    out['config_pesos'] = config
    out = out.merge(meta, on='artigo_id', how='left')
    cols = ['config_pesos', 'artigo_id', 'estrato', 'tarefa', 'score_global', 'n_itens', 'n_na', 'titulo', 'ano', 'venue', 'doi']
    return out[cols].sort_values(['config_pesos', 'estrato', 'score_global', 'artigo_id'], ascending=[True, True, False, True])


def scores_itens(df, meta, config):
    out = df.groupby(['artigo_id', 'estrato', 'item_id', 'item_label'], as_index=False).agg(
        score_item=('score_item', 'mean'),
        na=('na', 'max'),
    )
    out['config_pesos'] = config
    out = out.merge(meta, on='artigo_id', how='left')
    cols = ['config_pesos', 'artigo_id', 'estrato', 'tarefa', 'item_id', 'item_label', 'score_item', 'na', 'titulo', 'ano', 'venue', 'doi']
    return out[cols].sort_values(['config_pesos', 'estrato', 'artigo_id', 'item_id'])


def reamostra_estratos(df, rng):
    return pd.concat([
        grupo.sample(n=len(grupo), replace=True, random_state=int(rng.integers(0, 2**32 - 1)))
        for _, grupo in df.groupby('tarefa', sort=True)
    ], ignore_index=True)


def bootstrap_scores(valores, n_boot, rng):
    medias = np.empty(n_boot, dtype=float)
    medianas = np.empty(n_boot, dtype=float)
    n = len(valores)
    for i in range(n_boot):
        amostra = valores[rng.integers(0, n, n)]
        medias[i] = np.mean(amostra)
        medianas[i] = np.median(amostra)
    return medias, medianas


def resumo_artigos(df, n_boot, seed):
    rng = np.random.default_rng(seed)
    base = df[['artigo_id', 'estrato', 'tarefa', 'score_global']].drop_duplicates()
    ids = base[['artigo_id', 'estrato', 'tarefa']].drop_duplicates()
    config = df['config_pesos'].iat[0]
    valores = base['score_global'].dropna().to_numpy(dtype=float)

    medias_boot = []
    medianas_boot = []
    for _ in range(n_boot):
        amostra = reamostra_estratos(ids, rng).merge(base, on=['artigo_id', 'estrato', 'tarefa'], how='left')
        vals = amostra['score_global'].dropna().to_numpy(dtype=float)
        medias_boot.append(np.mean(vals))
        medianas_boot.append(np.median(vals))

    linhas = [{
        'config_pesos': config,
        'escopo': 'global',
        'estrato': 'TODOS',
        'n': int(len(valores)),
        'media': float(np.mean(valores)),
        'mediana': float(np.median(valores)),
        'q1': float(np.quantile(valores, 0.25)),
        'q3': float(np.quantile(valores, 0.75)),
        'ic95_media_inf': float(np.quantile(medias_boot, 0.025)),
        'ic95_media_sup': float(np.quantile(medias_boot, 0.975)),
        'ic95_mediana_inf': float(np.quantile(medianas_boot, 0.025)),
        'ic95_mediana_sup': float(np.quantile(medianas_boot, 0.975)),
    }]

    for estrato, grupo in base.groupby('estrato', sort=True):
        valores = grupo['score_global'].dropna().to_numpy(dtype=float)
        medias, medianas = bootstrap_scores(valores, n_boot, rng)
        linhas.append({
            'config_pesos': config,
            'escopo': 'estrato',
            'estrato': estrato,
            'n': int(len(valores)),
            'media': float(np.mean(valores)),
            'mediana': float(np.median(valores)),
            'q1': float(np.quantile(valores, 0.25)),
            'q3': float(np.quantile(valores, 0.75)),
            'ic95_media_inf': float(np.quantile(medias, 0.025)),
            'ic95_media_sup': float(np.quantile(medias, 0.975)),
            'ic95_mediana_inf': float(np.quantile(medianas, 0.025)),
            'ic95_mediana_sup': float(np.quantile(medianas, 0.975)),
        })
    return pd.DataFrame(linhas)


def resumo_itens(df, n_boot, seed):
    rng = np.random.default_rng(seed)
    linhas = []
    base = df[df['na'].eq(0)]
    for (config, estrato, item_id, item_label), grupo in base.groupby(['config_pesos', 'estrato', 'item_id', 'item_label'], sort=True):
        valores = grupo['score_item'].dropna().to_numpy(dtype=float)
        medias, medianas = bootstrap_scores(valores, n_boot, rng)
        linhas.append({
            'config_pesos': config,
            'estrato': estrato,
            'item_id': item_id,
            'item_label': item_label,
            'n': int(len(valores)),
            'media': float(np.mean(valores)),
            'mediana': float(np.median(valores)),
            'q1': float(np.quantile(valores, 0.25)),
            'q3': float(np.quantile(valores, 0.75)),
            'ic95_media_inf': float(np.quantile(medias, 0.025)),
            'ic95_media_sup': float(np.quantile(medias, 0.975)),
            'ic95_mediana_inf': float(np.quantile(medianas, 0.025)),
            'ic95_mediana_sup': float(np.quantile(medianas, 0.975)),
        })
    return pd.DataFrame(linhas)


def main():
    OUT_ANALISE_AUDITORIA_DIR.mkdir(parents=True, exist_ok=True)

    auditoria = normalize_columns(read_csv(INPUT_AUDITORIA))
    auditoria['artigo_id'] = auditoria['artigo_id'].astype(str).str.strip()
    auditoria['estrato'] = auditoria['estrato'].astype(str).str.strip().str.upper()
    auditoria['item_id'] = auditoria['item_id'].astype(str).str.strip().str.upper()
    auditoria['grau'] = pd.to_numeric(auditoria['grau'], errors='coerce').astype(float)
    auditoria['na'] = parse_bin01(auditoria['na'], 'NA', auditoria['artigo_id']).astype(int)
    auditoria['item_label'] = auditoria['item_id'].map(ROTULOS_ITENS).fillna(auditoria['item_id'])

    meta = normalize_columns(read_csv(INPUT_MAPEAMENTO_MASTER))
    meta['artigo_id'] = meta['artigo_id'].astype(str).str.strip()
    meta['tarefa'] = meta['tarefa'].astype(str).str.strip().str.upper()
    meta = meta[meta['artigo_id'].isin(auditoria['artigo_id'].unique())][['artigo_id', 'titulo', 'ano', 'venue', 'tarefa', 'doi']].drop_duplicates()

    tabela_pesos = mapa_pesos(sorted(auditoria['item_id'].unique()))
    todos_artigos = []
    todos_itens = []
    todos_resumos = []

    for config in CONFIGS:
        base = aplicar_pesos(auditoria, tabela_pesos[config])
        artigos = scores_artigos(base, meta, config)
        itens = scores_itens(base, meta, config)
        todos_artigos.append(artigos)
        todos_itens.append(itens)
        todos_resumos.append(resumo_artigos(artigos, ANALISE_AUDITORIA_N_BOOTSTRAP, ANALISE_AUDITORIA_SEED))

    todos_artigos = pd.concat(todos_artigos, ignore_index=True)
    todos_itens = pd.concat(todos_itens, ignore_index=True)
    todos_resumos = pd.concat(todos_resumos, ignore_index=True)
    resumo_itens_df = resumo_itens(todos_itens, ANALISE_AUDITORIA_N_BOOTSTRAP, ANALISE_AUDITORIA_SEED)

    out_dir = OUT_ANALISE_AUDITORIA_DIR
    todos_artigos.to_csv(out_dir / 'scores_artigos.csv', index=False, encoding='utf-8-sig')
    todos_itens.to_csv(out_dir / 'scores_itens.csv', index=False, encoding='utf-8-sig')
    todos_resumos.to_csv(out_dir / 'resumo_scores.csv', index=False, encoding='utf-8-sig')
    resumo_itens_df.to_csv(out_dir / 'resumo_itens.csv', index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    main()