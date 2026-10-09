from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from app.db import get_db, to_object_id

from app.repositories.counters import get_next_reference_no

# Security Projections: NEVER include private fields for normal users / public
SAFE_LOST_PROJECTION = {"private_verification_detail": 0}
SAFE_FOUND_PROJECTION = {"private_details": 0}


# ==========================================
# LOST ITEMS
# ==========================================

def create_lost_item(
    reporter_id: Any,
    name: str,
    category_id: Any,
    description: str,
    brand: str,
    color: str,
    lost_date: datetime,
    approx_time: str,
    last_seen_location_id: Any,
    private_verification_detail: str,
    image_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new lost item document."""
    db = get_db()
    ref_no = get_next_reference_no("LST")
    now = datetime.utcnow()
    doc = {
        "reference_no": ref_no,
        "reporter_id": to_object_id(reporter_id),
        "name": name.strip(),
        "category_id": to_object_id(category_id),
        "description": description.strip(),
        "brand": brand.strip(),
        "color": color.strip(),
        "lost_date": lost_date,
        "approx_time": approx_time.strip(),
        "last_seen_location_id": to_object_id(last_seen_location_id),
        "image_path": image_path,
        "private_verification_detail": private_verification_detail.strip(),
        "stage": "Reported",
        "created_at": now,
        "updated_at": now
    }
    res = db.lost_items.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


def get_lost_item_by_id(item_id: Any, is_staff: bool = False, is_owner: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a lost item by ID.
    If not staff and not the original reporter, strips private_verification_detail.
    """
    oid = to_object_id(item_id)
    if not oid:
        return None
    db = get_db()
    
    # We can fetch and attach related entities (category, location, reporter)
    item = db.lost_items.find_one({"_id": oid})
    if not item:
        return None
        
    if not is_staff and not is_owner:
        item.pop("private_verification_detail", None)
        
    _populate_item_relations(item, is_lost=True)
    return item


def get_lost_items(
    filter_query: Optional[Dict[str, Any]] = None,
    sort_by: str = "created_at",
    sort_dir: int = -1,
    limit: int = 10,
    skip: int = 0,
    is_staff: bool = False
) -> Tuple[List[Dict[str, Any]], int]:
    """List lost items with pagination and populated relations."""
    db = get_db()
    query = filter_query or {}
    projection = None if is_staff else SAFE_LOST_PROJECTION
    
    total = db.lost_items.count_documents(query)
    cursor = db.lost_items.find(query, projection).sort(sort_by, sort_dir).skip(skip).limit(limit)
    items = list(cursor)
    for it in items:
        _populate_item_relations(it, is_lost=True)
    return items, total


def update_lost_item(item_id: Any, update_data: Dict[str, Any]) -> bool:
    """Update fields of a lost item."""
    oid = to_object_id(item_id)
    if not oid:
        return False
    db = get_db()
    update_data["updated_at"] = datetime.utcnow()
    res = db.lost_items.update_one({"_id": oid}, {"$set": update_data})
    return res.acknowledged


# ==========================================
# FOUND ITEMS
# ==========================================

def create_found_item(
    finder_id: Any,
    name: str,
    category_id: Any,
    found_datetime: datetime,
    found_location_id: Any,
    description: str,
    brand: str,
    color: str,
    private_details: str,
    custody_location: str,
    custodian_id: Optional[Any] = None,
    image_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new found item document."""
    db = get_db()
    ref_no = get_next_reference_no("FND")
    now = datetime.utcnow()
    doc = {
        "reference_no": ref_no,
        "finder_id": to_object_id(finder_id),
        "name": name.strip(),
        "category_id": to_object_id(category_id),
        "found_datetime": found_datetime,
        "found_location_id": to_object_id(found_location_id),
        "description": description.strip(),
        "brand": brand.strip(),
        "color": color.strip(),
        "private_details": private_details.strip(),
        "image_path": image_path,
        "custody_location": custody_location.strip(),
        "custodian_id": to_object_id(custodian_id) if custodian_id else to_object_id(finder_id),
        "status": "Unmatched",
        "archive_eligible": False,
        "created_at": now,
        "updated_at": now
    }
    res = db.found_items.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


def get_found_item_by_id(item_id: Any, is_staff: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a found item by ID.
    If not staff, private_details is strictly stripped.
    """
    oid = to_object_id(item_id)
    if not oid:
        return None
    db = get_db()
    
    item = db.found_items.find_one({"_id": oid})
    if not item:
        return None
        
    if not is_staff:
        item.pop("private_details", None)
        
    _populate_item_relations(item, is_lost=False)
    return item


def get_found_items(
    filter_query: Optional[Dict[str, Any]] = None,
    sort_by: str = "created_at",
    sort_dir: int = -1,
    limit: int = 10,
    skip: int = 0,
    is_staff: bool = False
) -> Tuple[List[Dict[str, Any]], int]:
    """List found items with pagination and public-safe projections."""
    db = get_db()
    query = filter_query or {}
    projection = None if is_staff else SAFE_FOUND_PROJECTION
    
    total = db.found_items.count_documents(query)
    cursor = db.found_items.find(query, projection).sort(sort_by, sort_dir).skip(skip).limit(limit)
    items = list(cursor)
    for it in items:
        _populate_item_relations(it, is_lost=False)
    return items, total


def update_found_item(item_id: Any, update_data: Dict[str, Any]) -> bool:
    """Update fields of a found item."""
    oid = to_object_id(item_id)
    if not oid:
        return False
    db = get_db()
    update_data["updated_at"] = datetime.utcnow()
    res = db.found_items.update_one({"_id": oid}, {"$set": update_data})
    return res.acknowledged


# ==========================================
# DUPLICATE DETECTION HELPER
# ==========================================

def find_potential_duplicates(
    category_id: Any,
    location_id: Any,
    target_date: datetime,
    is_lost: bool = True,
    window_days: int = 2,
    exclude_id: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Finds existing items that have:
    - Same category
    - Same location or same building
    - Date within +/- window_days
    - Not archived or returned
    """
    db = get_db()
    cat_oid = to_object_id(category_id)
    loc_oid = to_object_id(location_id)
    if not cat_oid:
        return []

    # Get location and building
    target_loc = db.locations.find_one({"_id": loc_oid}) if loc_oid else None
    building_loc_ids = []
    if target_loc and target_loc.get("building"):
        b_locs = db.locations.find({"building": target_loc["building"]}, {"_id": 1})
        building_loc_ids = [l["_id"] for l in b_locs]
    elif loc_oid:
        building_loc_ids = [loc_oid]

    start_date = target_date - timedelta(days=window_days)
    end_date = target_date + timedelta(days=window_days)

    if is_lost:
        query: Dict[str, Any] = {
            "category_id": cat_oid,
            "lost_date": {"$gte": start_date, "$lte": end_date},
            "stage": {"$nin": ["Returned", "Archived"]}
        }
        if building_loc_ids:
            query["last_seen_location_id"] = {"$in": building_loc_ids}
        if exclude_id and to_object_id(exclude_id):
            query["_id"] = {"$ne": to_object_id(exclude_id)}
        items = list(db.lost_items.find(query, SAFE_LOST_PROJECTION).limit(5))
        for it in items:
            _populate_item_relations(it, is_lost=True)
        return items
    else:
        query = {
            "category_id": cat_oid,
            "found_datetime": {"$gte": start_date, "$lte": end_date},
            "status": {"$nin": ["Returned", "Archived"]}
        }
        if building_loc_ids:
            query["found_location_id"] = {"$in": building_loc_ids}
        if exclude_id and to_object_id(exclude_id):
            query["_id"] = {"$ne": to_object_id(exclude_id)}
        items = list(db.found_items.find(query, SAFE_FOUND_PROJECTION).limit(5))
        for it in items:
            _populate_item_relations(it, is_lost=False)
        return items


def _populate_item_relations(item: Dict[str, Any], is_lost: bool = True) -> None:
    """Helper to attach category and location info into the item dictionary."""
    db = get_db()
    if item.get("category_id"):
        cat = db.categories.find_one({"_id": item["category_id"]})
        item["category"] = cat or {"name": "Uncategorized", "icon": "bi-tag"}
    else:
        item["category"] = {"name": "Uncategorized", "icon": "bi-tag"}

    loc_key = "last_seen_location_id" if is_lost else "found_location_id"
    if item.get(loc_key):
        loc = db.locations.find_one({"_id": item[loc_key]})
        item["location"] = loc or {"name": "Unknown", "building": "Unknown", "zone": "Unknown"}
    else:
        item["location"] = {"name": "Unknown", "building": "Unknown", "zone": "Unknown"}
        
    user_key = "reporter_id" if is_lost else "finder_id"
    if item.get(user_key):
        usr = db.users.find_one({"_id": item[user_key]}, {"name": 1, "email": 1, "department": 1, "phone": 1})
        item["user"] = usr
