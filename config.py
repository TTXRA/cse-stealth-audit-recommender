from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BASE_DIR = ROOT_DIR / "data"

IN_DIR = BASE_DIR / "raw"
MID_DIR = BASE_DIR / "intermediate"
OUT_DIR = BASE_DIR / "output"

OUT_AMOSTRAS_DIR = OUT_DIR / "amostras"
OUT_PRISMA_DIR = OUT_DIR / "prisma"
OUT_LOGS_DIR = OUT_DIR / "logs"
OUT_ELEGIVEIS_DIR = OUT_DIR / "elegiveis"

INPUT_MAPEAMENTO_MASTER = IN_DIR / "mapeamento_master.csv"
INPUT_ROTULOS_ELEG = IN_DIR / "rotulos_elegibilidade.csv"

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
