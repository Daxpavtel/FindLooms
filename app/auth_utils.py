from functools import wraps
from flask import abort
from flask_login import current_user, UserMixin
from app.repositories.users import find_by_id



class User(UserMixin):
    """Flask-Login compatible user wrapper."""
    def __init__(self, user_doc: dict):
        self.doc = user_doc
        self.id = str(user_doc["_id"])
        self.name = user_doc.get("name", "")
        self.email = user_doc.get("email", "")
        self.role = user_doc.get("role", "user")
        self.department = user_doc.get("department", "")
        self.phone = user_doc.get("phone", "")
        self.is_active_user = user_doc.get("is_active", True)

    @property
    def is_active(self) -> bool:
        return self.is_active_user

    @property
    def is_staff(self) -> bool:
        return self.role in ("staff", "admin")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def get_id(self) -> str:
        return self.id


def load_user_from_db(user_id: str):
    """User loader callback for Flask-Login."""
    doc = find_by_id(user_id)
    if doc and doc.get("is_active", True):
        return User(doc)
    return None


def role_required(*roles):
    """
    Decorator to restrict view access to specific user roles.
    Aborts with 403 Forbidden if current_user does not have one of the required roles.
    """
    def decorator(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return decorator


def staff_required(fn):
    """Requires 'staff' or 'admin' role."""
    return role_required("staff", "admin")(fn)


def admin_required(fn):
    """Requires 'admin' role."""
    return role_required("admin")(fn)
