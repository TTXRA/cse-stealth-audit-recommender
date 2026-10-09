[English](README.md) | Português

# cse-stealth-audit-recommender

Repositório da pesquisa de mestrado sobre auditoria de qualidade de relato em avaliação furtiva de competências socioemocionais (CSE) e recomendação de famílias de modelos baseada em literatura como dados.

O projeto reúne instrumentos de auditoria, bases tabulares, scripts de processamento, resultados intermediários e saídas analíticas para apoiar a reprodução das etapas propostas na pesquisa.

## Relação com o artigo científico

Este repositório disponibiliza o material computacional e os instrumentos da
pesquisa de mestrado e será associado ao artigo:

*Auditing Reporting Quality in Affective Computing for Stealth Assessment:
Development and Evaluation of a 16-Item Checklist*.

Os metadados bibliográficos de publicação não foram fornecidos. Não há DOI de
arquivamento atribuído nesta preparação. A versão `1.0.0` em [CITATION.cff](CITATION.cff)
identifica a versão pretendida para arquivamento; nenhuma tag ou release foi criada.

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

Use Python 3.10 ou superior; a interface foi verificada localmente com Python 3.11.9.
As dependências e seus intervalos de versão estão em [requirements.txt](requirements.txt).
A partir da raiz do repositório, instale-as em um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente antes da instalação: `.venv\Scripts\Activate.ps1` no PowerShell
ou `source .venv/bin/activate` em Linux/macOS. Se a ativação não for permitida,
use diretamente o executável Python do ambiente virtual.

Instale então as dependências:

```bash
python -m pip install -r requirements.txt
```

As bibliotecas principais incluem:

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

A interface publicada está em [Evidência CSE](https://evidencia-cse.streamlit.app).
A seção **Como usar** explica os campos e a interpretação dos resultados.
Os detalhes de uso, persistência e rastreabilidade estão em [webapp/README.md](webapp/README.md).

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

A execução esperada segue a ordem dos scripts em [scripts/](scripts/).
Execute em uma cópia de trabalho: os comandos abaixo regeneram saídas e podem
sobrescrever artefatos existentes. A codificação dos artigos e a extração dos
cenários são entradas humanas já disponibilizadas, não etapas automatizadas.

Antes dos comandos, inclua a raiz do projeto no caminho de importação do Python:

```powershell
# PowerShell, a partir da raiz do repositório
$env:PYTHONPATH = (Get-Location).Path
```

```bash
# Linux/macOS, a partir da raiz do repositório
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
```

Em seguida:

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

Nas bases de artigos, amostras, piloto, auditoria e reteste, `modalidade`
identifica FER, SER ou MULTI. As tabelas de análise usam a mesma coluna,
sem duplicar a classificação do artigo.

Nos cenários, `modalidade` identifica a categoria operacional (FER, SER,
MULTIMODAL ou HER), enquanto `canais_dados_presentes` registra os canais de
entrada do experimento, como vídeo, áudio, texto e fisiologia. Esse identificador
é utilizado nos CSV, JSON, scripts e na interface.

`tarefa` identifica o problema de aprendizagem: multiclasse, multilabel,
regressão ou detecção. Estrato é o grupo amostral formado pela estratificação
por modalidade; os arquivos usam a coluna `modalidade` para registrar a categoria
dos artigos de cada grupo, sem um segundo campo para a mesma classificação.

- `artifacts/itens_checklist.csv`: itens do checklist de relato.
- `artifacts/auditoria_modelo.csv`: modelo de planilha para auditoria.
- `artifacts/piloto_checklist_codificacao.csv`: exemplo ou base de piloto de codificação.
- `artifacts/cenarios.csv`: cenários experimentais extraídos.
- `data/audit/auditoria.csv`: auditoria principal.
- `data/audit/reteste.csv`: base de recodificação para teste--reteste.
- `data/output/robustez/robustez_cenarios.csv`: índice de robustez por cenário.
- `data/output/robustez/ranking_recomendacao.csv`: ranking de famílias recomendado.
- `data/output/avaliacao_loso/avaliacao_loso.csv`: avaliação deixando um estudo de fora.


## Origem dos dados e instrumentos

A base [data/raw/mapeamento_master.csv](data/raw/mapeamento_master.csv) registra
os metadados dos 43 estudos do mapeamento. Os rótulos de elegibilidade estão em
[data/raw/rotulos_elegibilidade.csv](data/raw/rotulos_elegibilidade.csv).
A auditoria contém 22 artigos, e a base de cenários reúne 53 experimentos
extraídos da literatura auditada. O repositório contém registros derivados da
literatura; não reúne os conjuntos de dados originais citados pelos estudos.

O [checklist de 16 itens](artifacts/itens_checklist.csv) registra identificadores,
nomes, indicação de itens nucleares, permissão de NA e regras resumidas de NA.
A [planilha de auditoria](artifacts/auditoria_modelo.csv) apoia a codificação;
[artifacts/README.md](artifacts/README.md) descreve os instrumentos. O
[protocolo de extração](artifacts/protocolo_extracao_cenarios.md) e o
[dicionário de cenários](artifacts/cenarios_README.md) orientam os registros experimentais.
O manual completo das âncoras de pontuação do checklist não está incluído nesta cópia.

Para detalhes dos arquivos, consulte [data/README.md](data/README.md) e
[scripts/README.md](scripts/README.md).

## Limitações e preservação da versão

- A base cobre a literatura selecionada e as evidências de relato disponíveis;
  não constitui garantia de desempenho em novas aplicações.
- O recomendador utiliza regras determinísticas e critérios de suporte; pode
  abster-se quando não houver evidência suficiente para comparar famílias.
- As dependências usam intervalos de versão, não um ambiente totalmente congelado.
- `ANO_FIM` é derivado do ano corrente em `scripts/utils/config.py`; variáveis
  de ambiente também podem afetar a amostragem. Uma nova execução deve registrar
  ambiente, data e configuração, em vez de assumir resultados idênticos apenas pela semente.
- Os hashes existentes correspondem aos bytes da cópia local com terminações
  de linha CRLF. O Git normaliza arquivos textuais para LF; por isso, alguns
  hashes não conferem diretamente no arquivo baixado do GitHub. Essa pendência
  está registrada em [ARCHIVAL_READINESS.md](ARCHIVAL_READINESS.md).
- O registro de sorteio usa caminhos relativos ao repositório. Os caminhos
  absolutos originais permanecem em commits anteriores; a alteração apenas dos
  caminhos preserva parâmetros, artigos sorteados e resultados.

## Autores, instituição e contato

- [Thiago Teixeira](https://orcid.org/0009-0005-0385-2895).
- [Simone Nasser de Matos](https://orcid.org/0000-0002-5362-2343).
- [Helyane Bronoski Borges](https://orcid.org/0000-0002-9153-3819).

Federal University of Technology -- Paraná (UTFPR), Ponta Grossa, Paraná, Brazil.

Autor correspondente: Thiago Teixeira —
[thiago.070790@alunos.utfpr.edu.br](mailto:thiago.070790@alunos.utfpr.edu.br).

## Como citar

Consulte [CITATION.cff](CITATION.cff) para os autores, ORCIDs, a versão pretendida
`1.0.0` e a referência preferida ao artigo associado. Ao reutilizar o repositório,
registre também o commit ou a versão efetivamente utilizada. Data de release,
DOI e detalhes de periódico não foram inventados; serão completados quando disponíveis.

## Licenças

- Código-fonte: [MIT](LICENSE-CODE).
- Documentos, dados tabulares e demais artefatos: [CC BY 4.0](LICENSE).

As licenças existentes foram preservadas. A disponibilização de registros
extraídos da literatura não concede direitos sobre artigos ou datasets de terceiros.

## Estado de preparação para arquivamento

Veja [ARCHIVAL_READINESS.md](ARCHIVAL_READINESS.md) para verificações e pendências.
O `CITATION.cff` fornece os metadados para a futura integração GitHub–Zenodo;
nenhum `.zenodo.json` adicional foi necessário. Nenhuma tag, release ou depósito
no Zenodo foi criado nesta etapa.
