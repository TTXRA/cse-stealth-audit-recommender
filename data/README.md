# Diretório `data`

Este diretório concentra os dados de entrada, bases intermediárias, registros de auditoria e saídas analíticas produzidas pelos scripts do projeto.

## Estrutura

```text
data/
  raw/
  intermediate/
  audit/
  output/
```

## `raw/`

Contém os arquivos de entrada usados como ponto de partida do processamento.

Arquivos principais:

- `mapeamento_master.csv`: base mestre do corpus mapeado.
- `rotulos_elegibilidade.csv`: rótulos e indicadores usados na filtragem de elegibilidade.

Estes arquivos devem ser preservados como referência original do processamento.

## `intermediate/`

Contém bases intermediárias geradas a partir dos dados brutos.

Arquivos principais:

- `corpus_padronizado.csv`: corpus após padronização de campos e formatos.
- `corpus_janela.csv`: corpus filtrado pela janela temporal definida no protocolo.
- `corpus_empirico_quant.csv`: corpus filtrado para estudos empíricos com resultados quantitativos.

Esses arquivos documentam as transformações realizadas antes da seleção amostral.

## `audit/`

Contém as bases da auditoria de relato e suas saídas analíticas.

Arquivos principais:

- `auditoria.csv`: codificação principal dos artigos auditados.
- `auditoria.json`: versão em JSON da auditoria principal.
- `reteste.csv`: segunda codificação usada no teste--reteste.
- `reteste.json`: versão em JSON da base de reteste.

Subdiretórios principais:

- `saida_consistencia/`: resultados do teste--reteste e das métricas de consistência.
- `saida_analise_auditoria/`: escores, análises estatísticas, sensibilidade aos pesos, gráficos e relatório da auditoria.

Saídas relevantes de `saida_consistencia/`:

- `kappa_itens_nucleares.csv`: kappa ponderado dos itens nucleares.
- `icc_3_1.csv`: coeficiente de correlação intraclasse do escore global.
- `pareamento_item_a_item.csv`: pareamento entre auditoria e reteste por artigo e item.
- `scores_auditoria.csv`: escores da auditoria principal.
- `scores_reteste.csv`: escores da recodificação.
- `scores_pareados.csv`: escores pareados para análise de consistência.
- `resumo_validacao.json`: resumo estruturado da validação.

Saídas relevantes de `saida_analise_auditoria/`:

- `scores_artigos.csv`: escores por artigo.
- `scores_itens.csv`: escores por item.
- `scores_modalidades_*.png`: gráficos de distribuição por modalidade.
- `itens_criticos.csv`: itens menos atendidos.
- `heatmap_itens.png`: mapa de calor artigo por item.
- `sensibilidade_artigos.csv`: análise de sensibilidade por artigo.
- `correlacoes_configs.csv`: correlações entre configurações de pesos.
- `relatorio.md`: relatório textual da análise da auditoria.

## `output/`

Contém saídas finais e rastreáveis das etapas de amostragem, robustez, recomendação e avaliação.

Subdiretórios principais:

- `elegiveis/`: listas de artigos elegíveis por modalidade e registros de exclusão.
- `amostras/`: amostras sorteadas por modalidade.
- `logs/`: registros de sorteio, alocação e contingência.
- `prisma/`: tabelas para fluxograma PRISMA.
- `robustez/`: índices de robustez, rankings de recomendação e gráficos.
- `avaliacao_loso/`: avaliação deixando um estudo de fora.

Arquivos relevantes:

- `output/elegiveis/elegiveis_FER.csv`
- `output/elegiveis/elegiveis_SER.csv`
- `output/elegiveis/elegiveis_MULTI.csv`
- `output/amostras/amostra_FER.csv`
- `output/amostras/amostra_SER.csv`
- `output/amostras/amostra_MULTI.csv`
- `output/logs/registro_sorteio.csv`
- `output/prisma/prisma_final.csv`
- `output/robustez/robustez_cenarios.csv`
- `output/robustez/robustez_cenarios_clean.csv`
- `output/robustez/ranking_recomendacao.csv`
- `output/robustez/log_recomendacao.json`
- `output/avaliacao_loso/avaliacao_loso.csv`
- `output/avaliacao_loso/resumo_avaliacao_loso.csv`
- `output/avaliacao_loso/log_avaliacao_loso.json`

## Arquivos `.sha256`

Algumas saídas possuem arquivos `.sha256` correspondentes. Eles registram o resumo criptográfico do artefato e servem para verificar integridade e rastreabilidade.

Exemplo de verificação:

```bash
sha256sum -c data/output/logs/registro_sorteio.sha256
```

## Observações de uso

- Arquivos em `raw/` devem ser tratados como entrada original.
- Arquivos em `intermediate/` podem ser recriados a partir dos scripts da etapa 01.
- Arquivos em `output/` podem ser recriados pela execução ordenada dos scripts.
- Alterações manuais em bases de auditoria e cenários devem ser registradas no controle de versão.

## Modalidade e tarefa

Nas bases do corpus, de elegibilidade, de amostragem e de escores da auditoria,
`modalidade` identifica FER, SER ou MULTI (ou NA quando não informada).
Na base de cenários,
`modalidade` mantém seu domínio próprio (FER, SER, HER, MULTIMODAL), enquanto
`tarefa` identifica multiclasse, multilabel, regressao ou deteccao.

A base mestre, as bases de auditoria e os scripts utilizam exclusivamente a coluna `modalidade`.
Não há conversão ou leitura alternativa do nome antigo no fluxo do corpus.
