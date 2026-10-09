from datetime import datetime
from typing import Dict, Any, List
from app.db import get_db, to_object_id
from app.repositories.items import SAFE_LOST_PROJECTION, SAFE_FOUND_PROJECTION, _populate_item_relations


def upsert_match_candidate(
    lost_id: Any,
    found_id: Any,
    score: int,
    breakdown: Dict[str, Any]
) -> Dict[str, Any]:
    """Insert or update a match candidate with score and breakdown."""
    db = get_db()
    l_oid = to_object_id(lost_id)
    f_oid = to_object_id(found_id)
    if not l_oid or not f_oid:
        return {}

    now = datetime.utcnow()
    res = db.match_candidates.find_one_and_update(
        {"lost_id": l_oid, "found_id": f_oid},
        {
            "$set": {
                "score": score,
                "breakdown": breakdown,
                "updated_at": now
            },
            "$setOnInsert": {
                "is_dismissed": False,
                "created_at": now
            }
        },
        upsert=True,
        return_document=True
    )
    return res


def get_matches_for_lost_item(lost_id: Any, min_score: int = 0, is_staff: bool = False) -> List[Dict[str, Any]]:
    """Retrieve all match candidates for a lost item with populated found item data."""
    l_oid = to_object_id(lost_id)
    if not l_oid:
        return []
    db = get_db()
    matches = list(db.match_candidates.find({
        "lost_id": l_oid,
        "is_dismissed": False,
        "score": {"$gte": min_score}
    }).sort("score", -1))

    for m in matches:
        proj = None if is_staff else SAFE_FOUND_PROJECTION
        found = db.found_items.find_one({"_id": m["found_id"]}, proj)
        if found:
            _populate_item_relations(found, is_lost=False)
            m["found_item"] = found
        else:
            m["found_item"] = None
    return [m for m in matches if m["found_item"] is not None]


def get_matches_for_found_item(found_id: Any, min_score: int = 0, is_staff: bool = False) -> List[Dict[str, Any]]:
    """Retrieve all match candidates for a found item with populated lost item data."""
    f_oid = to_object_id(found_id)
    if not f_oid:
        return []
    db = get_db()
    matches = list(db.match_candidates.find({
        "found_id": f_oid,
        "is_dismissed": False,
        "score": {"$gte": min_score}
    }).sort("score", -1))

    for m in matches:
        proj = None if is_staff else SAFE_LOST_PROJECTION
        lost = db.lost_items.find_one({"_id": m["lost_id"]}, proj)
        if lost:
            _populate_item_relations(lost, is_lost=True)
            m["lost_item"] = lost
        else:
            m["lost_item"] = None
    return [m for m in matches if m["lost_item"] is not None]


def count_matches_for_lost(lost_id: Any, min_score: int = 50) -> int:
    """Count match candidates meeting score threshold for a lost item."""
    l_oid = to_object_id(lost_id)
    if not l_oid:
        return 0
    db = get_db()
    return db.match_candidates.count_documents({
        "lost_id": l_oid,
        "is_dismissed": False,
        "score": {"$gte": min_score}
    })


def dismiss_match(match_id: Any) -> bool:
    """Mark a match candidate as dismissed."""
    oid = to_object_id(match_id)
    if not oid:
        return False
    db = get_db()
    res = db.match_candidates.update_one({"_id": oid}, {"$set": {"is_dismissed": True}})
    return res.modified_count > 0
