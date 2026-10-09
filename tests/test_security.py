from datetime import datetime
from bson import ObjectId
from app.db import to_object_id
from app.repositories.items import get_found_item_by_id, get_lost_item_by_id


def test_nosql_injection_prevention():
    # Pass dictionary operator payload
    malicious_payload = {"$ne": "123"}
    assert to_object_id(malicious_payload) is None

    # Pass list
    assert to_object_id(["123456789012345678901234"]) is None

    # Pass malformed string
    assert to_object_id("not-a-valid-hex-object-id") is None

    # Valid hex ObjectId passes
    valid_id = "507f1f77bcf86cd799439011"
    assert to_object_id(valid_id) == ObjectId(valid_id)


def test_hidden_detail_leakage_found_item(client, db):
    now = datetime.utcnow()
    secret_text = "CONFIDENTIAL_ENGRAVED_INITIALS_9999"
    found_id = db.found_items.insert_one({
        "reference_no": "FND-SEC-01",
        "name": "Secret Watch",
        "description": "Safe public description of watch",
        "private_details": secret_text,
        "status": "Unmatched",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    # 1. Unauthenticated / Public access
    res = client.get(f"/found/{found_id}")
    assert res.status_code == 200
    assert secret_text not in res.get_data(as_text=True)
    assert "Safe public description of watch" in res.get_data(as_text=True)

    # 2. Regular User access
    client.post("/auth/login", data={"email": "user@example.com", "password": "Password123!"})
    res_user = client.get(f"/found/{found_id}")
    assert res_user.status_code == 200
    assert secret_text not in res_user.get_data(as_text=True)

    # 3. Staff access: should reveal private details
    client.get("/auth/logout")
    client.post("/auth/login", data={"email": "staff@example.com", "password": "Password123!"})
    res_staff = client.get(f"/found/{found_id}")
    assert res_staff.status_code == 200
    assert secret_text in res_staff.get_data(as_text=True)


def test_hidden_detail_leakage_lost_item(client, db):
    now = datetime.utcnow()
    secret_lost_clue = "TOP_SECRET_STICKER_ON_BOTTOM_CHASSIS"
    other_user_id = ObjectId()

    lost_id = db.lost_items.insert_one({
        "reference_no": "LST-SEC-01",
        "reporter_id": other_user_id,
        "name": "Secret Laptop",
        "description": "Public description of lost laptop",
        "private_verification_detail": secret_lost_clue,
        "stage": "Reported",
        "created_at": now,
        "updated_at": now
    }).inserted_id

    # Public/Unauthenticated access
    res = client.get(f"/lost/{lost_id}")
    assert res.status_code == 200
    assert secret_lost_clue not in res.get_data(as_text=True)
