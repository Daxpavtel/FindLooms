from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import auth_bp
from app.forms.auth_forms import LoginForm, RegisterForm, ProfileForm
from app.repositories.users import create_user, find_by_email, update_profile
from app.auth_utils import User
from app.services.events import emit_event


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user_id = create_user(
            name=form.name.data,
            email=form.email.data,
            password_hash=hashed_pw,
            role="user",
            department=form.department.data or "",
            phone=form.phone.data or ""
        )
        flash("Registration successful! You may now sign in.", "success")
        emit_event("user_registered", "user", user_id, payload={"email": form.email.data})
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user_doc = find_by_email(form.email.data)
        if user_doc and check_password_hash(user_doc.get("password_hash", ""), form.password.data):
            if not user_doc.get("is_active", True):
                flash("Your account is deactivated. Please contact an administrator.", "danger")
                return render_template("auth/login.html", form=form)

            user = User(user_doc)
            login_user(user)

            # Audit log staff and admin logins
            if user.is_staff or user.is_admin:
                emit_event("staff_login", "user", user.id, actor_id=user.id, payload={
                    "email": user.email,
                    "role": user.role
                })

            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(
        name=current_user.name,
        department=current_user.department,
        phone=current_user.phone
    )
    if form.validate_on_submit():
        success = update_profile(
            user_id=current_user.id,
            name=form.name.data,
            department=form.department.data,
            phone=form.phone.data
        )
        if success:
            flash("Profile updated successfully.", "success")
            emit_event("profile_updated", "user", current_user.id, actor_id=current_user.id)
            return redirect(url_for("auth.profile"))
        else:
            flash("Could not update profile.", "danger")

    return render_template("auth/profile.html", form=form)


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    """Role-based dashboard with KPI cards and recent activity."""
    from app.db import get_db
    db = get_db()
    
    # KPIs
    lost_count = db.lost_items.count_documents({"stage": {"$ne": "Archived"}})
    found_count = db.found_items.count_documents({"status": {"$ne": "Archived"}})
    pending_claims = db.claims.count_documents({"status": {"$in": ["New", "Under Review"]}})
    returned_count = db.found_items.count_documents({"status": "Returned"})

    # User specific KPIs
    my_lost = db.lost_items.count_documents({"reporter_id": current_user.doc["_id"]})
    my_found = db.found_items.count_documents({"finder_id": current_user.doc["_id"]})
    my_claims = db.claims.count_documents({"claimant_id": current_user.doc["_id"]})

    # Recent items
    from app.repositories.items import get_lost_items, get_found_items
    recent_lost, _ = get_lost_items(limit=5, is_staff=current_user.is_staff)
    recent_found, _ = get_found_items(limit=5, is_staff=current_user.is_staff)

    # Recent Audit activity for staff/admin
    recent_audit = []
    if current_user.is_staff:
        from app.repositories.audit import get_audit_logs
        recent_audit = get_audit_logs(limit=8)

    return render_template(
        "dashboard/index.html",
        kpis={
            "lost_count": lost_count,
            "found_count": found_count,
            "pending_claims": pending_claims,
            "returned_count": returned_count,
            "my_lost": my_lost,
            "my_found": my_found,
            "my_claims": my_claims
        },
        recent_lost=recent_lost,
        recent_found=recent_found,
        recent_audit=recent_audit
    )
