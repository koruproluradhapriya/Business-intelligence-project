from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.connection import get_collection
from ai_models.inventory_ai import analyze_inventory
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

DEMO_INVENTORY = [
    {"product": "Analytics Pro", "stock": 85, "reorderLevel": 50, "avgDailySales": 28, "price": 20.0},
    {"product": "DataViz Suite", "stock": 210, "reorderLevel": 40, "avgDailySales": 17, "price": 20.0},
    {"product": "Insight Engine", "stock": 32, "reorderLevel": 60, "avgDailySales": 14, "price": 30.0},
    {"product": "Report Builder", "stock": 190, "reorderLevel": 30, "avgDailySales": 12, "price": 20.0},
    {"product": "ML Forecaster", "stock": 14, "reorderLevel": 45, "avgDailySales": 10, "price": 40.0},
    {"product": "Dashboard Pro", "stock": 320, "reorderLevel": 20, "avgDailySales": 8, "price": 20.0},
]


@inventory_bp.route('/status', methods=['GET'])
@jwt_required()
def inventory_status():
    user_id = get_jwt_identity()

    # Try to get real inventory analytics
    inv_analytics = get_collection('analytics').find_one(
        {"userId": user_id, "uploadType": "inventory"},
        sort=[("createdAt", -1)]
    )

    if inv_analytics and inv_analytics.get('inventoryItems'):
        items_raw = inv_analytics['inventoryItems']
    else:
        items_raw = DEMO_INVENTORY

    analyzed = analyze_inventory(items_raw)

    critical = sum(1 for i in analyzed if i['status'] == 'critical')
    warning = sum(1 for i in analyzed if i['status'] == 'warning')
    healthy = sum(1 for i in analyzed if i['status'] == 'healthy')
    overstock = sum(1 for i in analyzed if i['status'] == 'overstock')

    return jsonify({
        "items": analyzed,
        "summary": {
            "critical": critical,
            "warning": warning,
            "healthy": healthy,
            "overstock": overstock,
            "total": len(analyzed),
        }
    })
