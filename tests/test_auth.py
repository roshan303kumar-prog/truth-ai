def test_registration_success(client):
    res = client.post(
        "/api/register",
        json={
            "username": "new_user",
            "email": "new_user@test.org",
            "password": "Password1234!",
            "full_name": "New Tester",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["username"] == "new_user"


def test_registration_duplicate_username(client):
    res = client.post(
        "/api/register",
        json={
            "username": "tester",  # already in fixture
            "email": "another@test.org",
            "password": "Password1234!",
        },
    )
    assert res.status_code == 409
    assert res.get_json()["success"] is False


def test_registration_short_password(client):
    res = client.post(
        "/api/register",
        json={
            "username": "short_pass",
            "email": "short@test.org",
            "password": "123",
        },
    )
    assert res.status_code == 400
    assert "Password must be at least 8 characters" in res.get_json()["error"]


def test_login_success(client):
    res = client.post(
        "/api/login",
        json={"login_id": "tester", "password": "SecurePassword123!"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["username"] == "tester"


def test_login_invalid_password(client):
    res = client.post(
        "/api/login",
        json={"login_id": "tester", "password": "WrongPassword"},
    )
    assert res.status_code == 401
    assert res.get_json()["success"] is False


def test_logout(auth_client):
    res = auth_client.post("/api/logout")
    assert res.status_code == 200
    assert res.get_json()["success"] is True
