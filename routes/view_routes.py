from flask import render_template, request, send_from_directory, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db
from database.models import VerificationReport, FeedbackMessage, UserSettings, UserReview
from utils.helpers import get_verdict_meta, get_confidence_tier, time_ago
from . import views_bp


@views_bp.route("/")
def index():
    # Fetch recent public verifications to display on homepage
    recent_checks = VerificationReport.query.order_by(VerificationReport.created_at.desc()).limit(4).all()
    total_checks = VerificationReport.query.count()
    featured_reviews = UserReview.query.filter_by(is_approved=True).order_by(UserReview.created_at.desc()).limit(3).all()
    total_reviews = UserReview.query.filter_by(is_approved=True).count()
    return render_template(
        "index.html",
        recent_checks=recent_checks,
        total_checks=total_checks,
        featured_reviews=featured_reviews,
        total_reviews=total_reviews,
    )


@views_bp.route("/news")
def news():
    return render_template("news.html")


@views_bp.route("/image")
def image():
    return render_template("image.html")


@views_bp.route("/video")
def video():
    return render_template("video.html")


@views_bp.route("/link")
def link():
    return render_template("link.html")


@views_bp.route("/reviews")
def reviews():
    all_reviews = UserReview.query.filter_by(is_approved=True).order_by(UserReview.created_at.desc()).all()
    total_count = len(all_reviews)
    avg_rating = round(sum(r.rating for r in all_reviews) / total_count, 1) if total_count > 0 else 5.0

    # Star distribution
    star_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in all_reviews:
        star_counts[r.rating] = star_counts.get(r.rating, 0) + 1

    star_percents = {
        s: round((count / total_count * 100), 1) if total_count > 0 else 0
        for s, count in star_counts.items()
    }

    return render_template(
        "reviews.html",
        reviews=all_reviews,
        total_count=total_count,
        avg_rating=avg_rating,
        star_counts=star_counts,
        star_percents=star_percents,
    )


@views_bp.route("/history")
def history():
    vtype = request.args.get("type", "")
    query = VerificationReport.query

    if current_user.is_authenticated:
        query = query.filter_by(user_id=current_user.id)
    else:
        query = query.filter_by(user_id=None)

    if vtype in ["news", "image", "video", "link"]:
        query = query.filter_by(verification_type=vtype)

    reports = query.order_by(VerificationReport.created_at.desc()).all()
    return render_template("history.html", reports=reports, selected_type=vtype)


@views_bp.route("/dashboard")
@login_required
def dashboard():
    reports_query = VerificationReport.query.filter_by(user_id=current_user.id)
    total_count = reports_query.count()
    supported_count = reports_query.filter(VerificationReport.verdict.ilike("%Supported%")).count()
    contradicted_count = reports_query.filter(VerificationReport.verdict.ilike("%False%")).count()
    misleading_count = reports_query.filter(VerificationReport.verdict.ilike("%Misleading%")).count()
    unverified_count = reports_query.filter(VerificationReport.verdict.ilike("%Unverified%")).count()
    insufficient_count = reports_query.filter(VerificationReport.verdict.ilike("%Insufficient%")).count()

    recent_reports = reports_query.order_by(VerificationReport.created_at.desc()).limit(6).all()
    saved_reports = reports_query.filter_by(is_saved=True).order_by(VerificationReport.created_at.desc()).all()

    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    return render_template(
        "dashboard.html",
        total_count=total_count,
        supported_count=supported_count,
        contradicted_count=contradicted_count,
        misleading_count=misleading_count,
        unverified_count=unverified_count,
        insufficient_count=insufficient_count,
        recent_reports=recent_reports,
        saved_reports=saved_reports,
        settings=settings,
    )


@views_bp.route("/report/<int:report_id>")
def report_detail(report_id):
    report = VerificationReport.query.get_or_404(report_id)
    verdict_meta = get_verdict_meta(report.verdict)
    confidence_tier, tier_desc = get_confidence_tier(report.confidence_score)
    return render_template(
        "report.html",
        report=report,
        verdict_meta=verdict_meta,
        confidence_tier=confidence_tier,
        confidence_desc=tier_desc,
    )


@views_bp.route("/about")
def about():
    return render_template("about.html")


@views_bp.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")


@views_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if name and email and message:
            fb = FeedbackMessage(name=name, email=email, subject=subject or "General Inquiry", message=message)
            db.session.add(fb)
            db.session.commit()
            flash("Thank you for reaching out! Your message has been received.", "success")
            return redirect(url_for("views.contact"))
        else:
            flash("Please fill out all required fields.", "warning")

    return render_template("contact.html")


@views_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@views_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Securely serve media files from upload subdirectories."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
