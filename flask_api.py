from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from threading import Thread
import os
from database.database import (
    get_all_users,
    get_all_admins,
    add_admin,
    remove_admin,
    get_all_approved_users,
    get_broadcast_count,
    get_pending_approvals_count,
    save_broadcast,
    remove_user,
    is_admin,
    update_user_name,
    get_user_by_id,  # <-- Add this line
)

from telegram import Bot
import asyncio
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)  # Remove pool_size and pool_timeout

flask_app = Flask("bot_api" )
flask_app.secret_key = "your_secret_key"  # Change this in production

# -------------------- Login Page --------------------
@flask_app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        chat_id = request.form.get("chat_id")
        name = request.form.get("name")
        if not chat_id or not name:
            flash("Both Admin ID and Name are required.", "danger")
            return render_template("login.html")
        # Check if admin exists and name matches
        admins = get_all_admins()
        for admin in admins:
            if str(admin[0]) == chat_id and (admin[1] == name or admin[1] is None):
                session["admin_logged_in"] = True
                session["admin_id"] = chat_id
                session["admin_name"] = name
                return redirect(url_for("dashboard"))
        flash("Invalid Admin ID or Name.", "danger")
        return render_template("login.html")
    return render_template("login.html")

# -------------------- Logout --------------------
@flask_app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------- Dashboard Route (Protected) --------------------
@flask_app.route("/")
def dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    users = get_all_users()
    admins = get_all_admins()
    broadcasts_sent = get_broadcast_count()
    pending_approvals = get_pending_approvals_count()

    # Calculate days left for each user
    users_with_days = []
    for user in users:
        subscription_end = user[3]  # (chat_id, name, subscription_start, subscription_end)
        days_left = ""
        if subscription_end:
            try:
                end_date = datetime.strptime(subscription_end, "%Y-%m-%d").date()
                today = datetime.today().date()
                days_left = (end_date - today).days
            except Exception:
                days_left = "?"
        users_with_days.append((*user, days_left))

    return render_template(
        "dashboard.html",
        users=users_with_days,
        admins=admins,
        broadcasts_sent=broadcasts_sent,
        pending_approvals=pending_approvals,
        admin_name=session.get("admin_name")
    )

# -------------------- Broadcast Route --------------------
@flask_app.route("/broadcast", methods=["POST"])
def api_broadcast():
    data = request.json if request.is_json else {"message": request.form.get("message")}
    message = data.get("message")
    if not message:
        flash("No message provided for broadcast.", "danger")
        return redirect(url_for("dashboard"))

    users = get_all_approved_users()
    sent_count = 0
    for chat_id, name in users:
        try:
            asyncio.run(bot.send_message(chat_id=chat_id, text=message))
            sent_count += 1
            print(f"Message sent to {chat_id}")  # Log successful sends
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")  # Log errors

    save_broadcast(message, sent_count)  # Save broadcast details in the database
    flash(f"Broadcast sent to {sent_count} users!", "success")
    return redirect(url_for("dashboard"))

# -------------------- Add Admin Route --------------------
@flask_app.route("/add_admin", methods=["POST"])
def add_admin_route():
    chat_id = request.form.get("chat_id")
    name = request.form.get("name")
    if not chat_id or not name:
        flash("Both Chat ID and Name are required.", "danger")
        return redirect(url_for("dashboard"))
    add_admin(chat_id, name)
    flash("Admin added!", "success")
    return redirect(url_for("dashboard"))

# -------------------- Remove Admin Route --------------------
@flask_app.route("/remove_admin/<chat_id>")
def remove_admin_route(chat_id):
    remove_admin(chat_id)
    flash("Admin removed!", "success")
    return redirect(url_for("dashboard"))

@flask_app.route("/remove_user/<chat_id>")
def remove_user_route(chat_id):
    remove_user(chat_id)  # Implement this function in database.py
    flash("User removed successfully!", "success")
    return redirect(url_for("dashboard"))

@flask_app.route("/test_message", methods=["GET"])
def test_message():
    try:
        asyncio.run(bot.send_message(chat_id="7752307956", text="Test message from bot"))
        return "Message sent successfully!"
    except Exception as e:
        return f"Failed to send message: {e}"

# Route to serve media files
@flask_app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory('media', filename)

@flask_app.route("/edit_user/<chat_id>", methods=["GET", "POST"])
def edit_user(chat_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    user = get_user_by_id(chat_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("dashboard"))
    # Calculate days left
    subscription_end = user[3]
    days_left = ""
    if subscription_end:
        try:
            end_date = datetime.strptime(subscription_end, "%Y-%m-%d").date()
            today = datetime.today().date()
            days_left = (end_date - today).days
        except Exception:
            days_left = "?"
    if request.method == "POST":
        new_name = request.form.get("name")
        if not new_name:
            flash("Name is required.", "danger")
            return render_template("edit_user.html", user=user, days_left=days_left)
        update_user_name(chat_id, new_name)
        flash("User updated successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("edit_user.html", user=user, days_left=days_left)

# -------------------- Run Flask --------------------
def run_flask():
    flask_app.run(host="0.0.0.0", port=5001)