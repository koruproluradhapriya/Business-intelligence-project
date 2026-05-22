from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database.connection import serialize_document
from services.persistence_service import (
    list_connectors,
    list_notifications,
    list_reports,
    mark_notification_read,
    upsert_connector,
)

workspace_bp = Blueprint("workspace", __name__)


@workspace_bp.route("/reports", methods=["GET"])
@jwt_required()
def reports():
    return jsonify({"reports": serialize_document(list_reports(get_jwt_identity()))})


@workspace_bp.route("/connectors", methods=["GET", "POST"])
@jwt_required()
def connectors():
    user_id = get_jwt_identity()
    if request.method == "GET":
        return jsonify({"connectors": serialize_document(list_connectors(user_id))})
    payload = request.get_json(silent=True) or {}
    connector = upsert_connector(user_id, payload)
    return jsonify({"connector": serialize_document(connector)}), 201


@workspace_bp.route("/notifications", methods=["GET"])
@jwt_required()
def notifications():
    return jsonify({"notifications": serialize_document(list_notifications(get_jwt_identity()))})


@workspace_bp.route("/notifications/<notification_id>/read", methods=["POST"])
@jwt_required()
def read_notification(notification_id):
    doc = mark_notification_read(get_jwt_identity(), notification_id)
    if not doc:
        return jsonify({"error": "Notification not found"}), 404
    return jsonify({"notification": serialize_document(doc)})
