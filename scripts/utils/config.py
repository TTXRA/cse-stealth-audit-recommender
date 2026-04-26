from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"

RAW_DIR = DATA_DIR / "raw"
MID_DIR = DATA_DIR / "intermediate"
OUT_DIR = DATA_DIR / "output"
AUDIT_DIR = DATA_DIR / "audit"

OUT_AMOSTRAS_DIR = OUT_DIR / "amostras"
OUT_PRISMA_DIR = OUT_DIR / "prisma"
OUT_LOGS_DIR = OUT_DIR / "logs"
OUT_ELEGIVEIS_DIR = OUT_DIR / "elegiveis"
OUT_ROBUSTEZ_DIR = OUT_DIR / "robustez"

INPUT_MAPEAMENTO_MASTER = RAW_DIR / "mapeamento_master.csv"
INPUT_ROTULOS_ELEG = RAW_DIR / "rotulos_elegibilidade.csv"

MID_CORPUS_PADRONIZADO = MID_DIR / "corpus_padronizado.csv"
MID_CORPUS_JANELA = MID_DIR / "corpus_janela.csv"
MID_CORPUS_EMP_QUANT = MID_DIR / "corpus_empirico_quant.csv"

OUT_ELEG_FER = OUT_ELEGIVEIS_DIR / "elegiveis_FER.csv"
OUT_ELEG_SER = OUT_ELEGIVEIS_DIR / "elegiveis_SER.csv"
OUT_ELEG_MULTI = OUT_ELEGIVEIS_DIR / "elegiveis_MULTI.csv"
OUT_EXCLUIDOS = OUT_ELEGIVEIS_DIR / "excluidos.csv"
OUT_PRISMA = OUT_PRISMA_DIR / "prisma_elegibilidade.csv"

OUT_LOG_CONTINGENCIA = OUT_LOGS_DIR / "log_contingencia.csv"
OUT_ALOCACAO_SORTEIO = OUT_LOGS_DIR / "alocacao_sorteio.csv"

OUT_AMOSTRA_FER = OUT_AMOSTRAS_DIR / "amostra_FER.csv"
OUT_AMOSTRA_SER = OUT_AMOSTRAS_DIR / "amostra_SER.csv"
OUT_AMOSTRA_MULTI = OUT_AMOSTRAS_DIR / "amostra_MULTI.csv"
OUT_REGISTRO_SORTEIO = OUT_LOGS_DIR / "registro_sorteio.csv"

ANO_INICIO = 2021
ANO_FIM = 2025

TAREFAS_VALIDAS = {"FER", "SER", "MULTI", "NA"}

RNG_SEED = 2025
N_ALVO_TOTAL = 16
MIN_POR_ESTRATO = 4
N_TITULARES = 8
N_SUPLENTES = 3

META_COLS = ["artigo_id", "ano", "titulo", "venue", "doi", "tarefa"]

ELEGIVEIS_POR_TAREFA = {
    "FER": OUT_ELEG_FER,
    "SER": OUT_ELEG_SER,
    "MULTI": OUT_ELEG_MULTI,
}

AMOSTRA_POR_TAREFA = {
    "FER": OUT_AMOSTRA_FER,
    "SER": OUT_AMOSTRA_SER,
    "MULTI": OUT_AMOSTRA_MULTI,
}

OUT_CONSISTENCIA_DIR = AUDIT_DIR / "saida_consistencia"

INPUT_AUDITORIA = AUDIT_DIR / "auditoria.csv"
INPUT_RETESTE = AUDIT_DIR / "reteste.csv"

OUT_PAREAMENTO_ITEM_A_ITEM = OUT_CONSISTENCIA_DIR / "pareamento_item_a_item.csv"
OUT_KAPPA_ITENS_NUCLEARES = OUT_CONSISTENCIA_DIR / "kappa_itens_nucleares.csv"
OUT_SCORES_AUDITORIA = OUT_CONSISTENCIA_DIR / "scores_auditoria.csv"
OUT_SCORES_RETESTE = OUT_CONSISTENCIA_DIR / "scores_reteste.csv"
OUT_SCORES_PAREADOS = OUT_CONSISTENCIA_DIR / "scores_pareados.csv"
OUT_ICC_3_1 = OUT_CONSISTENCIA_DIR / "icc_3_1.csv"
OUT_RESUMO_VALIDACAO = OUT_CONSISTENCIA_DIR / "resumo_validacao.json"

PESO_KAPPA = "quadratic"

OUT_ANALISE_AUDITORIA_DIR = AUDIT_DIR / "saida_analise_auditoria"

OUT_ANALISE_ARTIGOS_ESCORES = {
    "uniforme": OUT_ANALISE_AUDITORIA_DIR / "artigos_escores_uniforme.csv",
    "nucleares": OUT_ANALISE_AUDITORIA_DIR / "artigos_escores_nucleares.csv",
    "robustez": OUT_ANALISE_AUDITORIA_DIR / "artigos_escores_robustez.csv",
}

OUT_ANALISE_DISTRIBUICOES = {
    "uniforme": OUT_ANALISE_AUDITORIA_DIR / "distribuicao_score_uniforme.png",
    "nucleares": OUT_ANALISE_AUDITORIA_DIR / "distribuicao_score_nucleares.png",
    "robustez": OUT_ANALISE_AUDITORIA_DIR / "distribuicao_score_robustez.png",
}

OUT_ANALISE_ESCORES_POR_ITEM = OUT_ANALISE_AUDITORIA_DIR / "artigos_escores_por_item.csv"
OUT_ANALISE_TODAS_CONFIGURACOES = OUT_ANALISE_AUDITORIA_DIR / "artigos_escores_todas_configuracoes.csv"
OUT_ANALISE_RESUMO_ESTATISTICO = OUT_ANALISE_AUDITORIA_DIR / "resumo_estatistico_ic95.csv"
OUT_ANALISE_ITENS_CRITICOS = OUT_ANALISE_AUDITORIA_DIR / "itens_criticos_ic95.csv"
OUT_ANALISE_SENSIBILIDADE_RANKING = OUT_ANALISE_AUDITORIA_DIR / "sensibilidade_ranking_artigos.csv"
OUT_ANALISE_CORRELACOES = OUT_ANALISE_AUDITORIA_DIR / "correlacoes_spearman_configuracoes.csv"
OUT_ANALISE_RESUMO_MUDANCA_RANKING = OUT_ANALISE_AUDITORIA_DIR / "resumo_mudanca_ranking.csv"
OUT_ANALISE_CARACTERIZACAO_ARTIGOS = OUT_ANALISE_AUDITORIA_DIR / "caracterizacao_amostra_artigos.csv"
OUT_ANALISE_CARACTERIZACAO_RESUMO = OUT_ANALISE_AUDITORIA_DIR / "caracterizacao_amostra_resumo.csv"
OUT_ANALISE_HEATMAP = OUT_ANALISE_AUDITORIA_DIR / "heatmap_artigo_item.png"
OUT_ANALISE_CINCO_ITENS = OUT_ANALISE_AUDITORIA_DIR / "cinco_itens_menos_atendidos.png"

ANALISE_AUDITORIA_N_BOOTSTRAP = 1000
ANALISE_AUDITORIA_SEED = RNG_SEED

CONFIGS = ["uniforme", "nucleares", "robustez"]

LAMBDA_R = 0.7

ARQUIVO_CENARIOS = ARTIFACTS_DIR / "cenarios.csv"
ARQUIVO_AUDITORIA = AUDIT_DIR / "auditoria.csv"

ARQUIVO_SAIDA_ROBUSTEZ = OUT_ROBUSTEZ_DIR / "robustez_cenarios.csv"
ARQUIVO_RESUMO_MODALIDADE = OUT_ROBUSTEZ_DIR / "robustez_resumo_modalidade.csv"
ARQUIVO_RESUMO_FAMILIA = OUT_ROBUSTEZ_DIR / "robustez_resumo_familia.csv"

ITENS_W = ["PRT", "VZ", "MET", "EXT", "ROB"]

DATASETS_BASE_MULTICLASSE_PADRAO = {
    "FER-2013",
    "CK+",
    "JAFFE",
    "RAF-DB",
}