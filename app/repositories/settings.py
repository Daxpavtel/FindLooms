from typing import Any, Dict
from app.db import get_db


def get_setting(key: str, default: Any = None) -> Any:
    """Retrieve setting value by key."""
    db = get_db()
    doc = db.settings.find_one({"key": key})
    if doc and "value" in doc:
        return doc["value"]
    return default


def get_all_settings() -> Dict[str, Any]:
    """Retrieve all system settings as a dictionary."""
    db = get_db()
    docs = db.settings.find()
    result = {}
    for doc in docs:
        result[doc["key"]] = doc.get("value")
    return result


def update_setting(key: str, value: Any) -> bool:
    """Update or insert a system setting."""
    db = get_db()
    res = db.settings.update_one(
        {"key": key},
        {"$set": {"value": value}},
        upsert=True
    )
    return res.acknowledged
