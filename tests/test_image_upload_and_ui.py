import io
import pytest
from PIL import Image
from bson import ObjectId
from datetime import datetime, date


def create_dummy_image(format="JPEG", size=(800, 600), color="blue"):
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    buf.seek(0)
    return buf


def login(client, email, password):
    return client.post("/auth/login", data={
        "email": email,
        "password": password
    }, follow_redirects=True)


def test_lost_item_ui_confidential_clue_structure(client):
    """Test that the Confidential Verification Clue fieldset in lost/new renders with responsive classes and clear hierarchy."""
    login(client, "user@example.com", "Password123!")
    res = client.get("/lost/new")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Verify Confidential Verification Clue section
    assert "Confidential Verification Clue" in html
    assert "form-fieldset" in html
    assert "form-legend" in html
    assert "verification-clue-field" in html
    assert "private_verification_detail" in html
    assert "image_optimizer.js" in html


def test_found_item_ui_structure_and_optimizer(client):
    """Test that found/new includes image optimizer script and structured confidential section."""
    login(client, "staff@example.com", "Password123!")
    res = client.get("/found/new")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    assert "Staff Confidential Item Specifics" in html
    assert "verification-clue-field" in html
    assert "image_optimizer.js" in html
    assert "direct_image_path" in html or "name=\"image\"" in html


def test_api_upload_image_endpoint(client, db):
    """Test direct cloud/storage upload endpoint /api/upload-image."""
    login(client, "staff@example.com", "Password123!")
    img_buf = create_dummy_image()

    data = {
        "image": (img_buf, "test_item.jpg", "image/jpeg")
    }
    res = client.post("/api/upload-image", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert "image_path" in json_data
    assert json_data["image_path"].startswith("uploads/")

    # Verify the image was persisted to MongoDB
    filename = json_data["image_path"].split("/")[-1]
    doc = db.item_images.find_one({"filename": filename})
    assert doc is not None
    assert doc["filename"] == filename
    assert len(doc["data"]) > 0


def test_serve_uploaded_image_route(client, db):
    """Test /static/uploads/<filename> serves from MongoDB if file is in database."""
    img_buf = create_dummy_image(color="red")
    img_bytes = img_buf.getvalue()
    test_filename = "test_vercel_image.jpg"

    db.item_images.insert_one({
        "filename": test_filename,
        "content_type": "image/jpeg",
        "data": img_bytes,
        "created_at": datetime.utcnow()
    })

    res = client.get(f"/static/uploads/{test_filename}")
    assert res.status_code == 200
    assert res.content_type == "image/jpeg"
    assert res.data == img_bytes


def test_found_item_registration_with_direct_image_path(client, db):
    """Test registering a found item sending only direct_image_path (optimized lightweight request)."""
    login(client, "staff@example.com", "Password123!")

    # Seed a category and location with is_active=True
    cat_id = db.categories.insert_one({"name": "Electronics", "code": "ELEC", "icon": "bi-laptop", "is_active": True}).inserted_id
    loc_id = db.locations.insert_one({"name": "Library 2F", "code": "LIB2", "building": "Library", "is_active": True}).inserted_id

    # Simulate direct upload first
    img_buf = create_dummy_image()
    up_res = client.post("/api/upload-image", data={
        "image": (img_buf, "found_photo.jpg", "image/jpeg")
    }, content_type="multipart/form-data")
    assert up_res.status_code == 200
    image_path = up_res.get_json()["image_path"]

    # Submit registration form using direct_image_path without raw image in body
    form_data = {
        "name": "Found iPhone 13 Pro",
        "category_id": str(cat_id),
        "brand": "Apple",
        "color": "Sierra Blue",
        "found_date": date.today().isoformat(),
        "found_location_id": str(loc_id),
        "custody_location": "Main Desk Vault",
        "description": "Found near computer lab table 4",
        "private_details": "Cracked screen protector and dinosaur sticker",
        "direct_image_path": image_path
    }

    res = client.post("/found/new", data=form_data, follow_redirects=True)
    assert res.status_code == 200

    # Verify item created in database with the image_path
    found_item = db.found_items.find_one({"name": "Found iPhone 13 Pro"})
    assert found_item is not None
    assert found_item["image_path"] == image_path
    assert found_item["status"] in ("Reported", "Unmatched")


def test_lost_item_registration_with_direct_image_path(client, db):
    """Test registering a lost item sending direct_image_path."""
    login(client, "user@example.com", "Password123!")

    cat_id = db.categories.insert_one({"name": "Bags", "code": "BAG", "icon": "bi-bag", "is_active": True}).inserted_id
    loc_id = db.locations.insert_one({"name": "Cafeteria", "code": "CAF", "building": "Student Center", "is_active": True}).inserted_id

    form_data = {
        "name": "Black Backpack",
        "category_id": str(cat_id),
        "brand": "Nike",
        "color": "Black",
        "lost_date": date.today().isoformat(),
        "approx_time": "Noon",
        "last_seen_location_id": str(loc_id),
        "description": "Black backpack left near cafeteria entrance",
        "private_verification_detail": "Contains calculus notebook with initials 'AP'",
        "direct_image_path": "uploads/preloaded_backpack.jpg"
    }

    res = client.post("/lost/new", data=form_data, follow_redirects=True)
    assert res.status_code == 200

    lost_item = db.lost_items.find_one({"name": "Black Backpack"})
    assert lost_item is not None
    assert lost_item["image_path"] == "uploads/preloaded_backpack.jpg"
