from telegram import Update
from telegram.ext import ContextTypes
from database import get_all_users, is_admin
import os

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return

    users = get_all_users()
    if not users:
        await update.message.reply_text("Aucun utilisateur inscrit.")
        return

    message = "📋 Liste des utilisateurs :\n\n"
    for chat_id, name in users:
        if chat_id == ADMIN_CHAT_ID:
            continue
        message += f"🆔 {chat_id} — 👤 {name}\n"

    await update.message.reply_text(message)
