from datetime import datetime
from typing import Dict, Any, List
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.repositories.matches import upsert_match_candidate
from app.repositories.settings import get_setting
from app.services.events import emit_event


def calculate_match_score(
    lost: Dict[str, Any],
    found: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes a weighted match score (0 - 100) and explainable breakdown:
    - Category match: 30
    - Location: same location 25, same zone/building 12, else 0
    - Date proximity (found not before lost): <= 1 day: 20, <= 7 days: 10, else 0
    - Brand / color keyword overlap: up to 10
    - Description TF-IDF cosine similarity: up to 15
    """
    breakdown: Dict[str, Any] = {
        "category_score": 0,
        "location_score": 0,
        "date_score": 0,
        "keyword_score": 0,
        "tfidf_score": 0,
        "details": []
    }

    # 1. Category Match (30 pts)
    cat_match = False
    if lost.get("category_id") and found.get("category_id"):
        if str(lost["category_id"]) == str(found["category_id"]):
            breakdown["category_score"] = 30
            cat_match = True
            breakdown["details"].append("Category ✔")
        else:
            breakdown["details"].append("Category ✘")
    else:
        breakdown["details"].append("Category Unknown")

    # 2. Location Match (up to 25 pts)
    loc_score = 0
    lost_loc = lost.get("location") or {}
    found_loc = found.get("location") or {}
    
    lost_loc_id = str(lost.get("last_seen_location_id", ""))
    found_loc_id = str(found.get("found_location_id", ""))

    if lost_loc_id and found_loc_id and lost_loc_id == found_loc_id:
        loc_score = 25
        breakdown["details"].append("Location: Exact Match ✔")
    else:
        # Check building or zone
        lost_b = lost_loc.get("building", "").strip().lower()
        found_b = found_loc.get("building", "").strip().lower()
        lost_z = lost_loc.get("zone", "").strip().lower()
        found_z = found_loc.get("zone", "").strip().lower()
        
        if lost_b and found_b and lost_b == found_b:
            loc_score = 12
            breakdown["details"].append(f"Building: {lost_loc.get('building')} ✔")
        elif lost_z and found_z and lost_z == found_z:
            loc_score = 12
            breakdown["details"].append(f"Zone: {lost_loc.get('zone')} ✔")
        else:
            breakdown["details"].append("Location ✘")
            
    breakdown["location_score"] = loc_score

    # 3. Date Proximity (up to 20 pts)
    date_score = 0
    lost_dt = lost.get("lost_date")
    found_dt = found.get("found_datetime")

    if isinstance(lost_dt, datetime) and isinstance(found_dt, datetime):
        # Convert both to date-level or naive comparison
        diff_seconds = (found_dt - lost_dt).total_seconds()
        # Allow slight buffer (e.g. lost earlier same day or reported slightly offset)
        if diff_seconds < -86400:
            # Found more than 1 day before it was supposedly lost -> unlikely match
            date_score = 0
            breakdown["details"].append("Date: Found before reported lost ✘")
        else:
            diff_days = abs(diff_seconds) / 86400.0
            if diff_days <= 1.0:
                date_score = 20
                breakdown["details"].append("Within 24 hours ✔")
            elif diff_days <= 7.0:
                date_score = 10
                breakdown["details"].append(f"Within {int(diff_days)} days ✔")
            else:
                date_score = 0
                breakdown["details"].append(f"{int(diff_days)} days apart")
    breakdown["date_score"] = date_score

    # 4. Brand & Color Keyword Overlap (up to 10 pts: Brand 5, Color 5)
    keyword_score = 0
    lost_brand = (lost.get("brand") or "").strip().lower()
    found_brand = (found.get("brand") or "").strip().lower()
    if lost_brand and found_brand:
        if lost_brand == found_brand or lost_brand in found_brand or found_brand in lost_brand:
            keyword_score += 5
            breakdown["details"].append(f"Brand: {lost.get('brand')} ✔")
        else:
            # Check token overlap
            l_b_words = set(re.findall(r"\w+", lost_brand))
            f_b_words = set(re.findall(r"\w+", found_brand))
            if l_b_words & f_b_words:
                keyword_score += 3
                breakdown["details"].append(f"Brand partial match ✔")

    lost_color = (lost.get("color") or "").strip().lower()
    found_color = (found.get("color") or "").strip().lower()
    if lost_color and found_color:
        if lost_color == found_color or lost_color in found_color or found_color in lost_color:
            keyword_score += 5
            breakdown["details"].append(f"Color: {lost.get('color')} ✔")
        else:
            l_c_words = set(re.findall(r"\w+", lost_color))
            f_c_words = set(re.findall(r"\w+", found_color))
            if l_c_words & f_c_words:
                keyword_score += 3
                breakdown["details"].append("Color partial match ✔")

    breakdown["keyword_score"] = min(10, keyword_score)

    # 5. Description TF-IDF Cosine Similarity (up to 15 pts)
    tfidf_score = 0
    desc_l = f"{lost.get('name', '')} {lost.get('description', '')}".strip().lower()
    desc_f = f"{found.get('name', '')} {found.get('description', '')}".strip().lower()

    if desc_l and desc_f:
        try:
            vectorizer = TfidfVectorizer(stop_words="english", token_pattern=r"(?u)\b\w+\b")
            tfidf_mat = vectorizer.fit_transform([desc_l, desc_f])
            sim = cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:2])[0][0]
            # Scale sim (0.0 to 1.0) to 15 points
            tfidf_score = int(round(sim * 15))
            breakdown["details"].append(f"Description {int(round(sim * 100))}% similar")
        except Exception:
            tfidf_score = 0
    breakdown["tfidf_score"] = min(15, tfidf_score)

    # Total Score
    total = (
        breakdown["category_score"] +
        breakdown["location_score"] +
        breakdown["date_score"] +
        breakdown["keyword_score"] +
        breakdown["tfidf_score"]
    )
    total = max(0, min(100, total))
    breakdown["total_score"] = total
    breakdown["summary"] = " • ".join(breakdown["details"])
    return breakdown


def run_matching_for_lost_item(lost_id: Any) -> List[Dict[str, Any]]:
    """
    Compares a single lost item against all open found items.
    Updates match_candidates and auto-promotes to 'Possible Match' if score >= strong_match_threshold.
    """
    from app.repositories.items import get_lost_item_by_id, get_found_items, update_lost_item, update_found_item
    
    lost = get_lost_item_by_id(lost_id, is_staff=True, is_owner=True)
    if not lost or lost.get("stage") in ["Returned", "Archived"]:
        return []

    # Get open found items (Unmatched or Possible Match)
    open_found, _ = get_found_items(
        filter_query={"status": {"$in": ["Unmatched", "Possible Match"]}},
        limit=200,
        is_staff=True
    )

    strong_threshold = int(get_setting("strong_match_threshold", 60))
    matches_created = []
    has_strong_match = False

    for found in open_found:
        breakdown = calculate_match_score(lost, found)
        score = breakdown["total_score"]
        
        # Save or update candidate if score is meaningful (> 15)
        if score >= 15:
            cand = upsert_match_candidate(lost["_id"], found["_id"], score, breakdown)
            matches_created.append(cand)

        if score >= strong_threshold:
            has_strong_match = True
            # Auto-promote found item if still Unmatched
            if found.get("status") == "Unmatched":
                update_found_item(found["_id"], {"status": "Possible Match"})
                emit_event("status_changed", "found_item", found["_id"], actor_id=None, payload={
                    "old_status": "Unmatched",
                    "new_status": "Possible Match",
                    "reason": f"Strong match with {lost.get('reference_no')} (Score: {score})"
                })

    # Auto-promote lost item if still Reported
    if has_strong_match and lost.get("stage") == "Reported":
        update_lost_item(lost["_id"], {"stage": "Possible Match"})
        emit_event("stage_changed", "lost_item", lost["_id"], actor_id=None, payload={
            "old_stage": "Reported",
            "new_stage": "Possible Match",
            "reason": f"Strong match found (Threshold: {strong_threshold})"
        })

    return matches_created


def run_matching_for_found_item(found_id: Any) -> List[Dict[str, Any]]:
    """
    Compares a single found item against all open lost items.
    Updates match_candidates and auto-promotes to 'Possible Match' if score >= strong_match_threshold.
    """
    from app.repositories.items import get_found_item_by_id, get_lost_items, update_lost_item, update_found_item
    
    found = get_found_item_by_id(found_id, is_staff=True)
    if not found or found.get("status") in ["Returned", "Archived"]:
        return []

    # Get open lost items (Reported or Possible Match)
    open_lost, _ = get_lost_items(
        filter_query={"stage": {"$in": ["Reported", "Possible Match"]}},
        limit=200,
        is_staff=True
    )

    strong_threshold = int(get_setting("strong_match_threshold", 60))
    matches_created = []
    has_strong_match = False

    for lost in open_lost:
        breakdown = calculate_match_score(lost, found)
        score = breakdown["total_score"]
        
        if score >= 15:
            cand = upsert_match_candidate(lost["_id"], found["_id"], score, breakdown)
            matches_created.append(cand)

        if score >= strong_threshold:
            has_strong_match = True
            if lost.get("stage") == "Reported":
                update_lost_item(lost["_id"], {"stage": "Possible Match"})
                emit_event("stage_changed", "lost_item", lost["_id"], actor_id=None, payload={
                    "old_stage": "Reported",
                    "new_stage": "Possible Match",
                    "reason": f"Strong match with {found.get('reference_no')} (Score: {score})"
                })

    if has_strong_match and found.get("status") == "Unmatched":
        update_found_item(found["_id"], {"status": "Possible Match"})
        emit_event("status_changed", "found_item", found["_id"], actor_id=None, payload={
            "old_status": "Unmatched",
            "new_status": "Possible Match",
            "reason": f"Strong match found (Threshold: {strong_threshold})"
        })

    return matches_created
