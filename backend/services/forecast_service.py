from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

import numpy as np


@dataclass
class ModelResult:
    name: str
    predictions: list[float]
    fitted: list[float]
    residual_std: float
    mape: float
    mae: float
    rmse: float
    meta: dict


def _future_labels(last_label: str | None, periods: int) -> list[str]:
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if not last_label:
        return month_names[:periods]

    for pattern, step in [("%b %Y", "month"), ("%d %b", "week")]:
        try:
            last_dt = datetime.strptime(last_label, pattern)
            labels = []
            current = last_dt
            for _ in range(periods):
                if step == "month":
                    month = current.month + 1
                    year = current.year + (1 if month > 12 else 0)
                    month = 1 if month > 12 else month
                    current = datetime(year, month, 1)
                    labels.append(current.strftime("%b %Y"))
                else:
                    current = current + timedelta(days=7)
                    labels.append(current.strftime("%d %b"))
            return labels
        except ValueError:
            continue
    return month_names[:periods]


def _safe_mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _safe_std(values: list[float]) -> float:
    return float(np.std(values)) if len(values) > 1 else 1.0


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> tuple[float, float, float]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mae = float(np.mean(np.abs(actual - predicted)))
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    denom = np.where(actual == 0, 1.0, np.abs(actual))
    mape = float(np.mean(np.abs((actual - predicted) / denom)) * 100)
    return mae, rmse, mape


def _detect_anomalies(values: list[float]) -> list[int]:
    arr = np.asarray(values, dtype=float)
    if len(arr) < 6:
        return []
    rolling = []
    for index in range(len(arr)):
        left = max(0, index - 2)
        right = min(len(arr), index + 3)
        window = arr[left:right]
        rolling.append(float(np.median(window)))
    baseline = np.asarray(rolling)
    residuals = arr - baseline
    std = float(np.std(residuals))
    if std == 0:
        return []
    return [index for index, residual in enumerate(residuals) if abs(residual / std) >= 2.1]


def _clean_training_values(values: list[float]) -> tuple[list[float], list[int]]:
    clean = list(map(float, values))
    anomaly_indexes = _detect_anomalies(clean)
    if not anomaly_indexes:
        return clean, []
    for index in anomaly_indexes:
        left = max(0, index - 2)
        right = min(len(clean), index + 3)
        window = [clean[i] for i in range(left, right) if i != index]
        if window:
            clean[index] = float(np.median(window))
    return clean, anomaly_indexes


def _linear_model(values: list[float], periods: int) -> ModelResult:
    arr = np.asarray(values, dtype=float)
    x = np.arange(len(arr))
    coeffs = np.polyfit(x, arr, deg=1)
    fitted = np.polyval(coeffs, x)
    future_x = np.arange(len(arr), len(arr) + periods)
    predictions = np.polyval(coeffs, future_x)
    residual_std = _safe_std((arr - fitted).tolist())
    mae, rmse, mape = _metrics(arr, fitted)
    return ModelResult("Linear Trend", predictions.tolist(), fitted.tolist(), residual_std, mape, mae, rmse, {"trendSlope": float(coeffs[0])})


def _holt_winters(values: list[float], periods: int) -> ModelResult:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    arr = np.asarray(values, dtype=float)
    season_length = 12 if len(arr) >= 24 else 6 if len(arr) >= 12 else None
    if season_length and len(arr) <= season_length:
        season_length = None
    model = ExponentialSmoothing(
        arr,
        trend="add",
        seasonal="add" if season_length else None,
        seasonal_periods=season_length,
        initialization_method="estimated",
    )
    fit = model.fit(optimized=True, remove_bias=True)
    preds = fit.forecast(periods)
    fitted = fit.fittedvalues
    residual_std = _safe_std((arr - fitted).tolist())
    mae, rmse, mape = _metrics(arr, fitted)
    return ModelResult(
        "Holt-Winters",
        np.asarray(preds, dtype=float).tolist(),
        np.asarray(fitted, dtype=float).tolist(),
        residual_std,
        mape,
        mae,
        rmse,
        {"seasonLength": season_length},
    )


def _arima_model(values: list[float], periods: int) -> ModelResult:
    from statsmodels.tsa.arima.model import ARIMA

    arr = np.asarray(values, dtype=float)
    order = (1, 1, 1) if len(arr) >= 8 else (1, 0, 1)
    fit = ARIMA(arr, order=order).fit()
    preds = fit.forecast(steps=periods)
    fitted = fit.predict(start=0, end=len(arr) - 1)
    residual_std = _safe_std((arr - fitted).tolist())
    mae, rmse, mape = _metrics(arr, fitted)
    return ModelResult(
        "ARIMA",
        np.asarray(preds, dtype=float).tolist(),
        np.asarray(fitted, dtype=float).tolist(),
        residual_std,
        mape,
        mae,
        rmse,
        {"order": order},
    )


def _random_forest_model(values: list[float], periods: int) -> ModelResult:
    from sklearn.ensemble import RandomForestRegressor

    arr = np.asarray(values, dtype=float)
    lag = min(4, max(2, len(arr) // 4))
    features = []
    targets = []
    for index in range(lag, len(arr)):
        features.append(arr[index - lag:index])
        targets.append(arr[index])
    if len(features) < 3:
        raise ValueError("Insufficient data for random forest forecasting")

    model = RandomForestRegressor(n_estimators=250, random_state=42, min_samples_leaf=1)
    model.fit(np.asarray(features), np.asarray(targets))

    fitted = arr[:lag].tolist()
    predictions_in_sample = model.predict(np.asarray(features))
    fitted.extend(predictions_in_sample.tolist())

    history = arr.tolist()
    future = []
    for _ in range(periods):
        window = np.asarray(history[-lag:], dtype=float).reshape(1, -1)
        pred = float(model.predict(window)[0])
        history.append(pred)
        future.append(pred)

    aligned_actual = arr[lag:]
    aligned_pred = np.asarray(predictions_in_sample, dtype=float)
    residual_std = _safe_std((aligned_actual - aligned_pred).tolist())
    mae, rmse, mape = _metrics(aligned_actual, aligned_pred)
    return ModelResult(
        "Random Forest",
        future,
        fitted,
        residual_std,
        mape,
        mae,
        rmse,
        {"lag": lag},
    )


def _prophet_model(values: list[float], periods: int) -> ModelResult:
    from prophet import Prophet
    import pandas as pd

    arr = np.asarray(values, dtype=float)
    dates = pd.date_range("2024-01-01", periods=len(arr), freq="MS")
    frame = pd.DataFrame({"ds": dates, "y": arr})
    model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    model.fit(frame)
    future = model.make_future_dataframe(periods=periods, freq="MS")
    result = model.predict(future)
    fitted = result["yhat"].iloc[: len(arr)].astype(float).tolist()
    preds = result["yhat"].iloc[len(arr):].astype(float).tolist()
    residual_std = _safe_std((arr - np.asarray(fitted, dtype=float)).tolist())
    mae, rmse, mape = _metrics(arr, np.asarray(fitted, dtype=float))
    return ModelResult("Prophet", preds, fitted, residual_std, mape, mae, rmse, {"seasonalityMode": "additive"})


def _available_models(values: list[float], periods: int) -> list[Callable[[], ModelResult]]:
    candidates: list[Callable[[], ModelResult]] = [lambda: _linear_model(values, periods)]
    if len(values) >= 6:
        candidates.extend([lambda: _holt_winters(values, periods), lambda: _arima_model(values, periods)])
    if len(values) >= 8:
        candidates.append(lambda: _random_forest_model(values, periods))
    try:
        import prophet  # noqa: F401

        if len(values) >= 10:
            candidates.append(lambda: _prophet_model(values, periods))
    except Exception:
        pass
    return candidates


def _seasonality_strength(values: list[float]) -> float:
    if len(values) < 6:
        return 0.0
    arr = np.asarray(values, dtype=float)
    base = max(_safe_std(arr.tolist()), 1.0)
    lag = min(6, len(arr) - 1)
    diffs = arr[lag:] - arr[:-lag]
    return round(max(0.0, 1 - (_safe_std(diffs.tolist()) / base)), 3)


def _decomposition(values: list[float], labels: list[str]) -> list[dict]:
    if len(values) < 8:
        return []
    try:
        from statsmodels.tsa.seasonal import seasonal_decompose

        arr = np.asarray(values, dtype=float)
        period = 4 if len(arr) < 18 else 6 if len(arr) < 30 else 12
        result = seasonal_decompose(arr, period=period, model="additive", extrapolate_trend="freq")
        rows = []
        for index, label in enumerate(labels):
            rows.append(
                {
                    "period": label,
                    "observed": round(float(arr[index]), 2),
                    "trend": round(float(result.trend[index]), 2) if not np.isnan(result.trend[index]) else None,
                    "seasonal": round(float(result.seasonal[index]), 2) if not np.isnan(result.seasonal[index]) else None,
                    "residual": round(float(result.resid[index]), 2) if not np.isnan(result.resid[index]) else None,
                }
            )
        return rows
    except Exception:
        return []


def _narrative(values: list[float], forecast_values: list[float], model_name: str, seasonality_strength: float, anomaly_indexes: list[int]) -> tuple[str, list[str]]:
    first = values[0]
    last = values[-1]
    change = ((last - first) / first * 100) if first else 0.0
    direction = "upward" if change >= 0 else "downward"
    next_change = ((forecast_values[0] - last) / last * 100) if last else 0.0
    seasonality_text = "clear recurring seasonality" if seasonality_strength >= 0.45 else "limited seasonality"
    anomaly_text = f"{len(anomaly_indexes)} anomaly-adjusted periods" if anomaly_indexes else "no major anomaly adjustments"
    explanation = (
        f"{model_name} was selected as the strongest forecast model for this dataset. "
        f"The historical pattern shows a {direction} trend of {abs(round(change, 1))}% across the observed window, "
        f"with {seasonality_text} and {anomaly_text}. "
        f"The next projected period is {round(next_change, 1)}% {'above' if next_change >= 0 else 'below'} the latest actual value."
    )
    signals = [
        f"Historical trend: {'growth' if change >= 0 else 'decline'}",
        f"Seasonality strength: {round(seasonality_strength * 100, 1)}%",
        f"Anomaly-adjusted periods: {len(anomaly_indexes)}",
    ]
    return explanation, signals


def generate_forecast(time_series: list[dict], periods: int = 6, value_key: str = "value") -> dict:
    values = [float(item.get(value_key, 0) or 0) for item in time_series if item.get(value_key) is not None]
    labels = [item.get("period") for item in time_series if item.get(value_key) is not None]
    if len(values) < 3:
        return {
            "forecast": [],
            "accuracy": None,
            "model": "Insufficient data",
            "eligible": False,
            "explanation": "At least 3 historical data points are required before the forecasting engine can project future periods.",
            "modelCandidates": [],
            "decomposition": [],
            "signals": [],
            "anomaliesAdjusted": False,
        }

    clean_values, anomaly_indexes = _clean_training_values(values)
    results = []
    for builder in _available_models(clean_values, periods):
        try:
            result = builder()
            results.append(result)
        except Exception:
            continue

    if not results:
        fallback = _linear_model(clean_values, periods)
        results = [fallback]

    best = min(results, key=lambda item: (item.mape, item.mae))
    candidate_rows = [
        {
            "name": item.name,
            "mape": round(item.mape, 2),
            "mae": round(item.mae, 2),
            "rmse": round(item.rmse, 2),
            "meta": item.meta,
        }
        for item in sorted(results, key=lambda item: (item.mape, item.mae))
    ]

    last_label = labels[-1] if labels else None
    future_labels = _future_labels(last_label, periods)
    seasonality_strength = _seasonality_strength(clean_values)
    spread_base = max(best.residual_std, _safe_std(clean_values) * 0.18, 1.0)
    forecast_rows = []
    for index, (label, pred) in enumerate(zip(future_labels, best.predictions)):
        predicted = max(float(pred), 0.0)
        spread = spread_base * (1.0 + index * 0.08)
        confidence = max(62.0, min(97.0, 100.0 - best.mape - index * 1.2))
        forecast_rows.append(
            {
                "period": label,
                "predicted": round(predicted, 2),
                "lower": round(max(predicted - spread, 0.0), 2),
                "upper": round(predicted + spread, 2),
                "confidence": round(confidence, 1),
            }
        )

    explanation, signals = _narrative(clean_values, [row["predicted"] for row in forecast_rows], best.name, seasonality_strength, anomaly_indexes)
    decomposition = _decomposition(clean_values, labels)
    avg_confidence = round(_safe_mean([row["confidence"] for row in forecast_rows]), 1) if forecast_rows else None

    return {
        "forecast": forecast_rows,
        "accuracy": round(max(0.0, 100.0 - best.mape), 1),
        "model": best.name,
        "eligible": True,
        "explanation": explanation,
        "modelCandidates": candidate_rows,
        "decomposition": decomposition,
        "signals": signals,
        "seasonalityStrength": seasonality_strength,
        "anomaliesAdjusted": bool(anomaly_indexes),
        "anomalyIndexes": anomaly_indexes,
        "confidenceSummary": {
            "averageConfidence": avg_confidence,
            "residualStd": round(best.residual_std, 2),
        },
    }
