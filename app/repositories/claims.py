from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from app.db import get_db, to_object_id

from app.repositories.counters import get_next_reference_no
from app.repositories.items import _populate_item_relations, SAFE_FOUND_PROJECTION, SAFE_LOST_PROJECTION


def create_claim(
    claimant_id: Any,
    found_id: Any,
    proof_answer: str,
    lost_id: Optional[Any] = None,
    claim_type: str = "Direct"
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Files a claim.
    Enforces limit: Maximum 3 active/total claims per user per found item to prevent guessing/fraud.
    """
    db = get_db()
    c_oid = to_object_id(claimant_id)
    f_oid = to_object_id(found_id)
    l_oid = to_object_id(lost_id) if lost_id else None
    
    if not c_oid or not f_oid:
        return None, "Invalid claimant or found item identifier."

    # Enforce max 3 claims per user per found item
    existing_claims_count = db.claims.count_documents({
        "claimant_id": c_oid,
        "found_id": f_oid
    })
    if existing_claims_count >= 3:
        return None, "You have reached the maximum limit of 3 claims for this item."

    ref_no = get_next_reference_no("CLM")
    now = datetime.utcnow()
    doc = {
        "reference_no": ref_no,
        "claimant_id": c_oid,
        "found_id": f_oid,
        "lost_id": l_oid,
        "claim_type": claim_type if claim_type in ["Direct", "Suggested"] else "Direct",
        "proof_answer": proof_answer.strip(),
        "reviewer_id": None,
        "reviewer_notes": "",
        "status": "New",
        "created_at": now,
        "decided_at": None
    }
    res = db.claims.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc, None


def get_claim_by_id(claim_id: Any, is_staff: bool = False) -> Optional[Dict[str, Any]]:
    """Retrieve claim by ID and populate claimant, found item, and lost item."""
    oid = to_object_id(claim_id)
    if not oid:
        return None
    db = get_db()
    claim = db.claims.find_one({"_id": oid})
    if not claim:
        return None

    # Populate claimant
    claimant = db.users.find_one({"_id": claim["claimant_id"]}, {"name": 1, "email": 1, "department": 1, "phone": 1})
    claim["claimant"] = claimant

    # Populate found item (staff gets private_details, normal user does not)
    found_proj = None if is_staff else SAFE_FOUND_PROJECTION
    found = db.found_items.find_one({"_id": claim["found_id"]}, found_proj)
    if found:
        _populate_item_relations(found, is_lost=False)
        claim["found_item"] = found
    else:
        claim["found_item"] = None

    # Populate lost item if present
    if claim.get("lost_id"):
        lost_proj = None if is_staff else SAFE_LOST_PROJECTION
        lost = db.lost_items.find_one({"_id": claim["lost_id"]}, lost_proj)
        if lost:
            _populate_item_relations(lost, is_lost=True)
            claim["lost_item"] = lost
        else:
            claim["lost_item"] = None
    else:
        claim["lost_item"] = None

    # Populate reviewer if assigned
    if claim.get("reviewer_id"):
        reviewer = db.users.find_one({"_id": claim["reviewer_id"]}, {"name": 1, "email": 1})
        claim["reviewer"] = reviewer
    else:
        claim["reviewer"] = None

    # Populate handover if exists
    handover = db.handovers.find_one({"claim_id": claim["_id"]})
    claim["handover"] = handover

    return claim


def get_user_claims(user_id: Any) -> List[Dict[str, Any]]:
    """Get all claims filed by a specific user."""
    oid = to_object_id(user_id)
    if not oid:
        return []
    db = get_db()
    claims = list(db.claims.find({"claimant_id": oid}).sort("created_at", -1))
    for c in claims:
        # Populate safe found item
        found = db.found_items.find_one({"_id": c["found_id"]}, SAFE_FOUND_PROJECTION)
        if found:
            _populate_item_relations(found, is_lost=False)
            c["found_item"] = found
        c["handover"] = db.handovers.find_one({"claim_id": c["_id"]})
    return claims


def get_claims_for_found_item(found_id: Any, is_staff: bool = True) -> List[Dict[str, Any]]:
    """List all claims for a found item."""
    f_oid = to_object_id(found_id)
    if not f_oid:
        return []
    db = get_db()
    claims = list(db.claims.find({"found_id": f_oid}).sort("created_at", -1))
    for c in claims:
        c["claimant"] = db.users.find_one({"_id": c["claimant_id"]}, {"name": 1, "email": 1, "department": 1, "phone": 1})
        c["handover"] = db.handovers.find_one({"claim_id": c["_id"]})
    return claims


def count_open_claims_for_found(found_id: Any) -> int:
    """Count open/pending claims (New or Under Review) for a found item."""
    f_oid = to_object_id(found_id)
    if not f_oid:
        return 0
    db = get_db()
    return db.claims.count_documents({
        "found_id": f_oid,
        "status": {"$in": ["New", "Under Review"]}
    })


def get_all_claims(
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """Get claims with optional status filter for staff review."""
    db = get_db()
    query = {"status": status} if status else {}
    total = db.claims.count_documents(query)
    claims = list(db.claims.find(query).sort("created_at", -1).skip(skip).limit(limit))
    for c in claims:
        c["claimant"] = db.users.find_one({"_id": c["claimant_id"]}, {"name": 1, "email": 1})
        found = db.found_items.find_one({"_id": c["found_id"]})
        if found:
            _populate_item_relations(found, is_lost=False)
            c["found_item"] = found
    return claims, total
