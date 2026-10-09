from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.repositories.users import find_by_email


class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[
        DataRequired(message="Email is required."),
        Email(check_deliverability=False, message="Please enter a valid email address.")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required.")
    ])
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=80, message="Name must be between 2 and 80 characters.")
    ])
    email = StringField("Email Address", validators=[
        DataRequired(message="Email is required."),
        Email(check_deliverability=False, message="Please enter a valid email address."),
        Length(max=120)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters.")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo("password", message="Passwords must match.")
    ])
    department = StringField("Department / Organization / Hall", validators=[
        Length(max=100)
    ])
    phone = StringField("Contact Phone", validators=[
        Length(max=20)
    ])
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        existing = find_by_email(field.data)
        if existing:
            raise ValidationError("This email address is already registered.")


class ProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=80)
    ])
    department = StringField("Department / Organization", validators=[
        Length(max=100)
    ])
    phone = StringField("Contact Phone", validators=[
        Length(max=20)
    ])
    submit = SubmitField("Update Profile")
