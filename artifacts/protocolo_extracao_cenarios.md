# Protocolo de extração estruturada de cenários com apoio do NotebookLM

Este arquivo registra o prompt utilizado no NotebookLM como artefato complementar da etapa de extração estruturada de cenários e consolidação do dicionário de dados. O prompt define a unidade de extração, os campos da planilha, os domínios válidos, as regras de tratamento de ausências, os critérios de abertura de linhas e as verificações finais aplicadas à saída.

## Prompt utilizado

Leia cada artigo e extraia linhas estruturadas, gerando exatamente 1 linha por combinação:

artigo_titulo × dataset_id × modelo_especifico × regime_relevante

Considere “regime_relevante” apenas quando algum dos campos abaixo mudar para o mesmo artigo/dataset/modelo:
pretreino, protocolo_person_independent, protocolo_cross_dataset, tarefa, modalidade, metricas_principais, metrica_principal_valor.

Se o artigo tiver vários datasets, vários modelos ou vários regimes, gere várias linhas.

==================================================
SAÍDA
==================================================

Retorne apenas CSV puro, com uma única linha de cabeçalho e a seguinte ordem fixa de colunas:

artigo_titulo,dataset_id,modalidade,tarefa,ambiente_coleta,dependencia_temporal,n_amostras_total,pretreino,modalidades_presentes,modelo_familia,modelo_especifico,protocolo_person_independent,protocolo_cross_dataset,metricas_principais,metrica_principal_valor,code_available,weights_available,augmentations,observacoes

Não escreva nada antes ou depois do CSV.

==================================================
REGRAS GERAIS
==================================================

1. Não invente informação.
2. Se uma informação não estiver explicitamente presente no artigo, use NA.
3. Nunca deixe célula vazia. Use sempre um valor válido ou NA.
4. Use exatamente os nomes de coluna acima.
5. Na saída, use sempre o nome da coluna protocolo_person_independent.
6. Cada linha deve representar um experimento rastreável no artigo.
7. Se houver ambiguidade insolúvel sobre dataset, modelo, regime ou valor métrico, use NA no campo ambíguo.
8. Não use conhecimento externo ao artigo.
9. Não preencha campos com suposições plausíveis.
10. Se o mesmo artigo trouxer vários resultados para o mesmo dataset e mesmo modelo, selecione apenas o resultado principal/final reportado pelo artigo para aquele experimento.
11. Use observacoes para registrar decisões de consolidação, ambiguidades resolvidas, fallback aplicado ou qualquer caso-limite relevante.
12. Se não houver observação relevante, use NA em observacoes.

==================================================
DEFAULTS OBRIGATÓRIOS
==================================================

Use os defaults abaixo somente quando não houver menção explícita:

- protocolo_person_independent = nao
  Só use sim se houver evidência explícita como:
  subject-independent, person-independent, LOSO, leave-one-subject-out

- protocolo_cross_dataset = nao
  Só use sim se houver evidência explícita de treino em um dataset e teste em outro, por exemplo:
  train on X, test on Y, cross-database, cross-dataset

- pretreino = nao
  Só use sim se houver evidência explícita como:
  pretrained, pre-trained, fine-tune, fine-tuned, transfer learning, ImageNet, AudioSet, self-supervised, SSL, pretrained backbone

- code_available = nao
  Só use sim se houver URL, DOI, GitHub, repositório ou link explícito para código

- weights_available = nao
  Só use sim se houver URL, DOI, GitHub, repositório ou link explícito para pesos/model checkpoint

Não infira disponibilidade de código ou pesos a partir de frases genéricas.

==================================================
TIPOS E FORMATAÇÃO
==================================================

Use exatamente estes domínios:

- modalidade: FER | SER | MULTIMODAL | HER
- tarefa: multiclasse | multilabel | regressao | detecao
- ambiente_coleta: controlado | misto | selvagem | NA
- dependencia_temporal: sim | nao | NA
- n_amostras_total: inteiro positivo ou NA
- modalidades_presentes: lista JSON válida, subset de ["video","audio","texto","fisiologia","conhecimento"] ou NA
- modelo_familia: um dos valores controlados definidos abaixo
- modelo_especifico: nome textual do modelo exatamente ou quase exatamente como no artigo
- protocolo_person_independent: sim | nao
- protocolo_cross_dataset: sim | nao
- metricas_principais: lista JSON válida
- metrica_principal_valor: número em [0,1] ou NA
- code_available: sim | nao
- weights_available: sim | nao
- augmentations: lista JSON válida ou NA
- observacoes: texto curto ou NA

Regras de formatação:

- Use NA sem aspas.
- Use ponto decimal.
- Converta porcentagens para fração em [0,1].
- Se n_amostras_total for numérico, escreva como inteiro sem casas decimais.
- Exemplos válidos para n_amostras_total: 7356, 51440
- Exemplos inválidos para n_amostras_total: 7356.0, 51440.0
- Listas JSON devem ser válidas e, no CSV, com aspas escapadas.
- Não use listas como [video] ou [ACC].
- Se houver apenas uma métrica principal, ainda assim use lista JSON com um item.

==================================================
REGRAS DE EXTRAÇÃO POR CAMPO
==================================================

artigo_titulo
- Use o título do artigo.
- Preserve o título corretamente.

dataset_id
- Use o nome do dataset explicitamente citado.
- Se o artigo usar mais de um dataset, gere linhas separadas por dataset.
- Se um resultado não puder ser associado com segurança a um dataset específico, use NA.
- Normalize nomes canônicos quando estiver claro no artigo:
  FER-2013, RAF-DB, CK+, AffectNet-7, RAVDESS, IEMOCAP, MSP-Podcast, DEAP
- Normalize variantes óbvias:
  FER 2013 -> FER-2013
  CK+48 -> CK+
  CK + -> CK+

modalidade
- Use FER para reconhecimento de expressões faciais.
- Use SER para reconhecimento de emoções na fala.
- Use HER para reconhecimento de emoções humanas quando não se encaixar claramente em FER/SER e não houver fusão multimodal.
- Use MULTIMODAL apenas quando houver mais de uma modalidade presente e o modelo utilizar explicitamente fusão de informações para classificação.
- Se houver mais de uma modalidade presente mas não houver fusão explícita para classificação, não use MULTIMODAL; gere linhas unimodais separadas se o artigo reportar resultados separados.

tarefa
- multiclasse para classificação com mais de duas classes exclusivas
- multilabel para múltiplos rótulos simultâneos
- regressao para saída contínua
- detecao para detecção/localização

ambiente_coleta
- Use o valor explicitamente descrito no artigo.
- Se não houver menção explícita, aplique fallback apenas para datasets canônicos:
  FER-2013 -> misto
  RAF-DB -> selvagem
  AffectNet-7 -> selvagem
  CK+ -> controlado
- Se não houver menção e o dataset não estiver nessas regras, use NA.
- Sempre que ambiente_coleta for preenchido por fallback de dataset canônico e não por menção textual explícita, registre isso em observacoes.

dependencia_temporal
- Use sim quando o modelo ou protocolo depender de sequência temporal, frames em ordem, janelas temporais, vídeo contínuo, série temporal ou contexto temporal explícito.
- Use nao quando o experimento tratar amostras independentemente.
- Use NA se não der para determinar com segurança.

n_amostras_total
- Priorize o número total de amostras brutas usadas diretamente para treinamento.
- Para FER em vídeo/frame-based, prefira número de imagens ou frames se isso for o insumo direto de treino.
- Para SER, prefira número de amostras, segmentos ou clips efetivamente usados no treino.
- Não some datasets, folds ou partições se o artigo não fizer isso explicitamente.
- Se só houver número de participantes e não de amostras, use NA.
- Se o artigo informar tamanho total do dataset e não tamanho efetivamente usado no treino, use o total apenas se ficar claro que o conjunto inteiro foi usado no processo experimental.

pretreino
- Aplique a regra de default.
- Se o mesmo modelo tiver pretreino explícito em um dataset e reaparecer em outro dataset do mesmo artigo sem negação explícita, mantenha sim para esse mesmo modelo.
- Quando pretreino for mantido por consistência intra-artigo e não por menção explícita naquela linha específica, registre isso em observacoes.

modalidades_presentes
- Use lista JSON válida com itens entre:
  "video", "audio", "texto", "fisiologia", "conhecimento"
- Use apenas modalidades explicitamente presentes no experimento.
- Não infira modalidade a partir do tema geral do artigo.
- Se não for possível identificar, use NA.

observacoes
- Use observacoes para registrar decisões de consolidação, ambiguidades resolvidas, fallback aplicado, ou qualquer caso-limite relevante para rastreabilidade.
- Exemplos de uso:
  - resultado principal escolhido entre várias tabelas
  - ambiente_coleta inferido por fallback de dataset canônico
  - pretreino mantido por consistência intra-artigo
  - resultado não associado com segurança a um dataset específico
  - modelo_familia definida por bloco decisório final em arquitetura híbrida
- Se não houver observação relevante, use NA.
- Não deixe observacoes vazia.

==================================================
MODELO_FAMILIA PADRONIZADO
==================================================

Use somente estes valores:

CNN
Transformer
RNN
ANN
SVM
RF
Boosting_ML
Ensemble_ML
HMM
CRF
Autoencoder
Multimodal

Mapeamento obrigatório:

- ResNet, DenseNet, MobileNet, ShuffleNet, EfficientNet, CNN, ConvNet -> CNN
- ViT, Swin, TimeSformer, Transformer, wav2vec, HuBERT, AST, conformer baseado em Transformer -> Transformer
- RNN, LSTM, GRU, BiLSTM, CRNN, CNN-LSTM, ConvLSTM -> RNN
- ANN, MLP, Dense, Feedforward, Perceptron, DBN, DBFL, Deep Belief -> ANN
- SVM -> SVM
- Random Forest, RF -> RF
- XGBoost, LightGBM, CatBoost, AdaBoost, Gradient Boosting, Boosting -> Boosting_ML
- Ensemble, Voting, Weighted Voting, Stacking, Bagging, CNN+SVM híbrido de combinação -> Ensemble_ML
- HMM -> HMM
- CRF -> CRF
- Autoencoder, VAE -> Autoencoder
- Qualquer modelo com fusão multimodal explícita para classificação -> Multimodal

Importante:
- Não use valores fora desse vocabulário.
- Não use CNN-RNN, Multimodal_late, Multimodal_early, SSL_audio ou outros rótulos fora da lista controlada.
- Se a arquitetura for híbrida mas unimodal, escolha a família dominante segundo o bloco que produz a decisão final.
- Se o artigo descrever explicitamente combinação de classificadores de famílias diferentes no estágio de decisão, use Ensemble_ML.
- Se a escolha da família dominante em arquitetura híbrida exigir decisão interpretativa, registre o critério em observacoes.

modelo_especifico
- Use o nome específico do modelo como aparece no artigo:
  ResNet50, MobileNetV2, BiLSTM, wav2vec 2.0, MABD, LightGBM, XGBoost etc.
- Se o artigo só disser “CNN” ou “SVM”, use esse nome como modelo_especifico.
- Não crie nomes genéricos como “Hybrid Model”, “Speech Model”, “Video Model”, “Combined Model”, “Fusion Model” a menos que esse seja realmente o nome apresentado no artigo.

==================================================
MÉTRICAS
==================================================

Selecione a métrica principal de forma condicional ao tipo de tarefa:

Para tarefa = regressao, use esta prioridade:
1. CCC
2. PCC

Para tarefa = multiclasse, multilabel ou detecao, use esta prioridade:
1. macroF1
2. balanced_accuracy
3. ACC

Em qualquer modalidade, aceite também EER ou AUC somente se o artigo as declarar explicitamente como métrica principal ou co-principal.

Regras:

- metricas_principais deve conter apenas a métrica principal selecionada ou métricas explicitamente declaradas como co-principais.
- Não inclua métricas auxiliares ou secundárias como precision, recall, MAE, MSE, RMSE, specificity, sensitivity, etc., a menos que o artigo diga explicitamente que são métricas principais.
- metrica_principal_valor deve conter o valor numérico correspondente à métrica principal escolhida.
- Se metricas_principais estiver preenchida e o valor numérico correspondente estiver disponível no artigo, metrica_principal_valor não pode ser NA.
- Use NA em metrica_principal_valor somente se o artigo não fornecer um valor agregado comparável para a métrica principal.
- Se o artigo declarar duas ou mais métricas co-principais, inclua todas em metricas_principais, mas em metrica_principal_valor use o valor da métrica de maior prioridade conforme a tarefa.
- Se EER ou AUC forem explicitamente declaradas como métricas principais ou co-principais, elas podem ser mantidas em metricas_principais mesmo quando a tarefa for multiclasse, multilabel ou detecao.
- Se o artigo reportar várias tabelas, folds, splits, bases-alvo ou variações para o mesmo dataset e mesmo modelo, escolha apenas o resultado principal/final do experimento.
- Não gere linhas duplicadas apenas porque há múltiplas tabelas secundárias.
- Quando houver escolha entre várias tabelas ou variantes para definir o resultado principal, registre o critério em observacoes.

Normalização de nomes em metricas_principais:
- F1 macro, Macro-F1, macro F1 -> macroF1
- Balanced Accuracy, UAR -> balanced_accuracy
- Accuracy, Acc -> ACC
- AUC -> AUC
- EER -> EER
- CCC -> CCC
- PCC, Pearson, Pearson Correlation, Pearson's r -> PCC

Exemplos válidos:
"[""macroF1""]"
"[""balanced_accuracy""]"
"[""ACC""]"
"[""CCC""]"
"[""PCC""]"
"[""AUC""]"
"[""EER""]"

==================================================
AUGMENTATIONS
==================================================

- Use lista JSON somente com técnicas de data augmentation explicitamente mencionadas.
- Exemplos válidos:
  "[""flip"",""rotation""]"
  "[""oversampling""]"
  "[""horizontal flip"",""random crop""]"
- Se nada for mencionado explicitamente, use NA.
- Não use termos genéricos como:
  "augmentation", "data augmentation", "preprocessing"
- Não invente nomes de técnicas.
- Não trate pré-processamento genérico, normalização, resize, crop fixo, limpeza, segmentação ou extração de features como augmentation, a menos que o artigo o apresente explicitamente como data augmentation.
- Se os termos extraídos parecerem sem sentido, ambíguos ou não forem técnicas reconhecíveis de augmentation no texto do artigo, use NA.

==================================================
CONSISTÊNCIA DE LINHAS
==================================================

Gere linhas separadas quando houver:
- datasets diferentes
- modelos diferentes
- regimes diferentes
- protocolos diferentes
- tarefas diferentes
- modalidade diferente

Não gere linhas duplicadas.

Se o mesmo modelo aparecer no mesmo dataset com pequenas variações de hiperparâmetro, mas sem mudança nos campos do CSV, mantenha uma única linha correspondente ao resultado principal reportado.

Se houver uma linha com protocolo_cross_dataset = sim para um artigo/dataset/modelo, não crie outra linha idêntica com protocolo_cross_dataset = nao, a menos que o artigo descreva explicitamente dois regimes distintos e ambos tenham resultados separados.

Se houver várias tabelas, folds, splits ou variantes e apenas uma linha for mantida como resultado principal, registre em observacoes qual critério foi usado.

==================================================
VERIFICAÇÃO FINAL ANTES DE RESPONDER
==================================================

Antes de produzir o CSV final, faça silenciosamente esta checagem:

1. Há exatamente uma linha de cabeçalho.
2. Não há texto fora do CSV.
3. Não há células vazias.
4. Todo faltante está como NA.
5. Todas as listas estão em JSON válido.
6. Todos os valores de modelo_familia pertencem ao vocabulário controlado.
7. metrica_principal_valor está em [0,1] ou NA.
8. protocolo_person_independent, protocolo_cross_dataset, pretreino, code_available e weights_available usam apenas sim ou nao.
9. Há uma linha por artigo_titulo × dataset_id × modelo_especifico × regime_relevante.
10. Se modalidades_presentes tiver mais de um item e houver fusão explícita para classificação, modalidade deve ser MULTIMODAL e modelo_familia deve ser Multimodal.
11. Se metricas_principais incluir apenas uma métrica principal com valor disponível, metrica_principal_valor não pode ser NA.
12. Se augmentations contiver termo genérico, substitua por NA.
13. Se modelo_especifico for nome inventado ou excessivamente genérico não apoiado no texto do artigo, substitua pelo nome realmente usado no artigo ou por NA.
14. Se houver linhas duplicadas para o mesmo artigo_titulo × dataset_id × modelo_especifico sem diferença real de regime, mantenha apenas uma.
15. Se houver qualquer célula vazia em qualquer linha, substitua por NA antes de responder.
16. Rejeite internamente qualquer linha com duas vírgulas consecutivas ",," ou com vírgula final indicando campo vazio.

Retorne somente o CSV final.