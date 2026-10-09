# Changelog

## [Unreleased] — preparation for v1.0.0

### Sampling-log path correction
- With the author's explicit approval, replaced the three absolute local paths in `arquivo_amostra_csv` with repository-relative paths and updated the log's SHA-256.
- Preserved every other log field, sampling parameter, selected article, and scientific result; no script or pipeline was changed or executed.
- Original paths remain in earlier Git commits.

### Documentation and metadata
- Added the English README and preserved the Portuguese documentation in README.pt-BR.md.
- Updated citation metadata with the three authors, ORCIDs, institution, corresponding contact, and associated article title.
- Documented installation, Python import-path setup, existing licenses, and archival limitations.
- Recorded line-ending/hash discrepancies, local paths in the sampling log, and the missing complete scoring-anchor manual as pre-release items.
- Added ignore rules for IDE settings and macOS metadata; already tracked IDE settings remain unchanged pending cleanup approval.
- No research scripts, data, results, dependencies, or scientific artifacts were changed in this preparation.
- No release, tag, release date, or archival DOI has been assigned for v1.0.0.

## [Não lançado] - 2026-10-07

### Alterado
- Padronização da categoria dos artigos como `modalidade` nas bases de auditoria,
  piloto, reteste, amostragem e análises, com uma única coluna por classificação.
- Atualização de scripts, interface, documentação, parâmetros de amostragem,
  tabelas, figuras e arquivos de integridade correspondentes.

## [Não lançado] - 2026-10-06

### Alterado
- Padronização do campo `canais_dados_presentes` nos dados de cenários, scripts,
  interface e documentação, distinguindo os canais de entrada da modalidade
  operacional do cenário.
- Atualização dos artefatos derivados e dos respectivos arquivos de integridade.

## Planned v1.0.0 (not released)

Escopo planejado para a versão associada à dissertação e ao artigo; sem data de lançamento definida.

### Incluído
- Checklist de relato.
- Manual/protocolo de extração de cenários.
- Planilhas de auditoria e cenários.
- Scripts de cálculo de escores, robustez e recomendação.
- Resultados da avaliação deixando um estudo de fora.
- Arquivos de licença, citação e dependências.
