# cse-stealth-audit-recommender

Repositório da pesquisa de mestrado sobre auditoria de qualidade de relato em avaliação furtiva de competências socioemocionais (CSE) e recomendação de famílias de modelos baseada em literatura como dados.

O projeto reúne instrumentos de auditoria, bases tabulares, scripts de processamento, resultados intermediários e saídas analíticas para apoiar a reprodução das etapas propostas na pesquisa.

## Estrutura do repositório

```text
artifacts/
data/
scripts/
webapp/
README.md
```

- `artifacts/`: instrumentos, modelos de planilha, checklist, cenários extraídos e protocolo de extração.
- `data/`: dados brutos, intermediários, auditoria, amostragem, robustez, recomendação e avaliação fora da amostra.
- `scripts/`: códigos Python organizados por etapa da pesquisa.
- `webapp/`: interface Streamlit para consulta, atualização das bases e recomendação.

## Principais etapas implementadas

1. Padronização do corpus e filtragem de elegibilidade.
2. Amostragem estratificada com sorteio reprodutível.
3. Auditoria de relato com checklist 0/1/2 e regra de NA.
4. Teste--reteste e métricas de consistência.
5. Cálculo de escores de aderência e análise de sensibilidade.
6. Extração estruturada de cenários experimentais.
7. Cálculo do índice de robustez `R`.
8. Recomendação de famílias de modelos.
9. Avaliação fora da amostra por validação deixando um estudo de fora.

## Requisitos

O projeto utiliza Python 3.x e as seguintes bibliotecas principais:

```text
pandas
numpy
scipy
scikit-learn
matplotlib
streamlit
```

## Interface web

A interface local em `webapp/` permite consultar e cadastrar artigos, consultar
ou realizar auditorias em uma seção própria, explorar e adicionar cenários
experimentais, gerar novas recomendações e executar o fluxo científico completo.
Ela reutiliza diretamente os dados e as rotinas de `scripts/`.

Após instalar as dependências, inicie-a pela raiz do repositório:

```bash
python webapp/run.py
```

Os detalhes de uso, persistência e rastreabilidade estão em `webapp/README.md`.

### Publicação pelo GitHub

O repositório está preparado para o Streamlit Community Cloud. Na criação do app,
selecione este repositório, a branch desejada e o arquivo principal
`webapp/app.py`. As dependências são instaladas a partir de `requirements.txt` e
o tema está em `.streamlit/config.toml`.

Para que artigos, auditorias, cenários e sorteios não sejam perdidos após uma
reinicialização do serviço, configure no painel **Secrets** uma conexão PostgreSQL:

```toml
CSE_DATABASE_URL = "postgresql://usuario:senha@host:5432/banco?sslmode=require"
```

O exemplo está em `.streamlit/secrets.toml.example`. Sem essa variável, a
interface continua funcionando com os CSVs locais, comportamento adequado para
desenvolvimento, mas não oferece persistência durável em hospedagens efêmeras.

## Execução geral

A execução esperada segue a ordem dos scripts em `scripts/`:

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

## Reprodutibilidade

Os caminhos, sementes, parâmetros de amostragem e constantes de análise estão centralizados em `scripts/utils/config.py`. Os artefatos de saída relevantes incluem arquivos `.sha256` para verificação de integridade quando aplicável.

A semente padrão adotada nos scripts é `2025`.

## Artefatos principais

- `artifacts/itens_checklist.csv`: itens do checklist de relato.
- `artifacts/auditoria_modelo.csv`: modelo de planilha para auditoria.
- `artifacts/piloto_checklist_codificacao.csv`: exemplo ou base de piloto de codificação.
- `artifacts/cenarios.csv`: cenários experimentais extraídos.
- `data/audit/auditoria.csv`: auditoria principal.
- `data/audit/reteste.csv`: base de recodificação para teste--reteste.
- `data/output/robustez/robustez_cenarios.csv`: índice de robustez por cenário.
- `data/output/robustez/ranking_recomendacao.csv`: ranking de famílias recomendado.
- `data/output/avaliacao_loso/avaliacao_loso.csv`: avaliação deixando um estudo de fora.
