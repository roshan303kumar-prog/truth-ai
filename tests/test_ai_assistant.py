import base64
import io
from PIL import Image
import pytest
from services.ai_assistant import AIAssistant


@pytest.fixture
def sample_screenshot_b64():
    """Generates a small in-memory test PNG as base64 data."""
    img = Image.new("RGB", (640, 480), color=(15, 23, 42))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def test_assistant_general_conversation():
    assistant = AIAssistant()
    res = assistant.chat(message="Hello")
    assert res["success"] is True
    assert "NEO" in res["reply"]
    assert res["screen_analyzed"] is False


def test_assistant_screen_query_without_screenshot():
    assistant = AIAssistant()
    res = assistant.chat(message="What is wrong on my screen?")
    assert res["success"] is True
    assert "Screen Not Detected" in res["reply"] or "Capture Page" in res["reply"]
    assert res["screen_analyzed"] is False


def test_assistant_with_screenshot_analysis(sample_screenshot_b64):
    assistant = AIAssistant()
    res = assistant.chat(
        message="Where should I click next?",
        screenshot_b64=sample_screenshot_b64,
        page_context={
            "url": "http://localhost:5000/news",
            "path": "/news",
            "title": "Verify News & Factual Claims — TRUTH AI",
        },
    )
    assert res["success"] is True
    assert res["screen_analyzed"] is True
    assert "News & Claims" in res["reply"] or "Verify News" in res["reply"]
    assert "Click" in res["reply"] or "click" in res["reply"]


def test_assistant_troubleshooting_rate_limit():
    assistant = AIAssistant()
    res = assistant.chat(message="Why am I getting a 429 rate limit error?")
    assert res["success"] is True
    assert "429" in res["reply"]
    assert "60 seconds" in res["reply"] or "Rate Limit" in res["reply"]


def test_api_assistant_chat_success(client):
    response = client.post(
        "/api/assistant/chat",
        json={
            "message": "How do you verify fake news?",
            "page_context": {"path": "/news", "title": "TRUTH AI News"},
            "history": [],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["reply"]) > 20
    assert "model_used" in data


def test_api_assistant_chat_with_screenshot(client, sample_screenshot_b64):
    response = client.post(
        "/api/assistant/chat",
        json={
            "message": "Check this screen for any problems.",
            "screenshot": sample_screenshot_b64,
            "page_context": {"path": "/image", "title": "Image Forensics"},
            "history": [],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["screen_analyzed"] is True


def test_api_assistant_chat_empty_payload(client):
    response = client.post("/api/assistant/chat", json={"message": ""})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_assistant_point_to_point_user_name():
    assistant = AIAssistant()
    res = assistant.chat(message="mera name kiya hai", page_context={})
    assert res["success"] is True
    assert "Aapne mujhe abhi apna naam nahi bataya" in res["reply"]
    assert "Thank you for your question" not in res["reply"]


def test_assistant_point_to_point_help_summary():
    assistant = AIAssistant()
    res = assistant.chat(message="what kind of help you will do")
    assert res["success"] is True
    assert "Website & Screen Help" in res["reply"]
    assert "Thank you for your question" not in res["reply"]

