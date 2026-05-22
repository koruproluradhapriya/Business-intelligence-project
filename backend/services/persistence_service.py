from copy import deepcopy
import uuid

from database.mongo import (
    delete_one_by_id,
    find_one_by_id,
    get_collection,
    safe_insert_one,
    serialize_document,
    utcnow,
)


def default_settings(user_id):
    return {
        "userId": user_id,
        "theme": "dark",
        "dashboardLayout": {"mode": "adaptive", "widgets": []},
        "notifications": {"email": False, "product": True},
        "connectors": [],
        "exports": {"format": "json"},
        "updatedAt": utcnow(),
    }


def ensure_user_defaults(user_doc):
    user_id = str(user_doc["_id"])
    settings = get_collection("settings").find_one({"userId": user_id})
    if not settings:
        get_collection("settings").insert_one(default_settings(user_id))

    welcome = get_collection("notifications").find_one({"userId": user_id, "type": "welcome"})
    if not welcome:
        get_collection("notifications").insert_one(
            {
                "userId": user_id,
                "type": "welcome",
                "title": "Welcome to InsightIQ",
                "message": "Your Atlas-backed workspace is ready for uploads, dashboards, forecasts, and chat history.",
                "read": False,
                "createdAt": utcnow(),
            }
        )


def record_activity(user_id, action, entity_type=None, entity_id=None, metadata=None):
    get_collection("activity_logs").insert_one(
        {
            "userId": user_id,
            "action": action,
            "entityType": entity_type,
            "entityId": entity_id,
            "metadata": metadata or {},
            "createdAt": utcnow(),
        }
    )


def touch_session(user_id, request_meta=None):
    session_token = f"{user_id}:{uuid.uuid4()}"
    get_collection("user_sessions").insert_one(
        {
            "userId": user_id,
            "sessionToken": session_token,
            "requestMeta": request_meta or {},
            "startedAt": utcnow(),
            "lastSeenAt": utcnow(),
            "status": "active",
        }
    )
    return session_token


def update_user_settings(user_id, payload):
    existing = get_collection("settings").find_one({"userId": user_id}) or default_settings(user_id)
    merged = {**existing, **payload, "userId": user_id, "updatedAt": utcnow()}
    get_collection("settings").replace_one({"userId": user_id}, merged, upsert=True)
    record_activity(user_id, "settings.updated", "settings", user_id, {"keys": sorted(payload.keys())})
    return merged


def get_user_settings(user_id):
    settings = get_collection("settings").find_one({"userId": user_id})
    if settings:
        return settings
    defaults = default_settings(user_id)
    get_collection("settings").insert_one(defaults)
    return defaults


def persist_upload_bundle(user_id, upload_id, upload_doc, analytics_doc):
    upload_type = analytics_doc.get("uploadType", "auto")
    dataset_doc = {
        "userId": user_id,
        "uploadId": upload_id,
        "name": analytics_doc.get("dataset", {}).get("name", upload_doc.get("fileName")),
        "uploadType": upload_type,
        "columns": upload_doc.get("columns", []),
        "schema": upload_doc.get("schema", {}),
        "semanticGroups": upload_doc.get("semanticGroups", {}),
        "inferredSchema": upload_doc.get("inferredSchema", {}),
        "rowCount": upload_doc.get("rowCount", 0),
        "status": upload_doc.get("status", "processed"),
        "fileMetadata": upload_doc.get("fileMetadata", {}),
        "updatedAt": utcnow(),
        "createdAt": upload_doc.get("uploadedAt", utcnow()),
    }
    get_collection("datasets").replace_one({"userId": user_id, "uploadId": upload_id}, dataset_doc, upsert=True)

    dashboard_doc = {
        "userId": user_id,
        "uploadId": upload_id,
        "datasetName": dataset_doc["name"],
        "kpis": analytics_doc.get("kpis", []),
        "charts": analytics_doc.get("charts", []),
        "executiveSummary": analytics_doc.get("executiveSummary", {}),
        "recommendations": analytics_doc.get("recommendations", []),
        "layout": get_user_settings(user_id).get("dashboardLayout", {"mode": "adaptive", "widgets": []}),
        "updatedAt": utcnow(),
        "createdAt": analytics_doc.get("createdAt", utcnow()),
    }
    get_collection("dashboards").replace_one({"userId": user_id, "uploadId": upload_id}, dashboard_doc, upsert=True)

    forecast_doc = {
        "userId": user_id,
        "uploadId": upload_id,
        "datasetName": dataset_doc["name"],
        **deepcopy(analytics_doc.get("forecast", {})),
        "generatedAt": utcnow(),
    }
    get_collection("forecasts").replace_one({"userId": user_id, "uploadId": upload_id}, forecast_doc, upsert=True)

    insight_docs = []
    for insight in analytics_doc.get("insights", []):
        insight_docs.append(
            {
                "userId": user_id,
                "uploadId": upload_id,
                "sourceType": "analytics",
                "datasetName": dataset_doc["name"],
                "insight": insight,
                "createdAt": utcnow(),
            }
        )
    if insight_docs:
        get_collection("insights").delete_many({"userId": user_id, "uploadId": upload_id, "sourceType": "analytics"})
        get_collection("insights").insert_many(insight_docs)

    report_doc = {
        "userId": user_id,
        "uploadId": upload_id,
        "datasetName": dataset_doc["name"],
        "title": f"{dataset_doc['name']} executive report",
        "summary": analytics_doc.get("executiveSummary", {}),
        "highlights": analytics_doc.get("insights", [])[:5],
        "createdAt": utcnow(),
        "updatedAt": utcnow(),
        "status": "ready",
    }
    get_collection("reports").replace_one({"userId": user_id, "uploadId": upload_id}, report_doc, upsert=True)

    export_doc = {
        "userId": user_id,
        "uploadId": upload_id,
        "datasetName": dataset_doc["name"],
        "type": "analytics_snapshot",
        "format": "json",
        "status": "available",
        "createdAt": utcnow(),
    }
    get_collection("exports").replace_one(
        {"userId": user_id, "uploadId": upload_id, "type": "analytics_snapshot"},
        export_doc,
        upsert=True,
    )

    record_activity(
        user_id,
        "dataset.processed",
        "upload",
        upload_id,
        {"datasetName": dataset_doc["name"], "uploadType": upload_type, "rowCount": upload_doc.get("rowCount", 0)},
    )
    safe_insert_one(
        "notifications",
        {
            "userId": user_id,
            "type": "dataset_processed",
            "title": "Dataset processed",
            "message": f"{dataset_doc['name']} is ready for dashboard, forecast, and AI analysis.",
            "read": False,
            "createdAt": utcnow(),
        },
    )


def save_chat_exchange(user_id, question, answer_payload, analytics_snapshot=None):
    chat_doc = {
        "userId": user_id,
        "question": question,
        "answer": answer_payload.get("answer", ""),
        "answerPayload": deepcopy(answer_payload),
        "analyticsSnapshot": {
            "dataset": deepcopy((analytics_snapshot or {}).get("dataset", {})),
            "primaryMetric": (analytics_snapshot or {}).get("dataset", {}).get("primaryMetric"),
        },
        "createdAt": utcnow(),
    }
    get_collection("chat_history").insert_one(chat_doc)
    get_collection("insights").insert_one(
        {
            "userId": user_id,
            "sourceType": "chat",
            "datasetName": (analytics_snapshot or {}).get("dataset", {}).get("name"),
            "insight": {"question": question, "answer": answer_payload.get("answer", "")},
            "createdAt": utcnow(),
        }
    )
    record_activity(user_id, "chat.asked", "chat_history", None, {"question": question})
    return chat_doc


def latest_analytics(user_id):
    return get_collection("analytics").find_one({"userId": user_id}, sort=[("createdAt", -1)])


def latest_dashboard(user_id):
    return get_collection("dashboards").find_one({"userId": user_id}, sort=[("updatedAt", -1)])


def latest_forecast(user_id):
    return get_collection("forecasts").find_one({"userId": user_id}, sort=[("generatedAt", -1)])


def latest_recommendations(user_id):
    analytics = latest_analytics(user_id)
    recommendations = (analytics or {}).get("recommendations", [])
    if recommendations:
        get_collection("insights").replace_one(
            {"userId": user_id, "sourceType": "recommendations_cache"},
            {
                "userId": user_id,
                "sourceType": "recommendations_cache",
                "recommendations": recommendations,
                "createdAt": utcnow(),
            },
            upsert=True,
        )
    return recommendations


def list_chat_history(user_id, limit=20):
    return list(get_collection("chat_history").find({"userId": user_id}).sort([("createdAt", -1)]).limit(limit))


def list_notifications(user_id, limit=20):
    return list(get_collection("notifications").find({"userId": user_id}).sort([("createdAt", -1)]).limit(limit))


def mark_notification_read(user_id, notification_id):
    notification = find_one_by_id("notifications", notification_id, {"userId": user_id})
    if not notification:
        return None
    get_collection("notifications").update_one(
        {"userId": user_id, "_id": notification["_id"]},
        {"$set": {"read": True, "readAt": utcnow()}},
    )
    return find_one_by_id("notifications", notification["_id"], {"userId": user_id})


def list_reports(user_id, limit=20):
    return list(get_collection("reports").find({"userId": user_id}).sort([("createdAt", -1)]).limit(limit))


def list_connectors(user_id):
    return list(get_collection("connectors").find({"userId": user_id}).sort([("createdAt", -1)]))


def upsert_connector(user_id, payload):
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Connector name is required.")
    connector = {
        "userId": user_id,
        "name": name,
        "type": payload.get("type", "custom"),
        "status": payload.get("status", "active"),
        "config": payload.get("config", {}),
        "updatedAt": utcnow(),
        "createdAt": payload.get("createdAt", utcnow()),
    }
    get_collection("connectors").replace_one({"userId": user_id, "name": name}, connector, upsert=True)
    record_activity(user_id, "connector.saved", "connectors", name, {"type": connector["type"]})
    return get_collection("connectors").find_one({"userId": user_id, "name": name})


def delete_upload_bundle(user_id, upload_id):
    delete_one_by_id("uploads", upload_id, {"userId": user_id})
    get_collection("datasets").delete_many({"userId": user_id, "uploadId": upload_id})
    get_collection("analytics").delete_many({"userId": user_id, "uploadId": upload_id})
    get_collection("dashboards").delete_many({"userId": user_id, "uploadId": upload_id})
    get_collection("forecasts").delete_many({"userId": user_id, "uploadId": upload_id})
    get_collection("insights").delete_many({"userId": user_id, "uploadId": upload_id})
    get_collection("reports").delete_many({"userId": user_id, "uploadId": upload_id})
    get_collection("exports").delete_many({"userId": user_id, "uploadId": upload_id})
    record_activity(user_id, "dataset.deleted", "upload", upload_id)


def shape_report_payload(report):
    return serialize_document(report)
