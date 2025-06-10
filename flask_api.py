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
    get_user_by_id,
    get_all_pending_users,
    approve_user_db,
    decline_user_db,
)

from telegram import Bot, ReplyKeyboardMarkup
import asyncio
from datetime import datetime
from handlers.admin_edit import _send_user_status_notification

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)

flask_app = Flask("bot_api" )
flask_app.secret_key = "your_secret_key"  # Change this in production

# User Reply Keyboard Definition (copied from handlers/start.py)
# This is no longer needed here as it's handled by _send_user_status_notification
# USER_REPLY_KEYBOARD = [
#     ["📋 Mes Infos", "🤖 Assistant AI"],
#     ["🧠 Historique AI", "🔄 Renouveler"]
# ]
# USER_MARKUP = ReplyKeyboardMarkup(USER_REPLY_KEYBOARD, resize_keyboard=True)

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
            if str(admin[0]) == chat_id and admin[1] == name:
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
        subscription_end = user[3]  # (chat_id, name, subscription_start, subscription_end, status)
        status = user[4] # Get the status from the original user tuple
        days_left = ""
        if subscription_end:
            try:
                end_date = datetime.strptime(subscription_end, "%Y-%m-%d").date()
                today = datetime.today().date()
                days_left = (end_date - today).days
            except Exception:
                days_left = "?"
        # Ensure the order is: chat_id, name, sub_start, sub_end, days_left, status
        users_with_days.append((user[0], user[1], user[2], user[3], days_left, status))

    pending_users = get_all_pending_users()

    return render_template(
        "dashboard.html",
        users=users_with_days,
        admins=admins,
        broadcasts_sent=broadcasts_sent,
        pending_approvals=pending_approvals,
        pending_users=pending_users,
        admin_name=session.get("admin_name")
    )

# -------------------- Broadcast Page Route --------------------
@flask_app.route("/broadcast", methods=["GET"])
def broadcast_page():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    pending_approvals = get_pending_approvals_count()
    return render_template("broadcast.html", admin_name=session.get("admin_name"), pending_approvals=pending_approvals)

# -------------------- Add Admin Page Route --------------------
@flask_app.route("/add_admin", methods=["GET"])
def add_admin_page():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    pending_approvals = get_pending_approvals_count()
    return render_template("add_admin.html", admin_name=session.get("admin_name"), pending_approvals=pending_approvals)

# -------------------- Pending Approvals Page Route --------------------
@flask_app.route("/pending_approvals", methods=["GET"])
def pending_approvals_page():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    pending_users = get_all_pending_users()
    print(f"Pending Users: {pending_users}") # Temporarily print pending users
    pending_approvals = get_pending_approvals_count()
    return render_template("pending_approvals.html", pending_users=pending_users, admin_name=session.get("admin_name"), pending_approvals=pending_approvals)

# -------------------- Broadcast Route --------------------
@flask_app.route("/broadcast", methods=["POST"])
def api_broadcast():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    
    message = request.form.get("message")
    photo = request.files.get("photo")
    
    if not message and not photo:
        flash("Please provide either a message or a photo for broadcast.", "danger")
        pending_approvals = get_pending_approvals_count() # Fetch for re-render
        return render_template("broadcast.html", admin_name=session.get("admin_name"), pending_approvals=pending_approvals)

    users = get_all_approved_users()
    sent_count = 0
    
    for chat_id, name in users:
        try:
            if photo:
                # Save photo temporarily
                photo_path = os.path.join("media", "temp_broadcast.jpg")
                photo.save(photo_path)
                # Send photo with caption if message exists
                with open(photo_path, "rb") as photo_file:
                    asyncio.run(bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file,
                        caption=message if message else None
                    ))
                # Clean up temporary file
                os.remove(photo_path)
            else:
                asyncio.run(bot.send_message(chat_id=chat_id, text=message))
            sent_count += 1
            print(f"Message sent to {chat_id}")
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

    save_broadcast(message or "Photo broadcast", sent_count)
    flash(f"Broadcast sent to {sent_count} users!", "success")
    pending_approvals = get_pending_approvals_count() # Fetch for re-render
    return render_template("broadcast.html", admin_name=session.get("admin_name"), pending_approvals=pending_approvals)

# -------------------- Add Admin Route --------------------
@flask_app.route("/add_admin", methods=["POST"])
def add_admin_route():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
        
    chat_id = request.form.get("chat_id")
    name = request.form.get("name")
    
    if not chat_id or not name:
        flash("Both Chat ID and Name are required.", "danger")
        pending_approvals = get_pending_approvals_count() # Fetch for re-render
        return render_template("add_admin.html", admin_name=session.get("admin_name"), pending_approvals=pending_approvals)
        
    try:
        add_admin(chat_id, name)
        flash("Admin added successfully!", "success")
    except Exception as e:
        flash(f"Failed to add admin: {str(e)}", "danger")
    
    pending_approvals = get_pending_approvals_count() # Fetch for re-render
    return render_template("add_admin.html", admin_name=session.get("admin_name"), pending_approvals=pending_approvals)

# -------------------- Approve User Route --------------------
@flask_app.route("/approve_user/<int:chat_id>")
def approve_user(chat_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    try:
        approve_user_db(chat_id)
        # Send Telegram message to user using the unified helper
        asyncio.run(_send_user_status_notification(chat_id, bot, "approve"))
        flash(f"User {chat_id} approved successfully!", "success")
    except Exception as e:
        flash(f"Failed to approve user {chat_id}: {str(e)}", "danger")
    # Redirect back to pending approvals page
    pending_users = get_all_pending_users() # Re-fetch pending users after action
    pending_approvals = get_pending_approvals_count() # Re-fetch pending approvals for sidebar
    return render_template("pending_approvals.html", pending_users=pending_users, admin_name=session.get("admin_name"), pending_approvals=pending_approvals)

# -------------------- Decline User Route --------------------
@flask_app.route("/decline_user/<int:chat_id>")
def decline_user(chat_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    try:
        decline_user_db(chat_id)
        # Send Telegram message to user using the unified helper
        asyncio.run(_send_user_status_notification(chat_id, bot, "decline"))
        flash(f"User {chat_id} declined and removed.", "info")
    except Exception as e:
        flash(f"Failed to decline user {chat_id}: {str(e)}", "danger")
    # Redirect back to pending approvals page
    pending_users = get_all_pending_users() # Re-fetch pending users after action
    pending_approvals = get_pending_approvals_count() # Re-fetch pending approvals for sidebar
    return render_template("pending_approvals.html", pending_users=pending_users, admin_name=session.get("admin_name"), pending_approvals=pending_approvals)

# -------------------- Remove Admin Route --------------------
@flask_app.route("/remove_admin/<int:chat_id>")
def remove_admin_route(chat_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    if str(session.get("admin_id")) == str(chat_id):
        flash("You cannot remove yourself as an admin.", "danger")
        # Ensure pending_approvals is passed even on this redirect/render
        pending_approvals = get_pending_approvals_count()
        return render_template("dashboard.html", 
                               users=get_all_users(), 
                               admins=get_all_admins(), 
                               broadcasts_sent=get_broadcast_count(), 
                               pending_approvals=pending_approvals, 
                               pending_users=get_all_pending_users(), 
                               admin_name=session.get("admin_name"))
    try:
        remove_admin(chat_id)
        flash("Admin removed successfully!", "success")
    except Exception as e:
        flash(f"Failed to remove admin: {str(e)}", "danger")
    pending_approvals = get_pending_approvals_count() # Fetch for re-render
    return render_template("dashboard.html", 
                           users=get_all_users(), 
                           admins=get_all_admins(), 
                           broadcasts_sent=get_broadcast_count(), 
                           pending_approvals=pending_approvals, 
                           pending_users=get_all_pending_users(), 
                           admin_name=session.get("admin_name"))

@flask_app.route("/remove_user/<chat_id>")
def remove_user_route(chat_id):
    remove_user(chat_id)  # Implement this function in database.py
    flash("User removed successfully!", "success")
    pending_approvals = get_pending_approvals_count() # Fetch for re-render
    return render_template("dashboard.html", 
                           users=get_all_users(), 
                           admins=get_all_admins(), 
                           broadcasts_sent=get_broadcast_count(), 
                           pending_approvals=pending_approvals, 
                           pending_users=get_all_pending_users(), 
                           admin_name=session.get("admin_name"))

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

# -------------------- Edit User Route --------------------
@flask_app.route("/edit_user/<chat_id>", methods=["GET", "POST"])
def edit_user(chat_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    # Fetch pending approvals count for the sidebar notification badge
    pending_approvals = get_pending_approvals_count()

    if request.method == "POST":
        new_name = request.form.get("name")
        if not new_name:
            flash("Name cannot be empty!", "danger")
            return redirect(url_for("edit_user", chat_id=chat_id))
        try:
            update_user_name(chat_id, new_name)
            flash("User updated successfully!", "success")
        except Exception as e:
            flash(f"Error updating user: {e}", "danger")
        return redirect(url_for("dashboard"))
    else:
        user = get_user_by_id(chat_id)
        if user:
            subscription_end = user[3]  # (chat_id, name, subscription_start, subscription_end)
            days_left = ""
            if subscription_end:
                try:
                    end_date = datetime.strptime(subscription_end, "%Y-%m-%d").date()
                    today = datetime.today().date()
                    days_left = (end_date - today).days
                except Exception:
                    days_left = "?"
            return render_template("edit_user.html", user=user, days_left=days_left, admin_name=session.get("admin_name"), pending_approvals=pending_approvals)
        else:
            flash("User not found.", "danger")
            return redirect(url_for("dashboard"))

# -------------------- Run Flask --------------------
def run_flask():
    flask_app.run(host="0.0.0.0", port=5001)