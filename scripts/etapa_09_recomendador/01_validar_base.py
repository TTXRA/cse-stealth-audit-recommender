import json

import numpy as np
import pandas as pd

from scripts.utils.common import (
    as_text,
    is_missing,
    normalize_columns,
    normalizar_dominio,
    normalizar_lista,
    read_csv,
    remove_unnamed_columns,
    require_cols,
    write_sha256,
)
from scripts.utils.config import (
    ARQUIVO_ISSUES_ROBUSTEZ,
    ARQUIVO_SAIDA_ROBUSTEZ,
    ARQUIVO_SAIDA_ROBUSTEZ_CLEAN,
    COLUNAS_LISTA,
    COLUNAS_NUMERICAS,
    COLUNAS_OBRIGATORIAS,
    DOMINIOS,
)


def validar_base():
    df = read_csv(ARQUIVO_SAIDA_ROBUSTEZ)
    df = normalize_columns(df).rename(columns={"r": "R"})
    df = remove_unnamed_columns(df)

    require_cols(
        df,
        sorted(COLUNAS_OBRIGATORIAS | COLUNAS_NUMERICAS | COLUNAS_LISTA | set(DOMINIOS)),
        ARQUIVO_SAIDA_ROBUSTEZ.name,
    )

    for coluna in COLUNAS_NUMERICAS:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    for coluna in df.columns:
        if coluna in COLUNAS_NUMERICAS:
            continue
        if coluna in COLUNAS_LISTA:
            df[coluna] = df[coluna].map(normalizar_lista)
        elif coluna in DOMINIOS:
            df[coluna] = df[coluna].map(lambda value, c=coluna: normalizar_dominio(c, value))
        else:
            df[coluna] = df[coluna].map(as_text)

    issues = []
    valid_mask = pd.Series(True, index=df.index, dtype=bool)

    def add_issue(row_index, coluna, tipo, value):
        issues.append(
            {
                "row_index": int(row_index),
                "severity": "critical",
                "column": coluna,
                "issue_type": tipo,
                "value": None if is_missing(value) else str(value),
            }
        )

    for row_index, row in df.iterrows():
        valido = True

        for coluna in sorted(COLUNAS_OBRIGATORIAS):
            value = row[coluna]
            invalido = pd.isna(value) if coluna in COLUNAS_NUMERICAS else is_missing(value)

            if invalido:
                add_issue(row_index, coluna, "required_missing", value)
                valido = False

        for coluna, valores_validos in DOMINIOS.items():
            value = row[coluna]

            if not is_missing(value) and value not in valores_validos:
                add_issue(row_index, coluna, "invalid_domain", value)
                valido = False

        for coluna in sorted(COLUNAS_LISTA):
            value = row[coluna]

            if is_missing(value):
                continue

            try:
                if not isinstance(json.loads(value), list):
                    raise ValueError
            except (TypeError, ValueError, json.JSONDecodeError):
                add_issue(row_index, coluna, "invalid_list", value)
                valido = False

        for coluna in sorted(COLUNAS_NUMERICAS):
            value = row[coluna]

            if pd.isna(value) or np.isinf(value):
                add_issue(row_index, coluna, "invalid_numeric", value)
                valido = False
                continue

            if not 0.0 <= float(value) <= 1.0:
                add_issue(row_index, coluna, "out_of_range_0_1", value)
                valido = False

        valid_mask.at[row_index] = valido

    clean_df = df.loc[valid_mask].copy()
    issues_df = pd.DataFrame(issues)

    ARQUIVO_SAIDA_ROBUSTEZ_CLEAN.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(ARQUIVO_SAIDA_ROBUSTEZ_CLEAN, index=False)
    write_sha256(ARQUIVO_SAIDA_ROBUSTEZ_CLEAN)

    if issues_df.empty:
        if ARQUIVO_ISSUES_ROBUSTEZ.exists():
            ARQUIVO_ISSUES_ROBUSTEZ.unlink()

        sha_path = ARQUIVO_ISSUES_ROBUSTEZ.with_suffix(".sha256")
        if sha_path.exists():
            sha_path.unlink()

        issues_output_path = None
    else:
        ARQUIVO_ISSUES_ROBUSTEZ.parent.mkdir(parents=True, exist_ok=True)
        issues_df.to_csv(ARQUIVO_ISSUES_ROBUSTEZ, index=False)
        write_sha256(ARQUIVO_ISSUES_ROBUSTEZ)
        issues_output_path = str(ARQUIVO_ISSUES_ROBUSTEZ)

    return {
        "rows_input": int(len(df)),
        "rows_valid": int(len(clean_df)),
        "rows_invalid": int((~valid_mask).sum()),
        "issues_total": int(len(issues_df)),
        "input_path": str(ARQUIVO_SAIDA_ROBUSTEZ),
        "output_clean_path": str(ARQUIVO_SAIDA_ROBUSTEZ_CLEAN),
        "output_issues_path": issues_output_path,
        "issues_file_generated": not issues_df.empty,
    }


def executar():
    print(json.dumps(validar_base(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()