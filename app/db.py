import re
from typing import Optional, Any
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from flask import current_app, g


def get_db():
    """Get the current MongoDB database instance."""
    from flask import has_app_context
    if has_app_context():
        if "db" not in g:
            if current_app.config.get("TEST_MONGO_CLIENT") is not None:
                client = current_app.config["TEST_MONGO_CLIENT"]
                db_name = current_app.config.get("TEST_DB_NAME", "lostfound_test_db")
                g.db = client[db_name]
                return g.db
            mongo_uri = current_app.config["MONGO_URI"]
            client = MongoClient(mongo_uri)
            db_name = mongo_uri.split("/")[-1].split("?")[0] or "lostfound_db"
            g.mongo_client = client
            g.db = client[db_name]
        return g.db
    else:
        # Fallback when running standalone scripts, tests, or seed.py
        from app.config import Config
        mongo_uri = Config.MONGO_URI
        client = MongoClient(mongo_uri)
        db_name = mongo_uri.split("/")[-1].split("?")[0] or "lostfound_db"
        return client[db_name]


def close_db(e=None):
    """Close MongoDB connection on app context teardown."""
    from flask import has_app_context
    if has_app_context() and current_app.config.get("TEST_MONGO_CLIENT") is not None:
        g.pop("db", None)
        return
    client = g.pop("mongo_client", None)
    g.pop("db", None)
    if client is not None:
        client.close()


def to_object_id(val: Any) -> Optional[ObjectId]:
    """
    Safely converts a value to ObjectId.
    Rejects dicts, operators, non-strings, or malformed strings to prevent NoSQL injection.
    """
    if isinstance(val, ObjectId):
        return val
    if not isinstance(val, str):
        return None
    val = val.strip()
    if len(val) == 24 and re.fullmatch(r"^[0-9a-fA-F]{24}$", val):
        try:
            return ObjectId(val)
        except Exception:
            return None
    return None


def str_object_id(val: Any) -> Optional[str]:
    """Convert an ObjectId or string to string safely."""
    if val is None:
        return None
    return str(val)


def init_db(mongo_uri: str) -> None:
    """
    Idempotently initialize all MongoDB collections, indexes, and default settings.
    """
    client = MongoClient(mongo_uri)
    db_name = mongo_uri.split("/")[-1].split("?")[0] or "lostfound_db"
    db = client[db_name]

    # 1. users: unique index on email
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("role", ASCENDING)])

    # 2. categories: unique index on name
    db.categories.create_index([("name", ASCENDING)], unique=True)

    # 3. locations: index on name, building, zone
    db.locations.create_index([("name", ASCENDING)])
    db.locations.create_index([("building", ASCENDING)])
    db.locations.create_index([("zone", ASCENDING)])

    # 4. lost_items: reference_no, reporter_id, category_id, location, stage, created_at
    db.lost_items.create_index([("reference_no", ASCENDING)], unique=True)
    db.lost_items.create_index([("reporter_id", ASCENDING)])
    db.lost_items.create_index([("category_id", ASCENDING)])
    db.lost_items.create_index([("last_seen_location_id", ASCENDING)])
    db.lost_items.create_index([("stage", ASCENDING)])
    db.lost_items.create_index([("lost_date", DESCENDING)])
    db.lost_items.create_index([("created_at", DESCENDING)])

    # 5. found_items: reference_no, finder_id, category_id, location, status, created_at
    db.found_items.create_index([("reference_no", ASCENDING)], unique=True)
    db.found_items.create_index([("finder_id", ASCENDING)])
    db.found_items.create_index([("category_id", ASCENDING)])
    db.found_items.create_index([("found_location_id", ASCENDING)])
    db.found_items.create_index([("status", ASCENDING)])
    db.found_items.create_index([("found_datetime", DESCENDING)])
    db.found_items.create_index([("created_at", DESCENDING)])
    db.found_items.create_index([("archive_eligible", ASCENDING)])

    # 6. match_candidates: compound unique index on (lost_id, found_id), score
    db.match_candidates.create_index([("lost_id", ASCENDING), ("found_id", ASCENDING)], unique=True)
    db.match_candidates.create_index([("score", DESCENDING)])
    db.match_candidates.create_index([("is_dismissed", ASCENDING)])

    # 7. claims: reference_no, claimant_id, found_id, status, created_at
    db.claims.create_index([("reference_no", ASCENDING)], unique=True)
    db.claims.create_index([("claimant_id", ASCENDING)])
    db.claims.create_index([("found_id", ASCENDING), ("status", ASCENDING)])
    db.claims.create_index([("lost_id", ASCENDING)])
    db.claims.create_index([("created_at", DESCENDING)])

    # 8. handovers: claim_id
    db.handovers.create_index([("claim_id", ASCENDING)], unique=True)

    # 9. audit_logs: actor_id, entity_type, entity_id, timestamp (insert-only)
    db.audit_logs.create_index([("timestamp", DESCENDING)])
    db.audit_logs.create_index([("entity_type", ASCENDING), ("entity_id", ASCENDING)])
    db.audit_logs.create_index([("actor_id", ASCENDING)])

    # 10. settings: unique index on key
    db.settings.create_index([("key", ASCENDING)], unique=True)

    # 11. counters: sequence name
    # Ensure default settings are present
    default_settings = [
        {"key": "retention_days", "value": 30, "description": "Days before unclaimed found items become archive-eligible"},
        {"key": "strong_match_threshold", "value": 60, "description": "Match score percentage threshold to trigger Possible Match status"},
        {"key": "duplicate_window_days", "value": 2, "description": "Window in days to warn for potential duplicate reports"}
    ]
    for setting in default_settings:
        db.settings.update_one(
            {"key": setting["key"]},
            {"$setOnInsert": setting},
            upsert=True
        )

    # Initialize counters if not present
    for seq_name in ["LST", "FND", "CLM"]:
        db.counters.update_one(
            {"_id": seq_name},
            {"$setOnInsert": {"seq": 0}},
            upsert=True
        )

    client.close()
