from typing import Tuple, Optional, Any
from app.db import get_db, to_object_id
from app.services.events import emit_event
from app.repositories.items import (
    get_lost_item_by_id,
    get_found_item_by_id,
    update_lost_item,
    update_found_item
)

# Allowed stage transitions
LOST_TRANSITIONS = {
    "Reported": {"Possible Match", "Under Review", "Archived"},
    "Possible Match": {"Under Review", "Archived"},
    "Under Review": {"Returned", "Archived"},
    "Returned": {"Archived"},
    "Archived": set()
}

FOUND_TRANSITIONS = {
    "Unmatched": {"Possible Match", "Claimed", "Archived"},
    "Possible Match": {"Claimed", "Archived"},
    "Claimed": {"Returned", "Archived"},
    "Returned": {"Archived"},
    "Archived": set()
}

CLAIM_TRANSITIONS = {
    "New": {"Under Review", "Approved", "Rejected"},
    "Under Review": {"Approved", "Rejected"},
    "Approved": {"Returned", "Rejected"},
    "Rejected": set(),
    "Returned": set()
}


# ==========================================
# LOST ITEM WORKFLOW
# ==========================================

def transition_lost_stage(
    lost_id: Any,
    new_stage: str,
    actor_id: Optional[Any] = None,
    notes: str = ""
) -> Tuple[bool, str]:
    """
    Safely transitions a lost item to new_stage.
    Enforces valid state machine transition and writes an immutable audit log.
    """
    item = get_lost_item_by_id(lost_id, is_staff=True)
    if not item:
        return False, "Lost report not found."

    current_stage = item.get("stage", "Reported")
    if current_stage == new_stage:
        return True, f"Item is already in '{new_stage}' stage."

    allowed = LOST_TRANSITIONS.get(current_stage, set())
    if new_stage not in allowed:
        return False, f"Invalid transition: Cannot move lost report from '{current_stage}' to '{new_stage}'."

    success = update_lost_item(item["_id"], {"stage": new_stage})
    if not success:
        return False, "Failed to update item stage in database."

    emit_event("stage_changed", "lost_item", item["_id"], actor_id=actor_id, payload={
        "reference_no": item.get("reference_no"),
        "old_stage": current_stage,
        "new_stage": new_stage,
        "notes": notes
    })
    return True, f"Report moved from '{current_stage}' to '{new_stage}' successfully."


# ==========================================
# FOUND ITEM WORKFLOW
# ==========================================

def transition_found_status(
    found_id: Any,
    new_status: str,
    actor_id: Optional[Any] = None,
    notes: str = ""
) -> Tuple[bool, str]:
    """
    Safely transitions a found item to new_status.
    Enforces valid state machine transition and writes an immutable audit log.
    """
    item = get_found_item_by_id(found_id, is_staff=True)
    if not item:
        return False, "Found item not found."

    current_status = item.get("status", "Unmatched")
    if current_status == new_status:
        return True, f"Item is already in '{new_status}' status."

    allowed = FOUND_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        return False, f"Invalid transition: Cannot move found item from '{current_status}' to '{new_status}'."

    update_payload = {"status": new_status}
    if new_status == "Archived":
        update_payload["archive_eligible"] = True

    success = update_found_item(item["_id"], update_payload)
    if not success:
        return False, "Failed to update item status in database."

    emit_event("status_changed", "found_item", item["_id"], actor_id=actor_id, payload={
        "reference_no": item.get("reference_no"),
        "old_status": current_status,
        "new_status": new_status,
        "notes": notes
    })
    return True, f"Item moved from '{current_status}' to '{new_status}' successfully."


# ==========================================
# CLAIM WORKFLOW
# ==========================================

def transition_claim_status(
    claim_id: Any,
    new_status: str,
    reviewer_id: Optional[Any] = None,
    reviewer_notes: str = ""
) -> Tuple[bool, str]:
    """
    Safely transitions a claim status.
    When Approved:
      - Moves found item to 'Claimed'
      - If linked to a lost item, moves lost item to 'Under Review'
    When Returned:
      - Moves found item to 'Returned'
      - If linked to a lost item, moves lost item to 'Returned'
    """
    from datetime import datetime
    db = get_db()
    c_oid = to_object_id(claim_id)
    if not c_oid:
        return False, "Invalid claim identifier."

    claim = db.claims.find_one({"_id": c_oid})
    if not claim:
        return False, "Claim not found."

    current_status = claim.get("status", "New")
    if current_status == new_status:
        return True, f"Claim is already '{new_status}'."

    allowed = CLAIM_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        return False, f"Invalid transition: Cannot move claim from '{current_status}' to '{new_status}'."

    now = datetime.utcnow()
    update_data = {
        "status": new_status,
        "reviewer_id": to_object_id(reviewer_id) if reviewer_id else claim.get("reviewer_id"),
        "reviewer_notes": reviewer_notes.strip() if reviewer_notes else claim.get("reviewer_notes", ""),
        "decided_at": now if new_status in ["Approved", "Rejected"] else claim.get("decided_at")
    }

    db.claims.update_one({"_id": c_oid}, {"$set": update_data})

    # Side-effects on parent items
    found_id = claim.get("found_id")
    lost_id = claim.get("lost_id")

    if new_status == "Approved":
        # Found item becomes Claimed
        if found_id:
            update_found_item(found_id, {"status": "Claimed"})
        # Lost item becomes Under Review if linked
        if lost_id:
            update_lost_item(lost_id, {"stage": "Under Review"})

    elif new_status == "Returned":
        # Both parent items become Returned
        if found_id:
            update_found_item(found_id, {"status": "Returned"})
        if lost_id:
            update_lost_item(lost_id, {"stage": "Returned"})

    emit_event("claim_decided", "claim", c_oid, actor_id=reviewer_id, payload={
        "reference_no": claim.get("reference_no"),
        "old_status": current_status,
        "new_status": new_status,
        "reviewer_notes": reviewer_notes
    })

    return True, f"Claim transitioned from '{current_status}' to '{new_status}' successfully."
