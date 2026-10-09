"""
Database seeding script for LostFound.
Idempotent: clears and populates initial demo data with users, categories,
locations, matching item pairs, duplicates, claims, handovers, and audit logs.
"""
from datetime import datetime, timedelta
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

    # Clean existing collections for a fresh seed
    for coll in ["users", "categories", "locations", "lost_items", "found_items",
                 "match_candidates", "claims", "handovers", "audit_logs", "counters"]:
        db[coll].delete_many({})

    # Reset counters
    db.counters.insert_many([
        {"_id": "LST", "seq": 0},
        {"_id": "FND", "seq": 0},
        {"_id": "CLM", "seq": 0}
    ])

    print("Seeding Users...")
    users_data = [
        {
            "name": "Rajesh Sharma",
            "email": "admin@campus.edu",
            "password_hash": generate_password_hash("AdminPass123!"),
            "role": "admin",
            "department": "Campus Safety & Security",
            "phone": "+91 98201 00001",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=60)
        },
        {
            "name": "Priya Sharma",
            "email": "priya.sharma@campus.edu",
            "password_hash": generate_password_hash("StaffPass123!"),
            "role": "staff",
            "department": "Student Center Information Desk",
            "phone": "+91 98201 00002",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=55)
        },
        {
            "name": "Vikram Malhotra",
            "email": "vikram.malhotra@campus.edu",
            "password_hash": generate_password_hash("StaffPass123!"),
            "role": "staff",
            "department": "Central Library Custody Desk",
            "phone": "+91 98201 00003",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=50)
        },
        {
            "name": "Aarav Patel",
            "email": "aarav.patel@campus.edu",
            "password_hash": generate_password_hash("UserPass123!"),
            "role": "user",
            "department": "Computer Science",
            "phone": "+91 98201 10001",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=40)
        },
        {
            "name": "Rohan Verma",
            "email": "rohan.verma@campus.edu",
            "password_hash": generate_password_hash("UserPass123!"),
            "role": "user",
            "department": "Mechanical Engineering",
            "phone": "+91 98201 10002",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=38)
        },
        {
            "name": "Ananya Iyer",
            "email": "ananya.iyer@campus.edu",
            "password_hash": generate_password_hash("UserPass123!"),
            "role": "user",
            "department": "School of Business",
            "phone": "+91 98201 10003",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=35)
        },
        {
            "name": "Neha Gupta",
            "email": "neha.gupta@campus.edu",
            "password_hash": generate_password_hash("UserPass123!"),
            "role": "user",
            "department": "Biochemistry",
            "phone": "+91 98201 10004",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=30)
        },
        {
            "name": "Kabir Mehta",
            "email": "kabir.mehta@campus.edu",
            "password_hash": generate_password_hash("UserPass123!"),
            "role": "user",
            "department": "Athletics Department",
            "phone": "+91 98201 10005",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=25)
        }
    ]
    u_res = db.users.insert_many(users_data)
    user_map = {u["email"]: u_id for u, u_id in zip(users_data, u_res.inserted_ids)}

    print("Seeding Categories...")
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
    c_res = db.categories.insert_many(categories_data)
    cat_map = {c["name"]: c_id for c, c_id in zip(categories_data, c_res.inserted_ids)}

    print("Seeding Locations...")
    locations_data = [
        {"name": "Main Library Reading Room", "building": "Central Library", "zone": "North Academic Zone", "venue": "2nd Floor Quiet Area", "latitude": 23.0850, "longitude": 72.4550, "is_active": True},
        {"name": "Cafeteria Food Court", "building": "Student Canteen", "zone": "Central Campus", "venue": "Ground Floor Food Court", "latitude": 23.0848, "longitude": 72.4558, "is_active": True},
        {"name": "Campus Shuttle Bus Stand", "building": "Transit Depot", "zone": "Campus Perimeter", "venue": "Main Gate Bus Stop", "latitude": 23.0836, "longitude": 72.4540, "is_active": True},
        {"name": "Computer Science Lab 302", "building": "IITE Engineering Hall", "zone": "North Academic Zone", "venue": "Lab 302", "latitude": 23.0855, "longitude": 72.4553, "is_active": True},
        {"name": "Hostel Block C Common Room", "building": "Indus Hostel Complex", "zone": "South Living Zone", "venue": "Block C Lounge", "latitude": 23.0835, "longitude": 72.4560, "is_active": True},
        {"name": "Administration Reception", "building": "Admin Complex", "zone": "Central Campus", "venue": "Ground Floor Main Desk", "latitude": 23.0845, "longitude": 72.4548, "is_active": True},
        {"name": "Main Security Desk", "building": "Gate 1", "zone": "Campus Perimeter", "venue": "Main Entrance (Rancharda Road)", "latitude": 23.0838, "longitude": 72.4542, "is_active": True},
        {"name": "Sports Ground Bleachers", "building": "Athletic Center", "zone": "East Sports Zone", "venue": "Cricket & Football Field Stand B", "latitude": 23.0862, "longitude": 72.4545, "is_active": True},
        {"name": "Chemistry Research Lab B", "building": "Science Pavilion", "zone": "North Academic Zone", "venue": "Lab B12", "latitude": 23.0858, "longitude": 72.4555, "is_active": True},
        {"name": "University Auditorium", "building": "Arts & Cultural Center", "zone": "West Campus", "venue": "Main Auditorium Row F", "latitude": 23.0842, "longitude": 72.4554, "is_active": True}
    ]
    l_res = db.locations.insert_many(locations_data)
    loc_map = {l["name"]: l_id for l, l_id in zip(locations_data, l_res.inserted_ids)}

    print("Seeding Items & Matches...")
    from app.repositories.counters import get_next_reference_no
    from app.services.matching import calculate_match_score

    now = datetime.utcnow()

    # 1. Matching Pair 1: MacBook Pro (High Score ~90%)
    ref_lost_1 = get_next_reference_no("LST")
    lost_1 = {
        "reference_no": ref_lost_1,
        "reporter_id": user_map["aarav.patel@campus.edu"],
        "name": "MacBook Pro 14 Space Grey",
        "category_id": cat_map["Electronics"],
        "description": "Space grey Apple laptop with Python logo sticker on top cover. Left in black neoprene sleeve.",
        "brand": "Apple",
        "color": "Space Grey",
        "lost_date": now - timedelta(days=2),
        "approx_time": "Around 2:30 PM",
        "last_seen_location_id": loc_map["Main Library Reading Room"],
        "image_path": None,
        "private_verification_detail": "Serial number ends in X789. Lockscreen wallpaper is Yosemite Half Dome. Minor scratch on bottom-left corner.",
        "stage": "Possible Match",
        "created_at": now - timedelta(days=2),
        "updated_at": now - timedelta(days=2)
    }
    lost_1_id = db.lost_items.insert_one(lost_1).inserted_id

    ref_found_1 = get_next_reference_no("FND")
    found_1 = {
        "reference_no": ref_found_1,
        "finder_id": user_map["vikram.malhotra@campus.edu"],
        "name": "MacBook Pro 14 Laptop in Sleeve",
        "category_id": cat_map["Electronics"],
        "found_datetime": now - timedelta(days=2, hours=-2),
        "found_location_id": loc_map["Main Library Reading Room"],
        "description": "Apple MacBook Pro laptop recovered in neoprene protective case from a study desk on 2nd floor.",
        "brand": "Apple",
        "color": "Space Grey",
        "private_details": "Serial #C02DX789. Wallpaper shows Yosemite Half Dome mountain. Small scratch on bottom chassis corner.",
        "image_path": None,
        "custody_location": "Central Library Desk Locker 1",
        "custodian_id": user_map["vikram.malhotra@campus.edu"],
        "status": "Possible Match",
        "archive_eligible": False,
        "created_at": now - timedelta(days=2),
        "updated_at": now - timedelta(days=2)
    }
    found_1_id = db.found_items.insert_one(found_1).inserted_id

    # 2. Matching Pair 2: Fossil Wallet (High Score ~85%)
    ref_lost_2 = get_next_reference_no("LST")
    lost_2 = {
        "reference_no": ref_lost_2,
        "reporter_id": user_map["rohan.verma@campus.edu"],
        "name": "Brown Leather Fossil Trifold Wallet",
        "category_id": cat_map["Wallets"],
        "description": "Men's brown leather wallet containing university ID and driver's license.",
        "brand": "Fossil",
        "color": "Brown",
        "lost_date": now - timedelta(days=3),
        "approx_time": "Lunch ~12:45 PM",
        "last_seen_location_id": loc_map["Cafeteria Food Court"],
        "image_path": None,
        "private_verification_detail": "Contains student card for Rohan Verma #90214, transit pass, and a folded receipt from campus bookstore.",
        "stage": "Under Review",
        "created_at": now - timedelta(days=3),
        "updated_at": now - timedelta(days=3)
    }
    lost_2_id = db.lost_items.insert_one(lost_2).inserted_id

    ref_found_2 = get_next_reference_no("FND")
    found_2 = {
        "reference_no": ref_found_2,
        "finder_id": user_map["priya.sharma@campus.edu"],
        "name": "Brown Fossil Leather Wallet",
        "category_id": cat_map["Wallets"],
        "found_datetime": now - timedelta(days=3, hours=-1),
        "found_location_id": loc_map["Cafeteria Food Court"],
        "description": "Leather wallet found on cafeteria table near cash register.",
        "brand": "Fossil",
        "color": "Brown",
        "private_details": "University ID #90214 belonging to Rohan Verma, Metro transit card, bookstore receipt inside.",
        "image_path": None,
        "custody_location": "Student Union Safe Box 4",
        "custodian_id": user_map["priya.sharma@campus.edu"],
        "status": "Claimed",
        "archive_eligible": False,
        "created_at": now - timedelta(days=3),
        "updated_at": now - timedelta(days=3)
    }
    found_2_id = db.found_items.insert_one(found_2).inserted_id

    # 3. Matching Pair 3: Hydro Flask (Moderate Score ~65%)
    ref_lost_3 = get_next_reference_no("LST")
    lost_3 = {
        "reference_no": ref_lost_3,
        "reporter_id": user_map["ananya.iyer@campus.edu"],
        "name": "Hydro Flask 32oz Water Bottle",
        "category_id": cat_map["Accessories"],
        "description": "Navy blue insulated steel drink flask with black flex cap.",
        "brand": "Hydro Flask",
        "color": "Navy Blue",
        "lost_date": now - timedelta(days=4),
        "approx_time": "Evening practice 5 PM",
        "last_seen_location_id": loc_map["Sports Ground Bleachers"],
        "image_path": None,
        "private_verification_detail": "Small dent on base rim; red silicone boot on bottom.",
        "stage": "Possible Match",
        "created_at": now - timedelta(days=4),
        "updated_at": now - timedelta(days=4)
    }
    lost_3_id = db.lost_items.insert_one(lost_3).inserted_id

    ref_found_3 = get_next_reference_no("FND")
    found_3 = {
        "reference_no": ref_found_3,
        "finder_id": user_map["kabir.mehta@campus.edu"],
        "name": "Blue Metal Water Flask",
        "category_id": cat_map["Accessories"],
        "found_datetime": now - timedelta(days=4, hours=-3),
        "found_location_id": loc_map["Sports Ground Bleachers"],
        "description": "Navy blue insulated vacuum water bottle left on bleachers after soccer game.",
        "brand": "Hydro Flask",
        "color": "Navy Blue",
        "private_details": "Red silicone protective boot on bottom, slight dent on bottom edge.",
        "image_path": None,
        "custody_location": "Athletic Equipment Room Shelf B",
        "custodian_id": user_map["priya.sharma@campus.edu"],
        "status": "Possible Match",
        "archive_eligible": False,
        "created_at": now - timedelta(days=4),
        "updated_at": now - timedelta(days=4)
    }
    found_3_id = db.found_items.insert_one(found_3).inserted_id

    # 4. Matching Pair 4: North Face Backpack (Fair Score ~50%)
    ref_lost_4 = get_next_reference_no("LST")
    lost_4 = {
        "reference_no": ref_lost_4,
        "reporter_id": user_map["neha.gupta@campus.edu"],
        "name": "Black North Face Recon Backpack",
        "category_id": cat_map["Bags"],
        "description": "Black canvas daypack with front mesh pocket.",
        "brand": "North Face",
        "color": "Black",
        "lost_date": now - timedelta(days=6),
        "approx_time": "11:00 AM",
        "last_seen_location_id": loc_map["Computer Science Lab 302"],
        "image_path": None,
        "private_verification_detail": "Brass owl keychain attached to side zipper; contains biology lab notebook.",
        "stage": "Reported",
        "created_at": now - timedelta(days=6),
        "updated_at": now - timedelta(days=6)
    }
    lost_4_id = db.lost_items.insert_one(lost_4).inserted_id

    ref_found_4 = get_next_reference_no("FND")
    found_4 = {
        "reference_no": ref_found_4,
        "finder_id": user_map["rohan.verma@campus.edu"],
        "name": "Black School Backpack",
        "category_id": cat_map["Bags"],
        "found_datetime": now - timedelta(days=5),
        "found_location_id": loc_map["Computer Science Lab 302"],
        "description": "Black branded rucksack discovered near printer in lab.",
        "brand": "The North Face",
        "color": "Black",
        "private_details": "Brass owl charm on zipper pull; binder with notes inside.",
        "image_path": None,
        "custody_location": "Engineering Office Front Counter",
        "custodian_id": user_map["vikram.malhotra@campus.edu"],
        "status": "Unmatched",
        "archive_eligible": False,
        "created_at": now - timedelta(days=5),
        "updated_at": now - timedelta(days=5)
    }
    found_4_id = db.found_items.insert_one(found_4).inserted_id

    # Compute & save match candidates for pairs
    for l_doc, f_doc in [(lost_1, found_1), (lost_2, found_2), (lost_3, found_3), (lost_4, found_4)]:
        l_doc["location"] = db.locations.find_one({"_id": l_doc["last_seen_location_id"]})
        f_doc["location"] = db.locations.find_one({"_id": f_doc["found_location_id"]})
        bk = calculate_match_score(l_doc, f_doc)
        db.match_candidates.insert_one({
            "lost_id": l_doc["_id"] if "_id" in l_doc else lost_1_id,
            "found_id": f_doc["_id"] if "_id" in f_doc else found_1_id,
            "score": bk["total_score"],
            "breakdown": bk,
            "is_dismissed": False,
            "created_at": now,
            "updated_at": now
        })

    # 5. Duplicates (2 similar reports in Library within 2 days)
    ref_lost_dup1 = get_next_reference_no("LST")
    db.lost_items.insert_one({
        "reference_no": ref_lost_dup1,
        "reporter_id": user_map["ananya.iyer@campus.edu"],
        "name": "TI-84 Plus CE Calculator",
        "category_id": cat_map["Electronics"],
        "description": "Black graphing calculator with slide cover.",
        "brand": "Texas Instruments",
        "color": "Black",
        "lost_date": now - timedelta(days=1),
        "approx_time": "10:00 AM",
        "last_seen_location_id": loc_map["Main Library Reading Room"],
        "image_path": None,
        "private_verification_detail": "Initials 'CD' scratched on battery compartment cover.",
        "stage": "Reported",
        "created_at": now - timedelta(days=1),
        "updated_at": now - timedelta(days=1)
    })

    ref_lost_dup2 = get_next_reference_no("LST")
    db.lost_items.insert_one({
        "reference_no": ref_lost_dup2,
        "reporter_id": user_map["rohan.verma@campus.edu"],
        "name": "Texas Instruments TI-84 Graphing Calculator",
        "category_id": cat_map["Electronics"],
        "description": "Black TI-84 graphing calculator left on 1st floor study desk.",
        "brand": "Texas Instruments",
        "color": "Black",
        "lost_date": now - timedelta(days=1),
        "approx_time": "11:30 AM",
        "last_seen_location_id": loc_map["Main Library Reading Room"],
        "image_path": None,
        "private_verification_detail": "Yellow battery sticker inside battery door.",
        "stage": "Reported",
        "created_at": now - timedelta(days=1),
        "updated_at": now - timedelta(days=1)
    })

    # 6. Completed Handover Item (Returned status)
    ref_lost_ret = get_next_reference_no("LST")
    lost_ret_id = db.lost_items.insert_one({
        "reference_no": ref_lost_ret,
        "reporter_id": user_map["aarav.patel@campus.edu"],
        "name": "Calculus Early Transcendentals Hardcover",
        "category_id": cat_map["Documents"],
        "description": "Stewart Calculus 9th edition textbook.",
        "brand": "Cengage",
        "color": "Blue",
        "lost_date": now - timedelta(days=10),
        "approx_time": "Morning class",
        "last_seen_location_id": loc_map["Chemistry Research Lab B"],
        "image_path": None,
        "private_verification_detail": "Highlighted chapters 3 and 4; bookmark from City Lights bookstore.",
        "stage": "Returned",
        "created_at": now - timedelta(days=10),
        "updated_at": now - timedelta(days=8)
    }).inserted_id

    ref_found_ret = get_next_reference_no("FND")
    found_ret_id = db.found_items.insert_one({
        "reference_no": ref_found_ret,
        "finder_id": user_map["vikram.malhotra@campus.edu"],
        "name": "Calculus Textbook (Stewart 9th Edition)",
        "category_id": cat_map["Documents"],
        "found_datetime": now - timedelta(days=9),
        "found_location_id": loc_map["Chemistry Research Lab B"],
        "description": "Thick calculus textbook turned in from science pavilion bench.",
        "brand": "Cengage",
        "color": "Blue",
        "private_details": "City lights bookmark on page 142; Aarav Patel notes in margins.",
        "image_path": None,
        "custody_location": "Main Library Custody Shelf",
        "custodian_id": user_map["vikram.malhotra@campus.edu"],
        "status": "Returned",
        "archive_eligible": False,
        "created_at": now - timedelta(days=9),
        "updated_at": now - timedelta(days=8)
    }).inserted_id

    # Handover record for returned item
    ref_clm_ret = get_next_reference_no("CLM")
    claim_ret_id = db.claims.insert_one({
        "reference_no": ref_clm_ret,
        "claimant_id": user_map["aarav.patel@campus.edu"],
        "found_id": found_ret_id,
        "lost_id": lost_ret_id,
        "claim_type": "Suggested",
        "proof_answer": "Has City Lights bookstore bookmark and my highlighter in chapter 4.",
        "reviewer_id": user_map["vikram.malhotra@campus.edu"],
        "reviewer_notes": "Claimant verified details and student ID matched. Approved and collected.",
        "status": "Returned",
        "created_at": now - timedelta(days=9),
        "decided_at": now - timedelta(days=8)
    }).inserted_id

    db.handovers.insert_one({
        "claim_id": claim_ret_id,
        "receiver_name": "Aarav Patel",
        "reviewer_id": user_map["vikram.malhotra@campus.edu"],
        "scheduled_datetime": now - timedelta(days=8),
        "return_datetime": now - timedelta(days=8),
        "acknowledgement_note": "Verified with student card #48291. Physically received textbook in excellent condition.",
        "created_at": now - timedelta(days=8),
        "updated_at": now - timedelta(days=8)
    })

    # 7. Additional Claims in Different Statuses
    # Claim on Fossil Wallet (Status: Approved, ready for pickup)
    ref_clm_app = get_next_reference_no("CLM")
    clm_app_id = db.claims.insert_one({
        "reference_no": ref_clm_app,
        "claimant_id": user_map["rohan.verma@campus.edu"],
        "found_id": found_2_id,
        "lost_id": lost_2_id,
        "claim_type": "Suggested",
        "proof_answer": "My student ID #90214 is in the left card slot, along with my transit card.",
        "reviewer_id": user_map["priya.sharma@campus.edu"],
        "reviewer_notes": "Student card matches Rohan Verma. Approved for pickup at Student Union desk.",
        "status": "Approved",
        "created_at": now - timedelta(days=2),
        "decided_at": now - timedelta(days=1)
    }).inserted_id

    # Scheduled handover for tomorrow
    db.handovers.insert_one({
        "claim_id": clm_app_id,
        "receiver_name": "Rohan Verma",
        "reviewer_id": user_map["priya.sharma@campus.edu"],
        "scheduled_datetime": now + timedelta(days=1, hours=3),
        "return_datetime": None,
        "acknowledgement_note": "Scheduled for pickup tomorrow at Student Union front counter.",
        "created_at": now - timedelta(days=1),
        "updated_at": now - timedelta(days=1)
    })

    # Claim on MacBook (Status: Under Review)
    ref_clm_rev = get_next_reference_no("CLM")
    db.claims.insert_one({
        "reference_no": ref_clm_rev,
        "claimant_id": user_map["aarav.patel@campus.edu"],
        "found_id": found_1_id,
        "lost_id": lost_1_id,
        "claim_type": "Suggested",
        "proof_answer": "Space grey 14-inch with Half Dome lockscreen and serial ending in X789.",
        "reviewer_id": None,
        "reviewer_notes": "",
        "status": "Under Review",
        "created_at": now - timedelta(hours=12),
        "decided_at": None
    })

    # Rejected Claim
    ref_clm_rej = get_next_reference_no("CLM")
    db.claims.insert_one({
        "reference_no": ref_clm_rej,
        "claimant_id": user_map["kabir.mehta@campus.edu"],
        "found_id": found_3_id,
        "lost_id": None,
        "claim_type": "Direct",
        "proof_answer": "It is just a plain blue water bottle with no markings.",
        "reviewer_id": user_map["priya.sharma@campus.edu"],
        "reviewer_notes": "Incorrect proof: Claimant failed to describe silicone boot and specific dent.",
        "status": "Rejected",
        "created_at": now - timedelta(days=3),
        "decided_at": now - timedelta(days=2)
    })

    # 8. Archive-Eligible Item (35 days old, unclaimed)
    ref_found_arch = get_next_reference_no("FND")
    db.found_items.insert_one({
        "reference_no": ref_found_arch,
        "finder_id": user_map["priya.sharma@campus.edu"],
        "name": "Unclaimed Woolen Winter Beanie",
        "category_id": cat_map["Clothing"],
        "found_datetime": now - timedelta(days=36),
        "found_location_id": loc_map["Campus Shuttle Bus 4"],
        "description": "Grey knitted winter beanie hat left on rear passenger seat.",
        "brand": "Unbranded",
        "color": "Grey",
        "private_details": "No specific tags, worn fabric.",
        "image_path": None,
        "custody_location": "Shuttle Depot Storage Bin 9",
        "custodian_id": user_map["priya.sharma@campus.edu"],
        "status": "Unmatched",
        "archive_eligible": True,
        "created_at": now - timedelta(days=35),
        "updated_at": now - timedelta(days=5)
    })

    # 9. Additional Lost and Found items to satisfy 12+ lost and 12+ found
    more_lost = [
        ("Keys with Red Lanyard", "Keys", "Main Security Desk", "Set of 3 brass keys with red campus lanyard", "Red", "Unknown", 5),
        ("Prescription Glasses in Black Case", "Accessories", "Administration Reception", "Ray-Ban black frame reading glasses", "Black", "Ray-Ban", 4),
        ("Denim Jacket Size M", "Clothing", "Performing Arts Auditorium", "Blue denim jacket with metal buttons", "Blue", "Levi's", 7),
        ("Silver iPad Air 5th Gen", "Electronics", "Hostel Block C Common Room", "Silver 10.9-inch tablet in blue folio cover", "Silver", "Apple", 3),
        ("Leather Keychain with Honda Fob", "Keys", "Main Security Desk", "Car remote key for Honda Civic with gym tag", "Black", "Honda", 2),
        ("Navy Blue Umbrella", "Other", "Cafeteria Food Court", "Compact folding automatic umbrella with wooden handle", "Navy Blue", "Totes", 1),
        ("Leather Passport Holder", "Documents", "Administration Reception", "Black leather travel wallet containing ID cards", "Black", "TravelPro", 8)
    ]
    for name, cat_name, loc_name, desc, color, brand, days_ago in more_lost:
        ref = get_next_reference_no("LST")
        db.lost_items.insert_one({
            "reference_no": ref,
            "reporter_id": user_map["ananya.iyer@campus.edu"],
            "name": name,
            "category_id": cat_map[cat_name],
            "description": desc,
            "brand": brand,
            "color": color,
            "lost_date": now - timedelta(days=days_ago),
            "approx_time": "Afternoon",
            "last_seen_location_id": loc_map[loc_name],
            "image_path": None,
            "private_verification_detail": f"Secret code / label: {name[:5]}-SECRET",
            "stage": "Reported",
            "created_at": now - timedelta(days=days_ago),
            "updated_at": now - timedelta(days=days_ago)
        })

    more_found = [
        ("Key Ring with Gym Tag", "Keys", "Main Security Desk", "Found set of keys with gym barcode token", "Silver", "Unknown", 4),
        ("Reading Glasses in Case", "Accessories", "Administration Reception", "Found spectacles in hard shell case on chair", "Black", "Ray-Ban", 3),
        ("Blue Denim Jacket", "Clothing", "Performing Arts Auditorium", "Left on seat in auditorium row F", "Blue", "Levi's", 6),
        ("iPad in Folio Cover", "Electronics", "Hostel Block C Common Room", "Tablet discovered in lounge couch cushion", "Silver", "Apple", 2),
        ("Car Remote Key", "Keys", "Main Security Desk", "Vehicle electronic key turned into gate guards", "Black", "Honda", 1),
        ("Folding Umbrella", "Other", "Cafeteria Food Court", "Found near trash bin by exit", "Blue", "Totes", 1),
        ("Black Document Pouch", "Documents", "Administration Reception", "Travel pouch turned in at main visitor desk", "Black", "TravelPro", 7)
    ]
    for name, cat_name, loc_name, desc, color, brand, days_ago in more_found:
        ref = get_next_reference_no("FND")
        db.found_items.insert_one({
            "reference_no": ref,
            "finder_id": user_map["vikram.malhotra@campus.edu"],
            "name": name,
            "category_id": cat_map[cat_name],
            "found_datetime": now - timedelta(days=days_ago),
            "found_location_id": loc_map[loc_name],
            "description": desc,
            "brand": brand,
            "color": color,
            "private_details": f"Secret specifics: {name[:5]}-DETAIL",
            "image_path": None,
            "custody_location": f"Main Security Safe Shelf {days_ago}",
            "custodian_id": user_map["vikram.malhotra@campus.edu"],
            "status": "Unmatched",
            "archive_eligible": False,
            "created_at": now - timedelta(days=days_ago),
            "updated_at": now - timedelta(days=days_ago)
        })

    print("Seeding Audit Logs...")
    audit_events = [
        ("user_registered", "user", user_map["aarav.patel@campus.edu"], user_map["aarav.patel@campus.edu"], {"email": "aarav.patel@campus.edu"}),
        ("staff_login", "user", user_map["priya.sharma@campus.edu"], user_map["priya.sharma@campus.edu"], {"role": "staff"}),
        ("staff_login", "user", user_map["admin@campus.edu"], user_map["admin@campus.edu"], {"role": "admin"}),
        ("lost_item_created", "lost_item", lost_1_id, user_map["aarav.patel@campus.edu"], {"reference_no": ref_lost_1}),
        ("found_item_created", "found_item", found_1_id, user_map["vikram.malhotra@campus.edu"], {"reference_no": ref_found_1}),
        ("claim_filed", "claim", clm_app_id, user_map["rohan.verma@campus.edu"], {"reference_no": ref_clm_app}),
        ("claim_decided", "claim", clm_app_id, user_map["priya.sharma@campus.edu"], {"new_status": "Approved"}),
        ("handover_completed", "handover", None, user_map["vikram.malhotra@campus.edu"], {"claim_ref": ref_clm_ret, "receiver": "Aarav Patel"}),
        ("flagged_archive_eligible", "found_item", None, None, {"retention_days": 30})
    ]
    for action, etype, eid, aid, details in audit_events:
        db.audit_logs.insert_one({
            "action": action,
            "entity_type": etype,
            "entity_id": eid,
            "actor_id": aid,
            "details": details,
            "timestamp": now - timedelta(hours=len(audit_events))
        })

    print("Database seeding completed successfully!")
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
