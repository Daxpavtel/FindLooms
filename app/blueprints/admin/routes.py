from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from . import admin_bp
from app.auth_utils import admin_required, staff_required
from app.forms.admin_forms import CategoryForm, LocationForm, SettingsForm
from app.repositories.categories import (
    get_all_categories,
    create_category,
    get_category_by_id,
    update_category
)
from app.repositories.locations import (
    get_all_locations,
    create_location,
    get_location_by_id,
    update_location
)
from app.repositories.settings import get_all_settings, update_setting, get_setting
from app.repositories.users import get_all_users, find_by_id, update_user_role, update_user_status
from app.repositories.audit import get_audit_logs, count_audit_logs
from app.services.archive import get_archive_eligible_items, execute_disposal_action, run_archive_check
from app.services.events import emit_event



# ==========================================
# CATEGORIES MANAGEMENT
# ==========================================

@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        create_category(
            name=form.name.data,
            icon=form.icon.data,
            is_active=form.is_active.data
        )
        flash(f"Category '{form.name.data}' created successfully.", "success")
        emit_event("category_created", "category", actor_id=current_user.id, payload={"name": form.name.data})
        return redirect(url_for("admin.categories"))

    cats = get_all_categories()
    return render_template("admin/categories.html", categories=cats, form=form)


@admin_bp.route("/categories/<cat_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_category(cat_id: str):
    cat = get_category_by_id(cat_id)
    if not cat:
        abort(404)

    form = CategoryForm(
        name=cat.get("name"),
        icon=cat.get("icon"),
        is_active=cat.get("is_active", True)
    )

    if form.validate_on_submit():
        update_category(
            cat_id=cat["_id"],
            name=form.name.data,
            icon=form.icon.data,
            is_active=form.is_active.data
        )
        flash(f"Category '{form.name.data}' updated.", "success")
        emit_event("category_updated", "category", cat["_id"], actor_id=current_user.id)
        return redirect(url_for("admin.categories"))

    return render_template("admin/edit_category.html", category=cat, form=form)


# ==========================================
# LOCATIONS MANAGEMENT
# ==========================================

@admin_bp.route("/locations", methods=["GET", "POST"])
@login_required
@admin_required
def locations():
    form = LocationForm()
    if form.validate_on_submit():
        create_location(
            name=form.name.data,
            building=form.building.data,
            zone=form.zone.data,
            venue=form.venue.data or "",
            latitude=form.latitude.data or 0.0,
            longitude=form.longitude.data or 0.0,
            is_active=form.is_active.data
        )
        flash(f"Location '{form.name.data}' added successfully.", "success")
        emit_event("location_created", "location", actor_id=current_user.id, payload={"name": form.name.data})
        return redirect(url_for("admin.locations"))

    locs = get_all_locations()
    return render_template("admin/locations.html", locations=locs, form=form)


@admin_bp.route("/locations/<loc_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_location(loc_id: str):
    loc = get_location_by_id(loc_id)
    if not loc:
        abort(404)

    form = LocationForm(
        name=loc.get("name"),
        building=loc.get("building"),
        zone=loc.get("zone"),
        venue=loc.get("venue"),
        latitude=loc.get("latitude", 0.0),
        longitude=loc.get("longitude", 0.0),
        is_active=loc.get("is_active", True)
    )

    if form.validate_on_submit():
        update_location(
            loc_id=loc["_id"],
            name=form.name.data,
            building=form.building.data,
            zone=form.zone.data,
            venue=form.venue.data or "",
            latitude=form.latitude.data or 0.0,
            longitude=form.longitude.data or 0.0,
            is_active=form.is_active.data
        )
        flash(f"Location '{form.name.data}' updated.", "success")
        emit_event("location_updated", "location", loc["_id"], actor_id=current_user.id)
        return redirect(url_for("admin.locations"))

    return render_template("admin/edit_location.html", location=loc, form=form)


# ==========================================
# SYSTEM SETTINGS
# ==========================================

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    all_s = get_all_settings()
    form = SettingsForm(
        retention_days=all_s.get("retention_days", 30),
        strong_match_threshold=all_s.get("strong_match_threshold", 60),
        duplicate_window_days=all_s.get("duplicate_window_days", 2)
    )

    if form.validate_on_submit():
        update_setting("retention_days", form.retention_days.data)
        update_setting("strong_match_threshold", form.strong_match_threshold.data)
        update_setting("duplicate_window_days", form.duplicate_window_days.data)
        flash("System settings saved successfully.", "success")
        emit_event("settings_updated", "settings", actor_id=current_user.id, payload={
            "retention_days": form.retention_days.data,
            "strong_match_threshold": form.strong_match_threshold.data,
            "duplicate_window_days": form.duplicate_window_days.data
        })
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", form=form)


# ==========================================
# USER ROLES & PERMISSIONS
# ==========================================

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    users_list = get_all_users(limit=100)
    return render_template("admin/users.html", users=users_list)


@admin_bp.route("/users/<user_id>/role", methods=["POST"])
@login_required
@admin_required
def update_role(user_id: str):
    target_user = find_by_id(user_id)
    if not target_user:
        abort(404)

    new_role = request.form.get("role")
    if new_role not in ["user", "staff", "admin"]:
        flash("Invalid role specified.", "danger")
        return redirect(url_for("admin.users"))

    # Prevent admin from accidentally demoting themselves if only 1 admin
    if str(target_user["_id"]) == current_user.id and new_role != "admin":
        flash("You cannot demote your own account from administrator.", "danger")
        return redirect(url_for("admin.users"))

    update_user_role(target_user["_id"], new_role)
    emit_event("role_changed", "user", target_user["_id"], actor_id=current_user.id, payload={
        "old_role": target_user.get("role"),
        "new_role": new_role
    })

    flash(f"Role for {target_user.get('name')} updated to '{new_role}'.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<user_id>/toggle-status", methods=["POST"])
@login_required
@admin_required
def toggle_user_status(user_id: str):
    target_user = find_by_id(user_id)
    if not target_user:
        abort(404)

    if str(target_user["_id"]) == current_user.id:
        flash("You cannot deactivate your own administrator account.", "danger")
        return redirect(url_for("admin.users"))

    new_status = not target_user.get("is_active", True)
    update_user_status(target_user["_id"], new_status)
    emit_event("user_status_toggled", "user", target_user["_id"], actor_id=current_user.id, payload={
        "is_active": new_status
    })

    flash(f"User account {'activated' if new_status else 'deactivated'}.", "info")
    return redirect(url_for("admin.users"))


# ==========================================
# AUDIT LOG VIEWER
# ==========================================

@admin_bp.route("/audit")
@login_required
@staff_required
def audit():
    entity_filter = request.args.get("entity", "").strip()
    action_filter = request.args.get("action", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 25
    skip = (page - 1) * per_page

    logs = get_audit_logs(
        entity_type=entity_filter or None,
        action=action_filter or None,
        limit=per_page,
        skip=skip
    )
    total = count_audit_logs(
        entity_type=entity_filter or None,
        action=action_filter or None
    )
    total_pages = (total + per_page - 1) // per_page if per_page else 1

    return render_template(
        "admin/audit.html",
        logs=logs,
        page=page,
        total_pages=total_pages,
        total=total,
        current_entity=entity_filter,
        current_action=action_filter
    )


# ==========================================
# RETENTION & ARCHIVE DISPOSAL PANEL
# ==========================================

@admin_bp.route("/archive")
@login_required
@admin_required
def archive_panel():
    eligible_items = get_archive_eligible_items()
    retention_days = get_setting("retention_days", 30)
    return render_template(
        "admin/archive.html",
        items=eligible_items,
        retention_days=retention_days
    )


@admin_bp.route("/archive/run-check", methods=["POST"])
@login_required
@admin_required
def trigger_archive_check():
    res = run_archive_check()
    flash(f"Archive check completed: {res['flagged_count']} items flagged as eligible for disposal (older than {res['retention_days']} days).", "info")
    return redirect(url_for("admin.archive_panel"))


@admin_bp.route("/archive/action", methods=["POST"])
@login_required
@admin_required
def disposal_action():
    found_id = request.form.get("found_id")
    action_type = request.form.get("action_type")  # Archive, Donate, Dispose
    notes = request.form.get("notes", "")

    if not found_id or action_type not in ["Archive", "Donate", "Dispose"]:
        flash("Invalid disposal parameters.", "danger")
        return redirect(url_for("admin.archive_panel"))

    success = execute_disposal_action(
        found_id=found_id,
        action_type=action_type,
        actor_id=current_user.id,
        notes=notes
    )

    if success:
        flash(f"Item action '{action_type}' recorded and item moved to Archived stage.", "success")
    else:
        flash("Could not perform disposal action.", "danger")

    return redirect(url_for("admin.archive_panel"))
