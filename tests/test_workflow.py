from datetime import datetime
from bson import ObjectId
from app.services.workflow import (
    transition_lost_stage,
    transition_found_status,
    transition_claim_status
)


def test_lost_item_state_machine_valid(db):
    now = datetime.utcnow()
    lost_id = db.lost_items.insert_one({
        "reference_no": "LST-TEST-001",
        "name": "Test Item",
        "stage": "Reported",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    # 1. Reported -> Possible Match
    ok, msg = transition_lost_stage(lost_id, "Possible Match")
    assert ok is True
    doc = db.lost_items.find_one({"_id": lost_id})
    assert doc["stage"] == "Possible Match"

    # 2. Possible Match -> Under Review
    ok, msg = transition_lost_stage(lost_id, "Under Review")
    assert ok is True
    doc = db.lost_items.find_one({"_id": lost_id})
    assert doc["stage"] == "Under Review"

    # 3. Under Review -> Returned
    ok, msg = transition_lost_stage(lost_id, "Returned")
    assert ok is True
    doc = db.lost_items.find_one({"_id": lost_id})
    assert doc["stage"] == "Returned"

    # 4. Returned -> Archived
    ok, msg = transition_lost_stage(lost_id, "Archived")
    assert ok is True
    doc = db.lost_items.find_one({"_id": lost_id})
    assert doc["stage"] == "Archived"


def test_lost_item_state_machine_invalid(db):
    now = datetime.utcnow()
    lost_id = db.lost_items.insert_one({
        "reference_no": "LST-TEST-002",
        "name": "Archived Item",
        "stage": "Archived",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    # Archived is terminal - cannot move back to Reported
    ok, msg = transition_lost_stage(lost_id, "Reported")
    assert ok is False
    assert "Invalid transition" in msg


def test_found_item_state_machine_valid_and_invalid(db):
    now = datetime.utcnow()
    found_id = db.found_items.insert_one({
        "reference_no": "FND-TEST-001",
        "name": "Found Watch",
        "status": "Unmatched",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    # Valid: Unmatched -> Claimed
    ok, msg = transition_found_status(found_id, "Claimed")
    assert ok is True

    # Valid: Claimed -> Returned
    ok, msg = transition_found_status(found_id, "Returned")
    assert ok is True

    # Invalid: Returned cannot move back to Unmatched
    ok, msg = transition_found_status(found_id, "Unmatched")
    assert ok is False
    assert "Invalid transition" in msg


def test_claim_state_machine(db):
    now = datetime.utcnow()
    found_id = db.found_items.insert_one({
        "reference_no": "FND-CLM-01",
        "name": "Item for claim",
        "status": "Unmatched",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    claim_id = db.claims.insert_one({
        "reference_no": "CLM-TEST-01",
        "found_id": found_id,
        "status": "New",
        "created_at": now
    }).inserted_id

    # Valid: New -> Under Review
    ok, msg = transition_claim_status(claim_id, "Under Review")
    assert ok is True
    assert db.claims.find_one({"_id": claim_id})["status"] == "Under Review"

    # Valid: Under Review -> Approved
    ok, msg = transition_claim_status(claim_id, "Approved")
    assert ok is True
    assert db.claims.find_one({"_id": claim_id})["status"] == "Approved"
    # Found item should now be 'Claimed'
    assert db.found_items.find_one({"_id": found_id})["status"] == "Claimed"

    # Valid: Approved -> Returned
    ok, msg = transition_claim_status(claim_id, "Returned")
    assert ok is True
    assert db.claims.find_one({"_id": claim_id})["status"] == "Returned"
    # Found item should now be 'Returned'
    assert db.found_items.find_one({"_id": found_id})["status"] == "Returned"
