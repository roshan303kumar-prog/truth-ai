import re
from datetime import datetime, timezone
from flask import request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from database import db
from database.models import User, UserSettings
from . import auth_bp, api_bp


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()

        if not username or len(username) < 3:
            flash("Username must be at least 3 characters long.", "danger")
            return render_template("register.html", username=username, email=email, full_name=full_name)

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template("register.html", username=username, email=email, full_name=full_name)

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("register.html", username=username, email=email, full_name=full_name)

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email is already registered.", "warning")
            return render_template("register.html", username=username, email=email, full_name=full_name)

        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()

        login_user(user)
        flash("Welcome to TRUTH AI! Your account has been created.", "success")
        return redirect(url_for("views.dashboard"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))

    if request.method == "POST":
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.username == login_id) | (User.email == login_id.lower())
        ).first()

        if user and user.check_password(password):
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.full_name or user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page if next_page and next_page.startswith("/") else url_for("views.dashboard"))
        else:
            flash("Invalid username/email or password.", "danger")
            return render_template("login.html", login_id=login_id)

    return render_template("login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out securely.", "info")
    return redirect(url_for("views.index"))


# JSON API Auth endpoints for AJAX/SPA operations
@api_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()

    if not username or len(username) < 3:
        return jsonify({"success": False, "error": "Username must be at least 3 characters."}), 400
    if not is_valid_email(email):
        return jsonify({"success": False, "error": "Invalid email address format."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "error": "Password must be at least 8 characters."}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"success": False, "error": "Username or email is already registered."}), 409

    user = User(username=username, email=email, full_name=full_name)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    settings = UserSettings(user_id=user.id)
    db.session.add(settings)
    db.session.commit()

    login_user(user)
    return jsonify({"success": True, "message": "Account created successfully.", "user": user.to_dict()}), 201


@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    login_id = data.get("login_id", "").strip()
    password = data.get("password", "")
    remember = bool(data.get("remember", False))

    user = User.query.filter(
        (User.username == login_id) | (User.email == login_id.lower())
    ).first()

    if user and user.check_password(password):
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        login_user(user, remember=remember)
        return jsonify({"success": True, "message": "Login successful.", "user": user.to_dict()})

    return jsonify({"success": False, "error": "Invalid login credentials."}), 401


@api_bp.route("/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"success": True, "message": "Logged out successfully."})
