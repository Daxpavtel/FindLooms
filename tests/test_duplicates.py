from datetime import datetime, timedelta
from bson import ObjectId
from app.repositories.items import find_potential_duplicates


def test_duplicate_detection(db):
    now = datetime.utcnow()
    cat_id = ObjectId()
    loc_id = ObjectId()

    # Seed location
    db.locations.insert_one({"_id": loc_id, "name": "Lab A", "building": "SciHall", "zone": "North"})

    # Existing item from yesterday
    db.lost_items.insert_one({
        "reference_no": "LST-ORIG-01",
        "name": "Blue Umbrella",
        "category_id": cat_id,
        "last_seen_location_id": loc_id,
        "lost_date": now - timedelta(days=1),
        "stage": "Reported",
        "created_at": now - timedelta(days=1),
        "updated_at": now - timedelta(days=1)
    })

    # Search for duplicate today (within 2-day window, same category, same location)
    dups = find_potential_duplicates(
        category_id=cat_id,
        location_id=loc_id,
        target_date=now,
        is_lost=True,
        window_days=2
    )
    assert len(dups) == 1
    assert dups[0]["reference_no"] == "LST-ORIG-01"

    # Search with date 10 days away (outside window)
    dups_outside = find_potential_duplicates(
        category_id=cat_id,
        location_id=loc_id,
        target_date=now + timedelta(days=10),
        is_lost=True,
        window_days=2
    )
    assert len(dups_outside) == 0

    # Search with different category
    dups_diff_cat = find_potential_duplicates(
        category_id=ObjectId(),
        location_id=loc_id,
        target_date=now,
        is_lost=True,
        window_days=2
    )
    assert len(dups_diff_cat) == 0
