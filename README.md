English | [Português](README.pt-BR.md)

# cse-stealth-audit-recommender

Research repository for auditing reporting quality in stealth assessment of social-emotional competencies and recommending model families using literature as data. It contains auditing instruments, tabular data, processing scripts, intermediate results, and analytical outputs supporting the stages of the master's research.

## Relationship to the scientific article

This repository provides the computational materials and instruments associated with the master's research and the following scientific article:

*Auditing Reporting Quality in Affective Computing for Stealth Assessment: Development and Evaluation of a 16-Item Checklist*.

Publication details have not been supplied. No archival DOI has been assigned during this preparation. Version `1.0.0` in [CITATION.cff](CITATION.cff) identifies the intended archival version; no tag or release has been created.

## Repository structure

```text
artifacts/
data/
scripts/
webapp/
README.md
README.pt-BR.md
CITATION.cff
LICENSE
LICENSE-CODE
requirements.txt
```

- [artifacts/](artifacts/): instruments, spreadsheet templates, checklist, extracted scenarios, and the extraction protocol.
- [data/](data/): raw and intermediate data, audit records, sampling, robustness, recommendations, and leave-one-study-out evaluation.
- [scripts/](scripts/): Python code organized by research stage.
- [webapp/](webapp/): Streamlit interface for consultation, data entry, and recommendations.

See the directory guides for [artifacts](artifacts/README.md), [data](data/README.md), [scripts](scripts/README.md), and [the web interface](webapp/README.md). These detailed guides remain in Portuguese; this README provides the main instructions in English.

## Implemented research stages

1. Corpus standardization and eligibility filtering.
2. Stratified sampling with a reproducible random draw.
3. Reporting-quality auditing using a 0/1/2 checklist and an NA rule.
4. Test–retest assessment and consistency metrics.
5. Adherence scores and sensitivity analysis.
6. Structured extraction of experimental scenarios.
7. Computation of the robustness index `R`.
8. Model-family recommendation.
9. Out-of-sample evaluation through leave-one-study-out validation.

## Requirements and installation

Use Python 3.10 or newer; the interface was checked locally with Python 3.11.9. Dependencies and version ranges are declared in [requirements.txt](requirements.txt). The external imports are covered by pandas, NumPy, SciPy, scikit-learn, Matplotlib, Altair, Streamlit, and psycopg.

From the repository root, create a virtual environment:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on Linux/macOS, then install the dependencies:

```bash
python -m pip install -r requirements.txt
```

If activation is unavailable, use the virtual environment's Python executable directly. Dependencies are declared as version ranges, not a fully locked environment.

## Web interface

The published interface is [Evidência CSE](https://evidencia-cse.streamlit.app). Its **Como usar** (How to use) section explains the workflow, fields, ranking, support requirements, and abstention. The interface itself is in Portuguese.

The local interface lets users consult or register articles, consult or perform audits in a dedicated section, explore or add experimental scenarios, generate recommendations, and execute the complete scientific workflow. It directly reuses the data and routines in `scripts/`.

After installing dependencies, start it from the repository root:

```bash
python webapp/run.py
```

Usage, persistence, and traceability details are in [webapp/README.md](webapp/README.md).

### Deployment from GitHub

For Streamlit Community Cloud, select this repository, the desired branch, and `webapp/app.py` as the entrypoint. Dependencies are installed from `requirements.txt`; the theme is configured in `.streamlit/config.toml`.

For articles, audits, scenarios, and sampling records to survive service restarts, configure a PostgreSQL connection in the application's **Secrets** panel:

```toml
CSE_DATABASE_URL = "postgresql://usuario:senha@host:5432/banco?sslmode=require"
```

This is a placeholder, not a credential. The format is also provided in [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example). Without this setting, the interface uses local CSV files, which is suitable for development but does not provide durable storage on ephemeral hosting services.

## Running the research workflow

Run the following commands in a working copy: they regenerate outputs and can overwrite existing artifacts. Article coding and scenario extraction are human-produced inputs already supplied in the repository, not automated stages.

Before running the scripts, add the repository root to Python's import path:

```powershell
# PowerShell, from the repository root
$env:PYTHONPATH = (Get-Location).Path
```

```bash
# Linux/macOS, from the repository root
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
```

Then run the stages in order:

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

## Reproducibility and terminology

[scripts/utils/config.py](scripts/utils/config.py) centralizes paths, seeds, sampling parameters, and analysis constants. The default random seed is `2025`. Some outputs include `.sha256` files for integrity checking; see the line-ending limitation below before verifying downloaded artifacts.

In article, sample, pilot, audit, and retest tables, `modalidade` identifies FER, SER, or MULTI. Analysis tables use the same column without duplicating the classification.

In scenarios, `modalidade` identifies the operational category (FER, SER, MULTIMODAL, or HER), while `canais_dados_presentes` records input channels such as video, audio, text, and physiological signals. This identifier is used in CSV and JSON files, scripts, and the interface.

`tarefa` identifies the learning problem: `multiclasse`, `multilabel`, `regressao`, or `deteccao`. A stratum is a sampling group formed by stratification by modality; files use `modalidade` to record the article category rather than a second field for the same classification. Machine-readable field names and categorical values remain in their original language.

## Data provenance and main artifacts

[data/raw/mapeamento_master.csv](data/raw/mapeamento_master.csv) records the metadata of the 43 mapped studies. Eligibility labels are in [data/raw/rotulos_elegibilidade.csv](data/raw/rotulos_elegibilidade.csv). The audit covers 22 articles, and the scenario base contains 53 experiments extracted from the audited literature. The repository supplies literature-derived records, not the original datasets used by the studies.

- [artifacts/itens_checklist.csv](artifacts/itens_checklist.csv): the 16 checklist items, identifiers, names, core-item flags, NA permission, and summarized NA rules.
- [artifacts/auditoria_modelo.csv](artifacts/auditoria_modelo.csv): audit spreadsheet template.
- [artifacts/piloto_checklist_codificacao.csv](artifacts/piloto_checklist_codificacao.csv): pilot coding records.
- [artifacts/protocolo_extracao_cenarios.md](artifacts/protocolo_extracao_cenarios.md): scenario extraction and normalization protocol.
- [artifacts/cenarios_README.md](artifacts/cenarios_README.md): scenario data dictionary.
- [artifacts/cenarios.csv](artifacts/cenarios.csv) and [artifacts/cenarios.json](artifacts/cenarios.json): extracted scenarios.
- [data/audit/auditoria.csv](data/audit/auditoria.csv): main audit.
- [data/audit/reteste.csv](data/audit/reteste.csv): test–retest recoding records.
- [data/output/robustez/robustez_cenarios.csv](data/output/robustez/robustez_cenarios.csv): scenario-level robustness index.
- [data/output/robustez/ranking_recomendacao.csv](data/output/robustez/ranking_recomendacao.csv): model-family ranking.
- [data/output/avaliacao_loso/avaliacao_loso.csv](data/output/avaliacao_loso/avaliacao_loso.csv): leave-one-study-out evaluation.

The complete checklist scoring-anchor manual is not included in this snapshot. The extraction protocol documents scenarios, not the complete audit scoring manual.

## Limitations and preservation of the version

- Evidence is limited to the selected literature and its available reporting; it does not guarantee performance in new applications.
- The recommender uses deterministic rules and support requirements and may abstain when evidence is insufficient to compare model families.
- Dependency ranges do not fully freeze the execution environment.
- `ANO_FIM` is derived from the current year in `scripts/utils/config.py`; environment variables can also affect sampling. New executions should record their environment, date, and configuration rather than assume identical results solely from the random seed.
- Existing hashes refer to local bytes with CRLF line endings. Git normalizes text files to LF, so some hashes do not directly match GitHub downloads. This unresolved archival issue is documented in [ARCHIVAL_READINESS.md](ARCHIVAL_READINESS.md).
- The sampling log uses repository-relative paths. Original absolute paths remain in earlier Git commits; the path-only update preserves sampling parameters, selected articles, and results.

## Authors, institution, and contact

- [Thiago Teixeira](https://orcid.org/0009-0005-0385-2895).
- [Simone Nasser de Matos](https://orcid.org/0000-0002-5362-2343).
- [Helyane Bronoski Borges](https://orcid.org/0000-0002-9153-3819).

Federal University of Technology -- Paraná (UTFPR), Ponta Grossa, Paraná, Brazil.

Corresponding author: Thiago Teixeira — [thiago.070790@alunos.utfpr.edu.br](mailto:thiago.070790@alunos.utfpr.edu.br).

## Citation

See [CITATION.cff](CITATION.cff) for authors, ORCIDs, the intended version `1.0.0`, and the preferred citation to the associated article. When reusing the repository, also record the actual commit or version used. Release date, DOI, and journal details have not been invented; they can be completed when available.

## Licenses

- Source code: [MIT](LICENSE-CODE).
- Documents, tabular data, and other non-code artifacts: [CC BY 4.0](LICENSE).

The existing licenses have been preserved. Providing literature-derived records does not grant rights to third-party articles or datasets.
