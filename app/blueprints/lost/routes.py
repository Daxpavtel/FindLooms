from datetime import datetime, time
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user

from . import lost_bp
from app.forms.item_forms import LostItemForm
from app.repositories.categories import get_all_categories
from app.repositories.locations import get_all_locations
from app.repositories.items import (
    create_lost_item,
    get_lost_item_by_id,
    get_lost_items,
    update_lost_item,
    find_potential_duplicates
)
from app.repositories.matches import (
    get_matches_for_lost_item,
    count_matches_for_lost
)
from app.repositories.settings import get_setting
from app.services.upload import validate_and_save_image
from app.services.matching import run_matching_for_lost_item
from app.services.events import emit_event
from app.db import to_object_id


def _populate_form_choices(form: LostItemForm):
    cats = get_all_categories(active_only=True)
    locs = get_all_locations(active_only=True)
    form.category_id.choices = [(str(c["_id"]), c["name"]) for c in cats]
    form.last_seen_location_id.choices = [(str(l["_id"]), f"{l['name']} ({l['building']})") for l in locs]


@lost_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = LostItemForm()
    _populate_form_choices(form)

    potential_duplicates = []
    # Check duplicate detection if form submitted
    if request.method == "POST":
        cat_id = form.category_id.data
        loc_id = form.last_seen_location_id.data
        lost_d = form.lost_date.data
        window_days = int(get_setting("duplicate_window_days", 2))
        
        if cat_id and loc_id and lost_d:
            dt = datetime.combine(lost_d, time.min)
            potential_duplicates = find_potential_duplicates(
                category_id=cat_id,
                location_id=loc_id,
                target_date=dt,
                is_lost=True,
                window_days=window_days
            )

        # If duplicates exist and user hasn't explicitly clicked proceed
        proceed_anyway = request.form.get("proceed_anyway") == "true"
        if potential_duplicates and not proceed_anyway:
            flash("Warning: Similar reports already exist in this area around the same date. Please verify before proceeding.", "warning")
            return render_template(
                "lost/create.html",
                form=form,
                potential_duplicates=potential_duplicates
            )

    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            image_path, err = validate_and_save_image(form.image.data)
            if err:
                flash(err, "danger")
                return render_template("lost/create.html", form=form, potential_duplicates=potential_duplicates)

        dt = datetime.combine(form.lost_date.data, time.min)
        doc = create_lost_item(
            reporter_id=current_user.id,
            name=form.name.data,
            category_id=form.category_id.data,
            description=form.description.data,
            brand=form.brand.data or "",
            color=form.color.data,
            lost_date=dt,
            approx_time=form.approx_time.data or "",
            last_seen_location_id=form.last_seen_location_id.data,
            private_verification_detail=form.private_verification_detail.data,
            image_path=image_path
        )

        emit_event("lost_item_created", "lost_item", doc["_id"], actor_id=current_user.id, payload={
            "reference_no": doc["reference_no"],
            "name": doc["name"]
        })

        # Run Smart Match Engine asynchronously or inline
        run_matching_for_lost_item(doc["_id"])

        flash(f"Lost item report {doc['reference_no']} created successfully!", "success")
        return redirect(url_for("lost.detail", item_id=str(doc["_id"])))

    return render_template("lost/create.html", form=form, potential_duplicates=potential_duplicates)


@lost_bp.route("")
def list_items():
    page = int(request.args.get("page", 1))
    per_page = current_app.config.get("ITEMS_PER_PAGE", 10)
    skip = (page - 1) * per_page

    cat_filter = request.args.get("category")
    stage_filter = request.args.get("stage")
    q = request.args.get("q", "").strip()

    query = {}
    if cat_filter and to_object_id(cat_filter):
        query["category_id"] = to_object_id(cat_filter)
    if stage_filter:
        query["stage"] = stage_filter
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"reference_no": {"$regex": q, "$options": "i"}}
        ]

    is_staff = current_user.is_authenticated and current_user.is_staff
    items, total = get_lost_items(
        filter_query=query,
        limit=per_page,
        skip=skip,
        is_staff=is_staff
    )

    total_pages = (total + per_page - 1) // per_page if per_page else 1
    categories = get_all_categories()

    return render_template(
        "lost/list.html",
        items=items,
        page=page,
        total_pages=total_pages,
        total=total,
        categories=categories,
        current_category=cat_filter,
        current_stage=stage_filter,
        search_query=q
    )


@lost_bp.route("/<item_id>")
def detail(item_id: str):
    is_staff = current_user.is_authenticated and current_user.is_staff
    
    # Check owner
    item = get_lost_item_by_id(item_id, is_staff=True)
    if not item:
        abort(404)

    is_owner = current_user.is_authenticated and str(item.get("reporter_id")) == current_user.id
    
    # If not staff and not owner, ensure hidden detail is stripped
    if not is_staff and not is_owner:
        item.pop("private_verification_detail", None)

    # Count possible matches for smart badge
    match_count = count_matches_for_lost(item["_id"], min_score=40)

    return render_template(
        "lost/detail.html",
        item=item,
        is_owner=is_owner,
        is_staff=is_staff,
        match_count=match_count
    )


@lost_bp.route("/<item_id>/matches")
@login_required
def matches(item_id: str):
    is_staff = current_user.is_staff
    item = get_lost_item_by_id(item_id, is_staff=is_staff, is_owner=True)
    if not item:
        abort(404)

    # Only owner or staff may see match candidates
    if not is_staff and str(item.get("reporter_id")) != current_user.id:
        abort(403)

    match_candidates = get_matches_for_lost_item(item["_id"], min_score=20, is_staff=is_staff)
    return render_template(
        "lost/matches.html",
        item=item,
        matches=match_candidates
    )


@lost_bp.route("/<item_id>/edit", methods=["GET", "POST"])
@login_required
def edit(item_id: str):
    item = get_lost_item_by_id(item_id, is_staff=True)
    if not item:
        abort(404)

    is_owner = str(item.get("reporter_id")) == current_user.id
    if not current_user.is_staff and not is_owner:
        abort(403)

    form = LostItemForm(
        name=item.get("name"),
        category_id=str(item.get("category_id")),
        brand=item.get("brand"),
        color=item.get("color"),
        lost_date=item.get("lost_date").date() if item.get("lost_date") else None,
        approx_time=item.get("approx_time"),
        last_seen_location_id=str(item.get("last_seen_location_id")),
        description=item.get("description"),
        private_verification_detail=item.get("private_verification_detail", "")
    )
    _populate_form_choices(form)

    if form.validate_on_submit():
        update_data = {
            "name": form.name.data.strip(),
            "category_id": to_object_id(form.category_id.data),
            "brand": form.brand.data.strip(),
            "color": form.color.data.strip(),
            "lost_date": datetime.combine(form.lost_date.data, time.min),
            "approx_time": form.approx_time.data.strip(),
            "last_seen_location_id": to_object_id(form.last_seen_location_id.data),
            "description": form.description.data.strip(),
            "private_verification_detail": form.private_verification_detail.data.strip()
        }
        if form.image.data:
            image_path, err = validate_and_save_image(form.image.data)
            if err:
                flash(err, "danger")
                return render_template("lost/edit.html", form=form, item=item)
            if image_path:
                update_data["image_path"] = image_path

        update_lost_item(item["_id"], update_data)
        emit_event("lost_item_updated", "lost_item", item["_id"], actor_id=current_user.id)
        # Re-run matching
        run_matching_for_lost_item(item["_id"])

        flash("Lost report updated successfully.", "success")
        return redirect(url_for("lost.detail", item_id=str(item["_id"])))

    return render_template("lost/edit.html", form=form, item=item)
