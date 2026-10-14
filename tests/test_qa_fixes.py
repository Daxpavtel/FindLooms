from datetime import datetime, date, timedelta
from bson import ObjectId
from app.services.events import emit_event
from app.services.workflow import transition_claim_status
from app.services.matching import run_matching_for_found_item
from app.db import to_object_id


def login(client, email, password):
    return client.post("/auth/login", data={
        "email": email,
        "password": password
    }, follow_redirects=True)


def test_emit_event_accepts_details_and_payload_without_error(db):
    """Verify emit_event supports both payload and details keyword arguments without TypeError."""
    # Test with payload
    emit_event("test_action_1", "item", ObjectId(), actor_id=None, payload={"info": "alpha"})
    doc1 = db.audit_logs.find_one({"action": "test_action_1"})
    assert doc1 is not None
    assert doc1["details"]["info"] == "alpha"

    # Test with details kwarg (previously raised TypeError)
    emit_event("test_action_2", "item", ObjectId(), actor_id=None, details={"info": "beta"})
    doc2 = db.audit_logs.find_one({"action": "test_action_2"})
    assert doc2 is not None
    assert doc2["details"]["info"] == "beta"


def test_claim_direct_approval_transition(db):
    """Verify that claims can transition directly from 'New' to 'Approved'."""
    now = datetime.utcnow()
    found_id = db.found_items.insert_one({
        "reference_no": "FND-AUTO-01",
        "name": "Found Watch",
        "status": "Unmatched",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    claim_id = db.claims.insert_one({
        "reference_no": "CLM-AUTO-01",
        "found_id": found_id,
        "status": "New",
        "created_at": now
    }).inserted_id

    # Direct transition: New -> Approved
    ok, msg = transition_claim_status(claim_id, "Approved", reviewer_notes="Valid proof confirmed")
    assert ok is True
    claim_doc = db.claims.find_one({"_id": claim_id})
    assert claim_doc["status"] == "Approved"

    # Verify side effect: found item status became 'Claimed'
    found_doc = db.found_items.find_one({"_id": found_id})
    assert found_doc["status"] == "Claimed"


def test_strong_match_auto_promotion_flow(db):
    """Verify matching engine promotes both items on strong match without crash."""
    now = datetime.utcnow()
    cat_id = db.categories.insert_one({"name": "Electronics", "code": "ELEC", "is_active": True}).inserted_id
    loc_id = db.locations.insert_one({"name": "Library 1F", "code": "LIB1", "building": "Library", "is_active": True}).inserted_id

    lost_id = db.lost_items.insert_one({
        "reference_no": "LST-MATCH-01",
        "name": "MacBook Pro M2",
        "category_id": cat_id,
        "brand": "Apple",
        "color": "Space Gray",
        "lost_date": now,
        "last_seen_location_id": loc_id,
        "description": "MacBook Pro M2 with gray case",
        "stage": "Reported",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    found_id = db.found_items.insert_one({
        "reference_no": "FND-MATCH-01",
        "name": "MacBook Pro M2",
        "category_id": cat_id,
        "brand": "Apple",
        "color": "Space Gray",
        "found_datetime": now + timedelta(hours=1),
        "found_location_id": loc_id,
        "description": "MacBook Pro M2 found in Library",
        "status": "Unmatched",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    # Run matching for found item (should trigger strong match and auto-promote without TypeError)
    matches = run_matching_for_found_item(found_id)
    assert len(matches) > 0

    lost_item = db.lost_items.find_one({"_id": lost_id})
    found_item = db.found_items.find_one({"_id": found_id})
    assert lost_item["stage"] == "Possible Match"
    assert found_item["status"] == "Possible Match"


def test_api_upload_image_requires_login(client):
    """Verify /api/upload-image cannot be accessed anonymously."""
    res = client.post("/api/upload-image", data={})
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_claims_idor_protection(client, db):
    """Verify a student cannot view another student's claim details (IDOR test)."""
    now = datetime.utcnow()
    # Create two users
    user_a_id = db.users.insert_one({
        "email": "student_a@campus.edu",
        "name": "Student A",
        "role": "user",
        "is_active": True
    }).inserted_id

    user_b_id = db.users.insert_one({
        "email": "student_b@campus.edu",
        "name": "Student B",
        "role": "user",
        "is_active": True
    }).inserted_id

    found_id = db.found_items.insert_one({
        "reference_no": "FND-IDOR-01",
        "name": "Keys",
        "status": "Unmatched",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    claim_a_id = db.claims.insert_one({
        "reference_no": "CLM-IDOR-01",
        "found_id": found_id,
        "claimant_id": user_a_id,
        "proof_answer": "Has blue lanyard",
        "status": "New",
        "created_at": now
    }).inserted_id

    # Login as User B
    login(client, "user@example.com", "Password123!")
    # Attempt to access User A's claim
    res = client.get(f"/claims/{claim_a_id}")
    assert res.status_code == 403


def test_student_cannot_access_staff_review_queue(client):
    """Verify students are blocked from staff review queue."""
    login(client, "user@example.com", "Password123!")
    res = client.get("/claims/queue")
    assert res.status_code == 403


def test_staff_cannot_access_admin_categories(client):
    """Verify staff members cannot access admin-only settings."""
    login(client, "staff@example.com", "Password123!")
    res = client.get("/admin/categories")
    assert res.status_code == 403
