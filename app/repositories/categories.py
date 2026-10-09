from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.db import get_db, to_object_id


def create_category(name: str, icon: str = "bi-tag", is_active: bool = True) -> ObjectId:
    """Create a new category."""
    db = get_db()
    doc = {
        "name": name.strip(),
        "icon": icon.strip(),
        "is_active": is_active
    }
    res = db.categories.insert_one(doc)
    return res.inserted_id


def get_all_categories(active_only: bool = False) -> List[Dict[str, Any]]:
    """List categories sorted by name."""
    db = get_db()
    query = {"is_active": True} if active_only else {}
    return list(db.categories.find(query).sort("name", 1))


def get_category_by_id(cat_id: Any) -> Optional[Dict[str, Any]]:
    """Get category by id."""
    oid = to_object_id(cat_id)
    if not oid:
        return None
    db = get_db()
    return db.categories.find_one({"_id": oid})


def update_category(cat_id: Any, name: str, icon: str, is_active: bool) -> bool:
    """Update category details."""
    oid = to_object_id(cat_id)
    if not oid:
        return False
    db = get_db()
    res = db.categories.update_one(
        {"_id": oid},
        {"$set": {"name": name.strip(), "icon": icon.strip(), "is_active": is_active}}
    )
    return res.modified_count > 0 or res.matched_count > 0
