from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(
    page_title="Evidência CSE",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    if "CSE_DATABASE_URL" in st.secrets and not os.environ.get("CSE_DATABASE_URL"):
        os.environ["CSE_DATABASE_URL"] = str(st.secrets["CSE_DATABASE_URL"])
except FileNotFoundError:
    pass

from webapp.services import (  # noqa: E402
    PIPELINE_STEPS,
    add_article,
    add_scenario,
    audit_selection_funnel,
    audit_template,
    calculate_article_w,
    data_summary,
    generate_audit_sample,
    load_article_audit,
    load_articles,
    load_audited_article_ids,
    load_scenarios,
    prepare_storage,
    recommendation_task_options,
    rebuild_recommender_base,
    recommend,
    run_pipeline,
    sampling_allocation_preview,
    sampling_configuration,
    save_article_audit,
)
from scripts.utils.config import (  # noqa: E402
    RECOMENDACAO_MIN_ARTIGOS_POR_FAMILIA,
    RECOMENDACAO_MIN_FAMILIAS,
    RECOMENDACAO_MIN_OBSERVACOES_AGREGADAS,
)

try:
    STORAGE_STATUS = prepare_storage()
except Exception as exc:
    st.error(
        "A interface não pôde sincronizar o armazenamento persistente. "
        "Nenhuma alteração foi realizada."
    )
    st.exception(exc)
    st.stop()

st.markdown(
    """
    <style>
    :root {
        --ink: #14253d;
        --muted: #596b80;
        --line: #dce4e8;
        --paper: #f7f9f8;
        --teal: #0f766e;
        --teal-dark: #0a5d57;
        --teal-soft: #e6f4f1;
        --amber: #c96f2d;
    }
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: var(--paper);
        color: var(--ink);
        color-scheme: light;
    }
    [data-testid="stSidebar"] { background: #10273f; }
    [data-testid="stSidebar"] * { color: #f5f8fa !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        border-radius: 9px; padding: .3rem .45rem;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: #1a3a59; }
    .brand { padding: .5rem .1rem 1.25rem; }
    .brand-mark { color: #64d6c5; font-size: 1.4rem; letter-spacing: .08em; }
    .brand-title { font-size: 1.12rem; font-weight: 720; margin-top: .25rem; }
    .brand-sub { opacity: .7; font-size: .78rem; line-height: 1.35; margin-top: .35rem; }
    .eyebrow { color: var(--teal); font-size: .76rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
    .hero { padding: 1.25rem 0 .85rem; border-bottom: 1px solid var(--line); margin-bottom: 1.2rem; }
    .hero h1 { color: var(--ink); font-size: clamp(2rem, 4vw, 3.2rem); letter-spacing: -.045em; line-height: 1.05; margin: .4rem 0 .65rem; }
    .hero p {
        color: var(--muted);
        width: 100%;
        max-width: none;
        white-space: nowrap;
        font-size: 1.02rem;
        line-height: 1.65;
    }
    [data-testid="stMetric"] { background: white; border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.05rem; box-shadow: 0 5px 18px rgba(20,37,61,.035); }
    [data-testid="stMetricLabel"] p {
        color: #53657a !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] { color: var(--ink) !important; font-weight: 720; }
    [data-testid="stCaptionContainer"] p {
        color: #617287 !important;
        opacity: 1 !important;
    }
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span {
        color: #34475d !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
    .stButton > button, .stDownloadButton > button { border-radius: 9px; font-weight: 650; min-height: 2.65rem; }
    [data-testid="stBaseButton-primary"] {
        background: var(--teal) !important;
        border-color: var(--teal) !important;
        color: #ffffff !important;
    }
    [data-testid="stBaseButton-primary"]:hover {
        background: var(--teal-dark) !important;
        border-color: var(--teal-dark) !important;
    }
    [data-testid="stBaseButton-primary"] p,
    [data-testid="stBaseButton-primary"] span {
        color: #ffffff !important;
    }
    [data-testid="stDownloadButton"] button {
        background: var(--teal) !important;
        border-color: var(--teal) !important;
        color: #ffffff !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: var(--teal-dark) !important;
        border-color: var(--teal-dark) !important;
    }
    [data-testid="stDownloadButton"] button p,
    [data-testid="stDownloadButton"] button span {
        color: #ffffff !important;
    }
    [data-testid="stBaseButton-secondary"] {
        background: #ffffff !important;
        border-color: #b8c7d1 !important;
        color: var(--ink) !important;
    }
    [data-testid="stBaseButton-secondary"] p,
    [data-testid="stBaseButton-secondary"] span {
        color: var(--ink) !important;
    }
    [data-testid="stBaseButton-secondary"]:disabled {
        background: #edf1f3 !important;
        border-color: #d5dee3 !important;
    }
    [data-testid="stBaseButton-secondary"]:disabled p,
    [data-testid="stBaseButton-secondary"]:disabled span {
        color: #667789 !important;
    }
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {
        color: #334155 !important;
        opacity: 1 !important;
    }
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div {
        background: #ffffff !important;
        color: var(--ink) !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 1.2rem; }
    .stTabs [data-baseweb="tab"] { padding-left: 0; padding-right: 0; color: #3d5066 !important; }
    .stTabs [aria-selected="true"] { color: var(--teal-dark) !important; }
    .section-intro { color: var(--muted); margin-top: -.45rem; margin-bottom: 1rem; max-width: 780px; }
    .note { background: var(--teal-soft); border-left: 3px solid var(--teal); border-radius: 6px; padding: .8rem 1rem; color: #24514c; margin: .6rem 0 1rem; }
    .small-label { color: var(--muted); font-size: .8rem; }
    h2, h3 { color: var(--ink); letter-spacing: -.025em; }
    </style>
    """,
    unsafe_allow_html=True,
)


def hero(kicker: str, title: str, text: str) -> None:
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{kicker}</div><h1>{title}</h1><p>{text}</p></div>',
        unsafe_allow_html=True,
    )


def horizontal_bar_chart(series, color: str, value_title: str, value_format: str = ",d") -> None:
    frame = series.rename("valor").reset_index()
    category_column = frame.columns[0]
    frame = frame.rename(columns={category_column: "categoria"})
    order = frame["categoria"].astype(str).tolist()
    chart = (
        alt.Chart(frame)
        .mark_bar(color=color, cornerRadiusEnd=3)
        .encode(
            y=alt.Y(
                "categoria:N",
                sort=order,
                title=None,
                axis=alt.Axis(labelAngle=0, labelLimit=240),
            ),
            x=alt.X("valor:Q", title=value_title),
            tooltip=[
                alt.Tooltip("categoria:N", title="Categoria"),
                alt.Tooltip("valor:Q", title=value_title, format=value_format),
            ],
        )
        .properties(height=max(220, len(frame) * 34))
    )
    st.altair_chart(chart, width="stretch")


def render_overview() -> None:
    hero(
        "Painel da pesquisa",
        "Da literatura à recomendação.",
        "Explore o corpus, acompanhe a base experimental e consulte famílias de modelos sem perder a rastreabilidade da abordagem.",
    )
    summary = data_summary()
    cols = st.columns(4)
    cols[0].metric("Artigos no mapeamento", summary["articles"])
    cols[1].metric("Artigos auditados", summary["audited_articles"])
    cols[2].metric("Cenários experimentais", summary["scenarios"])
    cols[3].metric("Famílias observadas", summary["families"])

    st.info("Primeiro acesso? Abra **Como usar** no menu lateral para conhecer os campos e interpretar os resultados.")
    st.subheader("Como a interface organiza o fluxo")
    st.markdown(
        """
        1. **Cadastre ou consulte os artigos** e filtre o corpus mestre.
        2. **Verifique a elegibilidade e gere o sorteio** reprodutível da amostra.
        3. **Consulte ou realize a auditoria** dos 16 itens dos artigos sorteados.
        4. **Revise ou acrescente cenários** associados aos artigos.
        5. **Descreva a necessidade experimental** e receba um ranking fundamentado no índice de robustez.
        6. **Reprocesse a pesquisa** quando as bases de entrada forem atualizadas.
        """
    )
    st.markdown(
        '<div class="note">A abstenção é um resultado válido: ela indica que a base ainda não contém evidência mínima para comparar famílias com segurança.</div>',
        unsafe_allow_html=True,
    )

    scenarios = load_scenarios()
    st.subheader("Retrato da evidência")
    left, right = st.columns(2)
    with left:
        modality = scenarios.groupby("modalidade").size().sort_values(ascending=False)
        st.caption("Cenários por modalidade")
        horizontal_bar_chart(modality, "#0f766e", "Cenários")
    with right:
        families = scenarios.groupby("modelo_familia").size().sort_values(ascending=False)
        st.caption("Cenários por família de modelo")
        horizontal_bar_chart(families, "#c96f2d", "Cenários")


def render_help() -> None:
    hero(
        "Guia de uso",
        "Como usar a Evidência CSE",
        "Entenda por onde começar, como preencher os campos e o que os resultados significam.",
    )
    start_tab, fields_tab, results_tab, questions_tab = st.tabs(
        ["Primeiros passos", "Entenda os campos", "Leia os resultados", "Dúvidas frequentes"]
    )

    with start_tab:
        st.subheader("Quero consultar uma recomendação")
        st.markdown(
            """
            A base já contém artigos auditados e cenários experimentais. Você pode usá-la sem cadastrar novos dados.

            1. Abra **Recomendação** no menu lateral.
            2. Escolha a **modalidade** e a **tarefa**. As opções de tarefa acompanham a evidência disponível para a modalidade selecionada.
            3. Se necessário, selecione o conjunto de dados, o ambiente de coleta e os demais filtros. **Qualquer** deixa aquele filtro sem restrição.
            4. Clique em **Gerar recomendação** e confira a família indicada, o suporte e os filtros eventualmente relaxados.
            5. Consulte o ranking e, se desejar, use **Baixar ranking em CSV** para guardar o resultado.

            Por exemplo, para consultar classificação de expressões faciais, selecione **FER** e **multiclasse**.
            Comece com os filtros opcionais em **Qualquer** e depois especifique as condições do seu cenário.
            """
        )
        st.subheader("Quero acrescentar evidências à base")
        st.markdown(
            """
            1. Em **Artigos**, consulte o cadastro ou adicione um artigo com seus metadados e a indicação de resultados empíricos e quantitativos.
            2. Em **Elegibilidade**, confira os critérios, os artigos elegíveis e os parâmetros antes de gerar o sorteio da amostra.
            3. Em **Auditoria**, registre os 16 itens dos artigos selecionados, com evidências e justificativas.
            4. Em **Cenários**, acrescente os experimentos de um artigo auditado. Cada cenário reúne conjunto de dados, modelo, condições experimentais e resultado.
            5. Volte a **Recomendação** para consultar a evidência atualizada. Ao guardar um cenário, a interface também recalcula a robustez e valida a base do recomendador.

            **Executar fluxo** serve para atualizar todas as saídas derivadas após revisar as entradas.
            Consultar a base e gerar uma recomendação não exige executar o fluxo completo.
            """
        )

    with fields_tab:
        st.subheader("Modalidade, tarefa e canais de dados")
        st.markdown(
            """
            | Campo | O que representa | Como usar |
            | --- | --- | --- |
            | **Modalidade** | Categoria operacional do artigo ou cenário. | Nos cenários: FER, SER, MULTIMODAL ou HER. No cadastro de artigos, MULTI identifica multimodal. |
            | **Tarefa** | Problema de aprendizagem. | Multiclasse: escolher entre várias classes; multilabel: atribuir vários rótulos; regressão: estimar um valor; detecção: identificar a ocorrência do alvo. |
            | **Canais de dados presentes** | Fontes de informação usadas no experimento. | Vídeo, áudio, texto, fisiologia ou conhecimento. Não confundir esses canais com a categoria modalidade. |
            | **Ambiente de coleta** | Condições em que os dados foram obtidos. | Controlado, misto ou selvagem; use NA quando a informação não estiver disponível. |
            | **Dependência temporal** | Uso de relações temporais no experimento. | Indique sim, não ou NA conforme a evidência registrada. |
            | **Pré-treinamento** | Uso de um modelo previamente treinado. | Indique sim ou não conforme o experimento. |

            **Estrato** é o grupo amostral formado pela estratificação por modalidade.
            Nas tabelas e formulários, a coluna **Modalidade** identifica a categoria usada para formar esses grupos.
            """
        )
        st.subheader("Ao preencher uma auditoria ou um cenário")
        st.markdown(
            """
            - **Campos com asterisco** são obrigatórios.
            - **Pontuação da auditoria:** use 0, 1 ou 2 conforme as âncoras do manual; use NA apenas quando o item permitir e registre a justificativa.
            - **Evidência:** indique onde a informação pode ser encontrada no artigo, como seção, página, tabela ou figura.
            - **Valor da métrica principal:** o formulário recebe valores entre 0 e 1; uma acurácia de 85% deve ser informada como 0,85.
            - **Total de amostras:** use 0 quando não informado, conforme a orientação do formulário.
            - **Observações:** registre decisões de extração, condições específicas e ressalvas que ajudem a interpretar o experimento.
            """
        )

    with results_tab:
        st.subheader("O que significa o índice de robustez R?")
        st.markdown(
            "R combina desempenho normalizado em relação a uma linha de base operacional, "
            "sinal de protocolo experimental e qualidade de relato voltada à robustez. "
            "Um R maior indica uma avaliação mais favorável segundo esses critérios; "
            "ele não é uma porcentagem de acertos nem uma garantia de desempenho em um novo experimento."
        )
        st.subheader("Como ler o ranking")
        st.markdown(
            f"""
            - **Suporte principal:** a família possui evidências de pelo menos **{RECOMENDACAO_MIN_ARTIGOS_POR_FAMILIA} artigos distintos** na consulta atendida. Essas famílias aparecem antes das exploratórias.
            - **Suporte exploratório:** a família tem menos artigos que o mínimo exigido para suporte principal. Ela pode aparecer com R alto e, ainda assim, não ser escolhida.
            - **R médio:** para cada artigo e família, os cenários são resumidos pela mediana de R; o ranking usa a média desses valores entre artigos.
            - **IC95%:** intervalo calculado por reamostragem que expressa a incerteza da estimativa. Considere-o junto com o número de artigos disponíveis.
            - **Artigos e experimentos:** mostram a quantidade de estudos distintos e de cenários que sustentam cada família.

            A recomendação escolhe a família com maior R médio **entre as que atendem ao suporte principal**.
            Em empates, considera mais artigos, menor largura do intervalo e, por fim, o nome da família.
            """
        )
        st.subheader("Filtros relaxados e abstenção")
        st.markdown(
            f"""
            Quando os filtros deixam pouca evidência, o sistema pode retirar restrições opcionais progressivamente.
            **Modalidade e tarefa são sempre preservadas.** Os filtros relaxados aparecem no resultado;
            confira se a comparação ainda corresponde às condições de interesse.

            A recomendação exige pelo menos **{RECOMENDACAO_MIN_OBSERVACOES_AGREGADAS} evidências agregadas por artigo e família**
            e **{RECOMENDACAO_MIN_FAMILIAS} famílias com suporte principal**.
            Se esses critérios não forem atendidos mesmo após relaxar os filtros opcionais, ocorre **abstenção**.
            Isso significa que a base não oferece suporte mínimo para recomendar, embora possa apresentar um ranking exploratório.
            """
        )

    with questions_tab:
        with st.expander("Por que uma tarefa ou um filtro não aparece?"):
            st.write(
                "As opções da recomendação são extraídas dos cenários disponíveis. "
                "Os filtros seguintes acompanham as escolhas anteriores. "
                "Se uma opção não aparecer, consulte Cenários para verificar a evidência cadastrada."
            )
        with st.expander("Por que um artigo não aparece para auditoria ou inclusão de cenários?"):
            st.write(
                "A auditoria é restrita aos titulares e suplentes selecionados na amostra. "
                "O formulário de auditoria apresenta os que ainda não têm os 16 itens completos. "
                "Para adicionar cenários, o artigo precisa estar auditado. "
                "Confira a seleção em Elegibilidade e a situação do artigo em Auditoria."
            )
        with st.expander("Mudei os filtros. O resultado anterior ainda vale?"):
            st.write(
                "Clique novamente em Gerar recomendação. A interface identifica mudanças nos parâmetros "
                "e solicita uma nova consulta antes de apresentar o ranking correspondente."
            )
        with st.expander("Preciso executar o fluxo completo a cada consulta?"):
            st.write(
                "Não. Gerar recomendação já atualiza a robustez e valida a base necessária à consulta. "
                "Use Executar fluxo quando quiser recalcular também amostragem, consistência, "
                "escores, figuras e avaliação após revisar os dados de entrada. "
                "Essa ação gera novamente a amostra e atualiza as saídas da pesquisa."
            )
        with st.expander("Os registros que eu salvo ficam guardados?"):
            st.write(
                "Os registros são gravados nas bases usadas pelo sistema, com cópias de segurança antes das alterações. "
                "A consulta e os downloads permitem conferir os dados registrados. "
                "Em uma instalação local, os dados ficam na pasta do projeto; "
                "em uma instalação hospedada, a conservação entre reinicializações depende do armazenamento persistente configurado."
            )


def render_articles() -> None:
    hero(
        "Corpus",
        "Artigos mapeados",
        "Consulte os metadados bibliográficos que alimentam as etapas de elegibilidade, amostragem, auditoria e extração de cenários.",
    )
    consult_tab, add_tab = st.tabs(["Consultar artigos", "Adicionar artigo"])

    with consult_tab:
        articles = load_articles()

        filter_col, year_col = st.columns([3, 1])
        search = filter_col.text_input("Buscar", placeholder="Título, identificador, veículo ou DOI")
        years = sorted([year for year in articles["ano"].unique() if year])
        selected_year = year_col.selectbox("Ano", ["Todos"] + years)

        filtered = articles.copy()
        if search:
            mask = filtered.astype(str).apply(
                lambda column: column.str.contains(search, case=False, na=False, regex=False)
            ).any(axis=1)
            filtered = filtered.loc[mask]
        if selected_year != "Todos":
            filtered = filtered.loc[filtered["ano"].eq(selected_year)]

        st.caption(f"{len(filtered)} artigo(s) exibido(s)")
        st.dataframe(
            filtered[
                [
                    "artigo_id",
                    "titulo",
                    "ano",
                    "venue",
                    "modalidade",
                    "doi",
                ]
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "artigo_id": "ID",
                "titulo": st.column_config.TextColumn("Título", width="large"),
                "ano": "Ano",
                "venue": "Veículo",
                "modalidade": "Modalidade",
                "doi": "DOI",
            },
        )
        st.download_button(
            "Baixar seleção em CSV",
            filtered.to_csv(index=False).encode("utf-8-sig"),
            file_name="artigos_filtrados.csv",
            mime="text/csv",
        )

    with add_tab:
        st.markdown(
            '<div class="note">O identificador é gerado automaticamente. A classificação de elegibilidade deve ser informada explicitamente e será armazenada separadamente dos metadados do artigo.</div>',
            unsafe_allow_html=True,
        )

        with st.form("new_article", clear_on_submit=False):
            title = st.text_input("Título do artigo *", placeholder="Título completo da publicação")
            first, second, third = st.columns([1, 1, 2])
            year = first.number_input(
                "Ano *",
                min_value=1900,
                max_value=datetime.now().year + 1,
                value=datetime.now().year,
                step=1,
            )
            modality = second.selectbox("Modalidade *", ["NA", "FER", "SER", "MULTI"])
            venue = third.text_input("Veículo de publicação", placeholder="Periódico ou conferência")
            doi = st.text_input("DOI", placeholder="10.xxxx/xxxxx")

            st.markdown("#### Elegibilidade")
            first, second = st.columns(2)
            empirical_selection = first.selectbox(
                "Investigação empírica *",
                ["Selecione", "Sim", "Não"],
            )
            quantitative_selection = second.selectbox(
                "Apresenta resultados quantitativos *",
                ["Selecione", "Sim", "Não"],
            )
            first, second = st.columns(2)
            empirical_reason = first.text_area(
                "Justificativa de empiricidade",
                placeholder="Evidência que sustenta o rótulo",
                height=90,
            )
            quantitative_reason = second.text_area(
                "Justificativa de resultados quantitativos",
                placeholder="Métricas ou resultados reportados",
                height=90,
            )

            submitted = st.form_submit_button("Adicionar artigo", type="primary", width="stretch")

        if submitted:
            payload = {
                "titulo": title,
                "ano": int(year),
                "venue": venue,
                "modalidade": modality,
                "doi": doi,
                "empirico": True if empirical_selection == "Sim" else False if empirical_selection == "Não" else None,
                "just_empirico": empirical_reason,
                "quantitativo": True if quantitative_selection == "Sim" else False if quantitative_selection == "Não" else None,
                "just_quantitativo": quantitative_reason,
            }
            try:
                with st.spinner("Validando e registrando o artigo..."):
                    result = add_article(payload)
                st.success(f"Artigo {result['article_id']} adicionado à base mestre.")
                st.caption("Atualize a elegibilidade e o sorteio na seção Elegibilidade.")
                st.caption("Cópias de segurança das bases anteriores foram preservadas automaticamente.")
            except Exception as exc:
                st.error(str(exc))


def render_eligibility() -> None:
    hero(
        "Seleção metodológica",
        "Elegibilidade e sorteio",
        "Acompanhe os filtros aplicados ao corpus e gere a amostra reprodutível dos artigos que seguirão para auditoria.",
    )

    funnel = audit_selection_funnel()
    eligible = funnel["eligible"]
    selected = funnel["selected"]

    st.subheader("Funil de elegibilidade")
    st.caption("As contagens são cumulativas: cada etapa contém somente os artigos que passaram pela anterior.")
    steps = st.columns(4)
    steps[0].metric("Artigos cadastrados", len(funnel["mapped"]))
    steps[1].metric(
        f"Janela {funnel['window_start']}–{funnel['window_end']}", len(funnel["in_window"])
    )
    steps[2].metric("Empíricos e quantitativos", len(funnel["quantitative"]))
    steps[3].metric("Elegíveis para sorteio", len(eligible))

    modality_counts = {
        modality: int(eligible["modalidade"].astype(str).str.upper().eq(modality).sum())
        for modality in ("FER", "SER", "MULTI")
    }
    st.markdown(
        f"**Distribuição dos elegíveis:** FER {modality_counts['FER']} · "
        f"SER {modality_counts['SER']} · MULTI {modality_counts['MULTI']}"
    )

    st.subheader("Gerar novo sorteio")
    st.warning(
        "O sorteio recria as listas de titulares e suplentes com a semente configurada no projeto. "
        "Se o corpus ou os rótulos mudaram, a composição da amostra também poderá mudar."
    )

    sampling_defaults = sampling_configuration()
    total_eligible = len(eligible)
    smallest_modality = min(modality_counts.values()) if modality_counts else 0
    default_target = min(sampling_defaults["target_total"], max(1, total_eligible))
    default_minimum = min(
        sampling_defaults["minimum_per_modality"],
        smallest_modality,
        default_target // 3,
    )
    parameter_cols = st.columns(2)
    target_total = int(
        parameter_cols[0].number_input(
            "Total de titulares",
            min_value=1,
            max_value=max(1, total_eligible),
            value=default_target,
            step=1,
            help="Quantidade total de artigos titulares distribuídos entre FER, SER e MULTI.",
        )
    )
    minimum_per_modality = int(
        parameter_cols[1].number_input(
            "Mínimo por modalidade",
            min_value=0,
            max_value=smallest_modality,
            value=default_minimum,
            step=1,
            help="Quantidade mínima de titulares garantida para cada uma das três modalidades.",
        )
    )

    preview = None
    try:
        preview = sampling_allocation_preview(
            modality_counts,
            target_total,
            minimum_per_modality,
        )
        titulars = preview["titulars"]
        reserves = preview["reserves"]
        st.info(
            f"Previsão de titulares: FER {titulars['FER']} · SER {titulars['SER']} · "
            f"MULTI {titulars['MULTI']} = {target_total}. "
            f"Suplentes previstos: {sum(reserves.values())}. "
            f"Total selecionado: {preview['selected_total']}."
        )
    except ValueError as exc:
        st.error(str(exc))

    if not funnel["audited"].empty:
        st.caption(
            "Como já existem auditorias, o sorteio atual será preservado no histórico e a nova "
            "configuração criará outra versão da amostra."
        )
    confirmed = st.checkbox(
        "Revisei os parâmetros e desejo gerar uma nova versão da amostra.",
        key="confirm_eligibility_sample",
    )
    if st.button(
        "Atualizar elegibilidade e gerar sorteio",
        type="primary",
        disabled=not confirmed or preview is None or total_eligible == 0,
        width="stretch",
    ):
        with st.spinner("Atualizando o funil e sorteando a amostra..."):
            sample_run = generate_audit_sample(target_total, minimum_per_modality)
        st.session_state["eligibility_sample_results"] = sample_run
        st.rerun()

    previous_run = st.session_state.pop("eligibility_sample_results", None)
    if previous_run:
        previous_results = previous_run["results"]
        if previous_run["succeeded"]:
            st.success(
                "Elegibilidade atualizada e nova amostra gerada com sucesso. "
                f"Versão: {previous_run['version_id']}."
            )
        else:
            failed = next(result for result in previous_results if not result["ok"])
            st.error(
                f"O processamento foi interrompido em: {failed['label']}. "
                "A amostra anterior foi restaurada."
            )
        with st.expander("Ver detalhes do processamento", expanded=False):
            for result in previous_results:
                status = "Concluído" if result["ok"] else "Falhou"
                st.markdown(f"**{result['label']} — {status}**")
                if result["output"]:
                    st.code(result["output"])

    st.subheader("Amostra atual")
    st.caption(
        f"{len(selected)} artigo(s) selecionado(s): {funnel['titular_count']} titular(es) e "
        f"{funnel['reserve_count']} suplente(s)."
    )
    st.dataframe(
        eligible[
            ["artigo_id", "titulo", "ano", "modalidade", "selecao_amostra"]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "artigo_id": "ID",
            "titulo": st.column_config.TextColumn("Título", width="large"),
            "ano": "Ano",
            "modalidade": "Modalidade",
            "selecao_amostra": "Resultado do sorteio",
        },
    )


def render_audit() -> None:
    hero(
        "Qualidade de relato",
        "Auditoria dos artigos",
        "Consulte ou complete os 16 itens de qualidade de relato somente para os artigos selecionados no sorteio.",
    )
    funnel = audit_selection_funnel()
    selected = funnel["selected"]
    audited = funnel["audited"]
    pending = funnel["pending"]

    summary = st.columns(5)
    summary[0].metric("Sorteados", len(selected))
    summary[1].metric("Titulares", funnel["titular_count"])
    summary[2].metric("Suplentes", funnel["reserve_count"])
    summary[3].metric("Auditados", len(audited))
    summary[4].metric("Pendentes", len(pending))

    if selected.empty:
        st.info("Ainda não há artigos sorteados. Gere a amostra na seção Elegibilidade.")
        return

    consult_tab, fill_tab = st.tabs(["Artigos sorteados", "Auditar selecionado"])

    with consult_tab:
        st.dataframe(
            selected[
                [
                    "artigo_id",
                    "titulo",
                    "ano",
                    "modalidade",
                    "selecao_amostra",
                    "status_auditoria",
                    "itens_unicos",
                ]
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "artigo_id": "ID",
                "titulo": st.column_config.TextColumn("Título", width="large"),
                "ano": "Ano",
                "modalidade": "Modalidade",
                "selecao_amostra": "Seleção na amostra",
                "status_auditoria": "Situação",
                "itens_unicos": "Itens registrados",
            },
        )

        if audited.empty:
            st.info("Ainda não há auditorias completas para consultar.")
        else:
            st.subheader("Detalhes de uma auditoria")
            title_map = audited.set_index("artigo_id")["titulo"].to_dict()
            selected_article = st.selectbox(
                "Artigo auditado",
                audited["artigo_id"].tolist(),
                format_func=lambda value: f"{value} — {title_map.get(value, '')}",
                key="audit_consult_article",
            )
            audit_details = load_article_audit(selected_article)
            W = calculate_article_w(selected_article)
            metric_col, explanation_col = st.columns([1, 3])
            metric_col.metric("Qualidade de relato W", f"{W:.3f}")
            explanation_col.markdown(
                '<div class="note">W é calculado a partir dos itens PRT, VZ, MET, EXT e ROB aplicáveis e será associado aos cenários deste artigo.</div>',
                unsafe_allow_html=True,
            )
            audit_display = audit_details[
                ["item_id", "item_nome", "pontuacao", "evidencia", "justificativa_NA", "observacoes"]
            ].copy()
            st.dataframe(
                audit_display,
                width="stretch",
                hide_index=True,
                height=530,
                column_config={
                    "item_id": "Item",
                    "item_nome": st.column_config.TextColumn("Critério", width="medium"),
                    "pontuacao": "Pontuação",
                    "evidencia": st.column_config.TextColumn("Evidência", width="large"),
                    "justificativa_NA": st.column_config.TextColumn("Justificativa NA", width="large"),
                    "observacoes": st.column_config.TextColumn("Observações", width="large"),
                },
            )
            st.download_button(
                "Baixar auditoria deste artigo",
                audit_details.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"auditoria_{selected_article}.csv",
                mime="text/csv",
                key="download_selected_audit",
            )

    with fill_tab:
        if pending.empty:
            st.success("Todos os artigos selecionados na amostra possuem auditoria completa.")
        else:
            st.markdown(
                '<div class="note">A lista apresenta somente titulares ou suplentes da amostra que ainda não possuem os 16 itens completos.</div>',
                unsafe_allow_html=True,
            )
            pending_title_map = pending.set_index("artigo_id")["titulo"].to_dict()
            selected_pending = st.selectbox(
                "Artigo a auditar",
                pending["artigo_id"].tolist(),
                format_func=lambda value: f"{value} — {pending_title_map.get(value, '')}",
                key="audit_pending_article",
            )
            selected_status = pending.loc[
                pending["artigo_id"].eq(selected_pending), "status_auditoria"
            ].iloc[0]
            if selected_status == "Incompleto":
                st.warning("Este artigo possui uma auditoria incompleta. Os valores existentes foram carregados para conclusão.")

            with st.form("article_audit_form", clear_on_submit=False):
                template = audit_template(selected_pending)
                template["na_permitido"] = template["na_permitido"].map({"1": "Sim", "0": "Não"})
                audit_values = st.data_editor(
                    template,
                    key=f"audit_values_{selected_pending}",
                    width="stretch",
                    height=610,
                    hide_index=True,
                    disabled=["item_id", "item_nome", "na_permitido"],
                    column_config={
                        "item_id": st.column_config.TextColumn("Item", width="small"),
                        "item_nome": st.column_config.TextColumn("Critério", width="medium"),
                        "na_permitido": st.column_config.TextColumn("NA permitido", width="small"),
                        "pontuacao": st.column_config.SelectboxColumn(
                            "Pontuação",
                            options=["0", "1", "2", "NA"],
                            required=True,
                            width="small",
                        ),
                        "evidencia": st.column_config.TextColumn("Evidência", width="large"),
                        "justificativa_NA": st.column_config.TextColumn("Justificativa NA", width="large"),
                        "observacoes": st.column_config.TextColumn("Observações", width="large"),
                    },
                )
                submitted = st.form_submit_button(
                    "Salvar auditoria completa",
                    type="primary",
                    width="stretch",
                )

            if submitted:
                try:
                    with st.spinner("Validando e registrando os 16 itens..."):
                        result = save_article_audit(selected_pending, audit_values)
                    st.success(
                        f"Auditoria de {result['article_id']} registrada com 16 itens. W = {result['W']:.3f}."
                    )
                    st.caption("Uma cópia de segurança da auditoria anterior foi preservada automaticamente.")
                except Exception as exc:
                    st.error(str(exc))


def render_scenarios() -> None:
    hero(
        "Base experimental",
        "Cenários",
        "Cada linha representa uma combinação rastreável entre artigo, conjunto de dados, modelo e condição experimental.",
    )
    explore_tab, add_tab = st.tabs(["Explorar cenários", "Adicionar cenário"])

    with explore_tab:
        scenarios = load_scenarios()
        search_col, modality_col, family_col = st.columns([2, 1, 1])
        search = search_col.text_input("Buscar cenário", placeholder="Artigo, dataset ou modelo")
        modalities = ["Todas"] + sorted(scenarios["modalidade"].unique().tolist())
        modality = modality_col.selectbox("Modalidade", modalities)
        families = ["Todas"] + sorted(scenarios["modelo_familia"].unique().tolist())
        family = family_col.selectbox("Família", families)

        filtered = scenarios.copy()
        if search:
            mask = filtered.astype(str).apply(
                lambda column: column.str.contains(search, case=False, na=False, regex=False)
            ).any(axis=1)
            filtered = filtered.loc[mask]
        if modality != "Todas":
            filtered = filtered.loc[filtered["modalidade"].eq(modality)]
        if family != "Todas":
            filtered = filtered.loc[filtered["modelo_familia"].eq(family)]

        st.caption(f"{len(filtered)} de {len(scenarios)} cenário(s)")
        st.dataframe(filtered, width="stretch", hide_index=True, height=520)
        st.download_button(
            "Baixar cenários exibidos",
            filtered.to_csv(index=False).encode("utf-8-sig"),
            file_name="cenarios_filtrados.csv",
            mime="text/csv",
        )

    with add_tab:
        st.markdown(
            '<div class="note">Para que o índice R incorpore qualidade de relato, associe o cenário a um artigo já auditado.</div>',
            unsafe_allow_html=True,
        )
        articles = load_articles()
        audited_ids = load_audited_article_ids()
        options = articles.loc[articles["artigo_id"].isin(audited_ids), "artigo_id"].tolist()
        title_map = articles.set_index("artigo_id")["titulo"].to_dict()

        with st.form("new_scenario", clear_on_submit=False):
            article_id = st.selectbox(
                "Artigo auditado *",
                options,
                format_func=lambda value: f"{value} — {title_map.get(value, '')}",
            )
            first, second, third = st.columns(3)
            dataset_id = first.text_input("Conjunto de dados", placeholder="Ex.: RAVDESS")
            modality = second.selectbox("Modalidade *", ["FER", "SER", "MULTIMODAL", "HER"])
            task = third.selectbox("Tarefa *", ["multiclasse", "multilabel", "regressao", "deteccao"])

            first, second, third = st.columns(3)
            environment = first.selectbox("Ambiente de coleta", ["NA", "controlado", "misto", "selvagem"])
            temporal = second.selectbox("Dependência temporal", ["NA", "sim", "nao"])
            pretraining = third.selectbox("Pré-treinamento *", ["nao", "sim"])

            data_channels_present = st.multiselect(
                "Canais de dados presentes",
                ["video", "audio", "texto", "fisiologia", "conhecimento"],
            )

            first, second = st.columns(2)
            family = first.selectbox(
                "Família do modelo *",
                ["CNN", "Transformer", "RNN", "ANN", "SVM", "RF", "Boosting_ML", "Ensemble_ML", "HMM", "CRF", "Autoencoder", "Multimodal"],
            )
            specific_model = second.text_input("Modelo específico", placeholder="Nome reportado no artigo")

            first, second, third = st.columns(3)
            person_independent = first.selectbox("Independente por pessoa *", ["nao", "sim"])
            cross_dataset = second.selectbox("Teste entre bases *", ["nao", "sim"])
            sample_count = third.number_input("Total de amostras", min_value=0, step=1, help="Use 0 quando não informado.")

            first, second = st.columns([1, 1])
            metrics = first.text_input("Métricas principais *", placeholder="ACC, F1_MACRO")
            metric_value = second.number_input(
                "Valor da métrica principal *", min_value=0.0, max_value=1.0, value=0.80, step=0.001, format="%.3f"
            )

            augmentations = st.text_input("Aumentos de dados", placeholder="crop, noise — deixe vazio se não informado")
            first, second = st.columns(2)
            code_available = first.selectbox("Código disponível", ["NA", "nao", "sim"])
            weights_available = second.selectbox("Pesos disponíveis", ["NA", "nao", "sim"])
            notes = st.text_area("Observações", placeholder="Fonte do valor, tabela, ressalvas e decisões de codificação")
            submitted = st.form_submit_button("Guardar cenário e atualizar recomendador", type="primary", width="stretch")

        if submitted:
            payload = {
                "artigo_id": article_id,
                "artigo_titulo": title_map.get(article_id, ""),
                "dataset_id": dataset_id,
                "modalidade": modality,
                "tarefa": task,
                "ambiente_coleta": environment,
                "dependencia_temporal": temporal,
                "n_amostras_total": "NA" if sample_count == 0 else int(sample_count),
                "pretreino": pretraining,
                "canais_dados_presentes": data_channels_present,
                "modelo_familia": family,
                "modelo_especifico": specific_model,
                "protocolo_person_indep": person_independent,
                "protocolo_cross_dataset": cross_dataset,
                "metricas_principais": metrics,
                "metrica_principal_valor": metric_value,
                "augmentations": augmentations,
                "code_available": code_available,
                "weights_available": weights_available,
                "observacoes": notes,
            }
            try:
                with st.spinner("Validando o cenário e recalculando a base de robustez..."):
                    saved = add_scenario(payload)
                    validation = rebuild_recommender_base()
                st.success(
                    f"Cenário adicionado. A base agora contém {saved['rows']} linhas; "
                    f"{validation['rows_valid']} passaram pela validação do recomendador."
                )
                st.caption("Uma cópia de segurança da versão anterior foi preservada automaticamente.")
            except Exception as exc:
                st.error(str(exc))


def render_recommendation() -> None:
    hero(
        "Consulta orientada por evidência",
        "Recomendação",
        "Descreva o cenário pretendido. Filtros opcionais podem ser relaxados automaticamente quando a combinação exata não possui suporte suficiente.",
    )
    scenarios = load_scenarios()
    task_options = recommendation_task_options()
    with st.container(border=True):
        first, second = st.columns(2)
        modality = first.selectbox("Modalidade *", list(task_options))
        task = second.selectbox("Tarefa *", task_options[modality])

        compatible = scenarios.loc[
            scenarios["modalidade"].astype(str).str.strip().str.upper().eq(modality)
            & scenarios["tarefa"].astype(str).str.strip().str.lower().eq(task)
        ].copy()

        def available_values(frame, column, *, include_na=True):
            values = {
                str(value).strip()
                for value in frame[column]
                if str(value).strip() and (include_na or str(value).strip() != "NA")
            }
            return sorted(values, key=lambda value: (value == "NA", value.casefold()))

        def apply_optional_filter(frame, column, value):
            if value == "Qualquer":
                return frame
            return frame.loc[frame[column].astype(str).str.strip().eq(value)].copy()

        st.caption("Filtros opcionais")
        first, second, third = st.columns(3)
        datasets = available_values(compatible, "dataset_id", include_na=False)
        dataset_id = first.selectbox("Conjunto de dados", ["Qualquer"] + datasets)
        compatible = apply_optional_filter(compatible, "dataset_id", dataset_id)

        environments = available_values(compatible, "ambiente_coleta")
        environment = second.selectbox("Ambiente de coleta", ["Qualquer"] + environments)
        compatible = apply_optional_filter(compatible, "ambiente_coleta", environment)

        pretraining_options = available_values(compatible, "pretreino")
        pretraining = third.selectbox("Pré-treinamento", ["Qualquer"] + pretraining_options)
        compatible = apply_optional_filter(compatible, "pretreino", pretraining)

        first, second = st.columns(2)
        temporal_options = available_values(compatible, "dependencia_temporal")
        temporal = first.selectbox("Dependência temporal", ["Qualquer"] + temporal_options)
        compatible = apply_optional_filter(compatible, "dependencia_temporal", temporal)

        data_channel_sets = available_values(
            compatible,
            "canais_dados_presentes",
            include_na=False,
        )

        def format_data_channel_set(value):
            if value == "Qualquer":
                return value
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return value
            return ", ".join(parsed) if isinstance(parsed, list) else str(parsed)

        data_channel_set = second.selectbox(
            "Combinação de canais de dados",
            ["Qualquer"] + data_channel_sets,
            format_func=format_data_channel_set,
        )
        submit = st.button("Gerar recomendação", type="primary", width="stretch")

    query = {
        "modalidade": modality,
        "tarefa": task,
        "dataset_id": None if dataset_id == "Qualquer" else dataset_id,
        "ambiente_coleta": None if environment == "Qualquer" else environment,
        "pretreino": None if pretraining == "Qualquer" else pretraining,
        "dependencia_temporal": None if temporal == "Qualquer" else temporal,
        "canais_dados_presentes": None if data_channel_set == "Qualquer" else data_channel_set,
    }
    if submit:
        try:
            with st.spinner("Atualizando o índice de robustez e avaliando o suporte..."):
                validation = rebuild_recommender_base()
                if validation["rows_invalid"]:
                    raise ValueError(
                        f"A base possui {validation['rows_invalid']} cenário(s) inválido(s). Corrija-os antes da recomendação."
                    )
                log, ranking = recommend(query)
            st.session_state["last_recommendation"] = (log, ranking)
            st.session_state["last_recommendation_query"] = query
        except Exception as exc:
            st.error(str(exc))

    if "last_recommendation" not in st.session_state:
        st.info("Preencha os parâmetros para gerar o primeiro ranking desta sessão.")
        return
    if st.session_state.get("last_recommendation_query") != query:
        st.info("Os parâmetros foram alterados. Gere uma nova recomendação para atualizar o ranking.")
        return

    log, ranking = st.session_state["last_recommendation"]
    if log["abstencao"]:
        st.warning(
            "Recomendação não emitida: a literatura disponível não oferece suporte mínimo para comparar pelo menos duas famílias principais."
        )
    else:
        st.success(f"Família recomendada: **{log['familia_recomendada']}**")

    first, second, third, fourth = st.columns(4)
    first.metric("Linhas elegíveis", log["linhas_elegiveis"])
    second.metric("Evidências agregadas", log["observacoes_agregadas"])
    third.metric("Famílias candidatas", log["familias_candidatas"])
    fourth.metric("Famílias principais", log["familias_principais"])

    relaxed = log.get("filtros_relaxados", [])
    if relaxed:
        st.caption("Filtros relaxados por falta de suporte: " + ", ".join(relaxed))
    else:
        st.caption("A consulta foi atendida sem relaxar filtros opcionais.")

    if ranking.empty:
        st.info("Nenhuma família foi encontrada para os filtros obrigatórios informados.")
        return

    st.subheader("Ranking de famílias")
    display_columns = [
        "ordem",
        "modelo_familia",
        "status_suporte",
        "R_medio",
        "ic95_inf",
        "ic95_sup",
        "n_artigos",
        "n_experimentos",
    ]
    st.dataframe(
        ranking[display_columns],
        width="stretch",
        hide_index=True,
        column_config={
            "ordem": "Posição",
            "modelo_familia": "Família",
            "status_suporte": "Suporte",
            "R_medio": st.column_config.NumberColumn("R médio", format="%.3f"),
            "ic95_inf": st.column_config.NumberColumn("IC95% inferior", format="%.3f"),
            "ic95_sup": st.column_config.NumberColumn("IC95% superior", format="%.3f"),
            "n_artigos": "Artigos",
            "n_experimentos": "Experimentos",
        },
    )
    chart = ranking.set_index("modelo_familia")["R_medio"].sort_values(ascending=False)
    horizontal_bar_chart(chart, "#0f766e", "R médio", ".3f")
    st.download_button(
        "Baixar ranking em CSV",
        ranking.to_csv(index=False).encode("utf-8-sig"),
        file_name="ranking_recomendacao.csv",
        mime="text/csv",
    )


def render_pipeline() -> None:
    hero(
        "Reprodutibilidade",
        "Executar fluxo completo",
        "Reprocesse, na ordem metodológica, as bases, a auditoria, o índice de robustez, o recomendador e a avaliação fora da amostra.",
    )
    st.warning("O fluxo completo atualiza os artefatos derivados em `data/`. Execute-o apenas após revisar as entradas.")
    with st.expander("Ver etapas", expanded=False):
        for index, (label, path) in enumerate(PIPELINE_STEPS, 1):
            st.markdown(f"**{index}. {label}**  \n`{path}`")

    confirmed = st.checkbox("Revisei as entradas e desejo atualizar todas as saídas derivadas.")
    if st.button("Executar fluxo completo", type="primary", disabled=not confirmed, width="stretch"):
        with st.spinner("Executando as etapas metodológicas..."):
            results = run_pipeline()
        for result in results:
            if result["ok"]:
                st.success(result["label"])
            else:
                st.error(f"O fluxo foi interrompido em: {result['label']}")
            with st.expander(f"Detalhes — {result['label']}"):
                st.code(result["output"] or "Etapa concluída sem saída textual.")
        if results and all(result["ok"] for result in results):
            st.balloons()
            st.success("Fluxo completo executado com sucesso.")


with st.sidebar:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-mark">◈ CSE</div>
          <div class="brand-title">Evidência CSE</div>
          <div class="brand-sub">Auditoria e recomendação de famílias de modelos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navegação",
        [
            "Visão geral",
            "Como usar",
            "Artigos",
            "Elegibilidade",
            "Auditoria",
            "Cenários",
            "Recomendação",
            "Executar fluxo",
        ],
        label_visibility="collapsed",
    )


PAGES = {
    "Visão geral": render_overview,
    "Como usar": render_help,
    "Artigos": render_articles,
    "Elegibilidade": render_eligibility,
    "Auditoria": render_audit,
    "Cenários": render_scenarios,
    "Recomendação": render_recommendation,
    "Executar fluxo": render_pipeline,
}
PAGES[page]()
