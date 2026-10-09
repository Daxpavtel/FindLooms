from datetime import datetime
from typing import Optional, Dict, Any, List
from app.db import get_db, to_object_id



def create_or_update_handover(
    claim_id: Any,
    receiver_name: str,
    reviewer_id: Any,
    scheduled_datetime: Optional[datetime] = None,
    return_datetime: Optional[datetime] = None,
    acknowledgement_note: str = ""
) -> Dict[str, Any]:
    """Create or update a handover record linked to a claim."""
    db = get_db()
    c_oid = to_object_id(claim_id)
    r_oid = to_object_id(reviewer_id)
    if not c_oid:
        return {}

    now = datetime.utcnow()
    doc = {
        "claim_id": c_oid,
        "receiver_name": receiver_name.strip(),
        "reviewer_id": r_oid,
        "scheduled_datetime": scheduled_datetime,
        "return_datetime": return_datetime,
        "acknowledgement_note": acknowledgement_note.strip(),
        "updated_at": now
    }
    
    res = db.handovers.find_one_and_update(
        {"claim_id": c_oid},
        {
            "$set": doc,
            "$setOnInsert": {"created_at": now}
        },
        upsert=True,
        return_document=True
    )
    return res


def get_handover_by_claim_id(claim_id: Any) -> Optional[Dict[str, Any]]:
    """Retrieve handover details for a claim."""
    c_oid = to_object_id(claim_id)
    if not c_oid:
        return None
    db = get_db()
    return db.handovers.find_one({"claim_id": c_oid})


def get_scheduled_handovers(start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Get handovers scheduled within a date range for calendar views."""
    db = get_db()
    query = {
        "scheduled_datetime": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    return list(db.handovers.find(query))
