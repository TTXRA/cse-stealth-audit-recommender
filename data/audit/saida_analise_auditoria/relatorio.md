# Relatorio da etapa (vi)

## Escore global no esquema uniforme
- Media: 36.82
- Mediana: 35.62
- IC95% da media: [29.49, 44.72]
- IC95% da mediana: [20.00, 51.56]

## Mudancas de ranking entre configuracoes
- Artigos | uniforme_vs_nucleares: media abs ranking=0.36; max abs ranking=2.00; media abs score=1.63; max abs score=6.62
- Artigos | uniforme_vs_robustez: media abs ranking=0.91; max abs ranking=2.00; media abs score=3.27; max abs score=8.93
- Estratos | uniforme_vs_nucleares: media abs ranking=0.00; max abs ranking=0.00; media abs mediana=0.93; max abs mediana=1.71
- Estratos | uniforme_vs_robustez: media abs ranking=0.00; max abs ranking=0.00; media abs mediana=4.25; max abs mediana=5.00

## Correlacoes de Spearman
- Interpretar as correlacoes dos estratos com cautela, pois ha apenas tres estratos.
- artigos | uniforme vs nucleares: rho=0.9946; p=3.619e-21
- artigos | uniforme vs robustez: rho=0.9864; p=3.725e-17
- artigos | nucleares vs robustez: rho=0.9878; p=1.224e-17
- estratos | uniforme vs nucleares: rho=1.0000; p=<1e-300
- estratos | uniforme vs robustez: rho=1.0000; p=<1e-300
- estratos | nucleares vs robustez: rho=1.0000; p=<1e-300

## Itens mais criticos no esquema uniforme
- CAL (Calibracao): media=2.27; IC95%=[0.00, 6.82]
- REP (Reprodutibilidade e Artefatos): media=6.82; IC95%=[0.00, 13.64]
- EXT (Testes entre Bases): media=18.18; IC95%=[4.55, 34.09]
- SUB (Subgrupos e Equidade): media=20.45; IC95%=[11.36, 29.55]
- ETH (Etica, Privacidade e Uso Responsavel): media=22.73; IC95%=[9.09, 38.64]

## Estabilidade dos itens criticos
- nucleares_vs_robustez: rho dos ranks=1.0000; p=<1e-300; sobreposicao dos 5 piores itens=5
- uniforme_vs_nucleares: rho dos ranks=1.0000; p=<1e-300; sobreposicao dos 5 piores itens=5
- uniforme_vs_robustez: rho dos ranks=1.0000; p=<1e-300; sobreposicao dos 5 piores itens=5

## Itens com maiores medianas no esquema uniforme
- MULTI | PRE (Pre-processamento e Caracteristicas): mediana=100.00
- SER | ESC (Escopo e Construto): mediana=100.00
- SER | PRE (Pre-processamento e Caracteristicas): mediana=100.00
- SER | ROB (Robustez e Sensibilidade): mediana=100.00
- SER | VZ (Prevencao de Vazamento): mediana=100.00

## Itens com menores medianas no esquema uniforme
- FER | CAL (Calibracao): mediana=0.00
- FER | ETH (Etica, Privacidade e Uso Responsavel): mediana=0.00
- FER | EXT (Testes entre Bases): mediana=0.00
- FER | MET (Metricas e Incerteza): mediana=0.00
- FER | PRT (Particionamento e Validacao): mediana=0.00

## Cobertura dos itens no esquema uniforme
- FER | SIN (Sincronizacao Multimodal): NA=100.0% em n=9
- SER | SIN (Sincronizacao Multimodal): NA=50.0% em n=4
- FER | CST (Custo e Latencia): NA=11.1% em n=9
- FER | ROB (Robustez e Sensibilidade): NA=11.1% em n=9
- FER | VZ (Prevencao de Vazamento): NA=11.1% em n=9

## Relacao entre faltantes e score global
- Spearman entre n_na e score_global: rho=-0.3893
- n_na=0: n=11; mediana do score=53.12
- n_na=1: n=10; mediana do score=20.00
- n_na=4: n=1; mediana do score=12.50

## Artigos mais sensiveis a mudanca de pesos
- ID_42 (SER): Δ uniforme→nucleares=+5.50; Δ uniforme→robustez=+8.93
- ID_14 (MULTI): Δ uniforme→nucleares=+0.88; Δ uniforme→robustez=+6.40
- ID_31 (MULTI): Δ uniforme→nucleares=-0.25; Δ uniforme→robustez=-6.25
- ID_25 (FER): Δ uniforme→nucleares=+0.83; Δ uniforme→robustez=-5.00
- ID_18 (FER): Δ uniforme→nucleares=+0.83; Δ uniforme→robustez=-5.00

## Combinacoes sem resumo de item
- As combinacoes abaixo ficaram fora de resumo_itens.csv porque todos os registros eram NA:
- nucleares | FER | SIN
- robustez | FER | SIN
- uniforme | FER | SIN
