# Archival preparation for v1.0.0

This document records documentation-only preparation for a future public release
and Zenodo archive. It is not a release announcement. No tag, GitHub Release,
Zenodo deposit, release date, or archival DOI has been created or assigned.

## Initial repository state

- Working branch: `codex/streamlit-cloud-deployment`.
- Remote: `origin`, `https://github.com/TTXRA/cse-stealth-audit-recommender.git`.
- Default publication branch: `main`.
- Baseline commit: `f6b719e6320afbf25bafae48714ed3513d749a88`.
- A pre-existing local modification to `.idea/misc.xml` was outside this task
  and has been preserved and excluded from the archival preparation commit.

## Documentation and metadata

- [README.md](README.md) provides the main documentation in English.
- [README.pt-BR.md](README.pt-BR.md) preserves the Portuguese documentation and
  includes the same archival, citation, installation, and limitation information.
- [CITATION.cff](CITATION.cff) preserves the existing software title and supplies
  the three authors, ORCIDs, affiliation, corresponding contact, intended version
  `1.0.0`, and the associated article title under `preferred-citation`.
- The preferred article citation uses only the supplied title and authors;
  journal, publication date, DOI, volume, issue, and pages have not been invented.
- The existing [MIT code license](LICENSE-CODE) and
  [CC BY 4.0 non-code license](LICENSE) are preserved and distinguished in both READMEs.
- `CITATION.cff` represents the metadata needed here, so no `.zenodo.json` was added.
  Zenodo supports CFF metadata for GitHub archives; if a `.zenodo.json` is added
  later, it takes precedence over the CFF file.
  See [Zenodo's CFF documentation](https://help.zenodo.org/docs/github/describe-software/citation-file/).
- No CONTRIBUTING, code of conduct, packaging, container, or environment-lock
  files were added simply to complete a checklist.

## Preservation and dependency checks

During the original documentation-only preparation, scientific scripts, interface code, tabular data, JSON records, matrices,
figures, outputs, hashes, generated analytical reports, and `requirements.txt`
were preserved byte for byte against the initial local snapshot. No pipeline,
notebook, analysis, sampling, or result-generating command was executed.

Static inspection found external imports of Altair, Matplotlib, NumPy, pandas,
psycopg, SciPy, scikit-learn, and Streamlit. All are represented in
[requirements.txt](requirements.txt), whose version ranges were not changed.
Python 3.10 or newer is required by the declared Streamlit dependency; the
existing local interface environment uses Python 3.11.9.

## Items to review before creating the release

1. **Integrity hashes and line endings.** Fifteen existing hash/target pairs
   were checked. All match the local files, but fourteen do not match the bytes
   stored by Git. The recorded hashes use CRLF line endings, while Git's text
   normalization stores LF. These are representation differences, not evidence
   of altered numerical results. The affected targets are:
   - `data/audit/saida_consistencia/icc_3_1.csv`
   - `data/audit/saida_consistencia/kappa_itens_nucleares.csv`
   - `data/audit/saida_consistencia/pareamento_item_a_item.csv`
   - `data/audit/saida_consistencia/scores_auditoria.csv`
   - `data/audit/saida_consistencia/scores_pareados.csv`
   - `data/audit/saida_consistencia/scores_reteste.csv`
   - `data/output/avaliacao_loso/avaliacao_loso.csv`
   - `data/output/avaliacao_loso/resumo_avaliacao_loso.csv`
   - `data/output/logs/alocacao_sorteio.csv`
   - `data/output/logs/log_contingencia.csv`
   - `data/output/logs/registro_sorteio.csv`
   - `data/output/prisma/prisma_final.csv`
   - `data/output/robustez/ranking_recomendacao.csv`
   - `data/output/robustez/robustez_cenarios_clean.csv`
   No data, hash files, or Git normalization settings were changed. A policy for
   archival byte representation and corresponding checksums needs separate approval.
2. **Complete scoring-anchor manual.** `artifacts/itens_checklist.csv` contains
   identifiers, names, core-item flags, NA permission, and summarized NA rules.
   The complete audit scoring-anchor manual was not found in this repository.
   Supply an authorized copy or a stable reference before claiming that the
   instrument can be applied independently from this repository alone.
3. **Local paths in the sampling log.**
   Resolved in the current file with the author's subsequent explicit approval:
   the three values in `arquivo_amostra_csv` now use repository-relative paths.
   All other fields, selected articles, parameters, and scientific results are
   unchanged. The log's own SHA-256 was updated; no pipeline was executed and no
   script was modified. Earlier Git commits retain the original absolute paths.
4. **Tracked IDE settings.** Seven files in `.idea/` were already tracked.
   The ignore rule prevents new IDE files from being added, but does not remove
   tracked files. Existing files were deliberately preserved; review whether to
   remove them from a future archive in a separately authorized cleanup.
5. **Release-specific metadata.** Confirm the final version and release date
   when the release is actually created. Complete article publication details
   and the archival DOI only when assigned. Review Zenodo's representation of
   the two component licenses before publishing the archive.
6. **Execution environment.** Dependency ranges are not a locked environment,
   and the configured ending year uses the current calendar year. Record the
   intended environment and configuration before claiming exact re-execution
   of the archived analysis. No parameter or dependency change was made here.

## Sensitive-information check

Inspection of tracked text files found no token, private key, or non-placeholder
database credential matching the checked patterns. The PostgreSQL connection
strings in documentation and the example configuration are placeholders.
The former local-path finding and its resolution remain documented. This static inspection is not
a guarantee that every historical commit is free of sensitive information.

## Scope of the original preparation commit

Only README documentation, citation metadata, this readiness report, the
changelog, and necessary ignore rules belong to the preparation commit.
All protected scientific files and existing licenses remain unchanged.

The subsequent author-approved path-only correction changes the sampling log
and its corresponding hash, and updates documentation to record the resolution.
It does not change the sampling logic or the generated study results.
