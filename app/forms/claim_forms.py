from datetime import date
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ClaimForm(FlaskForm):
    proof_answer = TextAreaField("Proof of Ownership / Verification Details", validators=[
        DataRequired(message="Please provide details only the rightful owner would know."),
        Length(min=5, max=1000, message="Proof answer must be between 5 and 1000 characters.")
    ], description="Explain specific hidden details (e.g. engraving, sticker, scratch, exact contents, receipts, or wallpaper).")
    submit = SubmitField("Submit Claim")


class ReviewClaimForm(FlaskForm):
    action = SelectField("Decision", choices=[
        ("Approved", "Approve Claim (Valid Ownership Proven)"),
        ("Rejected", "Reject Claim (Insufficient or Incorrect Proof)"),
        ("Under Review", "Request Further In-Person Verification")
    ], validators=[DataRequired()])
    reviewer_notes = TextAreaField("Reviewer Assessment & Notes", validators=[
        DataRequired(message="Please record reasoning for approval or rejection."),
        Length(min=3, max=1000)
    ])
    submit = SubmitField("Record Verification Decision")


class HandoverForm(FlaskForm):
    receiver_name = StringField("Receiver Full Name", validators=[
        DataRequired(message="Full name of the person collecting the item is required."),
        Length(min=2, max=100)
    ])
    handover_date = DateField("Handover Date", default=date.today, validators=[
        DataRequired()
    ])
    scheduled_time = StringField("Scheduled Pickup Time / Slot", validators=[
        Optional(),
        Length(max=50)
    ], description="e.g. Tomorrow 3:00 PM at Main Security Desk")
    acknowledgement_note = TextAreaField("Handover / Receipt Notes", validators=[
        Optional(),
        Length(max=500)
    ], description="e.g. Verified with student ID card #10492; physical item handed over in good condition.")
    submit = SubmitField("Complete Handover & Mark Returned")
