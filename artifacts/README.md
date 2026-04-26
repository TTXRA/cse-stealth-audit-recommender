## Visão geral

Este arquivo documenta a base `cenarios`, construída para a **Etapa (vii): Extração Estruturada de Cenários e Construção do Dicionário de Dados**.

A unidade de análise da base é o **experimento**, isto é, cada linha representa uma combinação rastreável de:

- artigo
- conjunto de dados
- configuração de modelo
- condição experimental relevante

A base foi organizada para apoiar as etapas seguintes do estudo, especialmente:

- cálculo do índice de robustez por experimento
- recomendação de famílias de modelos
- avaliação fora da amostra por estudo (`artigo_id`)

## Arquivos

- `cenarios.csv`
- `cenarios.json`

Ambos contêm os mesmos registros, em formatos diferentes.

## Resumo da versão

- Linhas: **53**
- Artigos únicos (`artigo_id`): **22**
- Modalidades presentes: **FER, HER, MULTIMODAL, SER**
- Tarefas presentes: **detecao, multiclasse, regressao**
- Famílias de modelos presentes: **ANN, Boosting_ML, CNN, Ensemble_ML, Multimodal, RF, RNN, SVM, Transformer**

## Regras gerais de construção

1. Cada linha representa um experimento distinto.
2. A extração foi feita exclusivamente a partir do conteúdo publicado nos artigos.
3. Quando necessário, decisões de codificação foram registradas em `observacoes`.
4. Valores percentuais foram normalizados para o intervalo `[0,1]`.
5. Campos com listas no CSV foram serializados como **JSON válido em texto**.
6. O campo `artigo_id` foi incorporado a partir do arquivo de mapeamento mestre.
7. Em casos ambíguos, adotou-se postura conservadora, priorizando precisão sobre completude.

## Convenções de ausência

Nesta base, ausências devem ser interpretadas como **NA**, respeitando o domínio de cada campo.

- no **CSV**, ausências podem aparecer como `NA` ou, excepcionalmente, como célula vazia;
- no **JSON**, ausências podem aparecer como `null`.

Na interpretação analítica, esses casos devem ser tratados como **informação ausente**.

### Regra para campos binários com padrão negativo

Nos campos binários com padrão negativo definido no esquema, a ausência de menção explícita no artigo é codificada como `nao`, e não como `NA`.

Isso se aplica especialmente a:

- `pretreino`
- `protocolo_person_indep`
- `protocolo_cross_dataset`

Assim, `NA` deve ser reservado aos campos cujo esquema admite ausência sem imputação binária.

## Dicionário de dados

| Campo | Tipo esperado | Descrição | Domínio / Regra |
|---|---|---|---|
| `artigo_id` | string | Identificador único do artigo no mapeamento mestre | obrigatório |
| `artigo_titulo` | string | Título do artigo fonte | obrigatório |
| `dataset_id` | string ou NA | Conjunto de dados utilizado | livre; usar NA quando ausente |
| `modalidade` | string | Modalidade principal do estudo | `FER`, `SER`, `MULTIMODAL`, `HER` |
| `tarefa` | string | Tipo de tarefa | `multiclasse`, `multilabel`, `regressao`, `detecao` |
| `ambiente_coleta` | string ou NA | Ambiente de coleta do conjunto de dados | `controlado`, `misto`, `selvagem`, `NA` |
| `dependencia_temporal` | string ou NA | Dependência temporal entre amostras | `sim`, `nao`, `NA` |
| `n_amostras_total` | inteiro ou NA | Total de amostras usadas no treino | inteiro positivo ou NA |
| `pretreino` | string | Indica uso de pré-treinamento / transferência | `sim`, `nao` |
| `modalidades_presentes` | lista JSON ou NA | Modalidades presentes no experimento | subconjunto de `["video","audio","texto","fisiologia","conhecimento"]` |
| `modelo_familia` | string | Família do modelo | `CNN`, `Transformer`, `RNN`, `ANN`, `SVM`, `RF`, `Boosting_ML`, `Ensemble_ML`, `HMM`, `CRF`, `Autoencoder`, `Multimodal` |
| `modelo_especifico` | string ou NA | Nome específico do modelo | livre; usar NA quando ausente |
| `protocolo_person_indep` | string | Indica divisão independente por sujeito/pessoa | `sim`, `nao` |
| `protocolo_cross_dataset` | string | Indica teste entre conjuntos de dados | `sim`, `nao` |
| `metricas_principais` | lista JSON ou NA | Métrica(s) principal(is) reportada(s) | lista JSON válida |
| `metrica_principal_valor` | float ou NA | Valor da métrica principal | número em `[0,1]` ou NA |
| `augmentations` | lista JSON ou NA | Técnicas de aumento de dados | lista JSON válida ou NA |
| `code_available` | string ou NA | Indica disponibilidade de código | `sim`, `nao`, `NA` |
| `weights_available` | string ou NA | Indica disponibilidade de pesos | `sim`, `nao`, `NA` |
| `observacoes` | string ou NA | Registro de decisões, ressalvas e contexto de extração | livre |

## Regras de normalização adotadas

### Métricas

Os nomes das métricas foram padronizados, quando aplicável, para formas consistentes, como por exemplo:

- `ACC`
- `AB`
- `AUC`
- `CCC`
- `PCC`
- `F1_MACRO`

### Hierarquia de seleção da métrica principal

A seleção da métrica principal seguiu prioridade condicional ao tipo de tarefa:

- para **classificação** e **detecção**, priorizou-se `F1_MACRO`, depois `AB` e, por fim, `ACC`;
- para **regressão**, priorizou-se `CCC` e depois `PCC`;
- métricas como `AUC` e, quando pertinente, `EER` foram admitidas quando o artigo as declarava explicitamente como principais ou co-principais.

Quando o artigo apresentava múltiplas métricas, buscou-se preservar apenas a métrica principal ou as co-principais efetivamente assumidas pelo próprio estudo.

### Valores numéricos

- métricas originalmente em porcentagem foram convertidas para fração em `[0,1]`;
- valores não explicitamente reportados foram mantidos como NA;
- `metrica_principal_valor` não deve conter texto livre.

### Listas em CSV

Os campos abaixo foram gravados como texto JSON no CSV:

- `modalidades_presentes`
- `metricas_principais`
- `augmentations`

Exemplo:

```json
["video", "audio"]