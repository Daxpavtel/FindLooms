from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.db import get_db, to_object_id
from app.repositories.settings import get_setting
from app.services.events import emit_event


def run_archive_check() -> Dict[str, Any]:
    """
    Daily archiving routine:
    Identifies found items that:
    1. Are unclaimed or unmatched (status in ['Unmatched', 'Possible Match'])
    2. Have not been returned or archived
    3. Creation date is older than retention_days (default 30)
    Sets 'archive_eligible = True' so staff can review and dispose/donate/archive.
    Never hard deletes items.
    """
    db = get_db()
    retention_days = int(get_setting("retention_days", 30))
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    query = {
        "status": {"$in": ["Unmatched", "Possible Match"]},
        "archive_eligible": False,
        "created_at": {"$lte": cutoff_date}
    }

    eligible_items = list(db.found_items.find(query, {"_id": 1, "reference_no": 1}))
    count = 0
    for item in eligible_items:
        db.found_items.update_one(
            {"_id": item["_id"]},
            {"$set": {"archive_eligible": True, "updated_at": datetime.utcnow()}}
        )
        emit_event("flagged_archive_eligible", "found_item", item["_id"], payload={
            "reference_no": item.get("reference_no"),
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": retention_days
        })
        count += 1

    return {
        "flagged_count": count,
        "retention_days": retention_days,
        "cutoff_date": cutoff_date
    }


def get_archive_eligible_items() -> List[Dict[str, Any]]:
    """Retrieve all found items flagged as eligible for archiving/disposal."""
    from app.repositories.items import _populate_item_relations
    db = get_db()
    items = list(db.found_items.find({"archive_eligible": True, "status": {"$ne": "Archived"}}).sort("created_at", 1))
    for it in items:
        _populate_item_relations(it, is_lost=False)
    return items


def execute_disposal_action(
    found_id: Any,
    action_type: str,
    actor_id: Any,
    notes: str = ""
) -> bool:
    """
    Staff/Admin action on archive-eligible items:
    action_type: 'Archive', 'Donate', 'Dispose'
    Transitions status to Archived, records action details and audit log.
    """
    db = get_db()
    f_oid = to_object_id(found_id)
    if not f_oid:
        return False

    item = db.found_items.find_one({"_id": f_oid})
    if not item:
        return False

    now = datetime.utcnow()
    db.found_items.update_one(
        {"_id": f_oid},
        {
            "$set": {
                "status": "Archived",
                "archive_eligible": True,
                "disposal_action": action_type,
                "disposed_at": now,
                "disposal_notes": notes.strip(),
                "updated_at": now
            }
        }
    )

    emit_event("item_disposed", "found_item", f_oid, actor_id=actor_id, payload={
        "reference_no": item.get("reference_no"),
        "disposal_action": action_type,
        "notes": notes
    })
    return True
