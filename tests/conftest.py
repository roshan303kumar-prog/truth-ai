import pytest
from app import create_app
from config import TestConfig
from database import db
from database.models import User, UserSettings


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Create a test user
        test_user = User(username="tester", email="tester@example.com", full_name="Test User")
        test_user.set_password("SecurePassword123!")
        db.session.add(test_user)
        db.session.flush()

        settings = UserSettings(user_id=test_user.id)
        db.session.add(settings)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Client logged in as tester."""
    client.post(
        "/api/login",
        json={"login_id": "tester", "password": "SecurePassword123!"},
    )
    return client
