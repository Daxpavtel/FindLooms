from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class LostItemForm(FlaskForm):
    name = StringField("Item Title / Name", validators=[
        DataRequired(message="Item name is required."),
        Length(min=3, max=100, message="Name must be between 3 and 100 characters.")
    ])
    category_id = SelectField("Category", validators=[
        DataRequired(message="Please select a category.")
    ])
    brand = StringField("Brand / Manufacturer", validators=[
        Optional(),
        Length(max=60)
    ])
    color = StringField("Primary Color", validators=[
        DataRequired(message="Color is required."),
        Length(max=40)
    ])
    lost_date = DateField("Date Lost", default=date.today, validators=[
        DataRequired(message="Date lost is required.")
    ])
    approx_time = StringField("Approximate Time", validators=[
        Optional(),
        Length(max=50)
    ], description="e.g., Around 11:30 AM, During Lunch, Late evening")
    last_seen_location_id = SelectField("Last Seen Location", validators=[
        DataRequired(message="Please select where you last saw the item.")
    ])
    description = TextAreaField("Public Description", validators=[
        DataRequired(message="Please describe the item."),
        Length(min=10, max=1000)
    ], description="Public description of the item. Do not include confidential serial numbers or passcodes.")
    private_verification_detail = TextAreaField("Secret Verification Clue (Hidden)", validators=[
        DataRequired(message="Secret verification detail is required to securely prove your ownership."),
        Length(min=5, max=500)
    ], description="Never revealed publicly. Staff will check this secret clue when verifying claims (e.g., unique sticker, scratch on back, lockscreen image, contents).")
    image = FileField("Upload Photo (Optional)", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only (jpg, png, webp) - Max 5MB.")
    ])
    submit = SubmitField("Submit Lost Report")


class FoundItemForm(FlaskForm):
    name = StringField("Item Title / Name", validators=[
        DataRequired(message="Item name is required."),
        Length(min=3, max=100)
    ])
    category_id = SelectField("Category", validators=[
        DataRequired(message="Please select a category.")
    ])
    brand = StringField("Brand / Manufacturer", validators=[
        Optional(),
        Length(max=60)
    ])
    color = StringField("Primary Color", validators=[
        DataRequired(message="Color is required."),
        Length(max=40)
    ])
    found_date = DateField("Date Found", default=date.today, validators=[
        DataRequired(message="Date found is required.")
    ])
    found_location_id = SelectField("Found Location", validators=[
        DataRequired(message="Please select where the item was found.")
    ])
    custody_location = StringField("Custody Storage Location", validators=[
        DataRequired(message="Specify where the item is physically stored for safekeeping."),
        Length(max=100)
    ], description="e.g., Security Desk Cabinet A, Library Front Counter Box 2")
    description = TextAreaField("Public Description (Safe)", validators=[
        DataRequired(message="Public description is required."),
        Length(min=10, max=1000)
    ], description="Safe description visible to community. Do NOT include secret identifying markings or serials.")
    private_details = TextAreaField("Confidential Details (Hidden Specifics)", validators=[
        DataRequired(message="Confidential specifics are required for ownership verification."),
        Length(min=5, max=500)
    ], description="HIDDEN from normal users! Staff will use this to verify claimant answers (e.g. serial numbers, specific stickers, wallpaper description, contents inside).")
    image = FileField("Upload Photo (Optional)", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only (jpg, png, webp) - Max 5MB.")
    ])
    submit = SubmitField("Register Found Item")
