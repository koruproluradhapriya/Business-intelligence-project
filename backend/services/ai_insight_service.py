from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (float, np.floating)) and np.isnan(value):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_label(name: str) -> str:
    return str(name or "Metric").replace("_", " ").title()


def generate_insights(
    df: pd.DataFrame,
    dataset: dict,
    profile: dict,
    primary_metric: str | None,
    dimension_breakdown: list[dict],
    time_series: list[dict],
    anomalies: list[dict],
) -> list[dict]:
    insights = []
    metric_label = _format_label(primary_metric)

    if primary_metric and primary_metric in df.columns:
        metric_series = pd.to_numeric(df[primary_metric], errors="coerce").dropna()
        total = _safe_float(metric_series.sum())
        avg = _safe_float(metric_series.mean()) if len(metric_series) else 0
        insights.append(
            {
                "title": f"{metric_label} baseline",
                "summary": f"{metric_label} totals {round(total, 2):,} across {len(metric_series):,} populated records, with an average of {round(avg, 2):,} per row.",
                "severity": "low",
                "category": "overview",
            }
        )

    if time_series and len(time_series) >= 2:
        first = _safe_float(time_series[0]["value"])
        last = _safe_float(time_series[-1]["value"])
        change = ((last - first) / first * 100) if first else 0
        direction = "increased" if change >= 0 else "decreased"
        insights.append(
            {
                "title": "Trend explanation",
                "summary": f"{metric_label} {direction} by {abs(round(change, 1))}% across the observed time window, indicating a clear {'growth' if change >= 0 else 'decline'} pattern.",
                "severity": "medium" if abs(change) >= 10 else "low",
                "category": "trend",
            }
        )

    if dimension_breakdown:
        leader = dimension_breakdown[0]
        insights.append(
            {
                "title": f"Top contributor: {leader['name']}",
                "summary": f"{leader['name']} contributes {leader['share']}% of the tracked total, making it the leading business driver in this upload.",
                "severity": "medium",
                "category": "contribution",
            }
        )
        if len(dimension_breakdown) > 1:
            runner_up = dimension_breakdown[1]
            gap = round(leader["share"] - runner_up["share"], 2)
            insights.append(
                {
                    "title": "Concentration signal",
                    "summary": f"The top segment leads the second-ranked segment by {gap}% share, which suggests the dataset is {'highly concentrated' if gap >= 10 else 'fairly balanced'} around a few contributors.",
                    "severity": "medium" if gap >= 10 else "low",
                    "category": "mix",
                }
            )

    if anomalies:
        top = anomalies[0]
        insights.append(
            {
                "title": f"Anomaly detected in {top['date']}",
                "summary": f"A notable {top['type'].lower()} appears in {top['date']}. This often points to a campaign burst, demand shift, supply issue, pricing change, or reporting inconsistency that needs review.",
                "severity": top["severity"],
                "category": "anomaly",
            }
        )

    if profile.get("outliers"):
        strongest = max(profile["outliers"], key=lambda item: item["count"])
        insights.append(
            {
                "title": "Outlier-heavy metric",
                "summary": f"{_format_label(strongest['column'])} contains {strongest['count']} outlier values, so dashboards and forecasts should be interpreted with attention to extreme cases.",
                "severity": "medium",
                "category": "data_quality",
            }
        )

    if profile.get("missingValueCells", 0) > 0:
        insights.append(
            {
                "title": "Missing data still present",
                "summary": f"The processed dataset still contains {profile['missingValueCells']} missing cells after cleanup, which may soften confidence for some automatically generated findings.",
                "severity": "low",
                "category": "data_quality",
            }
        )

    if not insights:
        insights.append(
            {
                "title": "Dataset loaded successfully",
                "summary": "The platform understood the structure, but this file needs stronger numeric measures or business dimensions before deeper insights can be generated.",
                "severity": "low",
                "category": "setup",
            }
        )

    return insights[:8]


def generate_executive_summary(
    dataset: dict,
    profile: dict,
    primary_metric: str | None,
    time_series: list[dict],
    dimension_breakdown: list[dict],
    anomalies: list[dict],
    forecast: dict,
) -> dict:
    metric_label = _format_label(primary_metric)
    row_count = f"{dataset.get('rows', 0):,}"
    summary_parts = [f"This upload contains {row_count} rows"]
    if primary_metric:
        summary_parts.append(f"and uses {metric_label.lower()} as the primary business metric")
    if time_series:
        summary_parts.append("with enough historical coverage for trend and forecast analysis")
    if dimension_breakdown:
        summary_parts.append(f"and a leading segment of {dimension_breakdown[0]['name']}")
    overview = ", ".join(summary_parts) + "."

    risks = []
    if anomalies:
        risks.append(f"Investigate the {anomalies[0]['type'].lower()} flagged in {anomalies[0]['date']}.")
    if profile.get("missingValueCells", 0) > 0:
        risks.append(f"{profile['missingValueCells']} missing cells remain after cleanup.")
    if forecast.get("confidenceSummary", {}).get("averageConfidence") and forecast["confidenceSummary"]["averageConfidence"] < 75:
        risks.append("Forecast confidence is moderate, so planning should allow wider uncertainty bands.")

    opportunities = []
    if dimension_breakdown:
        opportunities.append(f"Scale learnings from {dimension_breakdown[0]['name']}, the top contributor.")
    if forecast.get("forecast"):
        opportunities.append(f"The forecast suggests {metric_label.lower()} remains actionable for forward planning.")
    if not opportunities:
        opportunities.append("Add more time-based and segment-level data to unlock richer optimization opportunities.")

    return {
        "overview": overview,
        "risks": risks[:3],
        "opportunities": opportunities[:3],
    }


def answer_question(question: str, analytics: dict | None) -> dict:
    if not analytics:
        return {
            "answer": "No dataset is loaded yet. Upload a file first, then ask about trends, top contributors, anomalies, forecasts, or data quality.",
            "references": [],
        }

    q = question.lower()
    dataset = analytics.get("dataset", {})
    insights = analytics.get("insights", [])
    forecast_rows = analytics.get("forecast", {}).get("forecast", [])
    breakdown = analytics.get("dimensionBreakdown", [])
    anomalies = analytics.get("anomalies", [])
    profile = analytics.get("profile", {})
    semantic_map = analytics.get("schemaMapping", {})
    refs = []

    if any(word in q for word in ["best", "top", "highest", "perform"]):
        if breakdown:
            leader = breakdown[0]
            refs.append(leader["name"])
            return {
                "answer": f"{leader['name']} is the current top performer, contributing {leader['share']}% of the measured total in this dataset.",
                "references": refs,
            }

    if any(word in q for word in ["forecast", "predict", "next", "future"]):
        if forecast_rows:
            first = forecast_rows[0]
            refs.append(first.get("period", "next period"))
            return {
                "answer": f"The next forecasted period is {first.get('period', 'upcoming')}, with an estimated value of {round(_safe_float(first.get('predicted')), 2):,}. Use the prediction range to plan for upside and downside scenarios.",
                "references": refs,
            }

    if any(word in q for word in ["drop", "anomal", "spike", "why"]):
        if anomalies:
            event = anomalies[0]
            refs.append(event["date"])
            return {
                "answer": f"The strongest flagged signal is a {event['type'].lower()} in {event['date']}. That usually means an unusual business event, data lag, pricing move, inventory constraint, or campaign effect deserves investigation.",
                "references": refs,
            }

    if any(word in q for word in ["missing", "quality", "clean"]):
        refs.append("profile")
        return {
            "answer": f"The dataset currently has {profile.get('missingValueCells', 0)} missing cells and {profile.get('duplicateRows', 0)} duplicate rows detected during profiling. Cleaning quality is reflected in the data quality KPI and profile view.",
            "references": refs,
        }

    if any(word in q for word in ["column", "schema", "map", "meaning"]):
        refs.extend(list(semantic_map.keys())[:4])
        return {
            "answer": f"The schema inference engine mapped your columns into business concepts such as {', '.join(list(semantic_map.keys())[:4]) or 'generic dimensions'} so downstream analytics can adapt without fixed column names.",
            "references": refs,
        }

    if insights:
        refs.append(dataset.get("name", "dataset"))
        return {"answer": insights[0]["summary"], "references": refs}

    return {
        "answer": f"The platform understood {dataset.get('name', 'your dataset')}, but I need stronger measures or dimensions in the file to answer that confidently.",
        "references": refs,
    }
