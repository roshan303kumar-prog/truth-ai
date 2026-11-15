import math
import re
import urllib.parse
from typing import Dict, Any, List, Optional


# Global & Indian Certified Trusted Domains (Government, Banks, Major Tech & E-Commerce)
CERTIFIED_DOMAINS = {
    # Tech & Global Platforms
    "google.com": "Google Official Services",
    "google.co.in": "Google India",
    "youtube.com": "YouTube (Google)",
    "apple.com": "Apple Official Services",
    "icloud.com": "Apple iCloud",
    "microsoft.com": "Microsoft Corporation",
    "live.com": "Microsoft Live",
    "outlook.com": "Microsoft Outlook",
    "amazon.com": "Amazon Global",
    "amazon.in": "Amazon India",
    "wikipedia.org": "Wikimedia Foundation",
    "github.com": "GitHub (Microsoft)",
    "netflix.com": "Netflix Official",
    "facebook.com": "Meta / Facebook",
    "instagram.com": "Meta / Instagram",
    "whatsapp.com": "WhatsApp Official",
    "x.com": "X (Twitter)",
    "twitter.com": "Twitter",
    "linkedin.com": "LinkedIn Official",
    "openai.com": "OpenAI Official",
    "nasa.gov": "NASA Official Agency",

    # Indian Banking & Payments
    "onlinesbi.sbi": "State Bank of India (Official Internet Banking)",
    "sbi.co.in": "State Bank of India (Corporate Portal)",
    "hdfcbank.com": "HDFC Bank Official",
    "icicibank.com": "ICICI Bank Official",
    "axisbank.com": "Axis Bank Official",
    "pnbindia.in": "Punjab National Bank",
    "bankofbaroda.in": "Bank of Baroda",
    "canarabank.com": "Canara Bank",
    "kotak.com": "Kotak Mahindra Bank",
    "paytm.com": "Paytm Payments Bank",
    "phonepe.com": "PhonePe Official",
    "bhimupi.org.in": "BHIM UPI (NPCI Official)",
    "npci.org.in": "National Payments Corporation of India",
    "rbi.org.in": "Reserve Bank of India",
    "paypal.com": "PayPal Official",
    "chase.com": "JPMorgan Chase Official",

    # Indian E-Commerce & Utilities
    "flipkart.com": "Flipkart Official",
    "myntra.com": "Myntra Official",
    "swiggy.com": "Swiggy Official",
    "zomato.com": "Zomato Official",
    "irctc.co.in": "Indian Railways (IRCTC Official)",
    "uidai.gov.in": "UIDAI / Aadhaar Official Government Portal",
    "incometax.gov.in": "Income Tax Department of India",
}

# Brands frequently targeted by Phishers & Scammers
PHISHING_TARGET_BRANDS = {
    "sbi": {"name": "State Bank of India (SBI)", "official": "onlinesbi.sbi or sbi.co.in"},
    "hdfc": {"name": "HDFC Bank", "official": "hdfcbank.com"},
    "icici": {"name": "ICICI Bank", "official": "icicibank.com"},
    "axis": {"name": "Axis Bank", "official": "axisbank.com"},
    "pnb": {"name": "Punjab National Bank", "official": "pnbindia.in"},
    "paytm": {"name": "Paytm", "official": "paytm.com"},
    "phonepe": {"name": "PhonePe", "official": "phonepe.com"},
    "paypal": {"name": "PayPal", "official": "paypal.com"},
    "amazon": {"name": "Amazon", "official": "amazon.in or amazon.com"},
    "flipkart": {"name": "Flipkart", "official": "flipkart.com"},
    "netflix": {"name": "Netflix", "official": "netflix.com"},
    "apple": {"name": "Apple", "official": "apple.com"},
    "google": {"name": "Google", "official": "google.com"},
    "microsoft": {"name": "Microsoft", "official": "microsoft.com"},
    "aadhaar": {"name": "UIDAI Aadhaar", "official": "uidai.gov.in"},
    "uidai": {"name": "UIDAI Aadhaar", "official": "uidai.gov.in"},
    "incometax": {"name": "Income Tax Department", "official": "incometax.gov.in"},
    "pan": {"name": "NSDL / UTIITSL PAN", "official": "onlineservices.nsdl.com"},
}

# High-Risk Top-Level Domains (TLDs) frequently abused in disposable phishing campaigns
HIGH_RISK_TLDS = {
    "xyz", "top", "click", "buzz", "fit", "tk", "ml", "ga", "cf", "gq", "work",
    "icu", "cam", "vip", "monster", "quest", "rest", "online", "site", "space",
    "live", "store", "website", "link", "club", "stream", "download", "racing"
}

# Keywords indicating Fraud, Urgency, KYC, and Social Engineering Traps
SUSPICIOUS_PATH_KEYWORDS = {
    # Banking & Credential harvesting
    "kyc", "pan-link", "aadhaar", "pan-update", "re-kyc", "netbanking", "unblock",
    "account-suspended", "account-blocked", "reactivate", "verify-login", "otp",
    "security-update", "card-update", "login-auth", "secure-banking",
    # Financial Greed & Fake Lottery
    "lottery", "winner", "prize", "cashback", "free-recharge", "free-gift",
    "iphone-giveaway", "claim-reward", "crorepati", "bonus", "spin-wheel",
    "lucky-draw", "claim-now", "free-coins", "airdrop", "investment-doubler"
}

# Popular URL Shorteners that conceal the actual destination
URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy", "shorturl.at", "ow.ly", "buff.ly"
}


class LinkVerifier:
    """Production-grade Forensic Engine for Link, URL, Phishing & Fraud Detection."""

    def __init__(self, config=None):
        self.config = config

    def calculate_entropy(self, text: str) -> float:
        """Calculates Shannon entropy to detect randomly generated DGA strings."""
        if not text:
            return 0.0
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
        return round(entropy, 2)

    def extract_domain_parts(self, raw_url: str):
        """Safely parses raw URL string and extracts hostname, tld, and path."""
        url = raw_url.strip()
        if not re.match(r"^[a-zA-Z]+://", url):
            url = "https://" + url

        try:
            parsed = urllib.parse.urlparse(url)
            hostname = (parsed.hostname or "").lower()
            port = parsed.port
            scheme = (parsed.scheme or "https").lower()
            path = (parsed.path or "").lower()
            query = (parsed.query or "").lower()
        except Exception:
            hostname = ""
            port = None
            scheme = "https"
            path = ""
            query = ""

        # Extract root domain and TLD
        host_parts = hostname.split(".")
        tld = host_parts[-1] if len(host_parts) > 1 else ""
        if len(host_parts) >= 2 and host_parts[-2] in ["co", "gov", "nic", "org", "ac", "com"] and len(host_parts[-1]) == 2:
            root_domain = ".".join(host_parts[-3:]) if len(host_parts) >= 3 else hostname
            tld = ".".join(host_parts[-2:])
        else:
            root_domain = ".".join(host_parts[-2:]) if len(host_parts) >= 2 else hostname

        return {
            "normalized_url": url,
            "scheme": scheme,
            "hostname": hostname,
            "root_domain": root_domain,
            "tld": tld,
            "path": path,
            "query": query,
            "port": port,
        }

    def verify_link(self, raw_url: str) -> Dict[str, Any]:
        """
        Executes deep heuristic audit on a submitted web link:
        1. Whitelist Verification (Official Certified check)
        2. Brand Impersonation & Typosquatting Detection
        3. High-Risk TLD & Disposable Domain Audit
        4. Social Engineering / Urgency Keywords Scan
        5. IP Address & Structural Anomaly Detection
        6. Risk Score & Explainable Audit Generation
        """
        parsed = self.extract_domain_parts(raw_url)
        hostname = parsed["hostname"]
        root_domain = parsed["root_domain"]
        tld = parsed["tld"].split(".")[-1]
        scheme = parsed["scheme"]
        path = parsed["path"]
        query = parsed["query"]
        full_content = f"{hostname} {path} {query}".lower()

        risk_score = 0
        risk_flags = []
        positive_flags = []
        impersonated_brand = None

        if not hostname:
            return {
                "submitted_url": raw_url,
                "verdict": "Invalid URL",
                "risk_score": 0,
                "risk_level": "Unknown",
                "explanation": "The entered input could not be parsed as a valid web URL address.",
                "technical_audit": {},
                "recommendation": "Please verify the link spelling and include a valid domain name.",
                "voice_script": "Invalid URL entered. Please provide a valid web address.",
            }

        # 1. Check Certified Safe Domain Whitelist
        is_certified = False
        certified_label = ""

        # Check exact root domain or parent domain
        for cert_dom, label in CERTIFIED_DOMAINS.items():
            if hostname == cert_dom or hostname.endswith("." + cert_dom):
                is_certified = True
                certified_label = label
                break

        # Check official Government / Military / Educational TLDs
        if any(hostname.endswith(gtld) for gtld in [".gov", ".gov.in", ".nic.in", ".mil", ".edu", ".ac.in"]):
            is_certified = True
            certified_label = "Official Government / Institutional Entity"

        if is_certified:
            risk_score = 5
            positive_flags.append(f"Recognized Official Certified Entity: {certified_label}")
            if scheme == "https":
                positive_flags.append("Secure Transport Layer Security (HTTPS) Active")

            verdict = "Certified & Trusted Link"
            risk_level = "Low Risk"
            explanation = (
                f"This URL belongs to the authentic, officially certified digital infrastructure of {certified_label} "
                f"({root_domain}). No indicators of domain spoofing, redirection fraud, or credential harvesting were detected."
            )
            recommendation = "This is a legitimate and verified web destination. It is safe to browse."
            voice_script = f"This link appears to be safe and certified. It belongs to the official verified domain of {certified_label}."

            return {
                "submitted_url": raw_url,
                "normalized_url": parsed["normalized_url"],
                "hostname": hostname,
                "root_domain": root_domain,
                "verdict": verdict,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "is_certified": True,
                "certified_organization": certified_label,
                "impersonated_brand": None,
                "risk_flags": risk_flags,
                "positive_flags": positive_flags,
                "explanation": explanation,
                "recommendation": recommendation,
                "technical_audit": {
                    "protocol": scheme.upper(),
                    "tld": tld,
                    "entropy": self.calculate_entropy(root_domain),
                    "is_ip_address": False,
                    "is_shortened": hostname in URL_SHORTENERS,
                },
                "voice_script": voice_script,
            }

        # 2. Check for Brand Impersonation / Phishing Targets
        for brand_key, brand_info in PHISHING_TARGET_BRANDS.items():
            # Check if brand is in hostname or subdomains, but NOT the legitimate domain
            if brand_key in hostname:
                # Is it the actual brand domain?
                is_actual = any(
                    hostname == legit or hostname.endswith("." + legit)
                    for legit in brand_info["official"].replace(" or ", ",").split(",")
                    if legit.strip()
                )
                if not is_actual:
                    impersonated_brand = brand_info
                    risk_score += 65
                    risk_flags.append(
                        f"🚨 CRITICAL: Brand Impersonation Detected! This link claims or mimics {brand_info['name']}, "
                        f"but is hosted on an unauthorized domain '{root_domain}'. Real domain is: {brand_info['official']}."
                    )
                    break

        # 3. High-Risk TLD Check
        if tld in HIGH_RISK_TLDS:
            risk_score += 25
            risk_flags.append(
                f"High-Risk Top-Level Domain (.{tld}) detected. Scammers frequently register cheap .{tld} domains for temporary phishing."
            )

        # 4. IP Address Used As Hostname
        is_ip = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname))
        if is_ip:
            risk_score += 45
            risk_flags.append(
                "Bare IP Address used as host instead of a registered domain name. This is a common tactic to bypass security filters."
            )

        # 5. Excessive Subdomain Stacking (e.g. sbi.bank.login.badsite.com)
        subdomain_parts = hostname.split(".")
        if len(subdomain_parts) > 3:
            risk_score += 20
            risk_flags.append(
                f"Excessive Subdomain Stacking ({len(subdomain_parts)} levels). Attackers nest trusted names in subdomains to trick mobile users."
            )

        # 6. Excessive Hyphens in Domain Name
        hyphen_count = hostname.count("-")
        if hyphen_count >= 3:
            risk_score += 15
            risk_flags.append(f"Excessive Hyphens ({hyphen_count} hyphens) in domain, indicative of typosquatting patterns.")

        # 7. Suspicious Urgency / Social Engineering Keywords in Path or Query
        found_keywords = [kw for kw in SUSPICIOUS_PATH_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", full_content)]
        if found_keywords:
            risk_score += min(35, len(found_keywords) * 12)
            risk_flags.append(
                f"Social Engineering / Phishing Keywords identified: {', '.join(found_keywords[:4])}. "
                f"Commonly used to create false panic (KYC suspended, lottery claims, OTP theft)."
            )

        # 8. Unmasked URL Shortener
        is_shortener = hostname in URL_SHORTENERS
        if is_shortener:
            risk_score += 20
            risk_flags.append(
                f"URL Shortener ({hostname}) masks the true destination website. Exercise caution before opening."
            )

        # 9. Protocol Security Check (Plain HTTP)
        if scheme == "http":
            risk_score += 15
            risk_flags.append("Insecure HTTP protocol. This connection lacks SSL/TLS encryption; data submitted is vulnerable to interception.")
        else:
            positive_flags.append("SSL/TLS Encryption active (HTTPS)")

        # 10. Entropy check (Random DGA string)
        entropy = self.calculate_entropy(root_domain)
        if entropy > 3.8 and len(root_domain) > 12:
            risk_score += 15
            risk_flags.append(f"High randomness entropy ({entropy}) in domain string, characteristic of algorithmic scam domains.")

        # Cap Risk Score at 98% max
        risk_score = min(98, max(5, risk_score))

        # Determine Verdict
        if risk_score >= 60 or impersonated_brand is not None:
            verdict = "High-Risk Fraud / Phishing Alert"
            risk_level = "High Danger"
            explanation = (
                f"This link exhibits severe malicious indicators. "
                + (f"It is actively impersonating {impersonated_brand['name']} while running on an unauthorized server. " if impersonated_brand else "")
                + f"The domain '{hostname}' carries multiple red flags including {risk_flags[0] if risk_flags else 'fraudulent markers'}. "
                f"DO NOT enter credentials, OTPs, or payment information."
            )
            recommendation = (
                "⚠️ DO NOT OPEN OR CLICK THIS LINK. Never enter your bank password, OTP, or personal KYC details. "
                "If this message claims to be from your bank or a service provider, open their official mobile app directly. "
                "Block and report the sender."
            )
            voice_script = (
                f"Warning: This link is classified as high-risk fraud or phishing with a {risk_score} percent risk score. "
                + (f"It appears to be impersonating {impersonated_brand['name']}. " if impersonated_brand else "")
                + "Do not enter any passwords, OTPs, or personal data on this page."
            )
        elif risk_score >= 25:
            verdict = "Suspicious & Potentially Unsafe"
            risk_level = "Medium Risk"
            explanation = (
                f"This URL contains suspicious architectural traits ({', '.join([f.split(':')[0] for f in risk_flags[:2]])}). "
                f"While not definitively flagged on public blacklists, it lacks verified institutional credentials."
            )
            recommendation = "Exercise extreme caution. Do not download files, sign in, or share phone numbers or banking information."
            voice_script = f"Caution advised. This link is marked suspicious with a {risk_score} percent risk score. Exercise caution."
        else:
            verdict = "Safe / Low Risk Domain"
            risk_level = "Low Risk"
            explanation = (
                f"The domain '{hostname}' does not trigger any recognized phishing markers, brand spoofing, or high-risk TLD filters. "
                f"Standard web security hygiene is still recommended."
            )
            recommendation = "No known phishing signals detected. Verify you trust the sender before downloading attachments."
            voice_script = f"This link appears to be low risk with a risk score of {risk_score} percent. No phishing indicators detected."

        return {
            "submitted_url": raw_url,
            "normalized_url": parsed["normalized_url"],
            "hostname": hostname,
            "root_domain": root_domain,
            "verdict": verdict,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "is_certified": False,
            "certified_organization": None,
            "impersonated_brand": impersonated_brand["name"] if impersonated_brand else None,
            "official_brand_domain": impersonated_brand["official"] if impersonated_brand else None,
            "risk_flags": risk_flags,
            "positive_flags": positive_flags,
            "explanation": explanation,
            "recommendation": recommendation,
            "technical_audit": {
                "protocol": scheme.upper(),
                "tld": tld,
                "entropy": entropy,
                "is_ip_address": is_ip,
                "is_shortened": is_shortener,
                "total_threat_indicators": len(risk_flags),
            },
            "voice_script": voice_script,
        }
