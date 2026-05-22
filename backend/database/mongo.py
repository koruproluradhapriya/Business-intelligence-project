import logging
import uuid
from copy import deepcopy
from datetime import UTC, datetime

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

_client = None
_db = None
_using_fallback = False
_last_error = None

CORE_COLLECTIONS = (
    "users",
    "datasets",
    "uploads",
    "dashboards",
    "analytics",
    "forecasts",
    "insights",
    "reports",
    "connectors",
    "chat_history",
    "notifications",
    "settings",
    "activity_logs",
    "exports",
    "user_sessions",
)


class MockCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, *args, **kwargs):
        if args:
            key_dir = args[0]
            if isinstance(key_dir, str):
                key_dir = [(key_dir, args[1] if len(args) > 1 else 1)]
            reverse = any(d == -1 for _, d in key_dir)
            key = key_dir[0][0] if key_dir else None
            if key:
                self._docs.sort(
                    key=lambda d: (d.get(key) is None, d.get(key) or ""),
                    reverse=reverse,
                )
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    def skip(self, n):
        self._docs = self._docs[n:]
        return self

    def __iter__(self):
        return iter(deepcopy(self._docs))

    def __len__(self):
        return len(self._docs)


class MockCollection:
    def __init__(self, name):
        self.name = name
        self._data = {}

    def _match(self, doc, query):
        for key, val in (query or {}).items():
            if key.startswith("$"):
                continue
            dval = doc.get(key)
            if isinstance(val, dict):
                if "$gte" in val and not (dval is not None and dval >= val["$gte"]):
                    return False
                if "$lte" in val and not (dval is not None and dval <= val["$lte"]):
                    return False
                if "$lt" in val and not (dval is not None and dval < val["$lt"]):
                    return False
                if "$gt" in val and not (dval is not None and dval > val["$gt"]):
                    return False
                if "$in" in val and dval not in val["$in"]:
                    return False
            elif dval != val:
                return False
        return True

    def _apply_projection(self, doc, projection):
        if not projection:
            return doc
        exclude = any(v == 0 for v in projection.values())
        if exclude:
            return {k: v for k, v in doc.items() if projection.get(k, 1) != 0}
        result = {"_id": doc.get("_id")}
        for k, v in projection.items():
            if v and k in doc:
                result[k] = doc[k]
        return result

    def find_one(self, query=None, projection=None, sort=None):
        docs = list(self._data.values())
        if sort:
            key_dir = sort if isinstance(sort, list) else [(sort, 1)]
            reverse = any(d == -1 for _, d in key_dir)
            key = key_dir[0][0] if key_dir else None
            if key:
                docs.sort(key=lambda d: (d.get(key) is None, d.get(key) or ""), reverse=reverse)
        for doc in docs:
            if self._match(doc, query or {}):
                return deepcopy(self._apply_projection(doc, projection))
        return None

    def find(self, query=None, projection=None, sort=None):
        matched = [
            deepcopy(self._apply_projection(doc, projection))
            for doc in self._data.values()
            if self._match(doc, query or {})
        ]
        cursor = MockCursor(matched)
        if sort:
            cursor.sort(sort)
        return cursor

    def insert_one(self, doc):
        doc = deepcopy(doc)
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        self._data[str(doc["_id"])] = doc

        class Result:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id

        return Result(doc["_id"])

    def insert_many(self, docs):
        ids = [self.insert_one(doc).inserted_id for doc in docs]

        class Result:
            def __init__(self, inserted_ids):
                self.inserted_ids = inserted_ids

        return Result(ids)

    def update_one(self, query, update, upsert=False):
        matched = 0
        modified = 0
        for key, doc in self._data.items():
            if self._match(doc, query):
                matched = 1
                if "$set" in update:
                    doc.update(update["$set"])
                if "$push" in update:
                    for field, value in update["$push"].items():
                        doc.setdefault(field, []).append(value)
                modified = 1
                break
        if not matched and upsert:
            new_doc = {**query, **(update.get("$set", {}))}
            self.insert_one(new_doc)
            matched = 1
            modified = 1

        class Result:
            def __init__(self, matched_count, modified_count):
                self.matched_count = matched_count
                self.modified_count = modified_count

        return Result(matched, modified)

    def replace_one(self, query, replacement, upsert=False):
        matched = 0
        modified = 0
        for key, doc in list(self._data.items()):
            if self._match(doc, query):
                oid = doc["_id"]
                new_doc = deepcopy(replacement)
                new_doc["_id"] = oid
                self._data[str(oid)] = new_doc
                matched = 1
                modified = 1
                break
        if not matched and upsert:
            self.insert_one(deepcopy(replacement))
            modified = 1

        class Result:
            def __init__(self, matched_count, modified_count):
                self.matched_count = matched_count
                self.modified_count = modified_count

        return Result(matched, modified)

    def delete_one(self, query):
        deleted = 0
        for key, doc in list(self._data.items()):
            if self._match(doc, query):
                del self._data[key]
                deleted = 1
                break

        class Result:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count

        return Result(deleted)

    def delete_many(self, query):
        deleted = 0
        to_del = [key for key, doc in self._data.items() if self._match(doc, query)]
        for key in to_del:
            del self._data[key]
            deleted += 1

        class Result:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count

        return Result(deleted)

    def count_documents(self, query=None):
        return sum(1 for doc in self._data.values() if self._match(doc, query or {}))

    def create_index(self, *args, **kwargs):
        return None


class MockDatabase:
    def __init__(self):
        self._collections = {}

    def __getitem__(self, name):
        return self._collections.setdefault(name, MockCollection(name))

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._collections.setdefault(name, MockCollection(name))

    def list_collection_names(self):
        return list(self._collections.keys())


def utcnow():
    return datetime.now(UTC)


def _use_fallback(reason):
    global _db, _using_fallback, _last_error
    _db = MockDatabase()
    _using_fallback = True
    _last_error = reason
    for name in CORE_COLLECTIONS:
        _db[name]
    logger.warning("Mongo fallback store enabled: %s", reason)


def validate_db_config(app):
    testing = bool(app.config.get("TESTING"))
    required = {
        "MONGO_URI": app.config.get("MONGO_URI", ""),
        "DATABASE_NAME": app.config.get("DATABASE_NAME") or app.config.get("MONGO_DB_NAME", ""),
        "SECRET_KEY": app.config.get("SECRET_KEY", ""),
        "JWT_SECRET_KEY": app.config.get("JWT_SECRET_KEY", ""),
    }
    placeholders = ("your-", "<user>", "<password>", "xxxxx", "change-in-prod")
    invalid = []
    for key, value in required.items():
        text = str(value or "").strip()
        if not text:
            invalid.append(key)
            continue
        if not testing and any(token in text for token in placeholders):
            invalid.append(key)
    if invalid:
        raise ValueError(f"Missing or placeholder configuration values: {', '.join(sorted(set(invalid)))}")


def init_db(app):
    global _client, _db, _using_fallback, _last_error

    allow_fallback = bool(app.config.get("ALLOW_DB_FALLBACK", False))
    try:
        validate_db_config(app)
    except ValueError as exc:
        if allow_fallback:
            _use_fallback(str(exc))
            return
        raise

    uri = app.config["MONGO_URI"]
    requested_database_name = app.config.get("DATABASE_NAME") or app.config.get("MONGO_DB_NAME")
    connect_kwargs = {
        "serverSelectionTimeoutMS": int(app.config.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", 15000)),
        "connectTimeoutMS": int(app.config.get("MONGO_CONNECT_TIMEOUT_MS", 15000)),
        "socketTimeoutMS": int(app.config.get("MONGO_SOCKET_TIMEOUT_MS", 30000)),
        "retryWrites": True,
        "maxPoolSize": int(app.config.get("MONGO_MAX_POOL_SIZE", 30)),
        "minPoolSize": int(app.config.get("MONGO_MIN_POOL_SIZE", 1)),
        "appname": "InsightIQ",
    }
    if "mongodb+srv" in uri or "mongodb.net" in uri:
        connect_kwargs["tls"] = True

    last_exc = None
    for attempt in range(1, int(app.config.get("MONGO_CONNECT_RETRIES", 3)) + 1):
        try:
            _client = MongoClient(uri, **connect_kwargs)
            _client.admin.command("ping")
            resolved_database_name = _resolve_database_name(_client, requested_database_name)
            _db = _client[resolved_database_name]
            _using_fallback = False
            _last_error = None
            _create_collections()
            _create_indexes()
            logger.info(
                "MongoDB connected to database '%s' on attempt %s",
                resolved_database_name,
                attempt,
            )
            return
        except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError, Exception) as exc:
            last_exc = exc
            logger.warning("MongoDB connection attempt %s failed: %s", attempt, exc)

    if allow_fallback:
        _use_fallback(str(last_exc))
        return
    raise RuntimeError(f"Unable to connect to MongoDB Atlas after retries: {last_exc}")


def get_client():
    if _client is None and not _using_fallback:
        raise RuntimeError("MongoDB client is not initialized.")
    return _client


def get_db():
    if _db is None:
        raise RuntimeError("MongoDB database is not initialized.")
    return _db


def get_collection(name):
    return get_db()[name]


def get_collection_names():
    db = get_db()
    try:
        names = set(db.list_collection_names())
    except Exception:
        names = set()
    return sorted(names.union(CORE_COLLECTIONS))


def is_using_fallback():
    return _using_fallback


def get_connection_status():
    return {
        "connected": _db is not None and not _using_fallback,
        "fallback": _using_fallback,
        "collections": get_collection_names() if _db is not None else list(CORE_COLLECTIONS),
        "lastError": _last_error,
    }


def health_check():
    if _using_fallback:
        return {
            "ok": True,
            "mode": "fallback",
            "collections": get_collection_names(),
            "lastError": _last_error,
        }
    client = get_client()
    client.admin.command("ping")
    return {
        "ok": True,
        "mode": "atlas",
        "database": get_db().name,
        "collections": get_collection_names(),
    }


def ensure_indexes():
    _create_indexes()


def to_object_id(value):
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def build_id_query(value):
    oid = to_object_id(value)
    return {"$in": [value, oid]} if oid is not None else value


def find_one_by_id(collection_name, value, extra_query=None):
    query = dict(extra_query or {})
    query["_id"] = build_id_query(value)
    return get_collection(collection_name).find_one(query)


def delete_one_by_id(collection_name, value, extra_query=None):
    query = dict(extra_query or {})
    query["_id"] = build_id_query(value)
    return get_collection(collection_name).delete_one(query)


def serialize_document(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_document(item) for item in doc]
    if isinstance(doc, dict):
        payload = {}
        for key, value in doc.items():
            if key == "_id":
                payload[key] = str(value)
            else:
                payload[key] = serialize_document(value)
        return payload
    if isinstance(doc, datetime):
        return doc.isoformat()
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc


def safe_insert_one(collection_name, payload):
    try:
        return get_collection(collection_name).insert_one(payload)
    except DuplicateKeyError:
        logger.info("Duplicate insert skipped for collection '%s'", collection_name)
        return None


def _create_collections():
    db = get_db()
    for name in CORE_COLLECTIONS:
        db[name]


def _create_indexes():
    db = get_db()
    try:
        db.users.create_index("email", unique=True)
        db.users.create_index("createdAt")
        db.uploads.create_index([("userId", 1), ("uploadedAt", -1)])
        db.datasets.create_index([("userId", 1), ("uploadId", 1)], unique=True)
        db.dashboards.create_index([("userId", 1), ("uploadId", 1)], unique=True)
        db.analytics.create_index([("userId", 1), ("createdAt", -1)])
        db.analytics.create_index([("userId", 1), ("uploadId", 1)], unique=True)
        db.forecasts.create_index([("userId", 1), ("uploadId", 1)], unique=True)
        db.insights.create_index([("userId", 1), ("sourceType", 1), ("createdAt", -1)])
        db.reports.create_index([("userId", 1), ("createdAt", -1)])
        db.connectors.create_index([("userId", 1), ("name", 1)], unique=True)
        db.chat_history.create_index([("userId", 1), ("createdAt", -1)])
        db.notifications.create_index([("userId", 1), ("createdAt", -1)])
        db.settings.create_index("userId", unique=True)
        db.activity_logs.create_index([("userId", 1), ("createdAt", -1)])
        db.exports.create_index([("userId", 1), ("createdAt", -1)])
        db.user_sessions.create_index([("userId", 1), ("lastSeenAt", -1)])
        db.user_sessions.create_index("sessionToken", unique=True)
    except Exception as exc:
        logger.warning("Index creation issue: %s", exc)


def _resolve_database_name(client, requested_name):
    try:
        existing_names = client.list_database_names()
    except Exception:
        return requested_name

    lowered = requested_name.lower()
    for name in existing_names:
        if name.lower() == lowered:
            if name != requested_name:
                logger.warning(
                    "Using existing database '%s' because Atlas already has the same database with different casing than '%s'.",
                    name,
                    requested_name,
                )
            return name
    return requested_name
