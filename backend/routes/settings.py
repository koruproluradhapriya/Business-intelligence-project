from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database.connection import serialize_document
from services.persistence_service import get_user_settings, update_user_settings

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("", methods=["GET"])
@jwt_required()
def get_settings():
    return jsonify({"settings": serialize_document(get_user_settings(get_jwt_identity()))})


@settings_bp.route("", methods=["PUT"])
@jwt_required()
def save_settings():
    payload = request.get_json(silent=True) or {}
    return jsonify({"settings": serialize_document(update_user_settings(get_jwt_identity(), payload))})
