from __future__ import annotations


def generate_recommendations(
    profile: dict,
    primary_metric: str | None,
    dimension_breakdown: list[dict],
    anomalies: list[dict],
    time_series: list[dict],
) -> list[dict]:
    recommendations = []

    if profile.get("missingValueCells", 0) > 0:
        recommendations.append(
            {
                "title": "Improve source data quality",
                "text": f"The dataset still contains {profile['missingValueCells']} missing cells. Filling key business fields upstream will make insights and forecasts more reliable.",
                "severity": "medium",
                "category": "data_quality",
                "action": "Fix missing values",
            }
        )

    if anomalies:
        recommendations.append(
            {
                "title": "Investigate the latest anomaly",
                "text": f"Review the period around {anomalies[0]['date']} to confirm whether the detected {anomalies[0]['type'].lower()} is a real business event or a data issue.",
                "severity": anomalies[0]["severity"],
                "category": "anomaly",
                "action": "Audit anomaly",
            }
        )

    if dimension_breakdown:
        leader = dimension_breakdown[0]
        recommendations.append(
            {
                "title": f"Scale what works in {leader['name']}",
                "text": f"{leader['name']} is the strongest contributor right now. Consider replicating its pricing, promotion, assortment, or channel strategy across lower-performing segments.",
                "severity": "medium",
                "category": "growth",
                "action": "Scale winning segment",
            }
        )

    if primary_metric and time_series:
        recommendations.append(
            {
                "title": "Set alerts on leading metrics",
                "text": f"Track {primary_metric.replace('_', ' ')} with automated alerts so sudden drops, spikes, and demand shifts are caught before they become missed opportunities.",
                "severity": "low",
                "category": "operations",
                "action": "Enable alerts",
            }
        )

    if len(time_series) >= 6:
        recommendations.append(
            {
                "title": "Use the forecast for planning",
                "text": "This dataset has enough time-based history to generate a forward view. Use the forecast band for inventory, cash-flow, or staffing planning.",
                "severity": "low",
                "category": "forecasting",
                "action": "Review forecast",
            }
        )

    return recommendations[:8]

