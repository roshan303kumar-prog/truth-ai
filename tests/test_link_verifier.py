import pytest
from services.link_verifier import LinkVerifier


def test_certified_banking_domain():
    verifier = LinkVerifier()
    res = verifier.verify_link("https://www.onlinesbi.sbi/portal")

    assert res["is_certified"] is True
    assert res["risk_score"] <= 5
    assert "Certified" in res["verdict"]
    assert "State Bank of India" in res["certified_organization"]
    assert any("Official Certified Entity" in flag for flag in res["positive_flags"])
    assert res["voice_script"] is not None


def test_phishing_brand_impersonation():
    verifier = LinkVerifier()
    res = verifier.verify_link("http://sbi-kyc-verify-update.xyz/login")

    assert res["is_certified"] is False
    assert res["risk_score"] >= 65
    assert "High-Risk" in res["verdict"] or "Suspicious" in res["verdict"]
    assert "SBI" in res["impersonated_brand"]
    assert "onlinesbi.sbi" in res["official_brand_domain"]
    assert any("Brand Impersonation" in flag for flag in res["risk_flags"])


def test_high_risk_tld_and_urgency():
    verifier = LinkVerifier()
    res = verifier.verify_link("http://free-iphone-winner-claim.top/bonus")

    assert res["risk_score"] >= 40
    assert any("High-Risk Top-Level Domain" in flag for flag in res["risk_flags"])
    assert any("Social Engineering" in flag for flag in res["risk_flags"])


def test_ip_address_host():
    verifier = LinkVerifier()
    res = verifier.verify_link("http://192.168.1.50/admin-login")

    assert res["technical_audit"]["is_ip_address"] is True
    assert any("IP Address" in flag for flag in res["risk_flags"])


def test_shortener_flag():
    verifier = LinkVerifier()
    res = verifier.verify_link("https://bit.ly/special-deal")

    assert res["technical_audit"]["is_shortened"] is True
    assert any("URL Shortener" in flag for flag in res["risk_flags"])


def test_api_verify_link(client):
    response = client.post("/api/verify-link", json={"url": "https://www.google.com"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "report_id" in data
    assert data["hostname"] == "www.google.com"
    assert data["is_certified"] is True


def test_api_verify_link_empty(client):
    response = client.post("/api/verify-link", json={"url": ""})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
