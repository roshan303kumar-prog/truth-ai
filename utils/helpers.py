from datetime import datetime, timezone

VERDICT_CATEGORIES = {
    "supported": "Supported by available evidence",
    "false": "False or contradicted by reliable evidence",
    "misleading": "Misleading or missing context",
    "unverified": "Unverified",
    "insufficient": "Insufficient evidence",
}

VERDICT_METADATA = {
    "Supported by available evidence": {
        "badge_class": "badge-supported",
        "icon": "fa-circle-check",
        "color": "#10b981",
        "bg_color": "rgba(16, 185, 129, 0.15)",
        "border_color": "#10b981",
    },
    "Certified & Trusted Link": {
        "badge_class": "badge-supported",
        "icon": "fa-circle-check",
        "color": "#10b981",
        "bg_color": "rgba(16, 185, 129, 0.15)",
        "border_color": "#10b981",
    },
    "Likely Safe Link": {
        "badge_class": "badge-supported",
        "icon": "fa-circle-check",
        "color": "#10b981",
        "bg_color": "rgba(16, 185, 129, 0.15)",
        "border_color": "#10b981",
    },
    "False or contradicted by reliable evidence": {
        "badge_class": "badge-false",
        "icon": "fa-circle-xmark",
        "color": "#ef4444",
        "bg_color": "rgba(239, 68, 68, 0.15)",
        "border_color": "#ef4444",
    },
    "High Risk Phishing / Fraud Alert": {
        "badge_class": "badge-false",
        "icon": "fa-circle-xmark",
        "color": "#ef4444",
        "bg_color": "rgba(239, 68, 68, 0.15)",
        "border_color": "#ef4444",
    },
    "Misleading or missing context": {
        "badge_class": "badge-misleading",
        "icon": "fa-triangle-exclamation",
        "color": "#f59e0b",
        "bg_color": "rgba(245, 158, 11, 0.15)",
        "border_color": "#f59e0b",
    },
    "Suspicious Link / Caution Advised": {
        "badge_class": "badge-misleading",
        "icon": "fa-triangle-exclamation",
        "color": "#f59e0b",
        "bg_color": "rgba(245, 158, 11, 0.15)",
        "border_color": "#f59e0b",
    },
    "Unverified": {
        "badge_class": "badge-unverified",
        "icon": "fa-circle-question",
        "color": "#00e5ff",
        "bg_color": "rgba(0, 229, 255, 0.15)",
        "border_color": "#00e5ff",
    },
    "Insufficient evidence": {
        "badge_class": "badge-insufficient",
        "icon": "fa-circle-info",
        "color": "#94a3b8",
        "bg_color": "rgba(148, 163, 184, 0.15)",
        "border_color": "#94a3b8",
    },
}


def get_verdict_meta(verdict: str) -> dict:
    """Returns visual style metadata for a given verdict."""
    if verdict in VERDICT_METADATA:
        return VERDICT_METADATA[verdict]

    # Heuristic fallback matching
    v_lower = (verdict or "").lower()
    if "safe" in v_lower or "certified" in v_lower or "trusted" in v_lower or "supported" in v_lower:
        return VERDICT_METADATA["Supported by available evidence"]
    if "phishing" in v_lower or "fraud" in v_lower or "false" in v_lower or "contradicted" in v_lower:
        return VERDICT_METADATA["False or contradicted by reliable evidence"]
    if "suspicious" in v_lower or "misleading" in v_lower or "caution" in v_lower:
        return VERDICT_METADATA["Misleading or missing context"]
    if "unverified" in v_lower:
        return VERDICT_METADATA["Unverified"]

    return {
        "badge_class": "badge-insufficient",
        "icon": "fa-circle-info",
        "color": "#94a3b8",
        "bg_color": "rgba(148, 163, 184, 0.15)",
        "border_color": "#94a3b8",
    }


def get_confidence_tier(score: float) -> tuple[str, str]:
    """Returns confidence tier name and description."""
    if score >= 80.0:
        return "High Confidence", "Multiple consistent and corroborated evidence sources identified."
    elif score >= 50.0:
        return "Moderate Confidence", "Partial evidence found with minor ambiguity or single corroborating source."
    else:
        return "Low Confidence", "Limited verifiable data available; interpret results with caution."


def time_ago(dt: datetime) -> str:
    """Returns a friendly relative time string."""
    if not dt:
        return "Just now"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        mins = seconds // 60
        return f"{mins} min{'s' if mins > 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days > 1 else ''} ago"
