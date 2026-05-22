from __future__ import annotations

import numpy as np
import pandas as pd


def _format_label(name: str) -> str:
    return str(name or "Metric").replace("_", " ").title()


def _distribution(df: pd.DataFrame, value_col: str | None) -> list[dict]:
    if not value_col or value_col not in df.columns:
        return []
    series = pd.to_numeric(df[value_col], errors="coerce").dropna()
    if len(series) < 4:
        return []
    counts, edges = np.histogram(series, bins=min(8, max(4, int(np.sqrt(len(series))))))
    return [
        {
            "bucket": f"{round(edges[index], 2)} - {round(edges[index + 1], 2)}",
            "count": int(count),
        }
        for index, count in enumerate(counts)
    ]


def _correlations(df: pd.DataFrame, numeric_cols: list[str]) -> list[dict]:
    if len(numeric_cols) < 2:
        return []
    corr = df[numeric_cols].corr(numeric_only=True)
    pairs = []
    seen = set()
    for left in numeric_cols:
        for right in numeric_cols:
            if left == right or (right, left) in seen:
                continue
            seen.add((left, right))
            value = corr.loc[left, right]
            if pd.isna(value):
                continue
            pairs.append({"x": left, "y": right, "correlation": round(float(value), 3)})
    return sorted(pairs, key=lambda item: abs(item["correlation"]), reverse=True)[:6]


def _heatmap_from_correlations(correlations: list[dict]) -> list[dict]:
    return [
        {"x": item["x"], "y": item["y"], "value": item["correlation"]}
        for item in correlations
    ]


def choose_charts(
    df: pd.DataFrame,
    primary_metric: str | None,
    time_series: list[dict],
    dimension_breakdown: list[dict],
    numeric_cols: list[str],
) -> list[dict]:
    charts = []
    primary_format = "currency" if primary_metric and any(token in primary_metric for token in ["revenue", "sales", "price", "cost", "profit"]) else "number"

    if time_series:
        charts.append(
            {
                "id": "primary_trend",
                "title": f"{_format_label(primary_metric)} Trend",
                "chartType": "line",
                "library": "recharts",
                "xKey": "period",
                "series": [{"key": "value", "label": _format_label(primary_metric), "format": primary_format}],
                "data": [{"period": item["period"], "value": item["value"]} for item in time_series],
            }
        )
        charts.append(
            {
                "id": "trend_area",
                "title": "Trend Momentum",
                "chartType": "area",
                "library": "recharts",
                "xKey": "period",
                "series": [{"key": "value", "label": _format_label(primary_metric), "format": primary_format}],
                "data": [{"period": item["period"], "value": item["value"]} for item in time_series],
            }
        )

    if dimension_breakdown:
        charts.append(
            {
                "id": "dimension_breakdown",
                "title": "Top Contributors",
                "chartType": "bar",
                "library": "recharts",
                "xKey": "name",
                "series": [{"key": "value", "label": "Value", "format": primary_format}],
                "data": dimension_breakdown,
            }
        )
        charts.append(
            {
                "id": "share_breakdown",
                "title": "Contribution Share",
                "chartType": "pie",
                "library": "recharts",
                "xKey": "name",
                "series": [{"key": "share", "label": "Share", "format": "percent"}],
                "data": dimension_breakdown,
            }
        )

    distribution = _distribution(df, primary_metric)
    if distribution:
        charts.append(
            {
                "id": "distribution",
                "title": f"{_format_label(primary_metric)} Distribution",
                "chartType": "histogram",
                "library": "recharts",
                "xKey": "bucket",
                "series": [{"key": "count", "label": "Rows", "format": "number"}],
                "data": distribution,
            }
        )

    correlations = _correlations(df, numeric_cols)
    if correlations:
        charts.append(
            {
                "id": "correlations",
                "title": "Strongest Metric Relationships",
                "chartType": "scatter",
                "library": "recharts",
                "xKey": "x",
                "series": [{"key": "correlation", "label": "Correlation", "format": "number"}],
                "data": correlations,
            }
        )
        charts.append(
            {
                "id": "correlation_heatmap",
                "title": "Correlation Heatmap",
                "chartType": "heatmap",
                "library": "plotly",
                "xKey": "x",
                "series": [{"key": "value", "label": "Correlation", "format": "number"}],
                "data": _heatmap_from_correlations(correlations),
            }
        )

    return charts[:8]

