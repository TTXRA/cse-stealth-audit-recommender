# Diretório `scripts`

Este diretório contém os códigos Python usados para executar as etapas computacionais da pesquisa.

Os scripts são organizados por etapa e utilizam funções e configurações compartilhadas em `scripts/utils/`.

## Estrutura

```text
scripts/
  etapa_01_corpus/
  etapa_02_amostragem/
  etapa_05_consistencia/
  etapa_06_auditoria/
  etapa_08_robustez/
  etapa_09_recomendador/
  etapa_10_avaliacao_loso/
  utils/
```

## Configuração central

Instale as dependências conforme o [README principal](../README.md) e inclua
a raiz do repositório no caminho de importação antes dos comandos abaixo:
`$env:PYTHONPATH = (Get-Location).Path` no PowerShell ou
`export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"` em Linux/macOS.
Reexecute em uma cópia de trabalho, pois as saídas podem ser sobrescritas.

O arquivo `scripts/utils/config.py` centraliza caminhos, parâmetros e constantes do projeto, incluindo:

- diretórios de entrada e saída;
- semente pseudoaleatória;
- janela temporal;
- parâmetros de amostragem;
- domínios válidos;
- configurações do recomendador;
- parâmetros de bootstrap e avaliação.

O arquivo `scripts/utils/common.py` reúne funções auxiliares reutilizadas pelos scripts, como leitura, validação, normalização, criação de diretórios e geração de hashes.

## Etapa 01: corpus

Scripts:

- `01_padronizar_master.py`
- `02_filtrar_elegibilidade.py`
- `03_gerar_rastreabilidade_corpus.py`

Finalidade:

- padronizar a base mestre;
- filtrar a janela temporal;
- identificar estudos empíricos quantitativos;
- gerar listas de elegíveis e excluídos;
- produzir arquivos de rastreabilidade.

Execução:

```bash
python scripts/etapa_01_corpus/01_padronizar_master.py
python scripts/etapa_01_corpus/02_filtrar_elegibilidade.py
python scripts/etapa_01_corpus/03_gerar_rastreabilidade_corpus.py
```

## Etapa 02: amostragem

Scripts:

- `01_sortear_amostra.py`
- `02_gerar_rastreabilidade_amostra.py`

Finalidade:

- sortear a amostra estratificada por modalidade;
- gerar listas de titulares e suplentes;
- registrar semente, parâmetros e alocação;
- gerar arquivos de rastreabilidade e hashes.

Execução:

```bash
python scripts/etapa_02_amostragem/01_sortear_amostra.py
python scripts/etapa_02_amostragem/02_gerar_rastreabilidade_amostra.py
```

## Etapa 05: consistência

Script:

- `01_calcular_consistencia.py`

Finalidade:

- parear auditoria principal e reteste;
- calcular kappa ponderado dos itens nucleares;
- calcular ICC(3,1) do escore global;
- gerar bases pareadas e resumo de validação.

Execução:

```bash
python scripts/etapa_05_consistencia/01_calcular_consistencia.py
```

## Etapa 06: auditoria

Scripts:

- `01_calcular_escores.py`
- `02_analisar_sensibilidade.py`
- `03_gerar_figuras_relatorio.py`

Finalidade:

- calcular escores globais e por item;
- comparar configurações de pesos;
- identificar itens críticos;
- gerar gráficos e relatório da auditoria.

Execução:

```bash
python scripts/etapa_06_auditoria/01_calcular_escores.py
python scripts/etapa_06_auditoria/02_analisar_sensibilidade.py
python scripts/etapa_06_auditoria/03_gerar_figuras_relatorio.py
```

## Etapa 08: robustez

Scripts:

- `01_calcular_indice_robustez.py`
- `02_gerar_figuras_robustez.py`

Finalidade:

- calcular o índice de robustez `R` por cenário;
- gerar resumos por modalidade e família de modelos;
- produzir gráficos exploratórios de robustez.

Execução:

```bash
python scripts/etapa_08_robustez/01_calcular_indice_robustez.py
python scripts/etapa_08_robustez/02_gerar_figuras_robustez.py
```

## Etapa 09: recomendador

Scripts:

- `01_validar_base.py`
- `02_recomendar_familias.py`

Finalidade:

- validar a base de robustez;
- aplicar regras de filtragem e recuo progressivo;
- gerar ranking de famílias de modelos por cenário;
- registrar suporte, incerteza e filtros relaxados.

Execução:

```bash
python scripts/etapa_09_recomendador/01_validar_base.py
python scripts/etapa_09_recomendador/02_recomendar_familias.py
```

## Etapa 10: avaliação deixando um estudo de fora

Script:

- `01_avaliar_recomendador.py`

Finalidade:

- executar validação leave-one-study-out;
- comparar o recomendador com linhas de base;
- calcular acerto top-1 e top-k;
- avaliar diferenças de robustez em relação aos baselines;
- gerar resumo e gráfico da avaliação.

Execução:

```bash
python scripts/etapa_10_avaliacao_loso/01_avaliar_recomendador.py
```

## Ordem geral recomendada

```bash
python scripts/etapa_01_corpus/01_padronizar_master.py
python scripts/etapa_01_corpus/02_filtrar_elegibilidade.py
python scripts/etapa_01_corpus/03_gerar_rastreabilidade_corpus.py
python scripts/etapa_02_amostragem/01_sortear_amostra.py
python scripts/etapa_02_amostragem/02_gerar_rastreabilidade_amostra.py
python scripts/etapa_05_consistencia/01_calcular_consistencia.py
python scripts/etapa_06_auditoria/01_calcular_escores.py
python scripts/etapa_06_auditoria/02_analisar_sensibilidade.py
python scripts/etapa_06_auditoria/03_gerar_figuras_relatorio.py
python scripts/etapa_08_robustez/01_calcular_indice_robustez.py
python scripts/etapa_08_robustez/02_gerar_figuras_robustez.py
python scripts/etapa_09_recomendador/01_validar_base.py
python scripts/etapa_09_recomendador/02_recomendar_familias.py
python scripts/etapa_10_avaliacao_loso/01_avaliar_recomendador.py
```

## Requisitos

Bibliotecas principais:

```text
pandas
numpy
scipy
scikit-learn
matplotlib
```

## Observações

- Execute os scripts a partir da raiz do repositório.
- Antes de reexecutar etapas, verifique se arquivos manuais em `artifacts/` e `data/audit/` estão atualizados.
- Arquivos em `__pycache__/` não devem ser versionados.
