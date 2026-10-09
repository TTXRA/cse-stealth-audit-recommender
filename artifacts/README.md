# Diretório `artifacts`

Este diretório reúne instrumentos, modelos de planilha, bases estruturadas e documentos de apoio usados nas etapas de auditoria, extração de cenários e recomendação.

## Arquivos

```text
artifacts/
  auditoria_modelo.csv
  cenarios.csv
  cenarios.json
  itens_checklist.csv
  piloto_checklist_codificacao.csv
  protocolo_extracao_cenarios.md
  README.md
```

## `itens_checklist.csv`

Contém os itens do checklist de relato usados para auditar os artigos.

Cada item representa um eixo ou componente de relato, com identificação, definição, regra de pontuação e indicação de aplicabilidade quando pertinente.

Este arquivo serve como base para:

- aplicação da auditoria principal;
- cálculo do escore de aderência;
- identificação de itens nucleares;
- cálculo da subescala de robustez usada no índice `R`.

## `auditoria_modelo.csv`

Modelo de planilha para codificação da auditoria.

A unidade esperada é a combinação artigo por item, com campos como:

- `artigo_id`;
- `modalidade`;
- `item_id`;
- `grau`;
- `NA`;
- `justificativa_NA`;
- `evidencia`;
- `observacoes`.

O campo `modalidade` registra a categoria do artigo (FER, SER ou MULTI)
utilizada na estratificação amostral.

A escala de pontuação é ordinal, com valores `0`, `1` e `2`. Itens marcados como `NA` devem ter justificativa técnica.

## `piloto_checklist_codificacao.csv`

Arquivo associado à etapa piloto de aplicação do checklist.

Seu objetivo é apoiar a revisão inicial do instrumento, permitindo registrar dificuldades de interpretação, casos-limite e ajustes necessários nas âncoras de pontuação.

## `cenarios.csv`

Base principal de cenários experimentais extraídos da literatura auditada.

A unidade de análise é o experimento, isto é, uma combinação de:

- artigo;
- conjunto de dados;
- configuração de modelo;
- protocolo experimental;
- métrica principal.

Essa base é usada como entrada para o cálculo do índice de robustez `R` e para o recomendador de famílias de modelos.

## `cenarios.json`

Versão em JSON da base `cenarios.csv`.

Contém os mesmos registros em formato estruturado, útil para inspeção, validação ou integração com outras ferramentas.

## `protocolo_extracao_cenarios.md`

Documento metodológico com regras para extração, normalização e codificação dos cenários experimentais.

Deve ser usado para orientar decisões como:

- o que conta como experimento distinto;
- como registrar múltiplos conjuntos de dados;
- como mapear modelos específicos para famílias;
- como normalizar métricas;
- como tratar campos ausentes;
- quando usar `NA`;
- como registrar observações e ambiguidades.

## Convenções principais

- Valores percentuais devem ser normalizados para o intervalo `[0,1]`.
- Campos de lista em CSV devem ser registrados como JSON válido em texto.
- Ausências informacionais devem ser registradas como `NA` quando o domínio do campo permitir.
- Campos binários com padrão negativo devem usar `nao` quando a ausência de menção explícita for interpretada como ausência do atributo.
- Decisões ambíguas devem ser registradas em campo de observação.

## Relação com os scripts

Arquivos deste diretório são consumidos principalmente por scripts das etapas:

- `etapa_06_auditoria`: cálculo de escores e análise da auditoria;
- `etapa_08_robustez`: cálculo do índice `R`;
- `etapa_09_recomendador`: validação da base e ranking de famílias;
- `etapa_10_avaliacao_loso`: avaliação fora da amostra.

## Observações de versionamento

Alterações nos arquivos deste diretório devem ser registradas no controle de versão, pois podem alterar diretamente os resultados da auditoria, do índice de robustez e da recomendação.
