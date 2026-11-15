import pytest
from services.content_verifier import ContentLinkVerifier, VERIFIED_NEWS_SOURCES, KNOWN_SATIRE_OR_HOAX_SITES


@pytest.fixture
def content_verifier(app):
    return ContentLinkVerifier(app.config)


def test_is_url(content_verifier):
    assert content_verifier.is_url("https://www.ndtv.com/india-news/story-1234") is True
    assert content_verifier.is_url("http://bbc.com/news") is True
    assert content_verifier.is_url("www.thehindu.com") is True
    assert content_verifier.is_url("just a normal claim text without any url") is False
    assert content_verifier.is_url("") is False


def test_is_video_url(content_verifier):
    assert content_verifier.is_video_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert content_verifier.is_video_url("https://youtu.be/dQw4w9WgXcQ") is True
    assert content_verifier.is_video_url("https://vimeo.com/123456") is True
    assert content_verifier.is_video_url("https://www.thehindu.com/news/national") is False


def test_youtube_video_id_extraction(content_verifier):
    res1 = content_verifier.extract_youtube_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert res1["video_id"] == "dQw4w9WgXcQ"
    assert res1["type"] == "video"

    res2 = content_verifier.extract_youtube_info("https://youtu.be/abcXYZ123")
    assert res2["video_id"] == "abcXYZ123"


def test_verified_news_source_recognition(content_verifier):
    res = content_verifier.verify_content_link("https://www.thehindu.com/news/national/isro-moon-mission-chandrayaan-success")
    assert res["success"] is True
    assert res["is_video"] is False
    assert "The Hindu" in res["publisher"]
    assert res["verdict_class"] == "success"
    assert res["authenticity_score"] >= 80.0


def test_satire_source_detection(content_verifier):
    res = content_verifier.verify_content_link("https://www.theonion.com/scientists-discover-new-planet-made-of-cheese")
    assert res["success"] is True
    assert res["verdict_class"] == "danger"
    assert "Satire" in res["verdict"] or "Fake" in res["verdict"]
    assert res["authenticity_score"] <= 25.0


def test_api_verify_content_link(client):
    response = client.post("/api/verify-content-link", json={
        "url": "https://www.ndtv.com/india-news/chandrayaan-3-lands-on-moon"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "verdict" in data
    assert "authenticity_score" in data
    assert "key_findings" in data
    assert "report_id" in data


def test_api_verify_news_with_url_autodetect(client):
    # Test pasting a URL into the standard news verification endpoint
    response = client.post("/api/verify-news", json={
        "claim": "https://www.thehindu.com/news/national/chandrayaan-3-moon-landing"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "verdict" in data
