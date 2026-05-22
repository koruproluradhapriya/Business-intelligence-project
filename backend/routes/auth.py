from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from database.connection import find_one_by_id, get_collection
import bcrypt
from datetime import datetime

from services.persistence_service import ensure_user_defaults, record_activity, touch_session
from database.mongo import utcnow

auth_bp = Blueprint('auth', __name__)


def _to_str_id(doc):
    """Convert _id to string regardless of type (ObjectId or str UUID)."""
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc


def _serialize_user(user):
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "businessName": user.get("businessName", ""),
        "plan": user.get("plan", "free"),
        "createdAt": user.get("createdAt", "").isoformat() if isinstance(user.get("createdAt"), datetime) else "",
    }


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    business_name = data.get('businessName', '').strip()

    if not all([name, email, password]):
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    users = get_collection('users')
    if users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_doc = {
        "name": name,
        "email": email,
        "password": pw_hash,
        "businessName": business_name,
        "plan": "free",
        "createdAt": utcnow(),
    }
    result = users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    ensure_user_defaults(user_doc)

    user_id = str(result.inserted_id)
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    session_token = touch_session(user_id, {"source": "register"})
    record_activity(user_id, "auth.registered", "users", user_id, {"email": email, "sessionToken": session_token})

    return jsonify({
        "message": "Account created successfully",
        "user": _serialize_user(user_doc),
        "accessToken": access_token,
        "refreshToken": refresh_token,
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    users = get_collection('users')
    user = users.find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"error": "Invalid email or password"}), 401

    user_id = str(user['_id'])
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    session_token = touch_session(user_id, {"source": "login"})
    record_activity(user_id, "auth.logged_in", "users", user_id, {"sessionToken": session_token})

    return jsonify({
        "message": "Login successful",
        "user": _serialize_user(user),
        "accessToken": access_token,
        "refreshToken": refresh_token,
    })


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = find_one_by_id('users', user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": _serialize_user(user)})


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"accessToken": access_token})


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    allowed = {k: v for k, v in data.items() if k in ('name', 'businessName')}
    if not allowed:
        return jsonify({"error": "No valid fields to update"}), 400

    user = find_one_by_id("users", user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    get_collection('users').update_one({"_id": user["_id"]}, {"$set": {**allowed, "updatedAt": utcnow()}})
    record_activity(user_id, "profile.updated", "users", user_id, {"fields": sorted(allowed.keys())})
    return jsonify({"message": "Profile updated"})
