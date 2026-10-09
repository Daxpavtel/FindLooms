from datetime import datetime
from pymongo import ReturnDocument
from app.db import get_db


def get_next_reference_no(prefix: str) -> str:
    """
    Atomically increments the sequence for prefix ('LST', 'FND', 'CLM')
    and returns a formatted reference number like 'LST-2026-0001'.
    """
    db = get_db()
    current_year = datetime.utcnow().year
    
    counter = db.counters.find_one_and_update(
        {"_id": prefix},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    
    seq_num = counter.get("seq", 1)
    return f"{prefix}-{current_year}-{seq_num:04d}"
