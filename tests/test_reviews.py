import pytest
from database import db
from database.models import UserReview


def test_get_reviews_page(client):
    response = client.get("/reviews")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "User Reviews & Ratings" in html
    assert "Write a Review" in html


def test_api_get_reviews(client):
    response = client.get("/api/reviews")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "count" in data
    assert "average_rating" in data
    assert isinstance(data["reviews"], list)


def test_api_submit_review_success(client):
    payload = {
        "name": "Karan Singhania",
        "role": "Cybersecurity Student",
        "rating": 5,
        "title": "NEO Assistant helped verify my phishing link",
        "review_text": "Superb experience, instant detection of fake domains.",
    }
    response = client.post("/api/reviews", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["review"]["user_name"] == "Karan Singhania"
    assert data["review"]["rating"] == 5


def test_api_submit_review_validation(client):
    # Empty name
    response = client.post("/api/reviews", json={"name": "", "title": "Good", "review_text": "Very good tool"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False

    # Short review text
    response2 = client.post("/api/reviews", json={"name": "Raj", "title": "Good", "review_text": "hi"})
    assert response2.status_code == 400
    assert response2.get_json()["success"] is False
