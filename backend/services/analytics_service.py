from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from services.ai_insight_service import answer_question, generate_executive_summary, generate_insights
from services.forecast_service import generate_forecast
from services.recommendation_service import generate_recommendations
from services.visualization_service import choose_charts


DEMO_MONTHS = [
    {"month": "Jan", "value": 51200},
    {"month": "Feb", "value": 48600},
    {"month": "Mar", "value": 56800},
    {"month": "Apr", "value": 63400},
    {"month": "May", "value": 71200},
    {"month": "Jun", "value": 78900},
]


def get_demo_monthly():
    return DEMO_MONTHS


def get_demo_dashboard() -> dict:
    total = sum(item["value"] for item in DEMO_MONTHS)
    return {
        "isDemo": True,
        "dataset": {
            "name": "Demo Revenue Dataset",
            "rows": 2480,
            "columns": 8,
            "detectedGrain": "monthly business performance",
        },
        "kpis": [
            {"label": "Total Revenue", "value": total, "format": "currency", "change": 12.6},
            {"label": "Periods", "value": len(DEMO_MONTHS), "format": "number", "change": None},
            {"label": "Average Revenue", "value": round(total / len(DEMO_MONTHS), 2), "format": "currency", "change": 4.2},
            {"label": "Data Quality", "value": 96, "format": "percent_whole", "change": None},
        ],
        "charts": [
            {
                "id": "demo_trend",
                "title": "Revenue Trend",
                "chartType": "line",
                "xKey": "month",
                "series": [{"key": "value", "label": "Revenue", "format": "currency"}],
                "data": DEMO_MONTHS,
            }
        ],
        "insights": [
            {
                "title": "Demo trend is healthy",
                "summary": "Revenue is climbing overall, with the strongest uplift appearing in late spring.",
                "severity": "medium",
                "category": "growth",
            }
        ],
        "recommendations": [
            {
                "title": "Upload a real dataset",
                "text": "Replace the demo view with your own CSV, Excel, JSON, TSV, or Parquet data to unlock tailored insights.",
                "severity": "medium",
                "category": "setup",
                "action": "Upload dataset",
            }
        ],
        "anomalies": [],
        "forecast": generate_forecast(DEMO_MONTHS, periods=6, value_key="value"),
        "profile": {
            "rowCount": 2480,
            "columnCount": 8,
            "missingValueCells": 12,
            "duplicateRows": 0,
        },
        "chatSuggestions": [
            "Which metric is growing fastest?",
            "What should I focus on first?",
            "Predict the next 3 periods",
        ],
    }


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (float, np.floating)) and math.isnan(value):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _serialize(value: Any):
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


def _format_label(name: str) -> str:
    return str(name).replace("_", " ").title()


def _first_semantic_column(column_profiles: list[dict], labels: set[str], detected_types: set[str] | None = None) -> str | None:
    for profile in column_profiles:
        if profile.get("semanticLabel") in labels:
            if not detected_types or profile.get("detectedType") in detected_types:
                return profile["name"]
    return None


def _numeric_columns(df: pd.DataFrame, column_profiles: list[dict]) -> list[str]:
    allowed = {"numeric", "currency", "percentage"}
    return [p["name"] for p in column_profiles if p.get("detectedType") in allowed and p["name"] in df.columns]


def _categorical_columns(df: pd.DataFrame, column_profiles: list[dict]) -> list[str]:
    return [p["name"] for p in column_profiles if p.get("detectedType") == "categorical" and p["name"] in df.columns]


def _datetime_columns(df: pd.DataFrame, column_profiles: list[dict]) -> list[str]:
    return [p["name"] for p in column_profiles if p.get("detectedType") == "datetime" and p["name"] in df.columns]


def _profile_summary(df: pd.DataFrame, column_profiles: list[dict]) -> dict:
    numeric_cols = _numeric_columns(df, column_profiles)
    outliers = []
    for col in numeric_cols[:6]:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 5:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        mask = (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)
        count = int(mask.sum())
        if count:
            outliers.append({"column": col, "count": count})

    return {
        "rowCount": int(len(df)),
        "columnCount": int(len(df.columns)),
        "missingValueCells": int(df.isna().sum().sum()),
        "duplicateRows": int(df.duplicated().sum()),
        "dtypeSummary": {
            "numeric": len([p for p in column_profiles if p["detectedType"] == "numeric"]),
            "categorical": len([p for p in column_profiles if p["detectedType"] == "categorical"]),
            "datetime": len([p for p in column_profiles if p["detectedType"] == "datetime"]),
            "currency": len([p for p in column_profiles if p["detectedType"] == "currency"]),
            "percentage": len([p for p in column_profiles if p["detectedType"] == "percentage"]),
        },
        "outliers": outliers,
        "columns": column_profiles,
    }


def _choose_primary_metric(df: pd.DataFrame, column_profiles: list[dict]) -> str | None:
    for labels in ({"revenue"}, {"profit"}, {"quantity"}, {"inventory"}, {"cost"}, {"price"}):
        column = _first_semantic_column(column_profiles, labels, {"numeric", "currency", "percentage"})
        if column:
            return column
    numeric_cols = _numeric_columns(df, column_profiles)
    return numeric_cols[0] if numeric_cols else None


def _time_series(df: pd.DataFrame, date_col: str | None, value_col: str | None) -> list[dict]:
    if not date_col or not value_col or date_col not in df.columns or value_col not in df.columns:
        return []

    work = df[[date_col, value_col]].copy()
    work = work.dropna(subset=[date_col, value_col])
    if work.empty:
        return []

    work.loc[:, date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna(subset=[date_col])
    if work.empty:
        return []

    span_days = (work[date_col].max() - work[date_col].min()).days
    freq = "MS" if span_days > 90 else "W" if span_days > 21 else "D"
    grouped = work.set_index(date_col)[value_col].resample(freq).sum().reset_index()
    label_format = "%b %Y" if freq == "MS" else "%d %b"
    return [
        {
            "period": row[date_col].strftime(label_format),
            "value": round(_safe_float(row[value_col]), 2),
            "date": row[date_col],
        }
        for _, row in grouped.iterrows()
    ]


def _dimension_breakdown(df: pd.DataFrame, dimension_col: str | None, value_col: str | None) -> list[dict]:
    if not dimension_col or not value_col or dimension_col not in df.columns or value_col not in df.columns:
        return []
    grouped = (
        df[[dimension_col, value_col]]
        .dropna(subset=[dimension_col])
        .groupby(dimension_col)[value_col]
        .sum()
        .sort_values(ascending=False)
        .head(8)
    )
    total = max(_safe_float(grouped.sum()), 1.0)
    return [
        {
            "name": str(index),
            "value": round(_safe_float(value), 2),
            "share": round(_safe_float(value) / total * 100, 2),
        }
        for index, value in grouped.items()
    ]


def _anomalies(time_series: list[dict]) -> list[dict]:
    if len(time_series) < 5:
        return []
    values = np.array([_safe_float(item["value"]) for item in time_series], dtype=float)
    std = float(values.std())
    if std == 0:
        return []
    mean = float(values.mean())
    anomalies = []
    rolling = pd.Series(values).rolling(window=3, center=True, min_periods=1).median().to_numpy()
    for idx, (item, value) in enumerate(zip(time_series, values)):
        z = (value - mean) / std
        expected = float(rolling[idx])
        delta = value - expected
        if abs(z) >= 1.7 or (expected and abs(delta / expected) >= 0.28):
            anomalies.append(
                {
                    "date": item["period"],
                    "type": "Spike" if z > 0 else "Drop",
                    "metric": "Primary Metric",
                    "value": round(value, 2),
                    "expected": round(expected, 2),
                    "delta": round(delta, 2),
                    "zScore": round(float(z), 2),
                    "severity": "high" if abs(z) >= 2.3 else "medium",
                }
            )
    return anomalies[:6]


def _kpis(df: pd.DataFrame, column_profiles: list[dict], primary_metric: str | None, time_series: list[dict]) -> list[dict]:
    cards = [
        {"label": "Rows", "value": int(len(df)), "format": "number", "change": None},
        {"label": "Columns", "value": int(len(df.columns)), "format": "number", "change": None},
    ]
    if primary_metric and primary_metric in df.columns:
        series = pd.to_numeric(df[primary_metric], errors="coerce").dropna()
        if len(series):
            cards.insert(0, {"label": _format_label(primary_metric), "value": round(_safe_float(series.sum()), 2), "format": "currency" if "revenue" in primary_metric or "sales" in primary_metric else "number", "change": None})
            cards.append({"label": f"Avg {_format_label(primary_metric)}", "value": round(_safe_float(series.mean()), 2), "format": "currency" if "revenue" in primary_metric or "sales" in primary_metric else "number", "change": None})

    if len(time_series) >= 2:
        current = _safe_float(time_series[-1]["value"])
        previous = _safe_float(time_series[-2]["value"])
        change = ((current - previous) / previous * 100) if previous else None
        cards.append({"label": "Latest Period Change", "value": round(change, 2) if change is not None else 0, "format": "percent", "change": change})

    missing_rate = 100 - round(df.isna().sum().sum() / max(df.size, 1) * 100, 2)
    cards.append({"label": "Data Quality", "value": max(min(missing_rate, 100), 0), "format": "percent_whole", "change": None})
    return cards[:6]

def compute_analytics(
    df: pd.DataFrame,
    upload_type: str,
    user_id: str,
    upload_id: str,
    dataset_name: str | None = None,
    column_profiles: list[dict] | None = None,
    quality_report: dict | None = None,
    inferred_schema: dict | None = None,
    semantic_groups: dict | None = None,
    file_metadata: dict | None = None,
    profile_report: dict | None = None,
) -> dict:
    column_profiles = column_profiles or []
    profile = _profile_summary(df, column_profiles)
    if profile_report:
        profile.update({
            "uniqueValueAnalysis": profile_report.get("uniqueValueAnalysis", []),
            "statisticalSummaries": profile_report.get("statisticalSummaries", []),
            "numericColumns": profile_report.get("numericColumns", []),
            "categoricalColumns": profile_report.get("categoricalColumns", []),
            "datetimeColumns": profile_report.get("datetimeColumns", []),
        })
    if quality_report:
        profile["ingestionQuality"] = quality_report
        profile["duplicateRows"] = quality_report.get("duplicateRowsRemoved", profile["duplicateRows"])

    primary_metric = _choose_primary_metric(df, column_profiles)
    date_col = _first_semantic_column(column_profiles, {"date"}, {"datetime"})
    dimension_col = _first_semantic_column(column_profiles, {"product", "category", "customer"}) or (_categorical_columns(df, column_profiles)[0] if _categorical_columns(df, column_profiles) else None)

    time_series = _time_series(df, date_col, primary_metric)
    dimension_breakdown = _dimension_breakdown(df, dimension_col, primary_metric)
    anomalies = _anomalies(time_series)
    forecast = generate_forecast(time_series, periods=6, value_key="value")
    numeric_cols = _numeric_columns(df, column_profiles)
    charts = choose_charts(df, primary_metric, time_series, dimension_breakdown, numeric_cols)

    dataset = {
        "name": dataset_name or "Uploaded Dataset",
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "primaryMetric": primary_metric,
        "dateColumn": date_col,
        "dimensionColumn": dimension_col,
        "detectedGrain": "time-series business data" if time_series else "tabular business data",
        "fileType": file_metadata.get("fileType") if file_metadata else None,
    }

    insights = generate_insights(df, dataset, profile, primary_metric, dimension_breakdown, time_series, anomalies)
    recommendations = generate_recommendations(profile, primary_metric, dimension_breakdown, anomalies, time_series)
    executive_summary = generate_executive_summary(dataset, profile, primary_metric, time_series, dimension_breakdown, anomalies, forecast)

    return {
        "isDemo": False,
        "dataset": dataset,
        "profile": profile,
        "kpis": _kpis(df, column_profiles, primary_metric, time_series),
        "charts": charts,
        "insights": insights,
        "recommendations": recommendations,
        "anomalies": anomalies,
        "forecast": forecast,
        "dimensionBreakdown": dimension_breakdown,
        "timeSeries": [{"period": item["period"], "value": item["value"]} for item in time_series],
        "schemaMapping": semantic_groups or {},
        "inferredSchema": inferred_schema or {},
        "fileMetadata": file_metadata or {},
        "executiveSummary": executive_summary,
        "chatSuggestions": [
            "What changed most recently?",
            "Which segment contributes the most?",
            "What anomalies should I investigate?",
            "What does the forecast suggest?",
            "How clean is this dataset?",
        ],
    }
