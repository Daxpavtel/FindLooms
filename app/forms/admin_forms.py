from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class CategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[
        DataRequired(message="Category name is required."),
        Length(min=2, max=50)
    ])
    icon = StringField("Icon Identifier", default="bi-tag", validators=[
        DataRequired(),
        Length(max=50)
    ], description="Bootstrap Icons class (e.g. bi-laptop, bi-wallet2, bi-file-earmark-text, bi-backpack, bi-key, bi-watch)")
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Category")


class LocationForm(FlaskForm):
    name = StringField("Location / Room Name", validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=80)
    ])
    building = StringField("Building / Complex", validators=[
        DataRequired(message="Building is required."),
        Length(min=2, max=80)
    ])
    zone = StringField("Campus Zone", validators=[
        DataRequired(message="Zone is required."),
        Length(min=2, max=60)
    ], description="e.g. North Campus, Academic Block, Student Center, Sports Complex")
    venue = StringField("Specific Venue / Landmark", validators=[
        Optional(),
        Length(max=80)
    ])
    latitude = FloatField("Latitude", default=0.0, validators=[
        Optional()
    ])
    longitude = FloatField("Longitude", default=0.0, validators=[
        Optional()
    ])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Location")


class SettingsForm(FlaskForm):
    retention_days = IntegerField("Retention Period (Days)", validators=[
        DataRequired(),
        NumberRange(min=1, max=365, message="Must be between 1 and 365 days.")
    ], description="Unclaimed found items older than this will be flagged as archive-eligible.")
    strong_match_threshold = IntegerField("Strong Match Threshold (%)", validators=[
        DataRequired(),
        NumberRange(min=20, max=100, message="Must be between 20 and 100%.")
    ], description="Match engine score to auto-promote items to Possible Match stage.")
    duplicate_window_days = IntegerField("Duplicate Warning Window (Days)", validators=[
        DataRequired(),
        NumberRange(min=1, max=30, message="Must be between 1 and 30 days.")
    ], description="Window before/after report date to scan for potential duplicate items.")
    submit = SubmitField("Save System Settings")


class UserRoleForm(FlaskForm):
    role = SelectField("Role", choices=[
        ("user", "User (Standard reporting and claims)"),
        ("staff", "Staff (Custody, review claims, kanban, matches)"),
        ("admin", "Administrator (Full access to all settings and records)")
    ], validators=[DataRequired()])
    is_active = BooleanField("Account Active", default=True)
    submit = SubmitField("Update User Permissions")
