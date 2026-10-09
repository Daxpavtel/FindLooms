import sys
import os
import pytest
import mongomock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.config import TestConfig
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta


@pytest.fixture
def app():
    test_client = mongomock.MongoClient()

    flask_app = create_app(TestConfig)
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["TESTING"] = True
    flask_app.config["TEST_MONGO_CLIENT"] = test_client
    flask_app.config["TEST_DB_NAME"] = "lostfound_test_db"

    with flask_app.app_context():
        # Populate minimal seed
        from app.db import get_db
        db = get_db()
        db.users.insert_many([
            {
                "name": "Regular User",
                "email": "user@example.com",
                "password_hash": generate_password_hash("Password123!"),
                "role": "user",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "name": "Staff Member",
                "email": "staff@example.com",
                "password_hash": generate_password_hash("Password123!"),
                "role": "staff",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "name": "Admin Member",
                "email": "admin@example.com",
                "password_hash": generate_password_hash("Password123!"),
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        ])
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        from app.db import get_db
        return get_db()
