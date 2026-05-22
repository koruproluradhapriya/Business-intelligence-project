from datetime import datetime

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.analytics_service import get_demo_dashboard
from services.persistence_service import latest_analytics, latest_recommendations, record_activity

recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.route("/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    analytics = latest_analytics(user_id)
    source = analytics or get_demo_dashboard()
    recommendations = latest_recommendations(user_id) or source.get("recommendations", [])

    now = datetime.now().isoformat()
    shaped = [{**rec, "createdAt": now} for rec in recommendations]
    record_activity(user_id, "recommendations.viewed", "insights", None, {"count": len(shaped)})
    return jsonify({"recommendations": shaped, "cached": False})
