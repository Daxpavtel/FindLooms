from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from . import claims_bp
from app.forms.claim_forms import ClaimForm, ReviewClaimForm, HandoverForm
from app.repositories.items import get_found_item_by_id
from app.repositories.claims import (
    create_claim,
    get_claim_by_id,
    get_user_claims,
    get_all_claims
)
from app.repositories.handovers import create_or_update_handover, get_handover_by_claim_id
from app.services.workflow import transition_claim_status
from app.services.events import emit_event
from app.auth_utils import staff_required



@claims_bp.route("/new/<found_id>", methods=["GET", "POST"])
@login_required
def create(found_id: str):
    found_item = get_found_item_by_id(found_id, is_staff=False)
    if not found_item:
        abort(404)

    if found_item.get("status") in ["Returned", "Archived"]:
        flash("This item is no longer available for claims.", "warning")
        return redirect(url_for("found.detail", item_id=found_id))

    lost_id = request.args.get("lost_id")
    claim_type = "Suggested" if lost_id else "Direct"

    form = ClaimForm()
    if form.validate_on_submit():
        doc, err = create_claim(
            claimant_id=current_user.id,
            found_id=found_item["_id"],
            proof_answer=form.proof_answer.data,
            lost_id=lost_id,
            claim_type=claim_type
        )
        if err:
            flash(err, "danger")
            return render_template("claims/create.html", form=form, found_item=found_item)

        emit_event("claim_filed", "claim", doc["_id"], actor_id=current_user.id, payload={
            "reference_no": doc["reference_no"],
            "found_ref": found_item.get("reference_no"),
            "claim_type": claim_type
        })

        flash(f"Claim {doc['reference_no']} submitted successfully! Staff will review your proof.", "success")
        return redirect(url_for("claims.my_claims"))

    return render_template("claims/create.html", form=form, found_item=found_item, claim_type=claim_type)


@claims_bp.route("/my")
@login_required
def my_claims():
    claims = get_user_claims(current_user.id)
    return render_template("claims/my_claims.html", claims=claims)


@claims_bp.route("/<claim_id>")
@login_required
def detail(claim_id: str):
    is_staff = current_user.is_staff
    claim = get_claim_by_id(claim_id, is_staff=is_staff)
    if not claim:
        abort(404)

    is_claimant = str(claim.get("claimant_id")) == current_user.id
    if not is_staff and not is_claimant:
        abort(403)

    return render_template("claims/detail.html", claim=claim, is_staff=is_staff)


@claims_bp.route("/<claim_id>/review", methods=["GET", "POST"])
@login_required
@staff_required
def review(claim_id: str):
    claim = get_claim_by_id(claim_id, is_staff=True)
    if not claim:
        abort(404)

    form = ReviewClaimForm()
    if form.validate_on_submit():
        decision = form.action.data
        notes = form.reviewer_notes.data
        ok, msg = transition_claim_status(
            claim_id=claim["_id"],
            new_status=decision,
            reviewer_id=current_user.id,
            reviewer_notes=notes
        )
        if ok:
            flash(f"Claim marked as {decision}. {msg}", "success")
            return redirect(url_for("claims.detail", claim_id=str(claim["_id"])))
        else:
            flash(f"Error: {msg}", "danger")

    return render_template("claims/review.html", claim=claim, form=form)


@claims_bp.route("/<claim_id>/handover", methods=["GET", "POST"])
@login_required
@staff_required
def handover(claim_id: str):
    claim = get_claim_by_id(claim_id, is_staff=True)
    if not claim:
        abort(404)

    if claim.get("status") not in ["Approved", "Returned"]:
        flash("Handover can only be scheduled or completed for Approved claims.", "warning")
        return redirect(url_for("claims.detail", claim_id=claim_id))

    existing_handover = get_handover_by_claim_id(claim["_id"])
    
    initial_receiver = (
        existing_handover.get("receiver_name") if existing_handover 
        else (claim.get("claimant", {}).get("name", "") if claim.get("claimant") else "")
    )
    
    form = HandoverForm(
        receiver_name=initial_receiver,
        acknowledgement_note=existing_handover.get("acknowledgement_note", "") if existing_handover else ""
    )

    if form.validate_on_submit():
        h_date = form.handover_date.data
        ret_dt = datetime.combine(h_date, datetime.now().time())

        h_rec = create_or_update_handover(
            claim_id=claim["_id"],
            receiver_name=form.receiver_name.data,
            reviewer_id=current_user.id,
            scheduled_datetime=ret_dt,
            return_datetime=ret_dt,
            acknowledgement_note=form.acknowledgement_note.data
        )

        # Transition claim to Returned
        ok, msg = transition_claim_status(
            claim_id=claim["_id"],
            new_status="Returned",
            reviewer_id=current_user.id,
            reviewer_notes=f"Physical handover completed to {form.receiver_name.data}"
        )

        emit_event("handover_completed", "handover", h_rec.get("_id"), actor_id=current_user.id, payload={
            "claim_ref": claim.get("reference_no"),
            "receiver": form.receiver_name.data
        })

        flash(f"Handover recorded! Claim and items successfully marked as Returned.", "success")
        return redirect(url_for("claims.detail", claim_id=str(claim["_id"])))

    return render_template("claims/handover.html", claim=claim, form=form, existing_handover=existing_handover)


@claims_bp.route("")
@claims_bp.route("/")
@claims_bp.route("/queue")
@login_required
@staff_required
def queue():
    status = request.args.get("status", "New")
    claims, total = get_all_claims(status=status if status != "All" else None)
    return render_template("claims/queue.html", claims=claims, total=total, current_status=status)
