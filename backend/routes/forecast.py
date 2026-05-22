from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from database.connection import serialize_document
from services.analytics_service import get_demo_dashboard
from services.persistence_service import latest_analytics, latest_forecast, record_activity

forecast_bp = Blueprint("forecast", __name__)


@forecast_bp.route("/sales", methods=["GET"])
@jwt_required()
def sales_forecast():
    user_id = get_jwt_identity()
    forecast_doc = latest_forecast(user_id)
    analytics = latest_analytics(user_id)
    source = analytics or get_demo_dashboard()
    forecast_payload = forecast_doc or source.get("forecast", {})
    response = {
        "historical": source.get("timeSeries", []),
        "forecast": forecast_payload.get("forecast", []),
        "accuracy": forecast_payload.get("accuracy"),
        "model": forecast_payload.get("model"),
        "explanation": forecast_payload.get("explanation"),
        "modelCandidates": forecast_payload.get("modelCandidates", []),
        "decomposition": forecast_payload.get("decomposition", []),
        "signals": forecast_payload.get("signals", []),
        "confidenceSummary": forecast_payload.get("confidenceSummary", {}),
        "anomaliesAdjusted": forecast_payload.get("anomaliesAdjusted", False),
        "usingRealData": bool(analytics),
        "dataPoints": len(source.get("timeSeries", [])),
        "primaryMetric": source.get("dataset", {}).get("primaryMetric"),
    }
    record_activity(user_id, "forecast.viewed", "forecasts", None)
    return jsonify(serialize_document(response))
