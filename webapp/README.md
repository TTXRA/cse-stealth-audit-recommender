# Interface web — Evidência CSE

A interface web oferece uma camada amigável sobre os dados e scripts científicos do projeto. Ela não duplica o algoritmo: o cálculo de robustez, a validação e a recomendação continuam sendo executados pelas rotinas em `scripts/`.

## Funcionalidades

- seção **Como usar**, com primeiros passos, explicação dos campos, leitura do ranking e dúvidas frequentes;
- consulta e filtragem da planilha mestre de artigos;
- inclusão de novos artigos com classificação explícita de empiricidade e resultados quantitativos;
- seção **Elegibilidade** com o funil cumulativo, configuração do total de titulares e do mínimo por modalidade, previsão da alocação e geração do sorteio reprodutível;
- seção **Auditoria** restrita aos artigos titulares e suplentes selecionados no sorteio;
- exploração e download dos cenários experimentais;
- inclusão validada de cenários para artigos auditados;
- sincronização de `artifacts/cenarios.csv` e `artifacts/cenarios.json`;
- cópia de segurança automática antes de cada inclusão;
- geração de recomendação com tarefas compatíveis com a modalidade e filtros opcionais;
- apresentação do suporte, intervalos de confiança, relaxamento de filtros e abstenção;
- execução opcional do fluxo científico completo.

## Executar

Na raiz do repositório, instale as dependências e inicie a interface:

```powershell
python -m pip install -r requirements.txt
python webapp/run.py
```

O navegador abrirá a interface local. Na ausência de uma conexão PostgreSQL, os
dados permanecem nos arquivos do próprio repositório.

## Publicar no Streamlit Community Cloud

1. Envie o projeto para um repositório GitHub.
2. Em `share.streamlit.io`, crie um app apontando para `webapp/app.py`.
3. Escolha uma versão de Python compatível e aguarde a instalação de
   `requirements.txt`.
4. Para uso com escrita, crie um banco PostgreSQL e adicione a variável abaixo
   no campo **Secrets** do app:

```toml
CSE_DATABASE_URL = "postgresql://usuario:senha@host:5432/banco?sslmode=require"
```

Não versione `.streamlit/secrets.toml`. O arquivo
`.streamlit/secrets.toml.example` contém somente o formato esperado.

## Persistência e rastreabilidade

Um cenário confirmado é acrescentado a `artifacts/cenarios.csv` e `artifacts/cenarios.json`. Antes da alteração, as versões anteriores são copiadas para `data/output/webapp/backups/`. Em seguida, a interface recalcula o índice de robustez e valida a base usada pelo recomendador.

Um novo artigo tem seus metadados acrescentados a `data/raw/mapeamento_master.csv`. As escolhas explícitas **Empírico** e **Quantitativo**, com suas justificativas, são gravadas somente em `data/raw/rotulos_elegibilidade.csv`. A tabela da seção **Artigos** exibe exclusivamente as colunas da base mestre; o cruzamento dos rótulos ocorre na seção **Elegibilidade**, sempre por `artigo_id`.

O botão de sorteio reexecuta somente as etapas de corpus, elegibilidade e amostragem. Os artigos dentro da janela temporal que sejam empíricos, quantitativos e pertençam a FER, SER ou MULTI compõem a população elegível; a semente configurada no projeto mantém o procedimento reprodutível. A interface valida `N_ALVO_TOTAL` e `MIN_POR_MODALIDADE`, apresenta a distribuição prevista e passa os valores escolhidos apenas para aquela execução.

Cada novo sorteio recebe um identificador de versão. Os artefatos anteriores e os recém-gerados são preservados em `data/output/amostras/historico/<versao>/`, com metadados da semente e dos parâmetros utilizados. O índice `historico_sorteios.csv` permite rastrear as versões; em caso de falha, a interface restaura automaticamente os artefatos anteriores.

A auditoria é registrada separadamente na seção **Auditoria**, que mostra somente os artigos sorteados; quando concluída, seus 16 itens são gravados em `data/audit/auditoria.csv` e `data/audit/auditoria.json`. Todas as bases envolvidas recebem cópias de segurança antes da alteração.

Quando `CSE_DATABASE_URL` está configurada, a aplicação usa os CSVs como carga
inicial e mantém no PostgreSQL uma cópia transacional dos arquivos editáveis.
Cada atualização arquiva a revisão anterior nas tabelas `cse_app_files` e
`cse_app_file_history`. Ao reiniciar, a versão persistida é restaurada antes que
a interface leia as bases. Assim, os scripts científicos continuam operando com
os mesmos arquivos, enquanto os dados modificados pela interface sobrevivem a
reinicializações e novos deployments.

## Modalidade e tarefa

Nas bases do corpus, de elegibilidade, de amostragem e de escores da auditoria,
`modalidade` identifica FER, SER ou MULTI (ou NA quando não informada).
Na base de cenários,
`modalidade` mantém seu domínio próprio (FER, SER, HER, MULTIMODAL), enquanto
`tarefa` identifica multiclasse, multilabel, regressao ou deteccao.

A base mestre, as bases de auditoria e os scripts utilizam exclusivamente a coluna `modalidade`.
Não há conversão ou leitura alternativa do nome antigo no fluxo do corpus.
