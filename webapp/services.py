from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.utils.config import (
    ANO_FIM,
    ANO_INICIO,
    MIN_POR_ESTRATO,
    N_ALVO_TOTAL,
    N_SUPLENTES,
    RNG_SEED,
)
from webapp.storage import initialize_storage, persist_files, persist_tree


ROOT_DIR = Path(__file__).resolve().parents[1]
ARTICLES_PATH = ROOT_DIR / "data" / "raw" / "mapeamento_master.csv"
ELIGIBILITY_PATH = ROOT_DIR / "data" / "raw" / "rotulos_elegibilidade.csv"
SCENARIOS_PATH = ROOT_DIR / "artifacts" / "cenarios.csv"
SCENARIOS_JSON_PATH = ROOT_DIR / "artifacts" / "cenarios.json"
CHECKLIST_PATH = ROOT_DIR / "artifacts" / "itens_checklist.csv"
AUDIT_PATH = ROOT_DIR / "data" / "audit" / "auditoria.csv"
AUDIT_JSON_PATH = ROOT_DIR / "data" / "audit" / "auditoria.json"
RANKING_PATH = ROOT_DIR / "data" / "output" / "robustez" / "ranking_recomendacao.csv"
BACKUP_DIR = ROOT_DIR / "data" / "output" / "webapp" / "backups"
SAMPLING_HISTORY_DIR = ROOT_DIR / "data" / "output" / "amostras" / "historico"
SAMPLING_HISTORY_INDEX = SAMPLING_HISTORY_DIR / "historico_sorteios.csv"
SAMPLE_PATHS = (
    ROOT_DIR / "data" / "output" / "amostras" / "amostra_FER.csv",
    ROOT_DIR / "data" / "output" / "amostras" / "amostra_SER.csv",
    ROOT_DIR / "data" / "output" / "amostras" / "amostra_MULTI.csv",
)
SAMPLING_ARTIFACT_PATHS = SAMPLE_PATHS + (
    ROOT_DIR / "data" / "intermediate" / "corpus_padronizado.csv",
    ROOT_DIR / "data" / "intermediate" / "corpus_janela.csv",
    ROOT_DIR / "data" / "intermediate" / "corpus_empirico_quant.csv",
    ROOT_DIR / "data" / "output" / "elegiveis" / "elegiveis_FER.csv",
    ROOT_DIR / "data" / "output" / "elegiveis" / "elegiveis_SER.csv",
    ROOT_DIR / "data" / "output" / "elegiveis" / "elegiveis_MULTI.csv",
    ROOT_DIR / "data" / "output" / "elegiveis" / "excluidos.csv",
    ROOT_DIR / "data" / "output" / "logs" / "registro_sorteio.csv",
    ROOT_DIR / "data" / "output" / "logs" / "registro_sorteio.sha256",
    ROOT_DIR / "data" / "output" / "logs" / "alocacao_sorteio.csv",
    ROOT_DIR / "data" / "output" / "logs" / "alocacao_sorteio.sha256",
    ROOT_DIR / "data" / "output" / "logs" / "log_contingencia.csv",
    ROOT_DIR / "data" / "output" / "logs" / "log_contingencia.sha256",
    ROOT_DIR / "data" / "output" / "prisma" / "prisma_elegibilidade.csv",
    ROOT_DIR / "data" / "output" / "prisma" / "prisma_final.csv",
    ROOT_DIR / "data" / "output" / "prisma" / "prisma_final.sha256",
)
PERSISTED_SEED_PATHS = (
    ARTICLES_PATH,
    ELIGIBILITY_PATH,
    SCENARIOS_PATH,
    SCENARIOS_JSON_PATH,
    AUDIT_PATH,
    AUDIT_JSON_PATH,
    *SAMPLING_ARTIFACT_PATHS,
    SAMPLING_HISTORY_INDEX,
)
_MUTATION_LOCK = threading.RLock()

SCENARIO_COLUMNS = [
    "artigo_id",
    "artigo_titulo",
    "dataset_id",
    "modalidade",
    "tarefa",
    "ambiente_coleta",
    "dependencia_temporal",
    "n_amostras_total",
    "pretreino",
    "modalidades_presentes",
    "modelo_familia",
    "modelo_especifico",
    "protocolo_person_indep",
    "protocolo_cross_dataset",
    "metricas_principais",
    "metrica_principal_valor",
    "augmentations",
    "code_available",
    "weights_available",
    "observacoes",
]

PIPELINE_STEPS = [
    ("Padronizar corpus", "scripts/etapa_01_corpus/01_padronizar_master.py"),
    ("Filtrar elegibilidade", "scripts/etapa_01_corpus/02_filtrar_elegibilidade.py"),
    ("Gerar rastreabilidade do corpus", "scripts/etapa_01_corpus/03_gerar_rastreabilidade_corpus.py"),
    ("Sortear amostra", "scripts/etapa_02_amostragem/01_sortear_amostra.py"),
    ("Gerar rastreabilidade da amostra", "scripts/etapa_02_amostragem/02_gerar_rastreabilidade_amostra.py"),
    ("Calcular consistência", "scripts/etapa_05_consistencia/01_calcular_consistencia.py"),
    ("Calcular escores", "scripts/etapa_06_auditoria/01_calcular_escores.py"),
    ("Analisar sensibilidade", "scripts/etapa_06_auditoria/02_analisar_sensibilidade.py"),
    ("Gerar figuras da auditoria", "scripts/etapa_06_auditoria/03_gerar_figuras_relatorio.py"),
    ("Calcular índice de robustez", "scripts/etapa_08_robustez/01_calcular_indice_robustez.py"),
    ("Gerar figuras de robustez", "scripts/etapa_08_robustez/02_gerar_figuras_robustez.py"),
    ("Validar base do recomendador", "scripts/etapa_09_recomendador/01_validar_base.py"),
    ("Gerar recomendação padrão", "scripts/etapa_09_recomendador/02_recomendar_familias.py"),
    ("Avaliar recomendador (LOSO)", "scripts/etapa_10_avaliacao_loso/01_avaliar_recomendador.py"),
]

ELIGIBILITY_SAMPLE_STEPS = PIPELINE_STEPS[:5]


def _synchronized(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with _MUTATION_LOCK:
            return function(*args, **kwargs)

    return wrapped


def prepare_storage() -> dict[str, str | bool]:
    """Restore the durable snapshot before the interface reads any dataset."""
    return initialize_storage(PERSISTED_SEED_PATHS).as_dict()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def load_articles() -> pd.DataFrame:
    return _read_csv(ARTICLES_PATH)


def load_articles_with_eligibility() -> pd.DataFrame:
    articles = load_articles()
    labels = _read_csv(ELIGIBILITY_PATH)
    labels = labels.loc[:, ~labels.columns.astype(str).str.startswith("Unnamed:")].copy()
    articles["artigo_id"] = articles["artigo_id"].astype(str).str.strip()
    labels["artigo_id"] = labels["artigo_id"].astype(str).str.strip()
    if labels["artigo_id"].duplicated().any():
        raise ValueError("Existem rótulos de elegibilidade duplicados para o mesmo artigo_id.")
    eligibility_columns = [
        "artigo_id",
        "empirico",
        "just_empirico",
        "quantitativo",
        "just_quantitativo",
    ]
    return articles.merge(
        labels[eligibility_columns], on="artigo_id", how="left", sort=False, validate="one_to_one"
    )


def load_scenarios() -> pd.DataFrame:
    return _read_csv(SCENARIOS_PATH)


def recommendation_task_options() -> dict[str, list[str]]:
    scenarios = load_scenarios()
    modality_order = ["FER", "SER", "MULTIMODAL", "HER"]
    task_order = ["multiclasse", "multilabel", "regressao", "deteccao"]
    scenarios["modalidade"] = scenarios["modalidade"].astype(str).str.strip().str.upper()
    scenarios["tarefa"] = scenarios["tarefa"].astype(str).str.strip().str.lower()

    present_modalities = set(scenarios["modalidade"])
    ordered_modalities = [value for value in modality_order if value in present_modalities]
    ordered_modalities.extend(sorted(present_modalities - set(ordered_modalities)))

    options: dict[str, list[str]] = {}
    for modality in ordered_modalities:
        present_tasks = set(scenarios.loc[scenarios["modalidade"].eq(modality), "tarefa"])
        tasks = [value for value in task_order if value in present_tasks]
        tasks.extend(sorted(present_tasks - set(tasks)))
        options[modality] = tasks
    return options


def load_checklist() -> pd.DataFrame:
    return _read_csv(CHECKLIST_PATH)


def load_article_audit(article_id: str) -> pd.DataFrame:
    audit = _read_csv(AUDIT_PATH)
    checklist = load_checklist()[["item_id", "item_nome", "na_permitido"]]
    selected = audit.loc[audit["artigo_id"].astype(str).str.strip().eq(str(article_id).strip())].copy()
    if selected.empty:
        return selected
    selected["pontuacao"] = selected.apply(
        lambda row: "NA" if str(row["NA"]).strip() == "1" else str(row["grau"]).strip(),
        axis=1,
    )
    order = {item_id: index for index, item_id in enumerate(checklist["item_id"])}
    return (
        selected.merge(checklist, on="item_id", how="left")
        .assign(_ordem=lambda frame: frame["item_id"].map(order))
        .sort_values("_ordem", kind="stable")
        .drop(columns="_ordem")
        .reset_index(drop=True)
    )


def load_audited_article_ids() -> set[str]:
    audit = _read_csv(AUDIT_PATH)
    return set(audit["artigo_id"].astype(str).str.strip())


def audit_status_table() -> pd.DataFrame:
    articles = load_articles_with_eligibility().copy()
    audit = _read_csv(AUDIT_PATH)
    counts = (
        audit.groupby("artigo_id", as_index=False)
        .agg(registros_auditoria=("item_id", "size"), itens_unicos=("item_id", "nunique"))
    )
    result = articles.merge(counts, on="artigo_id", how="left")
    result[["registros_auditoria", "itens_unicos"]] = result[
        ["registros_auditoria", "itens_unicos"]
    ].fillna(0).astype(int)
    result["status_auditoria"] = "Não auditado"
    complete = result["registros_auditoria"].eq(16) & result["itens_unicos"].eq(16)
    partial = result["registros_auditoria"].gt(0) & ~complete
    result.loc[complete, "status_auditoria"] = "Auditado"
    result.loc[partial, "status_auditoria"] = "Incompleto"
    return result


def load_sample_selection() -> pd.DataFrame:
    frames = []
    for path in SAMPLE_PATHS:
        sample = _read_csv(path)
        required = {"artigo_id", "tipo"}
        missing = required - set(sample.columns)
        if missing:
            raise ValueError(
                f"{path.name} não contém as colunas obrigatórias: {', '.join(sorted(missing))}."
            )
        frames.append(sample)

    selection = pd.concat(frames, ignore_index=True)
    selection["artigo_id"] = selection["artigo_id"].astype(str).str.strip()
    if selection["artigo_id"].duplicated().any():
        duplicated = selection.loc[
            selection["artigo_id"].duplicated(keep=False), "artigo_id"
        ].unique()
        raise ValueError(
            "Existem artigos duplicados nas amostras: " + ", ".join(sorted(duplicated)) + "."
        )
    return selection


def audit_selection_funnel() -> dict[str, Any]:
    status = audit_status_table()
    status["ano_num"] = pd.to_numeric(status["ano"], errors="coerce")
    status["tarefa"] = status["tarefa"].astype(str).str.strip().str.upper().replace("", "NA")
    status["empirico"] = status["empirico"].fillna("").astype(str).str.strip()
    status["quantitativo"] = status["quantitativo"].fillna("").astype(str).str.strip()

    in_window = status.loc[status["ano_num"].between(ANO_INICIO, ANO_FIM, inclusive="both")].copy()
    empirical = in_window.loc[in_window["empirico"].eq("1")].copy()
    quantitative = empirical.loc[empirical["quantitativo"].eq("1")].copy()
    eligible = quantitative.loc[quantitative["tarefa"].isin(["FER", "SER", "MULTI"])].copy()

    sample = load_sample_selection()
    sample_type = sample.set_index("artigo_id")["tipo"].astype(str).str.strip().str.lower()
    eligible["selecao_amostra"] = eligible["artigo_id"].map(sample_type)
    eligible["selecao_amostra"] = eligible["selecao_amostra"].map(
        {"titular": "Titular", "suplente": "Suplente"}
    ).fillna("Não selecionado")

    selected = eligible.loc[eligible["selecao_amostra"].ne("Não selecionado")].copy()
    audited = selected.loc[selected["status_auditoria"].eq("Auditado")].copy()
    pending = selected.loc[~selected["status_auditoria"].eq("Auditado")].copy()
    audited_ids = set(status.loc[status["status_auditoria"].eq("Auditado"), "artigo_id"])
    selected_ids = set(selected["artigo_id"])

    return {
        "window_start": ANO_INICIO,
        "window_end": ANO_FIM,
        "mapped": status,
        "in_window": in_window,
        "empirical": empirical,
        "quantitative": quantitative,
        "eligible": eligible,
        "selected": selected,
        "audited": audited,
        "pending": pending,
        "incomplete_count": int(selected["status_auditoria"].eq("Incompleto").sum()),
        "not_selected_count": int(eligible["selecao_amostra"].eq("Não selecionado").sum()),
        "titular_count": int(selected["selecao_amostra"].eq("Titular").sum()),
        "reserve_count": int(selected["selecao_amostra"].eq("Suplente").sum()),
        "audited_outside_sample": sorted(audited_ids - selected_ids),
    }


def calculate_article_w(article_id: str) -> float:
    details = load_article_audit(article_id)
    if details.empty:
        return 0.0
    relevant = details.loc[details["item_id"].isin(["PRT", "VZ", "MET", "EXT", "ROB"])].copy()
    applicable = relevant.loc[relevant["NA"].astype(str).str.strip().eq("0")]
    if applicable.empty:
        return 0.0
    return float(pd.to_numeric(applicable["grau"], errors="coerce").fillna(0).div(2).mean())


def data_summary() -> dict[str, int]:
    articles = load_articles()
    scenarios = load_scenarios()
    audited = load_audited_article_ids()
    return {
        "articles": int(articles["artigo_id"].nunique()),
        "audited_articles": len(audited),
        "scenarios": len(scenarios),
        "families": int(scenarios["modelo_familia"].nunique()),
    }


def _list_as_json(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    else:
        items = [str(item).strip() for item in value if str(item).strip()]
    return "NA" if not items else json.dumps(items, ensure_ascii=False)


def _optional_text(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    return text or "NA"


def normalize_scenario(payload: dict[str, Any]) -> dict[str, Any]:
    row = {column: "NA" for column in SCENARIO_COLUMNS}
    row.update(payload)

    for field in ("modalidades_presentes", "metricas_principais", "augmentations"):
        row[field] = _list_as_json(row.get(field))

    for field in (
        "dataset_id",
        "ambiente_coleta",
        "dependencia_temporal",
        "n_amostras_total",
        "modelo_especifico",
        "code_available",
        "weights_available",
        "observacoes",
    ):
        row[field] = _optional_text(row.get(field))

    row["artigo_id"] = str(row.get("artigo_id", "")).strip()
    row["artigo_titulo"] = str(row.get("artigo_titulo", "")).strip()
    row["modalidade"] = str(row.get("modalidade", "")).strip().upper()
    row["tarefa"] = str(row.get("tarefa", "")).strip().lower()
    row["pretreino"] = str(row.get("pretreino", "")).strip().lower()
    row["modelo_familia"] = str(row.get("modelo_familia", "")).strip()
    row["protocolo_person_indep"] = str(row.get("protocolo_person_indep", "")).strip().lower()
    row["protocolo_cross_dataset"] = str(row.get("protocolo_cross_dataset", "")).strip().lower()
    row["metrica_principal_valor"] = float(row["metrica_principal_valor"])
    return row


def validate_scenario(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "artigo_id": "Artigo",
        "artigo_titulo": "Título",
        "modalidade": "Modalidade",
        "tarefa": "Tarefa",
        "pretreino": "Pré-treinamento",
        "modelo_familia": "Família do modelo",
        "protocolo_person_indep": "Protocolo independente por pessoa",
        "protocolo_cross_dataset": "Protocolo entre bases",
    }
    for field, label in required.items():
        if str(row.get(field, "")).strip() in {"", "NA"}:
            errors.append(f"{label} é obrigatório.")

    try:
        metric = float(row.get("metrica_principal_valor"))
        if not 0 <= metric <= 1:
            errors.append("O valor da métrica principal deve estar entre 0 e 1.")
    except (TypeError, ValueError):
        errors.append("Informe um valor numérico para a métrica principal.")

    sample_count = row.get("n_amostras_total")
    if sample_count not in {None, "", "NA", 0, "0"}:
        try:
            if int(sample_count) <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors.append("O total de amostras deve ser um inteiro positivo ou NA.")

    valid_domains = {
        "modalidade": {"FER", "SER", "MULTIMODAL", "HER"},
        "tarefa": {"multiclasse", "multilabel", "regressao", "deteccao"},
        "pretreino": {"sim", "nao"},
        "protocolo_person_indep": {"sim", "nao"},
        "protocolo_cross_dataset": {"sim", "nao"},
    }
    for field, values in valid_domains.items():
        if row.get(field) not in values:
            errors.append(f"Valor inválido em {field}: {row.get(field)!r}.")
    return errors


def _atomic_write_dataframe(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False, dir=path.parent
    ) as handle:
        temp_path = Path(handle.name)
        df.to_csv(handle, index=False)
    temp_path.replace(path)


def _atomic_write_text(text: str, path: Path, suffix: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=suffix, delete=False, dir=path.parent
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(text)
    temp_path.replace(path)


def _write_scenarios_json(df: pd.DataFrame) -> None:
    records = []
    for raw_record in df.to_dict(orient="records"):
        record = dict(raw_record)
        for field in ("modalidades_presentes", "metricas_principais", "augmentations"):
            value = record.get(field)
            if value not in {None, "", "NA"}:
                record[field] = json.loads(str(value))
            else:
                record[field] = "NA"
        metric = record.get("metrica_principal_valor")
        record["metrica_principal_valor"] = "NA" if metric in {None, "", "NA"} else float(metric)
        sample_count = record.get("n_amostras_total")
        record["n_amostras_total"] = "NA" if sample_count in {None, "", "NA"} else int(float(sample_count))
        records.append(record)
    _atomic_write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        SCENARIOS_JSON_PATH,
        ".json",
    )


def _write_audit_json(df: pd.DataFrame) -> None:
    records = []
    for raw_record in df.to_dict(orient="records"):
        record = {column: ("" if value is None else value) for column, value in raw_record.items()}
        record["grau"] = int(record["grau"])
        record["NA"] = int(record["NA"])
        records.append(record)
    _atomic_write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        AUDIT_JSON_PATH,
        ".json",
    )


def next_article_id(
    articles: pd.DataFrame | None = None,
    labels: pd.DataFrame | None = None,
) -> str:
    articles = load_articles() if articles is None else articles
    labels = _read_csv(ELIGIBILITY_PATH) if labels is None else labels
    known_ids = pd.concat(
        [articles["artigo_id"], labels["artigo_id"]],
        ignore_index=True,
    )
    numbers = pd.to_numeric(
        known_ids.astype(str).str.extract(r"ID_(\d+)", expand=False),
        errors="coerce",
    ).dropna()
    next_number = 1 if numbers.empty else int(numbers.max()) + 1
    return f"ID_{next_number:02d}"


def audit_template(article_id: str | None = None) -> pd.DataFrame:
    checklist = load_checklist()
    template = checklist[["item_id", "item_nome", "na_permitido"]].assign(
        pontuacao="0",
        evidencia="",
        justificativa_NA="",
        observacoes="",
    )
    if article_id is None:
        return template

    existing = load_article_audit(article_id)
    if existing.empty:
        return template
    values = existing[
        ["item_id", "pontuacao", "evidencia", "justificativa_NA", "observacoes"]
    ].drop_duplicates("item_id", keep="last")
    return (
        template.drop(columns=["pontuacao", "evidencia", "justificativa_NA", "observacoes"])
        .merge(values, on="item_id", how="left")
        .fillna(
            {
                "pontuacao": "0",
                "evidencia": "",
                "justificativa_NA": "",
                "observacoes": "",
            }
        )
    )


def _validate_audit_values(values: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    checklist = load_checklist()
    expected = set(checklist["item_id"])
    received = set(values.get("item_id", pd.Series(dtype=str)).astype(str))
    if received != expected or len(values) != len(checklist):
        return ["A auditoria deve conter exatamente os 16 itens do checklist."]

    na_allowed = checklist.set_index("item_id")["na_permitido"].to_dict()
    for _, row in values.iterrows():
        item_id = str(row["item_id"]).strip()
        score = str(row.get("pontuacao", "")).strip().upper()
        evidence = str(row.get("evidencia", "")).strip()
        justification = str(row.get("justificativa_NA", "")).strip()
        if score not in {"0", "1", "2", "NA"}:
            errors.append(f"{item_id}: pontuação deve ser 0, 1, 2 ou NA.")
        elif score == "NA":
            if str(na_allowed.get(item_id, "0")) != "1":
                errors.append(f"{item_id}: o checklist não permite NA para este item.")
            if not justification:
                errors.append(f"{item_id}: informe a justificativa para NA.")
        elif not evidence:
            errors.append(f"{item_id}: informe a evidência que sustenta a pontuação.")
    return errors


def _audit_rows(article_id: str, stratum: str, values: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, value in values.iterrows():
        score = str(value["pontuacao"]).strip().upper()
        is_na = score == "NA"
        rows.append(
            {
                "artigo_id": article_id,
                "estrato": stratum,
                "item_id": str(value["item_id"]).strip(),
                "grau": 0 if is_na else int(score),
                "NA": 1 if is_na else 0,
                "justificativa_NA": str(value.get("justificativa_NA", "")).strip() if is_na else "",
                "evidencia": str(value.get("evidencia", "")).strip() or ("--" if is_na else ""),
                "observacoes": str(value.get("observacoes", "")).strip(),
            }
        )
    return pd.DataFrame(rows)


@_synchronized
def save_article_audit(article_id: str, audit_values: pd.DataFrame) -> dict[str, Any]:
    articles = load_articles()
    selected = articles.loc[articles["artigo_id"].astype(str).str.strip().eq(str(article_id).strip())]
    if selected.empty:
        raise ValueError("O artigo selecionado não existe na base mestre.")
    stratum = str(selected.iloc[0]["tarefa"]).strip().upper()
    if stratum not in {"FER", "SER", "MULTI"}:
        raise ValueError("Defina o estrato FER, SER ou MULTI antes de auditar este artigo.")

    errors = _validate_audit_values(audit_values)
    if errors:
        raise ValueError("\n".join(errors))

    audit = _read_csv(AUDIT_PATH)
    remaining = audit.loc[~audit["artigo_id"].astype(str).str.strip().eq(str(article_id).strip())]
    new_rows = _audit_rows(str(article_id).strip(), stratum, audit_values)
    updated = pd.concat([remaining, new_rows[audit.columns]], ignore_index=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups: dict[Path, Path] = {}
    for path in (AUDIT_PATH, AUDIT_JSON_PATH):
        backup = BACKUP_DIR / f"{path.stem}-{timestamp}{path.suffix}"
        shutil.copy2(path, backup)
        backups[path] = backup

    try:
        _atomic_write_dataframe(updated, AUDIT_PATH)
        _write_audit_json(updated)
        persist_files((AUDIT_PATH, AUDIT_JSON_PATH))
    except Exception:
        for original, backup in backups.items():
            shutil.copy2(backup, original)
        raise

    return {
        "article_id": str(article_id).strip(),
        "audit_rows": len(new_rows),
        "W": calculate_article_w(article_id),
        "backups": [str(path) for path in backups.values()],
    }


@_synchronized
def add_article(payload: dict[str, Any], audit_values: pd.DataFrame | None = None) -> dict[str, Any]:
    articles = load_articles()
    labels = _read_csv(ELIGIBILITY_PATH)
    labels = labels.loc[:, ~labels.columns.astype(str).str.startswith("Unnamed:")].copy()
    audit = _read_csv(AUDIT_PATH)

    title = str(payload.get("titulo", "")).strip()
    venue = str(payload.get("venue", "")).strip()
    doi = str(payload.get("doi", "")).strip()
    stratum = str(payload.get("tarefa", "NA")).strip().upper() or "NA"
    is_audited = audit_values is not None
    empirical = payload.get("empirico")
    quantitative = payload.get("quantitativo")
    errors: list[str] = []

    if not title:
        errors.append("O título do artigo é obrigatório.")
    try:
        year = int(payload.get("ano"))
        if not 1900 <= year <= datetime.now().year + 1:
            errors.append("Informe um ano válido para o artigo.")
    except (TypeError, ValueError):
        year = 0
        errors.append("O ano do artigo é obrigatório.")
    if stratum not in {"FER", "SER", "MULTI", "NA"}:
        errors.append("O estrato deve ser FER, SER, MULTI ou NA.")
    if not isinstance(empirical, bool):
        errors.append("Informe explicitamente se o artigo apresenta investigação empírica.")
    if not isinstance(quantitative, bool):
        errors.append("Informe explicitamente se o artigo apresenta resultados quantitativos.")
    if is_audited and stratum == "NA":
        errors.append("Um artigo auditado deve pertencer aos estratos FER, SER ou MULTI.")
    if title and articles["titulo"].astype(str).str.strip().str.casefold().eq(title.casefold()).any():
        errors.append("Já existe um artigo com este título na base mestre.")
    if doi and articles["doi"].astype(str).str.strip().str.casefold().eq(doi.casefold()).any():
        errors.append("Já existe um artigo com este DOI na base mestre.")
    if is_audited:
        errors.extend(_validate_audit_values(audit_values))
    if errors:
        raise ValueError("\n".join(errors))

    article_id = next_article_id(articles, labels)
    article_row = {
        "artigo_id": article_id,
        "titulo": title,
        "ano": str(year),
        "venue": venue,
        "tarefa": "" if stratum == "NA" else stratum,
        "doi": doi,
    }
    updated_articles = pd.concat(
        [articles, pd.DataFrame([article_row], columns=articles.columns)],
        ignore_index=True,
    )

    label_row = {column: "" for column in labels.columns}
    label_row.update(
        {
            "artigo_id": article_id,
            "ano": str(year),
            "tarefa": stratum,
            "titulo": title,
            "empirico": "1" if empirical else "0",
            "just_empirico": str(payload.get("just_empirico", "")).strip(),
            "quantitativo": "1" if quantitative else "0",
            "just_quantitativo": str(payload.get("just_quantitativo", "")).strip(),
        }
    )
    updated_labels = pd.concat(
        [labels, pd.DataFrame([label_row], columns=labels.columns)],
        ignore_index=True,
    )

    updated_audit = audit
    audit_rows = 0
    if is_audited:
        new_audit = _audit_rows(article_id, stratum, audit_values)
        audit_rows = len(new_audit)
        updated_audit = pd.concat([audit, new_audit[audit.columns]], ignore_index=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    paths = [ARTICLES_PATH, ELIGIBILITY_PATH]
    if is_audited:
        paths.extend([AUDIT_PATH, AUDIT_JSON_PATH])
    backups: dict[Path, Path] = {}
    for path in paths:
        backup = BACKUP_DIR / f"{path.stem}-{timestamp}{path.suffix}"
        shutil.copy2(path, backup)
        backups[path] = backup

    try:
        _atomic_write_dataframe(updated_articles, ARTICLES_PATH)
        _atomic_write_dataframe(updated_labels, ELIGIBILITY_PATH)
        if is_audited:
            _atomic_write_dataframe(updated_audit, AUDIT_PATH)
            _write_audit_json(updated_audit)
        persist_files(paths)
    except Exception:
        for original, backup in backups.items():
            shutil.copy2(backup, original)
        raise

    return {
        "article_id": article_id,
        "audited": is_audited,
        "audit_rows": audit_rows,
        "article_count": len(updated_articles),
        "backups": [str(path) for path in backups.values()],
    }


@_synchronized
def add_scenario(payload: dict[str, Any]) -> dict[str, Any]:
    row = normalize_scenario(payload)
    errors = validate_scenario(row)
    if errors:
        raise ValueError("\n".join(errors))

    articles = load_articles()
    known = articles.loc[articles["artigo_id"].eq(row["artigo_id"])]
    if known.empty:
        raise ValueError("O artigo selecionado não existe no mapeamento mestre.")

    row["artigo_titulo"] = known.iloc[0]["titulo"]
    scenarios = load_scenarios()
    new_row = pd.DataFrame([[row[column] for column in SCENARIO_COLUMNS]], columns=SCENARIO_COLUMNS)

    duplicate_columns = [
        "artigo_id",
        "dataset_id",
        "modelo_familia",
        "modelo_especifico",
        "metrica_principal_valor",
    ]
    comparison = scenarios[duplicate_columns].astype(str).apply(lambda col: col.str.strip())
    candidate = new_row.iloc[0][duplicate_columns].astype(str).str.strip()
    if comparison.eq(candidate, axis="columns").all(axis=1).any():
        raise ValueError("Este cenário já parece existir na base. Nenhuma linha foi adicionada.")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backups: dict[Path, Path] = {}
    for path in (SCENARIOS_PATH, SCENARIOS_JSON_PATH):
        if path.exists():
            backup = BACKUP_DIR / f"{path.stem}-{timestamp}{path.suffix}"
            shutil.copy2(path, backup)
            backups[path] = backup

    updated = pd.concat([scenarios[SCENARIO_COLUMNS], new_row], ignore_index=True)
    try:
        _atomic_write_dataframe(updated, SCENARIOS_PATH)
        _write_scenarios_json(updated)
        persist_files((SCENARIOS_PATH, SCENARIOS_JSON_PATH))
    except Exception:
        for original, backup in backups.items():
            shutil.copy2(backup, original)
        raise
    return {"row": row, "backups": list(backups.values()), "rows": len(updated)}


@_synchronized
def rebuild_recommender_base() -> dict[str, Any]:
    robustness = importlib.import_module(
        "scripts.etapa_08_robustez.01_calcular_indice_robustez"
    )
    validator = importlib.import_module("scripts.etapa_09_recomendador.01_validar_base")
    robustness.executar()
    return validator.validar_base()


@_synchronized
def recommend(query: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    modality = str(query.get("modalidade", "")).strip().upper()
    task = str(query.get("tarefa", "")).strip().lower()
    task_options = recommendation_task_options()
    if modality not in task_options:
        raise ValueError(f"A modalidade {modality or '(vazia)'} não está disponível na base de cenários.")
    if task not in task_options[modality]:
        available = ", ".join(task_options[modality])
        raise ValueError(
            f"A tarefa {task or '(vazia)'} não está disponível para {modality}. "
            f"Opções disponíveis: {available}."
        )

    recommender = importlib.import_module("scripts.etapa_09_recomendador.02_recomendar_familias")
    log = recommender.recomendar_familias(query)
    ranking = _read_csv(RANKING_PATH)
    for column in ("ordem", "R_medio", "ic95_inf", "ic95_sup", "largura_ic95", "n_artigos", "n_experimentos"):
        if column in ranking:
            ranking[column] = pd.to_numeric(ranking[column], errors="coerce")
    return log, ranking


def sampling_configuration() -> dict[str, int]:
    return {
        "target_total": int(N_ALVO_TOTAL),
        "minimum_per_stratum": int(MIN_POR_ESTRATO),
        "reserves_per_stratum": int(N_SUPLENTES),
        "seed": int(RNG_SEED),
    }


def sampling_allocation_preview(
    eligible_counts: dict[str, int],
    target_total: int,
    minimum_per_stratum: int,
) -> dict[str, Any]:
    strata = ("FER", "SER", "MULTI")
    counts = {stratum: int(eligible_counts.get(stratum, 0)) for stratum in strata}
    target_total = int(target_total)
    minimum_per_stratum = int(minimum_per_stratum)

    if target_total <= 0:
        raise ValueError("O total de titulares deve ser maior que zero.")
    if minimum_per_stratum < 0:
        raise ValueError("O mínimo por estrato não pode ser negativo.")
    unavailable = [
        stratum for stratum in strata if counts[stratum] < minimum_per_stratum
    ]
    if unavailable:
        details = ", ".join(f"{stratum} ({counts[stratum]})" for stratum in unavailable)
        raise ValueError(
            "O mínimo informado excede a quantidade elegível em: " + details + "."
        )
    if minimum_per_stratum * len(strata) > target_total:
        raise ValueError(
            "O total de titulares deve ser pelo menos três vezes o mínimo por estrato."
        )
    total_eligible = sum(counts.values())
    if target_total > total_eligible:
        raise ValueError(
            f"O total de titulares não pode exceder os {total_eligible} artigos elegíveis."
        )

    allocation = {stratum: minimum_per_stratum for stratum in strata}
    remaining = target_total - sum(allocation.values())
    capacity = {stratum: counts[stratum] - allocation[stratum] for stratum in strata}
    capacity_total = sum(capacity.values())
    if remaining:
        quotas = {
            stratum: (capacity[stratum] / capacity_total) * remaining
            if capacity_total
            else 0
            for stratum in strata
        }
        floors = {stratum: int(quotas[stratum] // 1) for stratum in strata}
        allocation = {
            stratum: allocation[stratum] + floors[stratum] for stratum in strata
        }
        remainder = remaining - sum(floors.values())
        order = sorted(
            strata,
            key=lambda stratum: (
                quotas[stratum] - floors[stratum],
                capacity[stratum],
            ),
            reverse=True,
        )
        for index in range(remainder):
            stratum = order[index % len(order)]
            if allocation[stratum] < counts[stratum]:
                allocation[stratum] += 1
            else:
                for candidate in order:
                    if allocation[candidate] < counts[candidate]:
                        allocation[candidate] += 1
                        break

    reserves = {
        stratum: min(N_SUPLENTES, counts[stratum] - allocation[stratum])
        for stratum in strata
    }
    return {
        "eligible": counts,
        "titulars": allocation,
        "reserves": reserves,
        "target_total": target_total,
        "minimum_per_stratum": minimum_per_stratum,
        "selected_total": target_total + sum(reserves.values()),
        "not_selected_total": total_eligible - target_total - sum(reserves.values()),
    }


def _copy_sampling_artifacts(destination: Path) -> list[str]:
    copied: list[str] = []
    for source in SAMPLING_ARTIFACT_PATHS:
        if not source.exists():
            continue
        relative_path = source.relative_to(ROOT_DIR)
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(relative_path.as_posix())
    return copied


def _restore_sampling_artifacts(snapshot: Path, copied_paths: list[str]) -> None:
    copied_set = set(copied_paths)
    for target in SAMPLING_ARTIFACT_PATHS:
        relative_path = target.relative_to(ROOT_DIR).as_posix()
        source = snapshot / Path(relative_path)
        if relative_path in copied_set and source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif target.exists():
            target.unlink()


def _append_sampling_history(metadata: dict[str, Any]) -> None:
    row = pd.DataFrame(
        [
            {
                "versao": metadata["version_id"],
                "gerado_em": metadata["generated_at"],
                "n_alvo_total": metadata["target_total"],
                "min_por_estrato": metadata["minimum_per_stratum"],
                "n_suplentes_por_estrato": metadata["reserves_per_stratum"],
                "seed": metadata["seed"],
                "elegiveis": sum(metadata["eligible"].values()),
                "titulares": sum(metadata["titulars"].values()),
                "suplentes": sum(metadata["reserves"].values()),
                "selecionados": metadata["selected_total"],
                "nao_selecionados": metadata["not_selected_total"],
                "diretorio_versao": metadata["version_directory"],
            }
        ]
    )
    if SAMPLING_HISTORY_INDEX.exists():
        history = _read_csv(SAMPLING_HISTORY_INDEX)
        row = row.reindex(columns=history.columns)
        history = pd.concat([history, row], ignore_index=True)
    else:
        history = row
    _atomic_write_dataframe(history, SAMPLING_HISTORY_INDEX)


def _run_steps(
    steps: list[tuple[str, str]],
    environment_overrides: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    environment = os.environ.copy()
    current_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = str(ROOT_DIR) + (
        os.pathsep + current_pythonpath if current_pythonpath else ""
    )
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    if environment_overrides:
        environment.update(environment_overrides)
    for label, relative_path in steps:
        process = subprocess.run(
            [sys.executable, str(ROOT_DIR / relative_path)],
            cwd=ROOT_DIR,
            env=environment,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        results.append(
            {
                "label": label,
                "path": relative_path,
                "ok": process.returncode == 0,
                "output": (process.stdout + "\n" + process.stderr).strip(),
            }
        )
        if process.returncode != 0:
            break
    return results


@_synchronized
def generate_audit_sample(
    target_total: int = N_ALVO_TOTAL,
    minimum_per_stratum: int = MIN_POR_ESTRATO,
) -> dict[str, Any]:
    """Rebuild eligibility outputs and create a versioned, reproducible sample."""
    funnel = audit_selection_funnel()
    eligible = funnel["eligible"]
    eligible_counts = {
        stratum: int(eligible["tarefa"].astype(str).str.upper().eq(stratum).sum())
        for stratum in ("FER", "SER", "MULTI")
    }
    preview = sampling_allocation_preview(
        eligible_counts,
        target_total,
        minimum_per_stratum,
    )

    version_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    version_directory = SAMPLING_HISTORY_DIR / version_id
    previous_snapshot = version_directory / "anterior"
    generated_snapshot = version_directory / "gerada"
    copied_paths = _copy_sampling_artifacts(previous_snapshot)

    try:
        results = _run_steps(
            ELIGIBILITY_SAMPLE_STEPS,
            {
                "CSE_N_ALVO_TOTAL": str(int(target_total)),
                "CSE_MIN_POR_ESTRATO": str(int(minimum_per_stratum)),
            },
        )
    except Exception as exc:
        results = [
            {
                "label": "Executar elegibilidade e sorteio",
                "path": "",
                "ok": False,
                "output": str(exc),
            }
        ]
    succeeded = bool(results) and all(result["ok"] for result in results)
    generated_at = datetime.now().isoformat(timespec="seconds")
    metadata = {
        "version_id": version_id,
        "generated_at": generated_at,
        "status": "concluido" if succeeded else "falhou",
        "target_total": int(target_total),
        "minimum_per_stratum": int(minimum_per_stratum),
        "reserves_per_stratum": int(N_SUPLENTES),
        "seed": int(RNG_SEED),
        "eligible": preview["eligible"],
        "titulars": preview["titulars"],
        "reserves": preview["reserves"],
        "selected_total": preview["selected_total"],
        "not_selected_total": preview["not_selected_total"],
        "version_directory": version_directory.relative_to(ROOT_DIR).as_posix(),
        "previous_artifacts": copied_paths,
    }

    if succeeded:
        try:
            metadata["generated_artifacts"] = _copy_sampling_artifacts(generated_snapshot)
            _append_sampling_history(metadata)
        except Exception as exc:
            succeeded = False
            metadata["status"] = "falhou"
            results.append(
                {
                    "label": "Versionar amostra",
                    "path": "",
                    "ok": False,
                    "output": str(exc),
                }
            )

    if not succeeded:
        _restore_sampling_artifacts(previous_snapshot, copied_paths)

    _atomic_write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        version_directory / "metadados.json",
        ".json",
    )
    if succeeded:
        try:
            persist_files((*SAMPLING_ARTIFACT_PATHS, SAMPLING_HISTORY_INDEX))
            persist_tree(version_directory)
        except Exception as exc:
            succeeded = False
            metadata["status"] = "falhou"
            results.append(
                {
                    "label": "Persistir amostra",
                    "path": "",
                    "ok": False,
                    "output": str(exc),
                }
            )
            _restore_sampling_artifacts(previous_snapshot, copied_paths)
            _atomic_write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                version_directory / "metadados.json",
                ".json",
            )
    return {
        "results": results,
        "version_id": version_id,
        "succeeded": succeeded,
        "preview": preview,
        "version_directory": str(version_directory),
    }


@_synchronized
def run_pipeline() -> list[dict[str, Any]]:
    results = _run_steps(PIPELINE_STEPS)
    if results and all(result["ok"] for result in results):
        persist_files(PERSISTED_SEED_PATHS)
    return results
