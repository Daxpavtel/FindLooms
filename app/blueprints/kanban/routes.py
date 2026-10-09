from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import kanban_bp
from app.auth_utils import staff_required
from app.db import get_db, to_object_id
from app.repositories.categories import get_all_categories
from app.repositories.locations import get_all_locations
from app.repositories.items import _populate_item_relations
from app.services.workflow import transition_lost_stage, transition_found_status, LOST_TRANSITIONS, FOUND_TRANSITIONS


KANBAN_STAGES = [
    "Reported",
    "Possible Match",
    "Under Review",
    "Returned",
    "Archived"
]

# Mapping between lost stage and found status
FOUND_STAGE_MAP = {
    "Reported": "Unmatched",
    "Possible Match": "Possible Match",
    "Under Review": "Claimed",
    "Returned": "Returned",
    "Archived": "Archived"
}


@kanban_bp.route("")
@login_required
@staff_required
def board():
    db = get_db()
    
    # Filter parameters
    cat_filter = request.args.get("category")
    loc_filter = request.args.get("location")
    item_type = request.args.get("type", "all")  # all, lost, found

    query_lost = {}
    query_found = {}

    if cat_filter and to_object_id(cat_filter):
        oid = to_object_id(cat_filter)
        query_lost["category_id"] = oid
        query_found["category_id"] = oid

    if loc_filter and to_object_id(loc_filter):
        oid = to_object_id(loc_filter)
        query_lost["last_seen_location_id"] = oid
        query_found["found_location_id"] = oid

    # Group items by column
    columns = {stage: [] for stage in KANBAN_STAGES}

    now = datetime.utcnow()

    # Load Lost items
    if item_type in ["all", "lost"]:
        lost_items = list(db.lost_items.find(query_lost))
        for it in lost_items:
            _populate_item_relations(it, is_lost=True)
            it["item_type"] = "lost"
            it["current_stage"] = it.get("stage", "Reported")
            
            # Calculate age
            created = it.get("created_at", now)
            age_days = (now - created).days
            it["age_days"] = age_days
            it["age_class"] = "danger" if age_days >= 14 else ("warning" if age_days >= 7 else "secondary")

            # Check top match score
            top_match = db.match_candidates.find_one({"lost_id": it["_id"], "is_dismissed": False}, sort=[("score", -1)])
            it["top_score"] = top_match.get("score") if top_match else None
            it["allowed_next"] = list(LOST_TRANSITIONS.get(it["current_stage"], set()))

            if it["current_stage"] in columns:
                columns[it["current_stage"]].append(it)

    # Load Found items
    if item_type in ["all", "found"]:
        found_items = list(db.found_items.find(query_found))
        for it in found_items:
            _populate_item_relations(it, is_lost=False)
            it["item_type"] = "found"
            status = it.get("status", "Unmatched")
            # Map Unmatched -> Reported, Claimed -> Under Review for board consistency
            mapped_stage = "Reported" if status == "Unmatched" else ("Under Review" if status == "Claimed" else status)
            it["current_stage"] = status
            it["board_stage"] = mapped_stage
            
            created = it.get("created_at", now)
            age_days = (now - created).days
            it["age_days"] = age_days
            it["age_class"] = "danger" if age_days >= 14 else ("warning" if age_days >= 7 else "secondary")

            top_match = db.match_candidates.find_one({"found_id": it["_id"], "is_dismissed": False}, sort=[("score", -1)])
            it["top_score"] = top_match.get("score") if top_match else None
            it["allowed_next"] = list(FOUND_TRANSITIONS.get(status, set()))

            if mapped_stage in columns:
                columns[mapped_stage].append(it)

    categories = get_all_categories()
    locations = get_all_locations()

    return render_template(
        "kanban/board.html",
        columns=columns,
        stages=KANBAN_STAGES,
        categories=categories,
        locations=locations,
        current_category=cat_filter,
        current_location=loc_filter,
        current_type=item_type
    )


@kanban_bp.route("/move", methods=["POST"])
@login_required
@staff_required
def move_card():
    item_type = request.form.get("item_type")
    item_id = request.form.get("item_id")
    target_stage = request.form.get("target_stage")

    if not item_id or not target_stage or not item_type:
        flash("Invalid stage move parameters.", "danger")
        return redirect(url_for("kanban.board"))

    if item_type == "lost":
        ok, msg = transition_lost_stage(
            lost_id=item_id,
            new_stage=target_stage,
            actor_id=current_user.id,
            notes=f"Moved via Kanban board by {current_user.name}"
        )
    elif item_type == "found":
        ok, msg = transition_found_status(
            found_id=item_id,
            new_status=target_stage,
            actor_id=current_user.id,
            notes=f"Moved via Kanban board by {current_user.name}"
        )
    else:
        ok, msg = False, "Unknown item type."

    if ok:
        flash(msg, "success")
    else:
        flash(f"Cannot move card: {msg}", "danger")

    return redirect(url_for("kanban.board"))
