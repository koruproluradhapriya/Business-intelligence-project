from __future__ import annotations

import os
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any

import numpy as np
import pandas as pd


SUPPORTED_EXTENSIONS = {"csv", "xlsx", "xls", "json", "tsv", "parquet"}

SEMANTIC_ALIASES = {
    "revenue": ["revenue", "sales", "amount", "income", "turnover", "total_sales", "gross_sales", "gmv"],
    "quantity": ["quantity", "qty", "units", "items_sold", "volume", "count", "unit_count"],
    "date": ["date", "order_date", "created_at", "timestamp", "period", "month", "day", "transaction_date"],
    "product": ["product", "item", "product_name", "sku", "product_id", "item_name"],
    "category": ["category", "segment", "department", "group", "class", "family"],
    "customer": ["customer", "customer_name", "client", "account", "buyer", "subscriber"],
    "profit": ["profit", "margin", "gross_profit", "net_profit", "operating_profit"],
    "cost": ["cost", "expense", "cogs", "unit_cost", "spend"],
    "price": ["price", "unit_price", "selling_price", "rate", "list_price"],
    "inventory": ["inventory", "stock", "stock_level", "quantity_on_hand", "on_hand", "available_stock"],
    "region": ["region", "territory", "country", "state", "city", "market", "location"],
    "discount": ["discount", "discount_rate", "markdown", "promotion"],
}

NULL_LIKE = {"", "na", "n/a", "null", "none", "nil", "nan", "-", "--", "missing", "unknown"}


def serialize_value(value: Any):
    if pd.isna(value) if not isinstance(value, (list, dict)) else False:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _normalize_name(name: str, used: Counter) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "_", str(name).strip().lower()).strip("_") or "column"
    count = used[base]
    used[base] += 1
    return base if count == 0 else f"{base}_{count + 1}"


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def _infer_semantic_label(column_name: str) -> tuple[str | None, float, list[str]]:
    best_label = None
    best_score = 0.0
    candidates = []
    tokens = set(column_name.split("_"))

    for label, aliases in SEMANTIC_ALIASES.items():
        for alias in [label, *aliases]:
            alias_tokens = set(alias.split("_"))
            score = _similarity(column_name, alias)
            if column_name == alias:
                score = 1.0
            elif alias in column_name or column_name in alias:
                score = max(score, 0.92)
            elif alias_tokens and alias_tokens.issubset(tokens):
                score = max(score, 0.9)

            if score >= 0.55:
                candidates.append({"label": label, "alias": alias, "score": round(score, 3)})
            if score > best_score:
                best_label = label
                best_score = score

    return (best_label if best_score >= 0.55 else None, round(best_score, 3), sorted(candidates, key=lambda item: item["score"], reverse=True)[:5])


def detect_file_type(file_path: str) -> str:
    return os.path.splitext(file_path)[1].lower().lstrip(".")


def read_dataset(file_path: str) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file_path)
    if ext == ".tsv":
        return pd.read_csv(file_path, sep="\t")
    if ext == ".json":
        try:
            return pd.read_json(file_path)
        except ValueError:
            return pd.read_json(file_path, lines=True)
    if ext == ".xlsx":
        return pd.read_excel(file_path, engine="openpyxl")
    if ext == ".xls":
        return pd.read_excel(file_path, engine="xlrd")
    if ext == ".parquet":
        return pd.read_parquet(file_path)
    raise ValueError(f"Unsupported file format: {ext}")


def _maybe_parse_numeric(series: pd.Series) -> tuple[pd.Series, bool, bool]:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce"), False, False

    text = series.astype(str).str.strip()
    percent_like = (text.str.contains("%", regex=False, na=False)).mean() >= 0.35
    currency_like = (
        text.str.contains(r"[$€£₹¥]", regex=True, na=False).mean() >= 0.2
        or text.str.contains(r"usd|eur|inr|gbp|aud|cad", regex=True, case=False, na=False).mean() >= 0.2
    )

    cleaned = text.str.replace(r"[$€£₹¥,]", "", regex=True)
    cleaned = cleaned.str.replace(r"usd|eur|inr|gbp|aud|cad", "", regex=True, case=False)
    cleaned = cleaned.str.replace(r"[()]", "", regex=True)
    cleaned = cleaned.str.replace("%", "", regex=False)
    numeric = pd.to_numeric(cleaned, errors="coerce")

    if numeric.notna().mean() >= 0.7:
        if percent_like:
            numeric = numeric / 100.0
        return numeric, currency_like, percent_like

    return series, False, False


def _maybe_parse_datetime(series: pd.Series) -> tuple[pd.Series, bool]:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce"), True
    if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
        return series, False

    parsed = pd.to_datetime(series, errors="coerce", utc=False)
    if parsed.notna().mean() >= 0.65:
        return parsed, True
    return series, False


def _classify_column(series: pd.Series, semantic_label: str | None, currency_hint: bool, percent_hint: bool) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if currency_hint:
        return "currency"
    if percent_hint:
        return "percentage"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if semantic_label == "date":
        return "datetime"
    return "categorical"


def _detect_outliers(series: pd.Series) -> dict:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 5:
        return {"count": 0, "rate": 0.0}
    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return {"count": 0, "rate": 0.0}
    mask = (numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)
    count = int(mask.sum())
    return {"count": count, "rate": round(count / max(len(numeric), 1), 4)}


def _column_profile(name: str, original_name: str, series: pd.Series, semantic_label: str | None, semantic_confidence: float, semantic_candidates: list[dict], currency_hint: bool, percent_hint: bool) -> dict:
    non_null = series.dropna()
    detected_type = _classify_column(series, semantic_label, currency_hint, percent_hint)
    profile = {
        "name": name,
        "originalName": original_name,
        "semanticLabel": semantic_label,
        "semanticConfidence": semantic_confidence,
        "semanticCandidates": semantic_candidates,
        "detectedType": detected_type,
        "missingCount": int(series.isna().sum()),
        "missingRate": round(float(series.isna().mean()), 4),
        "uniqueCount": int(series.nunique(dropna=True)),
        "sampleValues": [serialize_value(v) for v in non_null.head(5).tolist()],
    }

    if detected_type in {"numeric", "currency", "percentage"}:
        outlier = _detect_outliers(series)
        profile["stats"] = {
            "min": serialize_value(non_null.min()) if len(non_null) else None,
            "max": serialize_value(non_null.max()) if len(non_null) else None,
            "mean": serialize_value(non_null.mean()) if len(non_null) else None,
            "median": serialize_value(non_null.median()) if len(non_null) else None,
            "std": serialize_value(non_null.std()) if len(non_null) else None,
            "sum": serialize_value(non_null.sum()) if len(non_null) else None,
        }
        profile["outliers"] = outlier
    elif detected_type == "datetime":
        profile["stats"] = {
            "min": serialize_value(non_null.min()) if len(non_null) else None,
            "max": serialize_value(non_null.max()) if len(non_null) else None,
        }
    else:
        profile["topValues"] = [
            {"value": serialize_value(idx), "count": int(count)}
            for idx, count in non_null.astype(str).value_counts().head(5).items()
        ]

    return profile


def _normalize_and_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    original_columns = list(df.columns)
    used = Counter()
    normalized_columns = [_normalize_name(column, used) for column in original_columns]
    rename_map = dict(zip(original_columns, normalized_columns))
    df = df.rename(columns=rename_map)

    df = df.replace(list(NULL_LIKE), np.nan)
    df = df.dropna(how="all").reset_index(drop=True)

    duplicate_rows_detected = int(df.duplicated().sum())
    if duplicate_rows_detected:
        df = df.drop_duplicates().reset_index(drop=True)

    return df, {
        "originalColumns": original_columns,
        "normalizedColumns": normalized_columns,
        "renameMap": rename_map,
        "duplicateRowsDetected": duplicate_rows_detected,
    }


def _fill_missing_values(df: pd.DataFrame, profiles: list[dict]) -> dict:
    imputations = []
    for profile in profiles:
        column = profile["name"]
        series = df[column]
        if series.isna().sum() == 0:
            continue

        if profile["detectedType"] in {"numeric", "currency", "percentage"}:
            fill_value = pd.to_numeric(series, errors="coerce").median()
            if pd.notna(fill_value):
                df.loc[:, column] = pd.to_numeric(series, errors="coerce").fillna(fill_value)
                strategy = "median"
            else:
                strategy = "left_as_null"
        elif profile["detectedType"] == "categorical":
            mode = series.mode(dropna=True)
            if not mode.empty:
                df.loc[:, column] = series.fillna(mode.iloc[0])
                strategy = "mode"
            else:
                strategy = "left_as_null"
        else:
            strategy = "left_as_null"

        imputations.append({"column": column, "strategy": strategy, "filledCount": profile["missingCount"]})

    return {"imputations": imputations}


def _dataset_statistics(df: pd.DataFrame, profiles: list[dict]) -> dict:
    numeric_columns = [p["name"] for p in profiles if p["detectedType"] in {"numeric", "currency", "percentage"} and p["name"] in df.columns]
    categorical_columns = [p["name"] for p in profiles if p["detectedType"] == "categorical" and p["name"] in df.columns]
    datetime_columns = [p["name"] for p in profiles if p["detectedType"] == "datetime" and p["name"] in df.columns]

    missing_by_column = {
        column: {
            "count": int(df[column].isna().sum()),
            "rate": round(float(df[column].isna().mean()), 4),
        }
        for column in df.columns
    }

    unique_value_analysis = [
        {
            "column": profile["name"],
            "uniqueCount": profile["uniqueCount"],
            "uniquenessRate": round(profile["uniqueCount"] / max(len(df), 1), 4),
        }
        for profile in profiles
    ]

    outlier_summary = [
        {
            "column": profile["name"],
            "count": profile.get("outliers", {}).get("count", 0),
            "rate": profile.get("outliers", {}).get("rate", 0.0),
        }
        for profile in profiles
        if profile["detectedType"] in {"numeric", "currency", "percentage"} and profile.get("outliers", {}).get("count", 0) > 0
    ]

    statistical_summaries = []
    for profile in profiles:
        stats = profile.get("stats")
        if stats:
            statistical_summaries.append({"column": profile["name"], "type": profile["detectedType"], "stats": stats})

    return {
        "rowCount": int(len(df)),
        "columnCount": int(len(df.columns)),
        "missingValues": missing_by_column,
        "duplicateRows": 0,
        "datatypeSummary": {
            "numeric": len([p for p in profiles if p["detectedType"] == "numeric"]),
            "categorical": len([p for p in profiles if p["detectedType"] == "categorical"]),
            "datetime": len([p for p in profiles if p["detectedType"] == "datetime"]),
            "currency": len([p for p in profiles if p["detectedType"] == "currency"]),
            "percentage": len([p for p in profiles if p["detectedType"] == "percentage"]),
        },
        "outliers": outlier_summary,
        "uniqueValueAnalysis": unique_value_analysis,
        "statisticalSummaries": statistical_summaries,
        "numericColumns": numeric_columns,
        "categoricalColumns": categorical_columns,
        "datetimeColumns": datetime_columns,
    }


def process_dataset(file_path: str, upload_type: str = "auto") -> dict:
    df = read_dataset(file_path)
    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    raw_row_count = int(len(df))
    raw_column_count = int(len(df.columns))
    file_type = detect_file_type(file_path)

    df, normalization = _normalize_and_clean(df)

    profiles = []
    inferred_schema = {}
    semantic_groups: dict[str, list[str]] = {}

    for original_name, column_name in zip(normalization["originalColumns"], normalization["normalizedColumns"]):
        if column_name not in df.columns:
            continue

        series = df[column_name]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            series = series.astype(str).str.strip().replace(list(NULL_LIKE), np.nan)

        semantic_label, semantic_confidence, semantic_candidates = _infer_semantic_label(column_name)
        series, currency_hint, percent_hint = _maybe_parse_numeric(series)
        series, parsed_datetime = _maybe_parse_datetime(series)
        if parsed_datetime and semantic_label is None:
            semantic_label = "date"

        df.loc[:, column_name] = series
        profile = _column_profile(
            column_name,
            original_name,
            df[column_name],
            semantic_label,
            semantic_confidence,
            semantic_candidates,
            currency_hint,
            percent_hint,
        )
        profiles.append(profile)
        inferred_schema[column_name] = {
            "semanticLabel": semantic_label,
            "confidence": semantic_confidence,
            "detectedType": profile["detectedType"],
            "originalName": original_name,
            "candidateMatches": semantic_candidates,
        }
        if semantic_label:
            semantic_groups.setdefault(semantic_label, []).append(column_name)

    fill_report = _fill_missing_values(df, profiles)
    profile_report = _dataset_statistics(df, profiles)
    profile_report["duplicateRows"] = normalization["duplicateRowsDetected"]

    preview = [
        {key: serialize_value(value) for key, value in row.items()}
        for row in df.head(10).to_dict(orient="records")
    ]

    return {
        "rowCount": int(len(df)),
        "columnCount": int(len(df.columns)),
        "columns": list(df.columns),
        "schema": "universal_dataset",
        "preview": preview,
        "data": df,
        "fileType": file_type,
        "fileMetadata": {
            "fileType": file_type,
            "rawRowCount": raw_row_count,
            "rawColumnCount": raw_column_count,
            "processedRowCount": int(len(df)),
            "processedColumnCount": int(len(df.columns)),
        },
        "columnProfiles": profiles,
        "inferredSchema": inferred_schema,
        "semanticGroups": semantic_groups,
        "profileReport": profile_report,
        "qualityReport": {
            "duplicateRowsRemoved": normalization["duplicateRowsDetected"],
            "missingValues": profile_report["missingValues"],
            "dtypeSummary": profile_report["datatypeSummary"],
            "normalization": {
                "renameMap": normalization["renameMap"],
                "columnsRenamed": len(
                    [key for key, value in normalization["renameMap"].items() if str(key) != str(value)]
                ),
            },
            "cleaning": fill_report,
        },
    }

