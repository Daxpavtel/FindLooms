from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.db import get_db, to_object_id


def create_user(
    name: str,
    email: str,
    password_hash: str,
    role: str = "user",
    department: str = "",
    phone: str = "",
    is_active: bool = True
) -> ObjectId:
    """Create a new user document."""
    db = get_db()
    user_doc = {
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "role": role if role in ["user", "staff", "admin"] else "user",
        "department": department.strip(),
        "phone": phone.strip(),
        "is_active": is_active,
        "created_at": datetime.utcnow()
    }
    result = db.users.insert_one(user_doc)
    return result.inserted_id


def find_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Find a user by normalized email address."""
    if not isinstance(email, str):
        return None
    db = get_db()
    return db.users.find_one({"email": email.strip().lower()})


def find_by_id(user_id: Any) -> Optional[Dict[str, Any]]:
    """Find a user by ObjectId or string representation."""
    oid = to_object_id(user_id)
    if not oid:
        return None
    db = get_db()
    return db.users.find_one({"_id": oid})


def get_all_users(limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
    """List users ordered by creation date."""
    db = get_db()
    return list(db.users.find().sort("created_at", -1).skip(skip).limit(limit))


def count_users() -> int:
    """Count total registered users."""
    db = get_db()
    return db.users.count_documents({})


def update_user_role(user_id: Any, role: str) -> bool:
    """Update role for a user (user, staff, admin)."""
    oid = to_object_id(user_id)
    if not oid or role not in ["user", "staff", "admin"]:
        return False
    db = get_db()
    res = db.users.update_one({"_id": oid}, {"$set": {"role": role}})
    return res.modified_count > 0


def update_user_status(user_id: Any, is_active: bool) -> bool:
    """Toggle user active status."""
    oid = to_object_id(user_id)
    if not oid:
        return False
    db = get_db()
    res = db.users.update_one({"_id": oid}, {"$set": {"is_active": bool(is_active)}})
    return res.modified_count > 0


def update_profile(user_id: Any, name: str, department: str, phone: str) -> bool:
    """Update user personal profile fields."""
    oid = to_object_id(user_id)
    if not oid:
        return False
    db = get_db()
    res = db.users.update_one(
        {"_id": oid},
        {"$set": {
            "name": name.strip(),
            "department": department.strip(),
            "phone": phone.strip()
        }}
    )
    return res.modified_count > 0
