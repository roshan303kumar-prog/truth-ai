import io
from pathlib import Path
from PIL import Image
from config import TestConfig
from services.image_verifier import ImageVerifier


def test_image_verification_with_generated_jpeg(tmp_path):
    img_path = tmp_path / "test_sample.jpg"
    # Create a real test image
    img = Image.new("RGB", (300, 300), color=(73, 109, 137))
    img.save(img_path, "JPEG", quality=95)

    verifier = ImageVerifier(TestConfig)
    res = verifier.verify_image(img_path, "test_sample.jpg")

    assert "verdict" in res
    assert res["confidence_score"] > 0
    assert "ela_analysis" in res
    assert "metadata_findings" in res
    assert "image_properties" in res
    assert res["image_properties"]["dimensions"] == "300 x 300"
    assert len(res["limitations"]) > 0


def test_ai_generation_assessment_metadata():
    verifier = ImageVerifier(TestConfig)
    dummy_img = Image.new("RGB", (1024, 1024))
    exif_findings = {
        "detected_ai_software": "Midjourney",
        "has_exif": True,
        "camera_make": "Unknown / Not recorded",
    }
    assessment = verifier.assess_ai_generation(dummy_img, exif_findings)
    assert assessment["ai_probability_score"] >= 70.0
    assert "High Probability" in assessment["assessment"]
