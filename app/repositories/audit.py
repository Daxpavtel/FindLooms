from datetime import datetime
from typing import Optional, Any, Dict, List
from bson import ObjectId
from app.db import get_db, to_object_id


def log_event(
    action: str,
    entity_type: str,
    entity_id: Optional[Any] = None,
    actor_id: Optional[Any] = None,
    details: Optional[Dict[str, Any]] = None
) -> ObjectId:
    """
    Append-only audit log entry.
    Never updated or deleted.
    """
    db = get_db()
    entry = {
        "action": action,
        "entity_type": entity_type,
        "entity_id": to_object_id(entity_id) if entity_id else None,
        "actor_id": to_object_id(actor_id) if actor_id else None,
        "details": details or {},
        "timestamp": datetime.utcnow()
    }
    result = db.audit_logs.insert_one(entry)
    return result.inserted_id


def get_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    actor_id: Optional[Any] = None,
    limit: int = 50,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """Retrieve audit logs with optional filtering and pagination."""
    db = get_db()
    query: Dict[str, Any] = {}
    if entity_type:
        query["entity_type"] = entity_type
    if action:
        query["action"] = action
    if actor_id:
        oid = to_object_id(actor_id)
        if oid:
            query["actor_id"] = oid

    # Join or populate actor details if available
    logs = list(db.audit_logs.find(query).sort("timestamp", -1).skip(skip).limit(limit))
    for log in logs:
        if log.get("actor_id"):
            actor = db.users.find_one({"_id": log["actor_id"]}, {"name": 1, "email": 1, "role": 1})
            log["actor"] = actor
        else:
            log["actor"] = {"name": "System", "email": "system@lostfound.local", "role": "system"}
    return logs


def count_audit_logs(entity_type: Optional[str] = None, action: Optional[str] = None) -> int:
    """Count audit logs with filters."""
    db = get_db()
    query: Dict[str, Any] = {}
    if entity_type:
        query["entity_type"] = entity_type
    if action:
        query["action"] = action
    return db.audit_logs.count_documents(query)
