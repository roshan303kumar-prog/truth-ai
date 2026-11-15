import io
from PIL import Image


def test_api_verify_news_endpoint(client):
    res = client.post(
        "/api/verify-news",
        json={"claim": "Apollo 11 moon landing was staged on a Hollywood film set"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "report_id" in data
    assert data["verdict"] == "False or contradicted by reliable evidence"
    assert "explanation" in data


def test_api_verify_news_short_claim_error(client):
    res = client.post(
        "/api/verify-news",
        json={"claim": "hi"},
    )
    assert res.status_code == 400
    assert res.get_json()["success"] is False


def test_api_verify_image_endpoint(client):
    # Prepare dummy JPEG
    buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=(100, 150, 200))
    img.save(buf, "JPEG")
    buf.seek(0)

    res = client.post(
        "/api/verify-image",
        data={"image": (buf, "sample_test.jpg", "image/jpeg")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "report_id" in data
    assert "ela_image_filename" in data


def test_api_history_and_report_detail(client):
    # First verify a claim to populate history
    client.post(
        "/api/verify-news",
        json={"claim": "James Webb space telescope infrared discoveries"},
    )

    # Fetch history
    h_res = client.get("/api/history")
    assert h_res.status_code == 200
    h_data = h_res.get_json()
    assert h_data["success"] is True
    assert len(h_data["reports"]) > 0

    first_id = h_data["reports"][0]["id"]
    r_res = client.get(f"/api/report/{first_id}")
    assert r_res.status_code == 200
    r_data = r_res.get_json()
    assert r_data["success"] is True
    assert r_data["report"]["id"] == first_id


def test_api_dashboard_endpoint(auth_client):
    res = auth_client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "metrics" in data
    assert "type_breakdown" in data


def test_api_contact_endpoint(client):
    res = client.post(
        "/api/contact",
        json={
            "name": "Researcher John",
            "email": "john@university.edu",
            "subject": "Disinformation Inquiry",
            "message": "Interested in evaluating the forensic pipeline.",
        },
    )
    assert res.status_code == 200
    assert res.get_json()["success"] is True
