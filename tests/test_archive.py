from datetime import datetime, timedelta
from app.services.archive import run_archive_check


def test_archive_job_flags_old_unclaimed_items(db):
    now = datetime.utcnow()

    # 1. Old item (45 days old, Unmatched) -> should be flagged
    old_id = db.found_items.insert_one({
        "reference_no": "FND-OLD-01",
        "name": "Old Jacket",
        "status": "Unmatched",
        "archive_eligible": False,
        "created_at": now - timedelta(days=45),
        "updated_at": now - timedelta(days=45)
    }).inserted_id

    # 2. Recent item (5 days old, Unmatched) -> should NOT be flagged
    recent_id = db.found_items.insert_one({
        "reference_no": "FND-NEW-01",
        "name": "New Phone",
        "status": "Unmatched",
        "archive_eligible": False,
        "created_at": now - timedelta(days=5),
        "updated_at": now - timedelta(days=5)
    }).inserted_id

    # Run archive routine
    result = run_archive_check()
    assert result["flagged_count"] >= 1

    old_doc = db.found_items.find_one({"_id": old_id})
    assert old_doc["archive_eligible"] is True

    recent_doc = db.found_items.find_one({"_id": recent_id})
    assert recent_doc["archive_eligible"] is False
