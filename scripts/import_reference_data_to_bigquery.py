from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

import pandas as pd
from deploy_frameworks.bigquery import bigquery, insert


DEFAULT_DATASET = "jds-gcp-dev-dl-odm-analytics.RangeControlPlatform"

STORE_SOURCE_COLUMNS = {
    "No.": "branch_id",
    "Name": "branch_name",
    "Fascia": "fascia",
    "Status": "status",
    "Sq. Ft.": "square_footage",
    "2026": "budget_2026",
    "Grade": "store_grade",
    "Region": "region",
    "Fit type": "fit_type",
    "INDOOR TENT FIELD SQ FT": "indoor_tent_field_sqft",
    "OUTDOOR TENT FIELD SQ FT": "outdoor_tent_field_sqft",
}

GRADING_SOURCE_COLUMNS = {
    "Department": "department_name",
    "Grade": "grade",
    "Linear Meterage": "allowed_linear_meterage",
}

STAND_SOURCE_COLUMNS = {
    "Stand ID": "stand_id",
    "Stand Name": "stand_name",
    "Type": "stand_type",
    "Height": "stand_height",
    "Arms": "arms",
    "Sqm": "sqm",
}


def normalize_text(value: object, uppercase: bool = False) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.upper() if uppercase else text


def normalize_branch_id(value: object) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    if text.endswith(".0"):
        text = text[:-2]
    return text


def parse_int(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"[^0-9\-]", "", text)
    if not cleaned:
        return None
    return int(cleaned)


def parse_decimal(value: object) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def drop_blank_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(how="all").copy()


def prepare_department_grade_allocations(workbook_path: Path) -> pd.DataFrame:
    df = pd.read_excel(
        workbook_path,
        sheet_name="Grading Model",
        engine="openpyxl",
        dtype=object,
    )
    df = drop_blank_rows(df)
    df = df.loc[:, list(GRADING_SOURCE_COLUMNS.keys())].rename(columns=GRADING_SOURCE_COLUMNS)

    df["department_name"] = df["department_name"].apply(lambda v: normalize_text(v, uppercase=True))
    df["grade"] = df["grade"].apply(lambda v: normalize_text(v, uppercase=True))
    df["allowed_linear_meterage"] = df["allowed_linear_meterage"].apply(parse_decimal)

    df = df.dropna(subset=["department_name", "grade", "allowed_linear_meterage"])
    df = df.drop_duplicates(subset=["department_name", "grade"], keep="last")
    return df.reset_index(drop=True)


def prepare_stand_library(workbook_path: Path) -> pd.DataFrame:
    df = pd.read_excel(
        workbook_path,
        sheet_name="Stand Library",
        engine="openpyxl",
        dtype=object,
    )
    df = drop_blank_rows(df)
    df = df.loc[:, list(STAND_SOURCE_COLUMNS.keys())].rename(columns=STAND_SOURCE_COLUMNS)

    df["stand_id"] = df["stand_id"].apply(normalize_text)
    df["stand_name"] = df["stand_name"].apply(normalize_text)
    df["stand_type"] = df["stand_type"].apply(normalize_text)
    df["stand_height"] = df["stand_height"].apply(normalize_text)
    df["arms"] = df["arms"].apply(parse_int)
    df["sqm"] = df["sqm"].apply(parse_decimal)

    df = df.dropna(subset=["stand_id", "stand_name", "sqm"])
    df = df.drop_duplicates(subset=["stand_id"], keep="last")
    return df.reset_index(drop=True)


def prepare_stores(workbook_path: Path) -> pd.DataFrame:
    df = pd.read_excel(
        workbook_path,
        sheet_name="STORE_DEPT_GRADES",
        engine="openpyxl",
        header=1,
        dtype=object,
    )
    df = drop_blank_rows(df)

    normalized_source_columns = {str(col).strip(): col for col in df.columns}
    required_columns = {}
    for source_name, destination_name in STORE_SOURCE_COLUMNS.items():
        actual_column = normalized_source_columns.get(source_name)
        if actual_column is None:
            raise ValueError(
                f"Expected source column {source_name!r} was not found in STORE_DEPT_GRADES."
            )
        required_columns[actual_column] = destination_name

    df = df.loc[:, list(required_columns.keys())].rename(columns=required_columns)

    df["branch_id"] = df["branch_id"].apply(normalize_branch_id)
    df["branch_name"] = df["branch_name"].apply(normalize_text)
    df["fascia"] = df["fascia"].apply(lambda v: normalize_text(v, uppercase=True))
    df["status"] = df["status"].apply(normalize_text)
    df["square_footage"] = df["square_footage"].apply(parse_int)
    df["budget_2026"] = df["budget_2026"].apply(parse_decimal)
    df["store_grade"] = df["store_grade"].apply(lambda v: normalize_text(v, uppercase=True))
    df["region"] = df["region"].apply(normalize_text)
    df["fit_type"] = df["fit_type"].apply(normalize_text)
    df["indoor_tent_field_sqft"] = df["indoor_tent_field_sqft"].apply(parse_int)
    df["outdoor_tent_field_sqft"] = df["outdoor_tent_field_sqft"].apply(parse_int)

    df = df.dropna(subset=["branch_id"])
    df = df.drop_duplicates(subset=["branch_id"], keep="last")
    return df.reset_index(drop=True)


def export_csv(df: pd.DataFrame, output_dir: Path, table_name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{table_name}.csv"
    csv_df = df.copy()
    csv_df = csv_df.where(pd.notnull(csv_df), None)
    csv_df.to_csv(output_path, index=False)
    return output_path


def split_dataset_path(dataset: str) -> tuple[str, str]:
    parts = dataset.split(".")
    if len(parts) != 2:
        raise ValueError(
            f"Dataset must be in 'project.dataset' form. Received: {dataset}"
        )
    return parts[0], parts[1]


def load_dataframe_to_bigquery(df: pd.DataFrame, dataset: str, table_name: str, truncate: bool) -> None:
    project, dataset_name = split_dataset_path(dataset)
    full_table_name = f"{project}.{dataset_name}.{table_name}"

    if truncate:
        bigquery(f"TRUNCATE TABLE `{full_table_name}`", dataset_replacements={})

    insert(
        df_to_insert=df,
        table_name=f"{dataset_name}.{table_name}",
        project=project,
    )


def process_and_output(
    workbook_path: Path,
    table_name: str,
    dataset: str,
    mode: str,
    output_dir: Path | None,
    truncate: bool,
) -> pd.DataFrame:
    if table_name == "department_grade_allocations":
        df = prepare_department_grade_allocations(workbook_path)
    elif table_name == "stand_library":
        df = prepare_stand_library(workbook_path)
    elif table_name == "stores":
        df = prepare_stores(workbook_path)
    else:
        raise ValueError(f"Unsupported table name: {table_name}")

    if mode == "csv":
        if output_dir is None:
            raise ValueError("--output-dir is required when mode=csv")
        output_path = export_csv(df, output_dir, table_name)
        print(f"[csv] Wrote {len(df)} row(s) to {output_path}")
    elif mode == "bigquery":
        table_id = f"{dataset}.{table_name}"
        load_dataframe_to_bigquery(df, dataset, table_name, truncate=truncate)
        print(f"[bigquery] Loaded {len(df)} row(s) into {table_id}")
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return df


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Clean and import Excel reference data into BigQuery tables or CSV files."
    )
    parser.add_argument(
        "--mode",
        choices=["bigquery", "csv"],
        required=True,
        help="Load directly to BigQuery or export cleaned CSV files.",
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_DATASET,
        help="BigQuery dataset path in the form project.dataset.",
    )
    parser.add_argument(
        "--stores-workbook",
        type=Path,
        required=True,
        help="Path to Store Grade and Budget 2026.xlsx",
    )
    parser.add_argument(
        "--grading-workbook",
        type=Path,
        required=True,
        help="Path to grading_model.xlsx",
    )
    parser.add_argument(
        "--stands-workbook",
        type=Path,
        required=True,
        help="Path to stand_library.xlsx",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for cleaned CSV exports when mode=csv.",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Replace existing rows in the target BigQuery table instead of appending.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    process_and_output(
        workbook_path=args.grading_workbook,
        table_name="department_grade_allocations",
        dataset=args.dataset,
        mode=args.mode,
        output_dir=args.output_dir,
        truncate=args.truncate,
    )
    process_and_output(
        workbook_path=args.stands_workbook,
        table_name="stand_library",
        dataset=args.dataset,
        mode=args.mode,
        output_dir=args.output_dir,
        truncate=args.truncate,
    )
    process_and_output(
        workbook_path=args.stores_workbook,
        table_name="stores",
        dataset=args.dataset,
        mode=args.mode,
        output_dir=args.output_dir,
        truncate=args.truncate,
    )


if __name__ == "__main__":
    main()
