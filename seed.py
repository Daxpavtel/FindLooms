"""
Database seeding script for LostFound.
Clean seed: resets the database and seeds ONLY:
- 1 Administrator account
- 1 Staff member account
- 1 Regular User account
- Standard Categories and Campus Locations
- Atomic Sequence Counters & Default System Settings
NO dummy lost items, found items, claims, or handovers.
"""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from pymongo import MongoClient

from app.config import Config
from app.db import init_db


def seed_database(mongo_uri: str = None):
    if not mongo_uri:
        mongo_uri = Config.MONGO_URI

    print(f"Connecting to MongoDB at {mongo_uri}...")
    client = MongoClient(mongo_uri)
    db_name = mongo_uri.split("/")[-1].split("?")[0] or "lostfound_db"
    db = client[db_name]

    # Initialize collections and indexes idempotently
    init_db(mongo_uri)

    # Clean ALL existing collections for a completely fresh start
    collections_to_clean = [
        "users",
        "categories",
        "locations",
        "lost_items",
        "found_items",
        "match_candidates",
        "claims",
        "handovers",
        "audit_logs",
        "counters",
        "item_images"
    ]
    for coll in collections_to_clean:
        db[coll].delete_many({})

    # Reset atomic counters
    db.counters.insert_many([
        {"_id": "LST", "seq": 0},
        {"_id": "FND", "seq": 0},
        {"_id": "CLM", "seq": 0}
    ])

    now = datetime.now(timezone.utc)

    # Seed exactly 1 Admin, 1 Staff, and 1 User
    print("Seeding Users (1 Admin, 1 Staff, 1 User)...")
    users_data = [
        {
            "name": "System Administrator",
            "email": "admin@campus.edu",
            "password_hash": generate_password_hash("AdminPass123!"),
            "role": "admin",
            "department": "Campus Safety & Administration",
            "phone": "+91 98201 00001",
            "is_active": True,
            "created_at": now
        },
        {
            "name": "Campus Staff Desk",
            "email": "staff@campus.edu",
            "password_hash": generate_password_hash("StaffPass123!"),
            "role": "staff",
            "department": "Lost & Found Custody Desk",
            "phone": "+91 98201 00002",
            "is_active": True,
            "created_at": now
        },
        {
            "name": "Campus Student",
            "email": "user@campus.edu",
            "password_hash": generate_password_hash("UserPass123!"),
            "role": "user",
            "department": "Computer Science",
            "phone": "+91 98201 00003",
            "is_active": True,
            "created_at": now
        }
    ]
    db.users.insert_many(users_data)

    print("Seeding Master Categories...")
    categories_data = [
        {"name": "Electronics", "icon": "bi-laptop", "is_active": True},
        {"name": "Wallets", "icon": "bi-wallet2", "is_active": True},
        {"name": "Documents", "icon": "bi-file-earmark-text", "is_active": True},
        {"name": "Bags", "icon": "bi-backpack", "is_active": True},
        {"name": "Keys", "icon": "bi-key", "is_active": True},
        {"name": "Clothing", "icon": "bi-person-badge", "is_active": True},
        {"name": "Accessories", "icon": "bi-watch", "is_active": True},
        {"name": "Other", "icon": "bi-box", "is_active": True}
    ]
    db.categories.insert_many(categories_data)

    print("Seeding Campus Locations...")
    locations_data = [
        {"name": "Main Library Reading Room", "building": "Central Library", "zone": "North Academic Zone", "venue": "2nd Floor Quiet Area", "latitude": 23.0850, "longitude": 72.4550, "is_active": True},
        {"name": "Cafeteria Food Court", "building": "Student Canteen", "zone": "Central Campus", "venue": "Ground Floor Food Court", "latitude": 23.0848, "longitude": 72.4558, "is_active": True},
        {"name": "Campus Shuttle Bus Stand", "building": "Transit Depot", "zone": "Campus Perimeter", "venue": "Main Gate Bus Stop", "latitude": 23.0836, "longitude": 72.4540, "is_active": True},
        {"name": "Computer Science Lab 302", "building": "IITE Engineering Hall", "zone": "North Academic Zone", "venue": "Lab 302", "latitude": 23.0855, "longitude": 72.4553, "is_active": True},
        {"name": "Hostel Block C Common Room", "building": "Indus Hostel Complex", "zone": "South Living Zone", "venue": "Block C Lounge", "latitude": 23.0835, "longitude": 72.4560, "is_active": True},
        {"name": "Administration Reception", "building": "Admin Complex", "zone": "Central Campus", "venue": "Ground Floor Main Desk", "latitude": 23.0845, "longitude": 72.4548, "is_active": True},
        {"name": "Main Security Desk", "building": "Gate 1", "zone": "Campus Perimeter", "venue": "Main Entrance", "latitude": 23.0838, "longitude": 72.4542, "is_active": True},
        {"name": "Sports Ground Bleachers", "building": "Athletic Center", "zone": "East Sports Zone", "venue": "Main Sports Ground", "latitude": 23.0862, "longitude": 72.4545, "is_active": True},
        {"name": "Chemistry Research Lab B", "building": "Science Pavilion", "zone": "North Academic Zone", "venue": "Lab B12", "latitude": 23.0858, "longitude": 72.4555, "is_active": True},
        {"name": "University Auditorium", "building": "Arts & Cultural Center", "zone": "West Campus", "venue": "Main Hall", "latitude": 23.0842, "longitude": 72.4554, "is_active": True}
    ]
    db.locations.insert_many(locations_data)

    print("\nDatabase cleaned and seeded successfully!")
    print(f"Users: {db.users.count_documents({})}")
    print(f"Categories: {db.categories.count_documents({})}")
    print(f"Locations: {db.locations.count_documents({})}")
    print(f"Lost Reports: {db.lost_items.count_documents({})}")
    print(f"Found Items: {db.found_items.count_documents({})}")
    print(f"Match Candidates: {db.match_candidates.count_documents({})}")
    print(f"Claims: {db.claims.count_documents({})}")
    print(f"Handovers: {db.handovers.count_documents({})}")
    print(f"Audit Logs: {db.audit_logs.count_documents({})}")

    client.close()


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_database()
