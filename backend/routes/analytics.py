from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database.connection import serialize_document
from services.analytics_service import answer_question, get_demo_dashboard
from services.persistence_service import list_chat_history, latest_analytics, latest_dashboard, record_activity, save_chat_exchange

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    analytics = latest_analytics(user_id)
    dashboard_snapshot = latest_dashboard(user_id)
    payload = analytics or get_demo_dashboard()
    if dashboard_snapshot:
        payload = {**payload, "savedDashboard": serialize_document(dashboard_snapshot)}
    record_activity(user_id, "dashboard.viewed", "dashboards", None)
    return jsonify(serialize_document(payload))


@analytics_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    analytics = latest_analytics(get_jwt_identity())
    if not analytics:
        return jsonify({"profile": get_demo_dashboard()["profile"], "dataset": get_demo_dashboard()["dataset"]})
    return jsonify({"profile": serialize_document(analytics.get("profile", {})), "dataset": serialize_document(analytics.get("dataset", {}))})


@analytics_bp.route("/products", methods=["GET"])
@jwt_required()
def products():
    analytics = latest_analytics(get_jwt_identity())
    data = analytics or get_demo_dashboard()
    return jsonify({"products": serialize_document(data.get("dimensionBreakdown", []))})


@analytics_bp.route("/trends", methods=["GET"])
@jwt_required()
def trends():
    analytics = latest_analytics(get_jwt_identity())
    data = analytics or get_demo_dashboard()
    return jsonify({"trends": serialize_document(data.get("timeSeries", [])), "period": request.args.get("period", "auto")})


@analytics_bp.route("/segments", methods=["GET"])
@jwt_required()
def segments():
    analytics = latest_analytics(get_jwt_identity())
    data = analytics or get_demo_dashboard()
    return jsonify({"segments": serialize_document(data.get("dimensionBreakdown", []))})


@analytics_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400

    analytics = latest_analytics(user_id)
    answer = answer_question(question, analytics)
    save_chat_exchange(user_id, question, answer, analytics)
    return jsonify(serialize_document(answer))


@analytics_bp.route("/chat/history", methods=["GET"])
@jwt_required()
def chat_history():
    history = list_chat_history(get_jwt_identity())
    return jsonify({"items": serialize_document(history)})
