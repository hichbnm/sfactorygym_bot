from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Union
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
    get_user_name,
    get_all_approved_users
)
from telegram import Bot
import asyncio
from datetime import datetime
from handlers.admin_edit import _send_user_status_notification
from itsdangerous import URLSafeSerializer
from dotenv import load_dotenv
import sqlite3
load_dotenv()
app = FastAPI(title="S Factory Gym Bot")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# Templates
templates = Jinja2Templates(directory="templates")

# Session management
SECRET_KEY = "your-secret-key-here"  # Change this in production
serializer = URLSafeSerializer(SECRET_KEY)

# Bot initialization
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

# Flash message handling
def set_flash_message(response: Response, message: str, category: str = "error"):
    session_data = {}
    if hasattr(response, "cookies"):
        session_data = get_session(response)
    if "flash_messages" not in session_data:
        session_data["flash_messages"] = []
    session_data["flash_messages"].append({"message": message, "category": category})
    set_session(response, session_data)

def get_flash_messages(request: Request) -> List[Dict[str, str]]:
    session = get_session(request)
    messages = session.get("flash_messages", [])
    return messages

# Session management functions
def set_session(response: Response, data: dict):
    session_data = serializer.dumps(data)
    response.set_cookie(
        key="session",
        value=session_data,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=3600  # 1 hour
    )

def get_session(request_or_response: Union[Request, Response]) -> dict:
    if isinstance(request_or_response, Request):
        session_data = request_or_response.cookies.get("session")
    else:
        session_data = request_or_response.cookies.get("session") if hasattr(request_or_response, "cookies") else None
    
    if session_data:
        try:
            return serializer.loads(session_data)
        except:
            return {}
    return {}

# Dependency for checking admin authentication
async def get_current_admin(request: Request):
    session = get_session(request)
    if not session.get("admin_logged_in"):
        return None
    return session.get("admin_id")

# Login route
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    session = get_session(request)
    if session.get("admin_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    
    # Get flash messages and clear them from session
    flash_messages = get_flash_messages(request)
    if flash_messages:
        # Create a response to clear flash messages
        response = templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "flash_messages": flash_messages
            }
        )
        session["flash_messages"] = []
        set_session(response, session)
        return response
    
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "flash_messages": []
        }
    )

@app.post("/login")
async def login(
    response: Response,
    chat_id: str = Form(...),
    name: str = Form(...)
):
    admins = get_all_admins()
    for admin in admins:
        if str(admin[0]) == chat_id and admin[1] == name:
            session_data = {
                "admin_logged_in": True,
                "admin_id": chat_id,
                "admin_name": name
            }
            response = RedirectResponse(url="/", status_code=303)
            set_session(response, session_data)
            return response
    
    # Invalid credentials
    response = RedirectResponse(url="/login", status_code=303)
    set_flash_message(response, "Invalid Admin ID or Name.")
    return response

# Dashboard route
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    session = get_session(request)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    users = get_all_users()
    admins = get_all_admins()
    broadcasts_sent = get_broadcast_count()
    pending_approvals = get_pending_approvals_count()

    # Calculate days left for each user
    users_with_days = []
    for user in users:
        subscription_end = user[3]
        status = user[4]
        days_left = ""
        if subscription_end:
            try:
                end_date = datetime.strptime(subscription_end, "%Y-%m-%d").date()
                today = datetime.today().date()
                days_left = (end_date - today).days
            except Exception:
                days_left = "?"
        users_with_days.append((user[0], user[1], user[2], user[3], days_left, status))

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "users": users_with_days,
            "admins": admins,
            "broadcasts_sent": broadcasts_sent,
            "pending_approvals": pending_approvals,
            "admin_name": session.get("admin_name"),
            "flash_messages": get_flash_messages(request)
        }
    )

# Logout route
@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response

# Pending Approvals route
@app.get("/pending_approvals", response_class=HTMLResponse)
async def pending_approvals_page(request: Request):
    session = get_session(request)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    pending_users = get_all_pending_users()
    pending_approvals = get_pending_approvals_count()
    return templates.TemplateResponse(
        "pending_approvals.html",
        {
            "request": request,
            "pending_users": pending_users,
            "admin_name": session.get("admin_name"),
            "pending_approvals": pending_approvals,
            "flash_messages": get_flash_messages(request)
        }
    )

# Approve user route
@app.get("/approve_user/{chat_id}")
async def approve_user(chat_id: int, admin_id: str = Depends(get_current_admin)):
    try:
        approve_user_db(chat_id)
        await _send_user_status_notification(chat_id, bot, "approve")
        return RedirectResponse(url="/pending_approvals", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Decline user route
@app.get("/decline_user/{chat_id}")
async def decline_user(chat_id: int, admin_id: str = Depends(get_current_admin)):
    try:
        decline_user_db(chat_id)
        await _send_user_status_notification(chat_id, bot, "decline")
        return RedirectResponse(url="/pending_approvals", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Broadcast route
@app.get("/broadcast", response_class=HTMLResponse)
async def broadcast_page(request: Request):
    session = get_session(request)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    # Get flash messages and clear them from session
    flash_messages = get_flash_messages(request)
    if flash_messages:
        # Create a response to clear flash messages
        response = templates.TemplateResponse(
            "broadcast.html",
            {
                "request": request,
                "admin_name": session.get("admin_name"),
                "flash_messages": flash_messages,
                "pending_approvals": get_pending_approvals_count(),
                "users": get_all_approved_users()  # Add users list for selection
            }
        )
        session["flash_messages"] = []
        set_session(response, session)
        return response

    return templates.TemplateResponse(
        "broadcast.html",
        {
            "request": request,
            "admin_name": session.get("admin_name"),
            "flash_messages": [],
            "pending_approvals": get_pending_approvals_count(),
            "users": get_all_approved_users()  # Add users list for selection
        }
    )

# Broadcast POST route
@app.post("/broadcast")
async def broadcast_post(
    request: Request,
    message: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    recipient_type: str = Form(...),
    selected_users: Optional[List[str]] = Form(None)
):
    print("Starting broadcast process...")  # Debug log
    session = get_session(request)
    if not session.get("admin_logged_in"):
        print("User not logged in")  # Debug log
        return RedirectResponse(url="/login", status_code=303)

    try:
        print(f"Broadcast parameters: message={message}, recipient_type={recipient_type}, selected_users={selected_users}")  # Debug log
        
        # Save the broadcast message
        save_broadcast(message, session.get("admin_id"))
        print("Broadcast message saved to database")  # Debug log

        # Get recipients based on selection
        if recipient_type == "all":
            users = get_all_approved_users()
            print(f"Broadcasting to all users. Found {len(users)} approved users: {users}")  # Debug log
        else:
            if not selected_users:
                print("No users selected")  # Debug log
                raise ValueError("Please select at least one user")
            users = [(user_id, get_user_name(user_id)) for user_id in selected_users]
            print(f"Broadcasting to selected users: {users}")  # Debug log

        sent_count = 0
        failed_count = 0

        # Send message to each user
        for user in users:
            try:
                chat_id = str(user[0])  # Convert chat_id to string
                print(f"Attempting to send message to user {chat_id}")  # Debug log
                
                if photo and photo.filename:  # Check if photo was actually uploaded
                    print("Processing photo message")  # Debug log
                    # Save photo temporarily
                    photo_path = f"media/temp_{photo.filename}"
                    photo_content = await photo.read()
                    if photo_content:  # Check if photo has content
                        with open(photo_path, "wb") as f:
                            f.write(photo_content)
                        
                        # Send photo with caption
                        with open(photo_path, "rb") as f:
                            await bot.send_photo(
                                chat_id=chat_id,
                                photo=f,
                                caption=message
                            )
                        
                        # Clean up
                        os.remove(photo_path)
                    else:
                        print("Photo file is empty, sending text message instead")  # Debug log
                        await bot.send_message(
                            chat_id=chat_id,
                            text=message
                        )
                else:
                    print(f"Sending text message to {chat_id}")  # Debug log
                    # Send text message
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message
                    )
                sent_count += 1
                print(f"Successfully sent message to user {chat_id}")  # Debug log
            except Exception as e:
                failed_count += 1
                print(f"Error sending message to user {chat_id}: {str(e)}")  # Debug log
                print(f"Error type: {type(e)}")  # Debug log
                print(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")  # Debug log

        print(f"Broadcast complete. Sent: {sent_count}, Failed: {failed_count}")  # Debug log

        # Create response with preserved session
        response = RedirectResponse(url="/broadcast", status_code=303)
        success_message = f"Message sent successfully to {sent_count} users"
        if failed_count > 0:
            success_message += f". Failed: {failed_count}"
            
        set_session(response, {
            "admin_logged_in": True,
            "admin_id": session.get("admin_id"),
            "admin_name": session.get("admin_name"),
            "flash_messages": [{
                "message": success_message,
                "category": "success" if sent_count > 0 else "error"
            }]
        })
        return response

    except Exception as e:
        print(f"Broadcast error: {str(e)}")  # Debug log
        print(f"Error type: {type(e)}")  # Debug log
        print(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")  # Debug log
        response = RedirectResponse(url="/broadcast", status_code=303)
        set_session(response, {
            "admin_logged_in": True,
            "admin_id": session.get("admin_id"),
            "admin_name": session.get("admin_name"),
            "flash_messages": [{
                "message": f"Error sending broadcast: {str(e)}",
                "category": "error"
            }]
        })
        return response

# Add Admin route
@app.get("/add_admin", response_class=HTMLResponse)
async def add_admin_page(request: Request):
    session = get_session(request)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    # Get flash messages and clear them from session
    flash_messages = get_flash_messages(request)
    if flash_messages:
        # Create a response to clear flash messages
        response = templates.TemplateResponse(
            "add_admin.html",
            {
                "request": request,
                "admin_name": session.get("admin_name"),
                "flash_messages": flash_messages,
                "pending_approvals": get_pending_approvals_count()
            }
        )
        session["flash_messages"] = []
        set_session(response, session)
        return response

    return templates.TemplateResponse(
        "add_admin.html",
        {
            "request": request,
            "admin_name": session.get("admin_name"),
            "flash_messages": [],
            "pending_approvals": get_pending_approvals_count()
        }
    )

# Add Admin POST route
@app.post("/add_admin")
async def add_admin_post(
    request: Request,
    chat_id: str = Form(...),
    name: str = Form(...)
):
    session = get_session(request)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    try:
        # Validate input
        if not chat_id.strip() or not name.strip():
            response = RedirectResponse(url="/add_admin", status_code=303)
            set_session(response, {
                "admin_logged_in": True,
                "admin_id": session.get("admin_id"),
                "admin_name": session.get("admin_name"),
                "flash_messages": [{
                    "message": "Chat ID and name cannot be empty.",
                    "category": "error"
                }]
            })
            return response

        # Try to add admin
        add_admin(chat_id, name)
        response = RedirectResponse(url="/add_admin", status_code=303)
        set_session(response, {
            "admin_logged_in": True,
            "admin_id": session.get("admin_id"),
            "admin_name": session.get("admin_name"),
            "flash_messages": [{
                "message": "Admin added successfully.",
                "category": "success"
            }]
        })
        return response
    except Exception as e:
        print(f"Add admin error: {str(e)}")  # Add logging
        error_message = str(e)
        if "datatype mismatch" in error_message.lower():
            error_message = "Invalid Chat ID format. Please enter a valid numeric Chat ID."
        
        response = RedirectResponse(url="/add_admin", status_code=303)
        set_session(response, {
            "admin_logged_in": True,
            "admin_id": session.get("admin_id"),
            "admin_name": session.get("admin_name"),
            "flash_messages": [{
                "message": error_message,
                "category": "error"
            }]
        })
        return response

# Remove Admin route
@app.get("/remove_admin/{chat_id}")
async def remove_admin_route(chat_id: int, admin_id: str = Depends(get_current_admin)):
    if str(admin_id) == str(chat_id):
        raise HTTPException(status_code=400, detail="You cannot remove yourself as an admin")
    try:
        remove_admin(chat_id)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Edit User route
@app.get("/edit_user/{chat_id}", response_class=HTMLResponse)
async def edit_user_page(
    request: Request,
    chat_id: int,
    admin_id: str = Depends(get_current_admin)
):
    session = get_session(request)
    user = get_user_by_id(chat_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription_end = user[3]
    days_left = ""
    if subscription_end:
        try:
            end_date = datetime.strptime(subscription_end, "%Y-%m-%d").date()
            today = datetime.today().date()
            days_left = (end_date - today).days
        except Exception:
            days_left = "?"
    
    pending_approvals = get_pending_approvals_count()
    
    # Get flash messages and clear them from session
    flash_messages = get_flash_messages(request)
    if flash_messages:
        # Create a response to clear flash messages
        response = templates.TemplateResponse(
            "edit_user.html",
            {
                "request": request,
                "user": user,
                "days_left": days_left,
                "admin_name": session.get("admin_name"),
                "pending_approvals": pending_approvals,
                "flash_messages": flash_messages
            }
        )
        session["flash_messages"] = []
        set_session(response, session)
        return response
    
    return templates.TemplateResponse(
        "edit_user.html",
        {
            "request": request,
            "user": user,
            "days_left": days_left,
            "admin_name": session.get("admin_name"),
            "pending_approvals": pending_approvals,
            "flash_messages": get_flash_messages(request)
        }
    )

@app.post("/edit_user/{chat_id}")
async def edit_user(
    request: Request,
    chat_id: int,
    name: str = Form(...),
    admin_id: str = Depends(get_current_admin)
):
    session = get_session(request)
    try:
        update_user_name(chat_id, name)
        response = RedirectResponse(url=f"/edit_user/{chat_id}", status_code=303)
        set_session(response, {
            "admin_logged_in": True,
            "admin_id": session.get("admin_id"),
            "admin_name": session.get("admin_name"),
            "flash_messages": [{
                "message": "User name updated successfully.",
                "category": "success"
            }]
        })
        return response
    except Exception as e:
        response = RedirectResponse(url=f"/edit_user/{chat_id}", status_code=303)
        set_session(response, {
            "admin_logged_in": True,
            "admin_id": session.get("admin_id"),
            "admin_name": session.get("admin_name"),
            "flash_messages": [{
                "message": f"Error updating user: {str(e)}",
                "category": "error"
            }]
        })
        return response

@app.post("/edit_user/{user_id}")
async def edit_user_post(
    response: Response,
    user_id: str,
    name: str = Form(...),
    subscription_end: str = Form(...)
):
    session = get_session(response)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    try:
        update_user_name(user_id, name, subscription_end)
        response = RedirectResponse(url="/", status_code=303)
        set_flash_message(response, "User updated successfully.", "success")
        return response
    except Exception as e:
        response = RedirectResponse(url=f"/edit_user/{user_id}", status_code=303)
        set_flash_message(response, f"Error updating user: {str(e)}")
        return response

# Remove User route
@app.get("/remove_user/{chat_id}")
async def remove_user_route(chat_id: int, admin_id: str = Depends(get_current_admin)):
    try:
        remove_user(chat_id)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove_user/{user_id}")
async def remove_user_route(
    response: Response,
    user_id: str
):
    session = get_session(response)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    try:
        remove_user(user_id)
        response = RedirectResponse(url="/", status_code=303)
        set_flash_message(response, "User removed successfully.", "success")
        return response
    except Exception as e:
        response = RedirectResponse(url="/", status_code=303)
        set_flash_message(response, f"Error removing user: {str(e)}")
        return response

# Approve User route
@app.post("/approve_user/{user_id}")
async def approve_user(
    response: Response,
    user_id: str
):
    session = get_session(response)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    try:
        approve_user_db(user_id)
        await _send_user_status_notification(user_id, "approved")
        response = RedirectResponse(url="/pending_approvals", status_code=303)
        set_flash_message(response, "User approved successfully.", "success")
        return response
    except Exception as e:
        response = RedirectResponse(url="/pending_approvals", status_code=303)
        set_flash_message(response, f"Error approving user: {str(e)}")
        return response

# Decline User route
@app.post("/decline_user/{user_id}")
async def decline_user(
    response: Response,
    user_id: str
):
    session = get_session(response)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    try:
        decline_user_db(user_id)
        await _send_user_status_notification(user_id, "declined")
        response = RedirectResponse(url="/pending_approvals", status_code=303)
        set_flash_message(response, "User declined successfully.", "success")
        return response
    except Exception as e:
        response = RedirectResponse(url="/pending_approvals", status_code=303)
        set_flash_message(response, f"Error declining user: {str(e)}")
        return response

# Remove Admin route
@app.post("/remove_admin/{admin_id}")
async def remove_admin_route(
    response: Response,
    admin_id: str
):
    session = get_session(response)
    if not session.get("admin_logged_in"):
        return RedirectResponse(url="/login", status_code=303)

    try:
        remove_admin(admin_id)
        response = RedirectResponse(url="/", status_code=303)
        set_flash_message(response, "Admin removed successfully.", "success")
        return response
    except Exception as e:
        response = RedirectResponse(url="/", status_code=303)
        set_flash_message(response, f"Error removing admin: {str(e)}")
        return response
