from datetime import datetime, time
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user

from . import found_bp
from app.forms.item_forms import FoundItemForm
from app.repositories.categories import get_all_categories
from app.repositories.locations import get_all_locations
from app.repositories.items import (
    create_found_item,
    get_found_item_by_id,
    get_found_items,
    update_found_item,
    find_potential_duplicates
)
from app.repositories.claims import get_claims_for_found_item, count_open_claims_for_found
from app.repositories.settings import get_setting
from app.services.upload import validate_and_save_image
from app.services.matching import run_matching_for_found_item
from app.services.events import emit_event
from app.db import to_object_id
from app.auth_utils import staff_required


def _populate_form_choices(form: FoundItemForm):
    cats = get_all_categories(active_only=True)
    locs = get_all_locations(active_only=True)
    form.category_id.choices = [(str(c["_id"]), c["name"]) for c in cats]
    form.found_location_id.choices = [(str(l["_id"]), f"{l['name']} ({l['building']})") for l in locs]


@found_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = FoundItemForm()
    _populate_form_choices(form)

    potential_duplicates = []
    if request.method == "POST":
        cat_id = form.category_id.data
        loc_id = form.found_location_id.data
        found_d = form.found_date.data
        window_days = int(get_setting("duplicate_window_days", 2))
        
        if cat_id and loc_id and found_d:
            dt = datetime.combine(found_d, time.min)
            potential_duplicates = find_potential_duplicates(
                category_id=cat_id,
                location_id=loc_id,
                target_date=dt,
                is_lost=False,
                window_days=window_days
            )

        proceed_anyway = request.form.get("proceed_anyway") == "true"
        if potential_duplicates and not proceed_anyway:
            flash("Warning: A similar found item was recently registered in this location. Please check if this item has already been turned in.", "warning")
            return render_template(
                "found/create.html",
                form=form,
                potential_duplicates=potential_duplicates
            )

    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            image_path, err = validate_and_save_image(form.image.data)
            if err:
                flash(err, "danger")
                return render_template("found/create.html", form=form, potential_duplicates=potential_duplicates)

        dt = datetime.combine(form.found_date.data, time.min)
        doc = create_found_item(
            finder_id=current_user.id,
            name=form.name.data,
            category_id=form.category_id.data,
            found_datetime=dt,
            found_location_id=form.found_location_id.data,
            description=form.description.data,
            brand=form.brand.data or "",
            color=form.color.data,
            private_details=form.private_details.data,
            custody_location=form.custody_location.data,
            custodian_id=current_user.id if current_user.is_staff else None,
            image_path=image_path
        )

        emit_event("found_item_created", "found_item", doc["_id"], actor_id=current_user.id, payload={
            "reference_no": doc["reference_no"],
            "name": doc["name"]
        })

        # Run Smart Match Engine
        run_matching_for_found_item(doc["_id"])

        flash(f"Found item {doc['reference_no']} registered successfully!", "success")
        return redirect(url_for("found.detail", item_id=str(doc["_id"])))

    return render_template("found/create.html", form=form, potential_duplicates=potential_duplicates)


@found_bp.route("")
def list_items():
    page = int(request.args.get("page", 1))
    per_page = current_app.config.get("ITEMS_PER_PAGE", 10)
    skip = (page - 1) * per_page

    cat_filter = request.args.get("category")
    status_filter = request.args.get("status")
    q = request.args.get("q", "").strip()

    query = {}
    if cat_filter and to_object_id(cat_filter):
        query["category_id"] = to_object_id(cat_filter)
    if status_filter:
        query["status"] = status_filter
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"reference_no": {"$regex": q, "$options": "i"}}
        ]

    is_staff = current_user.is_authenticated and current_user.is_staff
    items, total = get_found_items(
        filter_query=query,
        limit=per_page,
        skip=skip,
        is_staff=is_staff
    )

    total_pages = (total + per_page - 1) // per_page if per_page else 1
    categories = get_all_categories()

    return render_template(
        "found/list.html",
        items=items,
        page=page,
        total_pages=total_pages,
        total=total,
        categories=categories,
        current_category=cat_filter,
        current_status=status_filter,
        search_query=q
    )


@found_bp.route("/<item_id>")
def detail(item_id: str):
    is_staff = current_user.is_authenticated and current_user.is_staff
    item = get_found_item_by_id(item_id, is_staff=is_staff)
    if not item:
        abort(404)

    open_claims_count = 0
    if is_staff:
        open_claims_count = count_open_claims_for_found(item["_id"])

    return render_template(
        "found/detail.html",
        item=item,
        is_staff=is_staff,
        open_claims_count=open_claims_count
    )


@found_bp.route("/<item_id>/claims")
@login_required
@staff_required
def claims_list(item_id: str):
    item = get_found_item_by_id(item_id, is_staff=True)
    if not item:
        abort(404)

    claims = get_claims_for_found_item(item["_id"], is_staff=True)
    return render_template(
        "found/claims_list.html",
        item=item,
        claims=claims
    )


@found_bp.route("/<item_id>/edit", methods=["GET", "POST"])
@login_required
def edit(item_id: str):
    item = get_found_item_by_id(item_id, is_staff=True)
    if not item:
        abort(404)

    is_finder = str(item.get("finder_id")) == current_user.id
    if not current_user.is_staff and not is_finder:
        abort(403)

    form = FoundItemForm(
        name=item.get("name"),
        category_id=str(item.get("category_id")),
        brand=item.get("brand"),
        color=item.get("color"),
        found_date=item.get("found_datetime").date() if item.get("found_datetime") else None,
        found_location_id=str(item.get("found_location_id")),
        custody_location=item.get("custody_location"),
        description=item.get("description"),
        private_details=item.get("private_details", "")
    )
    _populate_form_choices(form)

    if form.validate_on_submit():
        update_data = {
            "name": form.name.data.strip(),
            "category_id": to_object_id(form.category_id.data),
            "brand": form.brand.data.strip(),
            "color": form.color.data.strip(),
            "found_datetime": datetime.combine(form.found_date.data, time.min),
            "found_location_id": to_object_id(form.found_location_id.data),
            "custody_location": form.custody_location.data.strip(),
            "description": form.description.data.strip(),
            "private_details": form.private_details.data.strip()
        }
        if form.image.data:
            image_path, err = validate_and_save_image(form.image.data)
            if err:
                flash(err, "danger")
                return render_template("found/edit.html", form=form, item=item)
            if image_path:
                update_data["image_path"] = image_path

        update_found_item(item["_id"], update_data)
        emit_event("found_item_updated", "found_item", item["_id"], actor_id=current_user.id)
        run_matching_for_found_item(item["_id"])

        flash("Found item details updated successfully.", "success")
        return redirect(url_for("found.detail", item_id=str(item["_id"])))

    return render_template("found/edit.html", form=form, item=item)
