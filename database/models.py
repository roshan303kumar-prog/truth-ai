import json
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    reports = db.relationship("VerificationReport", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    settings = db.relationship("UserSettings", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name or self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_reports": self.reports.count(),
        }


class VerificationReport(db.Model):
    __tablename__ = "verification_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    verification_type = db.Column(db.String(20), nullable=False, index=True)  # 'news', 'image', 'video'
    title_or_claim = db.Column(db.String(500), nullable=False)
    submitted_content = db.Column(db.Text, nullable=True)
    verdict = db.Column(db.String(100), nullable=False)  # One of the 5 standard categories
    confidence_score = db.Column(db.Float, nullable=False, default=0.0)  # 0.0 - 100.0
    explanation = db.Column(db.Text, nullable=False)

    # Serialized JSON lists / dicts
    supporting_evidence_json = db.Column(db.Text, default="[]")
    contradicting_evidence_json = db.Column(db.Text, default="[]")
    technical_findings_json = db.Column(db.Text, default="{}")
    limitations_json = db.Column(db.Text, default="[]")
    source_links_json = db.Column(db.Text, default="[]")

    media_filename = db.Column(db.String(255), nullable=True)
    media_ela_path = db.Column(db.String(255), nullable=True)
    is_saved = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    @property
    def supporting_evidence(self):
        try:
            return json.loads(self.supporting_evidence_json or "[]")
        except Exception:
            return []

    @supporting_evidence.setter
    def supporting_evidence(self, val):
        self.supporting_evidence_json = json.dumps(val, ensure_ascii=False)

    @property
    def contradicting_evidence(self):
        try:
            return json.loads(self.contradicting_evidence_json or "[]")
        except Exception:
            return []

    @contradicting_evidence.setter
    def contradicting_evidence(self, val):
        self.contradicting_evidence_json = json.dumps(val, ensure_ascii=False)

    @property
    def technical_findings(self):
        try:
            return json.loads(self.technical_findings_json or "{}")
        except Exception:
            return {}

    @technical_findings.setter
    def technical_findings(self, val):
        self.technical_findings_json = json.dumps(val, ensure_ascii=False)

    @property
    def limitations(self):
        try:
            return json.loads(self.limitations_json or "[]")
        except Exception:
            return []

    @limitations.setter
    def limitations(self, val):
        self.limitations_json = json.dumps(val, ensure_ascii=False)

    @property
    def source_links(self):
        try:
            return json.loads(self.source_links_json or "[]")
        except Exception:
            return []

    @source_links.setter
    def source_links(self, val):
        self.source_links_json = json.dumps(val, ensure_ascii=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "verification_type": self.verification_type,
            "title_or_claim": self.title_or_claim,
            "submitted_content": self.submitted_content,
            "verdict": self.verdict,
            "confidence_score": round(self.confidence_score, 1),
            "explanation": self.explanation,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "technical_findings": self.technical_findings,
            "limitations": self.limitations,
            "source_links": self.source_links,
            "media_filename": self.media_filename,
            "media_ela_path": self.media_ela_path,
            "is_saved": self.is_saved,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    strict_mode = db.Column(db.Boolean, default=True)
    preferred_provider = db.Column(db.String(50), default="all")  # 'all', 'google', 'duckduckgo'
    email_notifications = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "strict_mode": self.strict_mode,
            "preferred_provider": self.preferred_provider,
            "email_notifications": self.email_notifications,
        }


class FeedbackMessage(db.Model):
    __tablename__ = "feedback_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


class UserReview(db.Model):
    __tablename__ = "user_reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_role = db.Column(db.String(100), default="Verified User")
    rating = db.Column(db.Integer, nullable=False, default=5)  # 1 to 5 stars
    title = db.Column(db.String(200), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_role": self.user_role or "Verified User",
            "rating": self.rating,
            "title": self.title,
            "review_text": self.review_text,
            "created_at": self.created_at.strftime("%B %d, %Y") if self.created_at else "Recently",
        }
