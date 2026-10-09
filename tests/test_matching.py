from datetime import datetime, timedelta
from bson import ObjectId
from app.services.matching import calculate_match_score


def test_calculate_match_score_perfect_match():
    now = datetime.utcnow()
    cat_id = ObjectId()
    loc_id = ObjectId()

    lost = {
        "category_id": cat_id,
        "last_seen_location_id": loc_id,
        "location": {"name": "Main Library", "building": "Library", "zone": "North"},
        "lost_date": now - timedelta(hours=5),
        "brand": "Apple",
        "color": "Space Grey",
        "name": "MacBook Pro",
        "description": "14 inch Apple laptop with stickers"
    }

    found = {
        "category_id": cat_id,
        "found_location_id": loc_id,
        "location": {"name": "Main Library", "building": "Library", "zone": "North"},
        "found_datetime": now - timedelta(hours=2),
        "brand": "Apple",
        "color": "Space Grey",
        "name": "MacBook Pro",
        "description": "14 inch Apple laptop with stickers found on desk"
    }

    result = calculate_match_score(lost, found)
    assert result["category_score"] == 30
    assert result["location_score"] == 25
    assert result["date_score"] == 20
    assert result["keyword_score"] == 10
    assert result["tfidf_score"] > 10
    assert result["total_score"] >= 90
    assert "Category ✔" in result["details"]


def test_calculate_match_score_different_category():
    now = datetime.utcnow()
    loc_id = ObjectId()

    lost = {
        "category_id": ObjectId(),
        "last_seen_location_id": loc_id,
        "location": {"name": "Cafeteria", "building": "Student Union", "zone": "Central"},
        "lost_date": now - timedelta(days=2),
        "brand": "Fossil",
        "color": "Brown",
        "name": "Wallet",
        "description": "Leather wallet"
    }

    found = {
        "category_id": ObjectId(),  # Different category
        "found_location_id": loc_id,
        "location": {"name": "Cafeteria", "building": "Student Union", "zone": "Central"},
        "found_datetime": now - timedelta(days=2),
        "brand": "Fossil",
        "color": "Brown",
        "name": "Wallet",
        "description": "Leather wallet"
    }

    result = calculate_match_score(lost, found)
    assert result["category_score"] == 0
    assert "Category ✘" in result["details"]


def test_calculate_match_score_same_building_different_room():
    now = datetime.utcnow()
    cat_id = ObjectId()

    lost = {
        "category_id": cat_id,
        "last_seen_location_id": ObjectId(),
        "location": {"name": "Lab 101", "building": "Science Center", "zone": "North"},
        "lost_date": now - timedelta(days=1),
        "brand": "Casio",
        "color": "Black",
        "name": "Watch",
        "description": "Digital watch"
    }

    found = {
        "category_id": cat_id,
        "found_location_id": ObjectId(),
        "location": {"name": "Auditorium S2", "building": "Science Center", "zone": "North"},
        "found_datetime": now - timedelta(days=1),
        "brand": "Casio",
        "color": "Black",
        "name": "Watch",
        "description": "Digital wristwatch"
    }

    result = calculate_match_score(lost, found)
    assert result["location_score"] == 12  # Same building score
    assert result["category_score"] == 30


def test_calculate_match_score_found_before_lost():
    now = datetime.utcnow()
    cat_id = ObjectId()
    loc_id = ObjectId()

    lost = {
        "category_id": cat_id,
        "last_seen_location_id": loc_id,
        "lost_date": now,
        "name": "Keys",
        "description": "Brass keys"
    }

    found = {
        "category_id": cat_id,
        "found_location_id": loc_id,
        "found_datetime": now - timedelta(days=5),  # Found 5 days BEFORE it was lost!
        "name": "Keys",
        "description": "Brass keys"
    }

    result = calculate_match_score(lost, found)
    assert result["date_score"] == 0
    assert "Date: Found before reported lost ✘" in result["details"]
