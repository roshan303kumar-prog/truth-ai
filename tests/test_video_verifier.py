from config import TestConfig
from services.video_verifier import VideoVerifier


def test_video_verifier_temporal_analysis():
    verifier = VideoVerifier(TestConfig)
    dummy_frames = [
        {"timestamp": "0.0s", "sharpness_score": 150.0, "mean_brightness": 120.0},
        {"timestamp": "1.0s", "sharpness_score": 152.0, "mean_brightness": 121.0},
        {"timestamp": "2.0s", "sharpness_score": 149.0, "mean_brightness": 119.0},
    ]
    res = verifier.analyze_temporal_consistency(dummy_frames)
    assert res["lighting_stability"] == "Stable"
    assert res["anomaly_count"] == 0


def test_video_verifier_anomaly_detection():
    verifier = VideoVerifier(TestConfig)
    # Consecutive frames with sudden sharp lighting jump
    dummy_frames = [
        {"timestamp": "0.0s", "sharpness_score": 150.0, "mean_brightness": 50.0},
        {"timestamp": "1.0s", "sharpness_score": 300.0, "mean_brightness": 180.0},
    ]
    res = verifier.analyze_temporal_consistency(dummy_frames)
    assert res["anomaly_count"] > 0


def test_video_modality_classification_authentic():
    verifier = VideoVerifier(TestConfig)
    kf_data = {
        "frames": [{"timestamp": f"{i}s"} for i in range(12)],
        "fps": 29.99,
        "duration_seconds": 8.5,
        "resolution": "480 x 864",
        "avg_saturation": 60.5,
        "avg_channel_std": 5.2,
        "avg_correlation": 0.94,
        "correlations": [0.95] * 11,
    }
    temporal_analysis = {"anomaly_count": 0, "anomalies": []}
    res = verifier.classify_video_modality(kf_data, temporal_analysis, "real_event.mp4")
    assert res["verdict"] == "Supported by available evidence"
    assert "Authentic" in res["detected_type"]
    assert res["confidence_score"] >= 85.0


def test_video_modality_classification_filter_mask():
    verifier = VideoVerifier(TestConfig)
    kf_data = {
        "frames": [{"timestamp": f"{i}s"} for i in range(12)],
        "fps": 24.0,
        "duration_seconds": 6.0,
        "resolution": "416 x 720",
        "avg_saturation": 0.04,
        "avg_channel_std": 0.0,
        "avg_correlation": 1.0,
        "correlations": [1.0] * 11,
    }
    temporal_analysis = {"anomaly_count": 0, "anomalies": []}
    res = verifier.classify_video_modality(kf_data, temporal_analysis, "spider_mask.mp4")
    assert res["verdict"] == "False or contradicted by reliable evidence"
    assert "Manipulated" in res["detected_type"]
    assert len(res["manipulation_indicators"]) > 0


def test_video_modality_classification_ai_generated():
    verifier = VideoVerifier(TestConfig)
    kf_data = {
        "frames": [{"timestamp": f"{i}s"} for i in range(6)],
        "fps": 24.0,
        "duration_seconds": 2.5,
        "resolution": "1024 x 1024",
        "avg_saturation": 40.0,
        "avg_channel_std": 3.0,
        "avg_correlation": 0.75,
        "correlations": [0.75] * 5,
    }
    temporal_analysis = {"anomaly_count": 0, "anomalies": []}
    res = verifier.classify_video_modality(kf_data, temporal_analysis, "sora_gen.mp4")
    assert res["verdict"] == "False or contradicted by reliable evidence"
    assert "Synthetic" in res["detected_type"]
