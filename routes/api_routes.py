import time
from pathlib import Path
from flask import request, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from database import db
from database.models import VerificationReport, FeedbackMessage, UserSettings, UserReview
from services.news_verifier import NewsVerifier
from services.image_verifier import ImageVerifier
from services.video_verifier import VideoVerifier
from services.link_verifier import LinkVerifier
from services.ai_assistant import AIAssistant
from services.content_verifier import ContentLinkVerifier
from utils.security import (
    sanitize_input_text,
    validate_image_file,
    validate_video_file,
    rate_limiter,
)
from . import api_bp


def check_rate_limit():
    client_ip = request.remote_addr or "127.0.0.1"
    return rate_limiter.is_allowed(client_ip)


@api_bp.route("/verify-news", methods=["POST"])
def verify_news():
    if not check_rate_limit():
        return jsonify({"success": False, "error": "Rate limit exceeded. Please wait a moment."}), 429

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    claim = sanitize_input_text(data.get("claim", ""))

    if not claim or len(claim) < 5:
        return jsonify({"success": False, "error": "Please provide a valid claim or news headline (min 5 characters)."}), 400

    content_verifier = ContentLinkVerifier(current_app.config)
    is_url_input = content_verifier.is_url(claim)

    if is_url_input:
        # User pasted a News or Video Link into the claim verifier
        result = content_verifier.verify_content_link(claim)
        claim_title = result.get("title", claim)
        v_type = "video_link" if result.get("is_video") else "news_link"
        conf_score = float(result.get("authenticity_score", 50.0))
        verdict = result.get("verdict", "Unverified")
    else:
        verifier = NewsVerifier(current_app.config)
        result = verifier.verify_claim(claim)
        claim_title = claim
        v_type = "news"
        conf_score = result["confidence_score"]
        verdict = result["verdict"]

    # Persist report in database
    report = VerificationReport(
        user_id=current_user.id if current_user.is_authenticated else None,
        verification_type=v_type,
        title_or_claim=claim_title[:450],
        submitted_content=claim,
        verdict=verdict,
        confidence_score=conf_score,
        explanation=result["explanation"],
    )
    report.supporting_evidence = result["supporting_evidence"]
    report.contradicting_evidence = result["contradicting_evidence"]
    report.source_links = result["source_links"]
    report.limitations = result.get("limitations", [
        "Online claim and media forensics inspect verifiable sources and cross-corroboration.",
        "Breaking real-time events may experience delayed official confirmation."
    ])
    report.technical_findings = {
        "linguistic_analysis": result.get("linguistic_analysis", result.get("linguistics", {})),
        "total_sources_evaluated": result.get("total_sources_evaluated", 1),
        "context_evidence": result.get("context_evidence", []),
        "is_url_input": is_url_input,
        "content_type": result.get("content_type"),
        "publisher": result.get("publisher"),
        "key_findings": result.get("key_findings", []),
    }

    db.session.add(report)
    db.session.commit()

    res_payload = result.copy()
    res_payload["report_id"] = report.id
    res_payload["success"] = True
    res_payload["confidence_score"] = conf_score
    return jsonify(res_payload), 200


@api_bp.route("/verify-link", methods=["POST"])
def verify_link():
    if not check_rate_limit():
        return jsonify({"success": False, "error": "Rate limit exceeded. Please wait a moment."}), 429

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    url = sanitize_input_text(data.get("url", ""))

    if not url or len(url) < 3:
        return jsonify({"success": False, "error": "Please provide a valid web link or URL."}), 400

    verifier = LinkVerifier(current_app.config)
    result = verifier.verify_link(url)

    # Persist report in database
    conf_score = float(100 - result["risk_score"])
    report = VerificationReport(
        user_id=current_user.id if current_user.is_authenticated else None,
        verification_type="link",
        title_or_claim=f"Link Scan: {result['hostname']}"[:450],
        submitted_content=url,
        verdict=result["verdict"],
        confidence_score=conf_score,
        explanation=result["explanation"],
    )
    report.supporting_evidence = [{"title": f, "source": "Security Heuristic"} for f in result.get("positive_flags", [])]
    report.contradicting_evidence = [{"title": f, "source": "Threat Indicator"} for f in result.get("risk_flags", [])]
    report.source_links = [{"title": result["hostname"], "url": result["normalized_url"], "publisher": "Scanned Target"}]
    report.limitations = [
        "Domain heuristic analysis evaluates structural anomalies, brand impersonation, and known abusive TLDs.",
        "Zero-day phishing domains registered within the last few hours may require additional network behavioral tracking.",
        "Always verify authentic sender identity on communication channels before clicking sensitive links."
    ]
    report.technical_findings = {
        "technical_audit": result.get("technical_audit", {}),
        "risk_score": result.get("risk_score", 0),
        "risk_level": result.get("risk_level", "Unknown"),
        "impersonated_brand": result.get("impersonated_brand"),
        "official_brand_domain": result.get("official_brand_domain"),
        "is_certified": result.get("is_certified", False),
        "certified_organization": result.get("certified_organization"),
    }

    db.session.add(report)
    db.session.commit()

    res_payload = result.copy()
    res_payload["report_id"] = report.id
    res_payload["success"] = True
    res_payload["confidence_score"] = conf_score
    return jsonify(res_payload), 200


@api_bp.route("/verify-content-link", methods=["POST"])
def verify_content_link():
    if not check_rate_limit():
        return jsonify({"success": False, "error": "Rate limit exceeded. Please wait a moment."}), 429

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    url = sanitize_input_text(data.get("url", ""))

    if not url or len(url) < 3:
        return jsonify({"success": False, "error": "Please provide a valid News or Video URL."}), 400

    verifier = ContentLinkVerifier(current_app.config)
    result = verifier.verify_content_link(url)

    # Persist report in database
    conf_score = float(result.get("authenticity_score", 50.0))
    report = VerificationReport(
        user_id=current_user.id if current_user.is_authenticated else None,
        verification_type="video_link" if result.get("is_video") else "news_link",
        title_or_claim=f"{result.get('content_type', 'Link')}: {result.get('title', '')}"[:450],
        submitted_content=url,
        verdict=result["verdict"],
        confidence_score=conf_score,
        explanation=result["explanation"],
    )
    report.supporting_evidence = result.get("supporting_evidence", [])
    report.contradicting_evidence = result.get("contradicting_evidence", [])
    report.source_links = result.get("source_links", [])
    report.limitations = [
        "Online link verification inspects live article headlines, video descriptions, and publisher domain trust.",
        "Breaking stories published within the last hour may have limited peer-corroboration."
    ]
    report.technical_findings = {
        "content_type": result.get("content_type"),
        "is_video": result.get("is_video"),
        "publisher": result.get("publisher"),
        "source_trust_score": result.get("source_trust_score"),
        "source_badge": result.get("source_badge"),
        "authenticity_score": result.get("authenticity_score"),
        "key_findings": result.get("key_findings", []),
        "linguistics": result.get("linguistics", {}),
    }

    db.session.add(report)
    db.session.commit()

    res_payload = result.copy()
    res_payload["report_id"] = report.id
    res_payload["success"] = True
    res_payload["confidence_score"] = conf_score
    return jsonify(res_payload), 200


@api_bp.route("/verify-image", methods=["POST"])
def verify_image():
    if not check_rate_limit():
        return jsonify({"success": False, "error": "Rate limit exceeded. Please wait a moment."}), 429

    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file uploaded."}), 400

    file = request.files["image"]
    is_valid, ext, err_msg = validate_image_file(file, max_size_bytes=current_app.config["MAX_IMAGE_SIZE"])
    if not is_valid:
        return jsonify({"success": False, "error": err_msg}), 400

    orig_filename = secure_filename(file.filename)
    timestamp = int(time.time())
    saved_filename = f"img_{timestamp}_{orig_filename}"

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "images"
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / saved_filename
    file.save(saved_path)

    verifier = ImageVerifier(current_app.config)
    result = verifier.verify_image(saved_path, orig_filename)

    # Persist report
    report = VerificationReport(
        user_id=current_user.id if current_user.is_authenticated else None,
        verification_type="image",
        title_or_claim=f"Image Analysis: {orig_filename}"[:450],
        submitted_content=f"Uploaded photo: {orig_filename} ({result['image_properties']['dimensions']})",
        verdict=result["verdict"],
        confidence_score=result["confidence_score"],
        explanation=result["explanation"],
        media_filename=saved_filename,
        media_ela_path=result.get("ela_image_filename"),
    )
    report.limitations = result["limitations"]
    report.technical_findings = {
        "image_properties": result["image_properties"],
        "metadata_findings": result["metadata_findings"],
        "ela_analysis": result["ela_analysis"],
        "ai_generation_assessment": result["ai_generation_assessment"],
        "ocr_findings": result["ocr_findings"],
    }
    report.source_links = result.get("reverse_search_links", [])

    db.session.add(report)
    db.session.commit()

    res_payload = result.copy()
    res_payload["report_id"] = report.id
    res_payload["saved_filename"] = saved_filename
    res_payload["success"] = True
    return jsonify(res_payload), 200


@api_bp.route("/verify-video", methods=["POST"])
def verify_video():
    if not check_rate_limit():
        return jsonify({"success": False, "error": "Rate limit exceeded. Please wait a moment."}), 429

    if "video" not in request.files:
        return jsonify({"success": False, "error": "No video file uploaded."}), 400

    file = request.files["video"]
    is_valid, ext, err_msg = validate_video_file(file, max_size_bytes=current_app.config["MAX_VIDEO_SIZE"])
    if not is_valid:
        return jsonify({"success": False, "error": err_msg}), 400

    orig_filename = secure_filename(file.filename)
    timestamp = int(time.time())
    saved_filename = f"vid_{timestamp}_{orig_filename}"

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "videos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / saved_filename
    file.save(saved_path)

    verifier = VideoVerifier(current_app.config)
    result = verifier.verify_video(saved_path, orig_filename)

    # Persist report
    report = VerificationReport(
        user_id=current_user.id if current_user.is_authenticated else None,
        verification_type="video",
        title_or_claim=f"Video Analysis: {orig_filename}"[:450],
        submitted_content=f"Uploaded video: {orig_filename} ({result['video_properties']['duration']})",
        verdict=result["verdict"],
        confidence_score=result["confidence_score"],
        explanation=result["explanation"],
        media_filename=saved_filename,
    )
    report.limitations = result["limitations"]
    report.technical_findings = {
        "video_properties": result["video_properties"],
        "analyzed_frames": result["analyzed_frames"],
        "temporal_analysis": result["temporal_analysis"],
        "ocr_findings": result["ocr_findings"],
        "audio_transcript": result["audio_transcript"],
        "manipulation_indicators": result["manipulation_indicators"],
    }

    db.session.add(report)
    db.session.commit()

    res_payload = result.copy()
    res_payload["report_id"] = report.id
    res_payload["saved_filename"] = saved_filename
    res_payload["success"] = True
    return jsonify(res_payload), 200


@api_bp.route("/history", methods=["GET"])
def get_history():
    vtype = request.args.get("type", "").strip()
    verdict = request.args.get("verdict", "").strip()
    limit = min(int(request.args.get("limit", 50)), 100)

    query = VerificationReport.query

    if current_user.is_authenticated:
        query = query.filter_by(user_id=current_user.id)
    else:
        # Show recent public or guest verifications
        query = query.filter_by(user_id=None)

    if vtype in ["news", "image", "video", "link"]:
        query = query.filter_by(verification_type=vtype)

    if verdict:
        query = query.filter(VerificationReport.verdict.ilike(f"%{verdict}%"))

    reports = query.order_by(VerificationReport.created_at.desc()).limit(limit).all()
    return jsonify({"success": True, "count": len(reports), "reports": [r.to_dict() for r in reports]})


@api_bp.route("/report/<int:report_id>", methods=["GET"])
def get_report(report_id):
    report = VerificationReport.query.get_or_404(report_id)
    return jsonify({"success": True, "report": report.to_dict()})


@api_bp.route("/report/<int:report_id>/bookmark", methods=["POST"])
@login_required
def toggle_bookmark(report_id):
    report = VerificationReport.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    report.is_saved = not report.is_saved
    db.session.commit()
    return jsonify({"success": True, "is_saved": report.is_saved})


@api_bp.route("/report/<int:report_id>", methods=["DELETE"])
@login_required
def delete_report(report_id):
    report = VerificationReport.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    db.session.delete(report)
    db.session.commit()
    return jsonify({"success": True, "message": "Report deleted successfully."})


@api_bp.route("/dashboard", methods=["GET"])
@login_required
def get_dashboard_data():
    reports_query = VerificationReport.query.filter_by(user_id=current_user.id)
    total_checks = reports_query.count()

    supported_count = reports_query.filter(VerificationReport.verdict.ilike("%Supported%")).count()
    contradicted_count = reports_query.filter(VerificationReport.verdict.ilike("%False%")).count()
    misleading_count = reports_query.filter(VerificationReport.verdict.ilike("%Misleading%")).count()
    unverified_count = reports_query.filter(VerificationReport.verdict.ilike("%Unverified%")).count()
    insufficient_count = reports_query.filter(VerificationReport.verdict.ilike("%Insufficient%")).count()

    news_count = reports_query.filter_by(verification_type="news").count()
    image_count = reports_query.filter_by(verification_type="image").count()
    video_count = reports_query.filter_by(verification_type="video").count()
    link_count = reports_query.filter_by(verification_type="link").count()

    saved_reports = reports_query.filter_by(is_saved=True).order_by(VerificationReport.created_at.desc()).all()
    recent_reports = reports_query.order_by(VerificationReport.created_at.desc()).limit(8).all()

    return jsonify({
        "success": True,
        "metrics": {
            "total_checks": total_checks,
            "supported": supported_count,
            "contradicted": contradicted_count,
            "misleading": misleading_count,
            "unverified": unverified_count,
            "insufficient": insufficient_count,
            "saved_count": len(saved_reports),
        },
        "type_breakdown": {
            "news": news_count,
            "image": image_count,
            "video": video_count,
            "link": link_count,
        },
        "recent_reports": [r.to_dict() for r in recent_reports],
        "saved_reports": [r.to_dict() for r in saved_reports],
    })


@api_bp.route("/contact", methods=["POST"])
def submit_contact():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    name = sanitize_input_text(data.get("name", ""))
    email = sanitize_input_text(data.get("email", "")).lower()
    subject = sanitize_input_text(data.get("subject", ""))
    message = sanitize_input_text(data.get("message", ""))

    if not name or not email or not message:
        return jsonify({"success": False, "error": "Please provide your name, email, and message."}), 400

    feedback = FeedbackMessage(name=name, email=email, subject=subject or "General Feedback", message=message)
    db.session.add(feedback)
    db.session.commit()

    return jsonify({"success": True, "message": "Thank you! Your feedback has been received."})


@api_bp.route("/assistant/chat", methods=["POST"])
def assistant_chat():
    if not check_rate_limit():
        return jsonify({"success": False, "error": "Rate limit exceeded. Please wait a moment."}), 429

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    screenshot = data.get("screenshot")  # base64 string or None
    page_context = data.get("page_context") or {}
    history = data.get("history") or []

    if not message and not screenshot:
        return jsonify({"success": False, "error": "Please provide a message or screenshot."}), 400

    if current_user.is_authenticated:
        page_context["user_name"] = current_user.full_name or current_user.username

    clean_message = sanitize_input_text(message) if message else "Analyze this screen screenshot."

    assistant = AIAssistant(current_app.config)
    result = assistant.chat(
        message=clean_message,
        screenshot_b64=screenshot,
        page_context=page_context,
        history=history,
    )

    return jsonify(result), 200


@api_bp.route("/reviews", methods=["GET"])
def get_reviews():
    all_reviews = UserReview.query.filter_by(is_approved=True).order_by(UserReview.created_at.desc()).all()
    total_count = len(all_reviews)
    avg_rating = round(sum(r.rating for r in all_reviews) / total_count, 1) if total_count > 0 else 5.0
    return jsonify({
        "success": True,
        "count": total_count,
        "average_rating": avg_rating,
        "reviews": [r.to_dict() for r in all_reviews],
    })


@api_bp.route("/reviews", methods=["POST"])
def submit_review():
    if not check_rate_limit():
        return jsonify({"success": False, "error": "Rate limit exceeded. Please wait a moment."}), 429

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    name = sanitize_input_text(data.get("name", "")).strip()
    role = sanitize_input_text(data.get("role", "")).strip() or "Verified User"
    title = sanitize_input_text(data.get("title", "")).strip()
    review_text = sanitize_input_text(data.get("review_text", "")).strip()

    try:
        rating = int(data.get("rating", 5))
        rating = max(1, min(5, rating))
    except (ValueError, TypeError):
        rating = 5

    if not name or len(name) < 2:
        return jsonify({"success": False, "error": "Please provide your name (at least 2 characters)."}), 400
    if not title or len(title) < 3:
        return jsonify({"success": False, "error": "Please provide a review headline (at least 3 characters)."}), 400
    if not review_text or len(review_text) < 5:
        return jsonify({"success": False, "error": "Please write your review feedback (at least 5 characters)."}), 400

    review = UserReview(
        user_id=current_user.id if current_user.is_authenticated else None,
        user_name=name,
        user_role=role,
        rating=rating,
        title=title,
        review_text=review_text,
        is_approved=True,
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Thank you! Your review has been published.",
        "review": review.to_dict(),
    }), 201
