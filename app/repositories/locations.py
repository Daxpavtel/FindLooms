from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.db import get_db, to_object_id


def create_location(
    name: str,
    building: str,
    zone: str,
    venue: str = "",
    latitude: float = 0.0,
    longitude: float = 0.0,
    is_active: bool = True
) -> ObjectId:
    """Create a new campus/facility location."""
    db = get_db()
    doc = {
        "name": name.strip(),
        "building": building.strip(),
        "zone": zone.strip(),
        "venue": venue.strip(),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "is_active": is_active
    }
    res = db.locations.insert_one(doc)
    return res.inserted_id


def get_all_locations(active_only: bool = False) -> List[Dict[str, Any]]:
    """List locations sorted by building and name."""
    db = get_db()
    query = {"is_active": True} if active_only else {}
    return list(db.locations.find(query).sort([("building", 1), ("name", 1)]))


def get_location_by_id(loc_id: Any) -> Optional[Dict[str, Any]]:
    """Get location by id."""
    oid = to_object_id(loc_id)
    if not oid:
        return None
    db = get_db()
    return db.locations.find_one({"_id": oid})


def update_location(
    loc_id: Any,
    name: str,
    building: str,
    zone: str,
    venue: str,
    latitude: float,
    longitude: float,
    is_active: bool
) -> bool:
    """Update location details."""
    oid = to_object_id(loc_id)
    if not oid:
        return False
    db = get_db()
    res = db.locations.update_one(
        {"_id": oid},
        {"$set": {
            "name": name.strip(),
            "building": building.strip(),
            "zone": zone.strip(),
            "venue": venue.strip(),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "is_active": is_active
        }}
    )
    return res.modified_count > 0 or res.matched_count > 0


def get_zones() -> List[str]:
    """Get list of distinct zones."""
    db = get_db()
    return db.locations.distinct("zone")


def get_buildings() -> List[str]:
    """Get list of distinct buildings."""
    db = get_db()
    return db.locations.distinct("building")
