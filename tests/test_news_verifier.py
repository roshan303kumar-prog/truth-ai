from config import TestConfig
from services.news_verifier import NewsVerifier


def test_sensationalism_detection():
    verifier = NewsVerifier(TestConfig)
    sensational = "SHOCKING SECRET THEY DON'T WANT YOU TO KNOW!! MUST SEE!!!"
    res = verifier.analyze_linguistics(sensational)
    assert res["sensationalism_detected"] is True
    assert res["sentiment_tone"] == "Sensational / Urgent"

    normal = "NASA planetary scientists published findings on Martian mineral composition."
    res_normal = verifier.analyze_linguistics(normal)
    assert res_normal["sensationalism_detected"] is False
    assert res_normal["sentiment_tone"] == "Standard / Informative"


def test_verify_known_debunked_claim():
    verifier = NewsVerifier(TestConfig)
    res = verifier.verify_claim("COVID-19 vaccines contain tracking 5G microchips")
    assert res["verdict"] == "False or contradicted by reliable evidence"
    assert res["confidence_score"] >= 75.0
    assert len(res["contradicting_evidence"]) > 0
    assert "explanation" in res
    assert len(res["limitations"]) > 0


def test_verify_supported_claim():
    verifier = NewsVerifier(TestConfig)
    res = verifier.verify_claim("James Webb Space Telescope discovered ancient distant galaxies")
    assert res["verdict"] == "Supported by available evidence"
    assert res["confidence_score"] >= 70.0
    assert len(res["supporting_evidence"]) > 0


def test_verify_entity_mismatch_false_claim():
    verifier = NewsVerifier(TestConfig)
    # Testing false attribution where James Webb is replaced by "alon mask" or "elon musk"
    res1 = verifier.verify_claim("NASA alon mask Space Telescope discovered ancient distant galaxies")
    assert res1["verdict"] == "False or contradicted by reliable evidence"
    assert len(res1["contradicting_evidence"]) > 0
    assert len(res1["supporting_evidence"]) == 0

    res2 = verifier.verify_claim("Elon Musk Space Telescope discovered ancient distant galaxies")
    assert res2["verdict"] == "False or contradicted by reliable evidence"
    assert len(res2["contradicting_evidence"]) > 0
    assert len(res2["supporting_evidence"]) == 0


def test_verify_insufficient_evidence():
    verifier = NewsVerifier(TestConfig)
    # Obscure fictitious claim that has no hits
    res = verifier.verify_claim("Zyglotron-99 asteroid has purple crystalline lakes on sector 4")
    assert res["verdict"] in ["Insufficient evidence", "Unverified"]
    assert "explanation" in res
    # Ensure it never claims "False" without evidence
    assert res["verdict"] != "False or contradicted by reliable evidence"


def test_voice_script_generation():
    verifier = NewsVerifier(TestConfig)
    res = verifier.verify_claim("NASA Perseverance rover landed on Mars in February 2021")
    assert "voice_script" in res
    assert len(res["voice_script"]) > 20
    assert "Perseverance" in res["voice_script"] or "true" in res["voice_script"].lower()
